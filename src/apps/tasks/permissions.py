from rest_framework import permissions
from apps.tasks.models import TaskShare


class IsTaskOwner(permissions.BasePermission):    
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsTaskOwnerOrSharedWith(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.owner == request.user:
            return True
        
        try:
            share = TaskShare.objects.get(task=obj, shared_with=request.user)
            
            if request.method in permissions.SAFE_METHODS:
                return True
            
            return share.permission == TaskShare.Permission.EDIT
            
        except TaskShare.DoesNotExist:
            return False


class CanShareTask(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
