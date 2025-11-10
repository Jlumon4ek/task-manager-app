from django_filters import rest_framework as filters
from apps.tasks.models import Task


class TaskFilter(filters.FilterSet):
    status = filters.ChoiceFilter(
        field_name='status',
        choices=Task.Status.choices,
        help_text='Filter by status (new, in_progress, done)'
    )
    
    priority = filters.ChoiceFilter(
        field_name='priority',
        choices=Task.Priority.choices,
        help_text='Filter by priority (low, medium, high)'
    )
        
    class Meta:
        model = Task
        fields = ['status', 'priority']
