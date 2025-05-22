from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import Token

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['gender'] = str(user.profile.gender)
        token['user_id'] = user.id
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        access = refresh.access_token
        
        data = {
            'user_id': self.user.id,
            'access': str(access),
            'refresh': str(refresh),
            'gender': str(self.user.profile.gender),
            'username': self.user.username,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name
        }
        return data 