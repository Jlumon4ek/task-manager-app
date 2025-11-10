from django.db import models
from django.conf import settings
from django.utils import timezone
from common.mixins import TimestampMixin

class Task(TimestampMixin, models.Model):
    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['-created_at']
        db_table = 'tasks'
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['owner', 'priority']),
            models.Index(fields=['deadline']),
            models.Index(fields=['-created_at']),
        ]


    class Status(models.TextChoices):
        NEW = 'new', 'New'
        IN_PROGRESS = 'in_progress', 'In Progress'
        DONE = 'done', 'Done'
    
    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
    
    title = models.CharField(
        max_length=255,
        verbose_name='Title',
        help_text='Task title'
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Description',
        help_text='Task description'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name='Status',
        help_text='Task status'
    )
    
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name='Priority',
        help_text='Task priority'
    )
    
    deadline = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Deadline',
        help_text='Task deadline'
    )
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_tasks',
        verbose_name='Owner',
        help_text='Task owner'
    )
    

    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def is_overdue(self):
        if self.deadline and self.status != self.Status.DONE:
            return timezone.now() > self.deadline
        return False
    
    def is_due_soon(self, hours=24):
        if self.deadline and self.status != self.Status.DONE:
            time_until_deadline = self.deadline - timezone.now()
            return 0 < time_until_deadline.total_seconds() <= (hours * 3600)
        return False


class TaskShare(models.Model):

    class Meta:
        verbose_name = 'Task Share'
        verbose_name_plural = 'Task Shares'
        unique_together = [['task', 'shared_with']]
        ordering = ['-shared_at']
        db_table = 'task_shares'
        indexes = [
            models.Index(fields=['shared_with', 'permission']),
            models.Index(fields=['task']),
        ]


    class Permission(models.TextChoices):
        VIEW = 'view', 'View Only'
        EDIT = 'edit', 'View and Edit'
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='shares',
        verbose_name='Task'
    )
    
    shared_with = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shared_tasks',
        verbose_name='Shared With'
    )
    
    permission = models.CharField(
        max_length=10,
        choices=Permission.choices,
        default=Permission.VIEW,
        verbose_name='Permission',
        help_text='Access permission level'
    )
    
    shared_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Shared At'
    )
    
    
    def __str__(self):
        return f"{self.task.title} shared with {self.shared_with.email} ({self.get_permission_display()})"
