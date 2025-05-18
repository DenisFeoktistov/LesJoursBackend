from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import UserProfile
from django.core.validators import RegexValidator
from rest_framework.validators import UniqueValidator


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['gender', 'birth_date', 'favorite_masterclasses', 'cart']
        read_only_fields = ['cart']


class LoginSerializer(serializers.Serializer):
    username = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    username = serializers.EmailField(validators=[
        UniqueValidator(
            queryset=get_user_model().objects.all(),
            message="This email is already registered."
        )
    ])
    phone = serializers.CharField(required=True)
    gender = serializers.CharField(required=True)
    is_mailing_list = serializers.BooleanField(required=True)

    class Meta:
        model = get_user_model()
        fields = ['username', 'password', 'first_name', 'last_name', 'phone', 'gender', 'is_mailing_list']

    def to_internal_value(self, data):
        # Handle form-urlencoded data
        if isinstance(data, dict) and all(isinstance(v, list) for v in data.values()):
            # Convert form data format to single values
            return {k: v[0] if v else None for k, v in data.items()}
        return super().to_internal_value(data)

    def validate_gender(self, value):
        gender_mapping = {
            'male': 'M',
            'Male': 'M',
            'M': 'M',
            'female': 'F',
            'Female': 'F',
            'F': 'F',
            'other': 'O',
            'Other': 'O',
            'O': 'O',
        }
        mapped = gender_mapping.get(value)
        if not mapped:
            raise serializers.ValidationError('Недопустимое значение пола. Используйте M, F, O или male/female/other.')
        return mapped

    def create(self, validated_data):
        phone = validated_data.pop('phone')
        gender = self.validate_gender(validated_data.pop('gender')) 
        is_mailing_list = validated_data.pop('is_mailing_list')
        
        user = get_user_model().objects.create_user(
            username=validated_data['username'].lower().strip(),
            email=validated_data['username'].lower().strip(),
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        
        # Явно создаём профиль, если он не был создан
        if not hasattr(user, 'profile'):
            UserProfile.objects.create(user=user)
        
        user.profile.gender = gender
        user.profile.phone = phone
        user.profile.is_mailing_list = is_mailing_list
        user.profile.save()
        
        return user


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = get_user_model()
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'password', 'profile']
        read_only_fields = ['id']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        return super().update(instance, validated_data) 