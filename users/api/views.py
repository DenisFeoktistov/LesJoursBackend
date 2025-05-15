from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserSerializer, UserProfileSerializer, RegistrationSerializer
from .permissions import IsProfileOwner
from ..models import UserProfile
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class RegistrationView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Register a new user",
        request_body=RegistrationSerializer,
        responses={
            201: openapi.Response(
                description="User registered successfully",
                schema=RegistrationSerializer
            ),
            400: "Bad Request"
        }
    )
    def post(self, request):
        try:
            serializer = RegistrationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user_id': user.id,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'gender': user.profile.gender,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': 'Account with this email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all users",
        responses={
            200: openapi.Response(
                description="List of users",
                schema=UserSerializer(many=True)
            )
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new user",
        request_body=UserSerializer,
        responses={
            201: openapi.Response(
                description="User created successfully",
                schema=UserSerializer
            ),
            400: "Bad Request"
        }
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        Token.objects.create(user=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Get a specific user",
        responses={
            200: openapi.Response(
                description="User details",
                schema=UserSerializer
            ),
            404: "Not Found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a user",
        request_body=UserSerializer,
        responses={
            200: openapi.Response(
                description="User updated successfully",
                schema=UserSerializer
            ),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a user",
        request_body=UserSerializer,
        responses={
            200: openapi.Response(
                description="User partially updated successfully",
                schema=UserSerializer
            ),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a user",
        responses={
            204: "No Content",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get the current user's profile",
        responses={
            200: openapi.Response(
                description="User profile details",
                schema=UserProfileSerializer
            ),
            404: "Not Found"
        }
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfileOwner]

    @swagger_auto_schema(
        operation_description="List all user profiles",
        responses={
            200: openapi.Response(
                description="List of user profiles",
                schema=UserProfileSerializer(many=True)
            )
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new user profile",
        request_body=UserProfileSerializer,
        responses={
            201: openapi.Response(
                description="User profile created successfully",
                schema=UserProfileSerializer
            ),
            400: "Bad Request"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get a specific user profile",
        responses={
            200: openapi.Response(
                description="User profile details",
                schema=UserProfileSerializer
            ),
            404: "Not Found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a user profile",
        request_body=UserProfileSerializer,
        responses={
            200: openapi.Response(
                description="User profile updated successfully",
                schema=UserProfileSerializer
            ),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a user profile",
        request_body=UserProfileSerializer,
        responses={
            200: openapi.Response(
                description="User profile partially updated successfully",
                schema=UserProfileSerializer
            ),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a user profile",
        responses={
            204: "No Content",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def add_to_favorites(self, request, pk=None):
        user = self.get_object()
        masterclass_id = request.data.get('masterclass_id')
        if not masterclass_id:
            return Response(
                {'error': 'masterclass_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.profile.favorite_masterclasses.add(masterclass_id)
        return Response({'status': 'added to favorites'})

    @action(detail=True, methods=['post'])
    def remove_from_favorites(self, request, pk=None):
        user = self.get_object()
        masterclass_id = request.data.get('masterclass_id')
        if not masterclass_id:
            return Response(
                {'error': 'masterclass_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.profile.favorite_masterclasses.remove(masterclass_id)
        return Response({'status': 'removed from favorites'})

    @action(detail=True, methods=['get'])
    def favorites(self, request, pk=None):
        user = self.get_object()
        favorites = user.profile.favorite_masterclasses.all()
        serializer = MasterClassSerializer(favorites, many=True)
        return Response(serializer.data) 