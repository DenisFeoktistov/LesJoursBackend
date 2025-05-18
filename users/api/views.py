from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model, authenticate
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserSerializer, UserProfileSerializer, RegistrationSerializer, LoginSerializer
from .permissions import IsProfileOwner
from ..models import UserProfile
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from datetime import datetime
from masterclasses.models import MasterClass
from masterclasses.api.serializers import MasterClassSerializer
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError

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
            400: "Bad Request",
            500: "Internal Server Error"
        }
    )
    def post(self, request):
        try:
            print("DEBUG: Registration request data:", request.data)
            serializer = RegistrationSerializer(data=request.data)
            if not serializer.is_valid():
                print("DEBUG: Validation errors:", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
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
        except serializers.ValidationError as e:
            print("DEBUG: Validation error:", str(e))
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("DEBUG: Unexpected error:", str(e))
            import traceback
            print("DEBUG: Traceback:", traceback.format_exc())
            return Response(
                {'error': f'Registration failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Login user",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="User logged in successfully",
                schema=LoginSerializer
            ),
            400: "Bad Request"
        }
    )
    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            user = authenticate(
                username=serializer.validated_data['username'].lower().strip(),
                password=serializer.validated_data['password']
            )
            
            if user is None:
                return Response(
                    {'error': 'Invalid password'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
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
            })
        except Exception as e:
            return Response(
                {'error': 'Invalid password'},
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

class CustomTokenRefreshView(APIView):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Refresh token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token')
            },
            required=['refresh']
        ),
        responses={
            200: openapi.Response(
                description="Token refreshed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description='New access token')
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    def post(self, request):
        # Извлекаем refresh токен из запроса, поддерживая разные форматы
        refresh_token = None
        
        # Проверяем все возможные источники данных
        sources = [
            # Form-data
            lambda: request.POST.get('refresh') if hasattr(request, 'POST') else None,
            # JSON в body
            lambda: request.data.get('refresh') if hasattr(request, 'data') and hasattr(request.data, 'get') else None,
            # JSON в виде словаря
            lambda: request.data.get('refresh') if isinstance(request.data, dict) else None,
            # Строка в body
            lambda: getattr(request, '_body', b'').decode('utf-8') if hasattr(request, '_body') else None
        ]
        
        # Пробуем извлечь токен из различных источников
        for source_func in sources:
            try:
                possible_token = source_func()
                if possible_token:
                    refresh_token = possible_token
                    break
            except:
                continue
        
        # Если токен - строка JSON
        if not refresh_token and isinstance(request.data, str):
            try:
                import json
                json_data = json.loads(request.data)
                refresh_token = json_data.get('refresh')
            except:
                pass
                
        # Если refresh_token - это строка JSON
        if refresh_token and isinstance(refresh_token, str) and refresh_token.startswith('{'):
            try:
                import json
                json_data = json.loads(refresh_token)
                if isinstance(json_data, dict) and 'refresh' in json_data:
                    refresh_token = json_data.get('refresh')
            except:
                pass
                
        # Проверяем наличие токена
        if not refresh_token:
            return Response({'refresh': ['Обязательное поле.']}, status=status.HTTP_400_BAD_REQUEST)
            
        # Обрабатываем токен
        try:
            token = RefreshToken(refresh_token)
            access_token = str(token.access_token)
            
            return Response({
                'access': access_token
            })
        except TokenError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, id):
        try:
            user = User.objects.get(id=id)
            profile = user.profile
            
            return Response({
                'id': user.id,
                'formatted_happy_birthday_date': profile.birth_date.strftime('%d.%m.%Y') if profile.birth_date else None,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone': profile.phone,
                'gender': {
                    'id': 1 if profile.gender == 'M' else 2,
                    'name': 'male' if profile.gender == 'M' else 'female'
                }
            })
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request, id):
        try:
            user = User.objects.get(id=id)
            profile = user.profile
            
            # Update user fields
            user.first_name = request.data.get('first_name', user.first_name)
            user.last_name = request.data.get('last_name', user.last_name)
            user.email = request.data.get('email', user.email)
            user.username = request.data.get('username', user.username)
            
            # Update profile fields
            gender = request.data.get('gender', profile.gender)
            if gender in ['M', 'F']:
                gender = 'male' if gender == 'M' else 'female'
            profile.gender = gender
            
            if 'date' in request.data:
                try:
                    profile.birth_date = datetime.strptime(request.data['date'], '%d.%m.%Y').date()
                except ValueError:
                    return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)
            
            user.save()
            profile.save()
            
            return Response({'message': 'User info updated successfully'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class UserLastSeenView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, id):
        try:
            user = User.objects.get(id=id)
            last_seen = user.profile.last_seen_masterclasses.all()
            serializer = MasterClassSerializer(last_seen, many=True)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request, id):
        try:
            user = User.objects.get(id=id)
            product_id = request.data.get('product_id')
            
            if not product_id:
                return Response({'error': 'Product ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                masterclass = MasterClass.objects.get(id=product_id)
            except MasterClass.DoesNotExist:
                return Response({'error': 'Masterclass not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Add to last seen
            user.profile.last_seen_masterclasses.add(masterclass)
            
            return Response({'message': 'Masterclass added to last seen'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, id):
        try:
            user = User.objects.get(id=id)
            old_password = request.data.get('old_password')
            new_password = request.data.get('new_password')
            
            if not old_password or not new_password:
                return Response({'error': 'Both old and new passwords are required'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            if not user.check_password(old_password):
                return Response({'error': 'Invalid old password'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(new_password)
            user.save()
            
            return Response({'message': 'Password changed successfully'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND) 