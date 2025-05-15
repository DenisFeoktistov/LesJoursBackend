from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

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
            'phone': '+7 916 114-92-27',
            'gender': 'M',
            'is_mailing_list': True
        }

    def test_registration_success(self):
        """Test successful user registration"""
        response = self.client.post(self.register_url, self.valid_payload)
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
        self.assertEqual(response.data['error'], 'Account with this email already exists')

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