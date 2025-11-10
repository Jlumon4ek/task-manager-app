from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    LogoutSerializer,
    TokenObtainResponseSerializer,
    TokenRefreshResponseSerializer,
    ErrorResponseSerializer
)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    @extend_schema(
        request=UserRegistrationSerializer,
        responses={
            201: OpenApiResponse(
                response=TokenObtainResponseSerializer,
                description='User successfully registered'
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Validation error'
            ),
        },
        tags=['Authentication'],
        summary='Register a new user',
        description='Register a new user with email and password. Returns JWT tokens upon successful registration.'
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'detail': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    @extend_schema(
        request=UserLoginSerializer,
        responses={
            200: OpenApiResponse(
                response=TokenObtainResponseSerializer,
                description='Successfully authenticated'
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Invalid credentials'
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Authentication failed'
            ),
        },
        tags=['Authentication'],
        summary='Login user',
        description='Authenticate user with email and password. Returns JWT access and refresh tokens.'
    )
    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            'detail': 'Authentication failed',
            'errors': serializer.errors
        }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    @extend_schema(
        request=LogoutSerializer,
        responses={
            200: OpenApiResponse(
                description='Successfully logged out'
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Invalid token'
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Authentication required'
            ),
        },
        tags=['Authentication'],
        summary='Logout user',
        description='Logout user by blacklisting the refresh token. Requires authentication.'
    )
    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    'detail': 'Successfully logged out'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'detail': 'Invalid or expired token',
                    'errors': {'refresh': [str(e)]}
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'detail': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'refresh': {
                        'type': 'string',
                        'description': 'Refresh token'
                    }
                },
                'required': ['refresh']
            }
        },
        responses={
            200: OpenApiResponse(
                response=TokenRefreshResponseSerializer,
                description='Token successfully refreshed'
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Invalid token'
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Token expired or invalid'
            ),
        },
        tags=['Authentication'],
        summary='Refresh access token',
        description='Get a new access token using a valid refresh token.'
    )
    def post(self, request):
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response({
                'detail': 'Refresh token is required',
                'errors': {'refresh': ['This field is required.']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'detail': 'Invalid or expired refresh token',
                'errors': {'refresh': [str(e)]}
            }, status=status.HTTP_401_UNAUTHORIZED)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=UserSerializer,
                description='Current user information'
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Authentication required'
            ),
        },
        tags=['Users'],
        summary='Get current user',
        description='Get information about the currently authenticated user.'
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
