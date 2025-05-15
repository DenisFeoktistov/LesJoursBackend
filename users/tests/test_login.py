from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class LoginAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('login')
        
        # Create test user
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.user.profile.gender = 'M'
        self.user.profile.save()
        
        self.valid_payload = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }

    def test_login_success(self):
        """Test successful user login"""
        response = self.client.post(self.login_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user_id', response.data)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('gender', response.data)
        self.assertIn('username', response.data)
        self.assertIn('first_name', response.data)
        self.assertIn('last_name', response.data)
        
        # Verify response data
        self.assertEqual(response.data['username'], self.valid_payload['username'])
        self.assertEqual(response.data['first_name'], self.user.first_name)
        self.assertEqual(response.data['last_name'], self.user.last_name)
        self.assertEqual(response.data['gender'], self.user.profile.gender)

    def test_login_invalid_password(self):
        """Test login with invalid password"""
        payload = self.valid_payload.copy()
        payload['password'] = 'wrongpassword'
        
        response = self.client.post(self.login_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Invalid password')

    def test_login_nonexistent_user(self):
        """Test login with nonexistent user"""
        payload = {
            'username': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Invalid password')

    def test_login_missing_fields(self):
        """Test login with missing required fields"""
        # Remove required field
        payload = self.valid_payload.copy()
        del payload['password']
        
        response = self.client.post(self.login_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) 