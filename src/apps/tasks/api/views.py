from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.tasks.models import Task, TaskShare
from apps.tasks.filters import TaskFilter
from apps.tasks.permissions import (
    IsTaskOwnerOrSharedWith,
    CanShareTask
)
from .serializers import (
    TaskSerializer,
    TaskCreateUpdateSerializer,
    TaskListSerializer,
    TaskShareSerializer,
    TaskShareCreateSerializer,
    TaskErrorResponseSerializer
)


class TaskViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsTaskOwnerOrSharedWith]
    filterset_class = TaskFilter
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'deadline', 'priority', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Task.objects.none()
        
        user = self.request.user
        
        owned_tasks = Q(owner=user)
        
        shared_tasks = Q(shares__shared_with=user)
        
        return Task.objects.filter(
            owned_tasks | shared_tasks
        ).select_related('owner').distinct()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TaskCreateUpdateSerializer
        return TaskSerializer
    
    @extend_schema(
        summary='List tasks',
        description='Get a list of tasks owned by or shared with the authenticated user. Supports filtering, search, and pagination.',
        parameters=[
            OpenApiParameter(
                name='status',
                description='Filter by status (new, in_progress, done)',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='priority',
                description='Filter by priority (low, medium, high)',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='search',
                description='Search in title and description',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='limit',
                description='Number of results to return per page',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='offset',
                description='The initial index from which to return the results',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='ordering',
                description='Which field to use when ordering the results (prefix with - for descending)',
                required=False,
                type=str
            ),
        ],
        responses={
            200: TaskListSerializer(many=True),
            401: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Authentication required'
            ),
        },
        tags=['Tasks']
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary='Create task',
        description='Create a new task. The authenticated user will be set as the owner.',
        request=TaskCreateUpdateSerializer,
        responses={
            201: TaskSerializer,
            400: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Validation error'
            ),
            401: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Authentication required'
            ),
        },
        tags=['Tasks']
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            task = serializer.save(owner=request.user)
            response_serializer = TaskSerializer(task)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response({
            'detail': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary='Retrieve task',
        description='Get details of a specific task.',
        responses={
            200: TaskSerializer,
            401: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Authentication required'
            ),
            403: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Permission denied'
            ),
            404: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Task not found'
            ),
        },
        tags=['Tasks']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        summary='Update task',
        description='Update all fields of a task. Only owner or users with edit permission can update.',
        request=TaskCreateUpdateSerializer,
        responses={
            200: TaskSerializer,
            400: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Validation error'
            ),
            401: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Authentication required'
            ),
            403: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Permission denied'
            ),
            404: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Task not found'
            ),
        },
        tags=['Tasks']
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        
        if serializer.is_valid():
            task = serializer.save()
            response_serializer = TaskSerializer(task)
            return Response(response_serializer.data)
        
        return Response({
            'detail': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary='Partial update task',
        description='Update specific fields of a task. Only owner or users with edit permission can update.',
        request=TaskCreateUpdateSerializer,
        responses={
            200: TaskSerializer,
            400: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Validation error'
            ),
            401: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Authentication required'
            ),
            403: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Permission denied'
            ),
            404: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Task not found'
            ),
        },
        tags=['Tasks']
    )
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            task = serializer.save()
            response_serializer = TaskSerializer(task)
            return Response(response_serializer.data)
        
        return Response({
            'detail': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary='Delete task',
        description='Delete a task. Only the owner can delete tasks.',
        responses={
            204: OpenApiResponse(description='Task deleted successfully'),
            401: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Authentication required'
            ),
            403: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Permission denied - only owner can delete'
            ),
            404: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Task not found'
            ),
        },
        tags=['Tasks']
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if instance.owner != request.user:
            return Response({
                'detail': 'Only task owner can delete tasks'
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @extend_schema(
        summary='Share task',
        description='Share a task with another user. Only the task owner can share tasks.',
        request=TaskShareCreateSerializer,
        responses={
            201: TaskShareSerializer,
            400: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Validation error'
            ),
            401: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Authentication required'
            ),
            403: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Permission denied - only owner can share'
            ),
            404: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Task not found'
            ),
        },
        tags=['Tasks']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanShareTask])
    def share(self, request, pk=None):
        task = self.get_object()
        serializer = TaskShareCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'detail': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from apps.users.models import User
        
        shared_with_email = serializer.validated_data['shared_with_email']
        permission = serializer.validated_data['permission']
        
        try:
            shared_with_user = User.objects.get(email=shared_with_email)
        except User.DoesNotExist:
            return Response({
                'detail': 'User not found',
                'errors': {'shared_with_email': ['User with this email does not exist.']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if shared_with_user == request.user:
            return Response({
                'detail': 'Cannot share task with yourself',
                'errors': {'shared_with_email': ['You cannot share a task with yourself.']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        share, created = TaskShare.objects.update_or_create(
            task=task,
            shared_with=shared_with_user,
            defaults={'permission': permission}
        )
        
        response_serializer = TaskShareSerializer(share)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    @extend_schema(
        summary='List task shares',
        description='Get list of users this task is shared with. Only the task owner can view shares.',
        responses={
            200: TaskShareSerializer(many=True),
            401: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Authentication required'
            ),
            403: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Permission denied - only owner can view shares'
            ),
            404: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Task not found'
            ),
        },
        tags=['Tasks']
    )
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, CanShareTask])
    def shares(self, request, pk=None):
        task = self.get_object()
        shares = TaskShare.objects.filter(task=task).select_related('shared_with')
        serializer = TaskShareSerializer(shares, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary='Revoke task share',
        description='Revoke task access from a user. Only the task owner can revoke shares.',
        parameters=[
            OpenApiParameter(
                name='user_id',
                description='ID of the user to revoke access from',
                required=True,
                type=int,
                location=OpenApiParameter.PATH
            )
        ],
        responses={
            204: OpenApiResponse(description='Share revoked successfully'),
            401: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Authentication required'
            ),
            403: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Permission denied - only owner can revoke shares'
            ),
            404: OpenApiResponse(
                response=TaskErrorResponseSerializer,
                description='Task or share not found'
            ),
        },
        tags=['Tasks']
    )
    @action(
        detail=True,
        methods=['delete'],
        url_path='shares/(?P<user_id>[0-9]+)',
        permission_classes=[IsAuthenticated, CanShareTask]
    )
    def revoke_share(self, request, pk=None, user_id=None):
        task = self.get_object()
        
        try:
            share = TaskShare.objects.get(task=task, shared_with_id=user_id)
            share.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TaskShare.DoesNotExist:
            return Response({
                'detail': 'Share not found'
            }, status=status.HTTP_404_NOT_FOUND)
