from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import UserProfile
from django.core.validators import RegexValidator
from rest_framework.validators import UniqueValidator
import json


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['gender', 'birth_date', 'favorite_masterclasses', 'cart']
        read_only_fields = ['cart']


class LoginSerializer(serializers.Serializer):
    username = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def to_internal_value(self, data):
        import json
        # Если data — QueryDict с одним ключом, который похож на JSON-строку
        if isinstance(data, dict) and len(data) == 1:
            key = next(iter(data.keys()))
            try:
                json_data = json.loads(key)
                if isinstance(json_data, dict):
                    return super().to_internal_value(json_data)
            except json.JSONDecodeError:
                pass
        # Если data — строка (например, всё тело — JSON-строка)
        if isinstance(data, str):
            try:
                json_data = json.loads(data)
                if isinstance(json_data, dict):
                    return super().to_internal_value(json_data)
            except json.JSONDecodeError:
                pass
        # Если data — dict с одним ключом 'data', внутри которого JSON-строка
        if isinstance(data, dict) and 'data' in data and isinstance(data['data'], str):
            try:
                json_data = json.loads(data['data'])
                if isinstance(json_data, dict):
                    return super().to_internal_value(json_data)
            except json.JSONDecodeError:
                pass
        # Обычная обработка form-urlencoded
        if isinstance(data, dict) and all(isinstance(v, list) for v in data.values()):
            data = {k: v[0] if v else None for k, v in data.items()}
        return super().to_internal_value(data)


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
        print('DEBUG REGISTRATION DATA:', data)
        import json
        # Если data — QueryDict с одним ключом, который похож на JSON-строку
        if isinstance(data, dict) and len(data) == 1:
            key = next(iter(data.keys()))
            try:
                json_data = json.loads(key)
                if isinstance(json_data, dict):
                    return super().to_internal_value(json_data)
            except json.JSONDecodeError:
                pass
        # Если data — строка (например, всё тело — JSON-строка)
        if isinstance(data, str):
            try:
                json_data = json.loads(data)
                if isinstance(json_data, dict):
                    return super().to_internal_value(json_data)
            except json.JSONDecodeError:
                pass
        # Если data — dict с одним ключом 'data', внутри которого JSON-строка
        if isinstance(data, dict) and 'data' in data and isinstance(data['data'], str):
            try:
                json_data = json.loads(data['data'])
                if isinstance(json_data, dict):
                    return super().to_internal_value(json_data)
            except json.JSONDecodeError:
                pass
        # Обычная обработка form-urlencoded
        if isinstance(data, dict) and all(isinstance(v, list) for v in data.values()):
            data = {k: v[0] if v else None for k, v in data.items()}
        return super().to_internal_value(data)

    def validate_gender(self, value):
        gender_mapping = {
            'male': 'male',
            'Male': 'male',
            'M': 'male',
            'female': 'female',
            'Female': 'female',
            'F': 'female',
        }
        mapped = gender_mapping.get(value)
        if not mapped:
            raise serializers.ValidationError('Недопустимое значение пола. Используйте male/female или M/F.')
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