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
    phone = serializers.CharField(
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    gender = serializers.ChoiceField(choices=UserProfile.GENDER_CHOICES, required=True)
    is_mailing_list = serializers.BooleanField(required=True)

    class Meta:
        model = get_user_model()
        fields = ['username', 'password', 'first_name', 'last_name', 'phone', 'gender', 'is_mailing_list']

    def create(self, validated_data):
        phone = validated_data.pop('phone')
        gender = validated_data.pop('gender')
        is_mailing_list = validated_data.pop('is_mailing_list')
        
        user = get_user_model().objects.create_user(
            username=validated_data['username'].lower().strip(),
            email=validated_data['username'].lower().strip(),
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        
        # Update profile
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