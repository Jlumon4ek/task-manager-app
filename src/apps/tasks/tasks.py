from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
import logging

from apps.tasks.models import Task
from shared.email import email_client  

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def check_task_deadlines(self) -> dict:
    try:
        now = timezone.now()
        twenty_four_hours_later = now + timedelta(hours=24)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        tasks_due_soon = Task.objects.filter(
            deadline__isnull=False,
            deadline__gt=now,
            deadline__lte=twenty_four_hours_later
        ).exclude(
            Q(created_at__gte=today_start) & 
            Q(created_at__lte=today_end) &
            Q(deadline__gte=today_start) &
            Q(deadline__lte=today_end)
        ).exclude(
            status=Task.Status.DONE
        ).select_related('owner').prefetch_related('shares__shared_with')
        
        tasks_count = tasks_due_soon.count()
        emails_sent = 0
        
        logger.info(f"Found {tasks_count} tasks with upcoming deadlines")
        
        for task in tasks_due_soon:
            time_remaining = task.deadline - now
            hours_remaining = int(time_remaining.total_seconds() / 3600)
            
            subject = f"Task Deadline Reminder: {task.title}"
            body = _build_reminder_email(task, hours_remaining)
            
            if email_client.send_email(task.owner.email, subject, body):
                emails_sent += 1
                logger.info(f"Sent deadline reminder to {task.owner.email}")
            
            shared_users_emails = [
                share.shared_with.email 
                for share in task.shares.select_related('shared_with')
            ]
            
            if shared_users_emails:
                result = email_client.send_bulk_email(shared_users_emails, subject, body)
                emails_sent += result['success']
                logger.info(f"Sent {result['success']} shared task reminders")
        
        return {
            'status': 'success',
            'tasks_processed': tasks_count,
            'emails_sent': emails_sent,
            'timestamp': now.isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error in check_task_deadlines: {str(exc)}")
        raise self.retry(exc=exc)


def _build_reminder_email(task, hours_remaining: int) -> str:
    return f"""
Hello!

This is a reminder that your task is due soon:

Task: {task.title}
Status: {task.get_status_display()}
Priority: {task.get_priority_display()}
Deadline: {task.deadline.strftime('%Y-%m-%d %H:%M UTC')}
Time Remaining: ~{hours_remaining} hours

{f'Description: {task.description}' if task.description else ''}

Please make sure to complete this task before the deadline.

Best regards,
Task Manager System
    """.strip()


@shared_task
def send_task_notification(task_id: int, notification_type: str, user_email: str) -> dict:
    try:
        task = Task.objects.select_related('owner').get(id=task_id)
        subject, body = _build_notification_email(task, notification_type)
        
        if email_client.send_email(user_email, subject, body):
            logger.info(f"Sent {notification_type} notification to {user_email}")
            return {'status': 'success', 'task_id': task_id, 'email': user_email}
        else:
            return {'status': 'error', 'error': 'Email send failed'}
        
    except Exception as exc:
        logger.error(f"Error sending notification: {str(exc)}")
        return {'status': 'error', 'error': str(exc)}


def _build_notification_email(task, notification_type: str) -> tuple:
    messages = {
        'task_created': (
            f"New Task Created: {task.title}",
            f"Task: {task.title}\nPriority: {task.get_priority_display()}"
        ),
        'task_updated': (
            f"Task Updated: {task.title}",
            f"Task: {task.title}\nStatus: {task.get_status_display()}"
        ),
        'task_shared': (
            f"Task Shared: {task.title}",
            f"Owner: {task.owner.email}\nTask: {task.title}"
        ),
        'task_completed': (
            f"Task Completed: {task.title}",
            f"Task: {task.title} has been completed"
        ),
    }
    
    return messages.get(
        notification_type,
        (f"Task Notification: {task.title}", f"Task: {task.title}")
    )