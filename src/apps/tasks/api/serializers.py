from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from apps.tasks.models import Task, TaskShare
from apps.users.api.serializers import UserSerializer


class TaskSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'status',
            'priority',
            'deadline',
            'owner',
            'is_overdue',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at', 'is_overdue']
    
    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['is_overdue'] = instance.is_overdue()
        return representation


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'status',
            'priority',
            'deadline'
        ]
    
    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()


class TaskListSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'status',
            'priority',
            'deadline',
            'owner_email',
            'is_overdue',
            'created_at'
        ]
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_overdue(self, obj) -> bool:
        return obj.is_overdue()


class TaskShareSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)
    shared_with = UserSerializer(read_only=True)
    shared_with_email = serializers.EmailField(write_only=True, required=False)
    
    class Meta:
        model = TaskShare
        fields = [
            'id',
            'task',
            'shared_with',
            'shared_with_email',
            'permission',
            'shared_at'
        ]
        read_only_fields = ['id', 'task', 'shared_with', 'shared_at']
    
    def validate_permission(self, value):
        if value not in [TaskShare.Permission.VIEW, TaskShare.Permission.EDIT]:
            raise serializers.ValidationError("Invalid permission value.")
        return value


class TaskShareCreateSerializer(serializers.Serializer):
    shared_with_email = serializers.EmailField(required=True)
    permission = serializers.ChoiceField(
        choices=TaskShare.Permission.choices,
        default=TaskShare.Permission.VIEW
    )
    
    def validate_shared_with_email(self, value):
        from apps.users.models import User
        
        try:
            User.objects.get(email=value.lower())
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        
        return value.lower()


class TaskErrorResponseSerializer(serializers.Serializer):
    detail = serializers.CharField(help_text="Error message")
    errors = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
        required=False,
        help_text="Field-specific errors"
    )