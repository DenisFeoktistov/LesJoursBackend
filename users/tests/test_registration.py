from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from masterclasses.models import MasterClass

User = get_user_model()

class RegistrationAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.valid_payload = {
            'username': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '+79161149227',
            'gender': 'M',
            'is_mailing_list': True
        }

    def test_registration_success(self):
        """Test successful user registration"""
        response = self.client.post(self.register_url, self.valid_payload)
        print('DEBUG registration response:', response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user_id', response.data)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('gender', response.data)
        self.assertIn('username', response.data)
        self.assertIn('first_name', response.data)
        self.assertIn('last_name', response.data)
        
        # Verify user was created
        user = User.objects.get(email=self.valid_payload['username'])
        self.assertEqual(user.first_name, self.valid_payload['first_name'])
        self.assertEqual(user.last_name, self.valid_payload['last_name'])
        self.assertEqual(user.profile.gender, self.valid_payload['gender'])

    def test_registration_duplicate_email(self):
        """Test registration with existing email"""
        # Create user first
        User.objects.create_user(
            username=self.valid_payload['username'],
            email=self.valid_payload['username'],
            password=self.valid_payload['password']
        )
        
        # Try to register with same email
        response = self.client.post(self.register_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        self.assertIn('already registered', str(response.data['username'][0]))

    def test_registration_missing_fields(self):
        """Test registration with missing required fields"""
        # Remove required field
        payload = self.valid_payload.copy()
        del payload['phone']
        
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_invalid_gender(self):
        """Test registration with invalid gender"""
        payload = self.valid_payload.copy()
        payload['gender'] = 'INVALID'
        
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class TokenRefreshTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.refresh_url = reverse('token_refresh')
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )
        self.refresh_token = RefreshToken.for_user(self.user)

    def test_token_refresh_success(self):
        """Test successful token refresh"""
        response = self.client.post(self.refresh_url, {'refresh': str(self.refresh_token)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_token_refresh_invalid_token(self):
        """Test refresh with invalid token"""
        response = self.client.post(self.refresh_url, {'refresh': 'invalid_token'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh_missing_token(self):
        """Test refresh without token"""
        response = self.client.post(self.refresh_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UserInfoTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.profile = self.user.profile
        self.profile.gender = 'M'
        self.profile.save()
        
        self.token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.access_token}')
        
        self.user_info_url = reverse('user_info', kwargs={'id': self.user.id})

    def test_get_user_info_success(self):
        """Test successful user info retrieval"""
        response = self.client.get(self.user_info_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['first_name'], self.user.first_name)
        self.assertEqual(response.data['last_name'], self.user.last_name)
        self.assertEqual(response.data['gender']['name'], self.profile.gender)

    def test_update_user_info_success(self):
        """Test successful user info update"""
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
            'username': 'updated@example.com',
            'gender': 'F',
            'date': '01.01.2000'
        }
        response = self.client.post(self.user_info_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify updates
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, update_data['first_name'])
        self.assertEqual(self.user.last_name, update_data['last_name'])
        self.assertEqual(self.user.email, update_data['email'])
        self.assertEqual(self.profile.gender, update_data['gender'])
        self.assertEqual(self.profile.birth_date.strftime('%d.%m.%Y'), update_data['date'])

class LastSeenTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )
        self.masterclass = MasterClass.objects.create(
            name='Test Masterclass',
            short_description='Test Description',
            long_description='Test Long Description',
            start_price=1000,
            final_price=1000
        )
        
        self.token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.access_token}')
        
        self.last_seen_url = reverse('last_seen', kwargs={'id': self.user.id})

    def test_add_last_seen_success(self):
        """Test successful addition to last seen"""
        response = self.client.post(self.last_seen_url, {'product_id': self.masterclass.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.masterclass in self.user.profile.favorite_masterclasses.all() or self.masterclass in self.user.profile.last_seen_masterclasses.all())

    def test_get_last_seen_success(self):
        """Test successful retrieval of last seen items"""
        self.user.profile.last_seen_masterclasses.add(self.masterclass)
        response = self.client.get(self.last_seen_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.masterclass.id)

class ChangePasswordTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='oldpass123'
        )
        
        self.token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.access_token}')
        
        self.change_password_url = reverse('change_password', kwargs={'id': self.user.id})

    def test_change_password_success(self):
        """Test successful password change"""
        response = self.client.post(self.change_password_url, {
            'old_password': 'oldpass123',
            'new_password': 'newpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))

    def test_change_password_invalid_old_password(self):
        """Test password change with invalid old password"""
        response = self.client.post(self.change_password_url, {
            'old_password': 'wrongpass',
            'new_password': 'newpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) 