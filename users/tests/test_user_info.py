import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from users.models import UserProfile
from datetime import datetime

User = get_user_model()

class UserInfoAPITest(TestCase):
    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword',
            first_name='Иван',
            last_name='Иванов'
        )
        
        # Создаем профиль для пользователя
        self.profile = UserProfile.objects.get(user=self.user)
        self.profile.gender = 'male'
        self.profile.phone = '+7 999 123-45-67'
        self.profile.birth_date = datetime.strptime('01.01.1990', '%d.%m.%Y').date()
        self.profile.save()
        
        # Настраиваем клиент API
        self.client = APIClient()
        
        # Аутентифицируем пользователя
        self.client.force_authenticate(user=self.user)
        
        # URL для тестирования
        self.url = f'/api/user/user_info/{self.user.id}/'
    
    def test_get_user_info(self):
        """Тест получения информации о пользователе"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user.id)
        self.assertEqual(response.data['first_name'], 'Иван')
        self.assertEqual(response.data['last_name'], 'Иванов')
        self.assertEqual(response.data['email'], 'testuser@example.com')
        self.assertEqual(response.data['phone_number'], '+7 999 123-45-67')
        self.assertEqual(response.data['formatted_happy_birthday_date'], '01.01.1990')
        self.assertEqual(response.data['gender']['id'], 1)
        self.assertEqual(response.data['gender']['name'], 'M')
    
    def test_update_user_info(self):
        """Тест обновления информации о пользователе"""
        # Данные для обновления
        update_data = {
            'first_name': 'Петр',
            'last_name': 'Петров',
            'email': 'petrov@example.com',
            'username': 'petrov@example.com',
            'phone': '+7 999 987-65-43',
            'gender': 'female',
            'date': '15.05.1995'
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        # Проверяем статус ответа
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем обновленные данные в ответе
        self.assertEqual(response.data['first_name'], 'Петр')
        self.assertEqual(response.data['last_name'], 'Петров')
        self.assertEqual(response.data['email'], 'petrov@example.com')
        self.assertEqual(response.data['phone_number'], '+7 999 987-65-43')
        self.assertEqual(response.data['formatted_happy_birthday_date'], '15.05.1995')
        self.assertEqual(response.data['gender']['id'], 2)
        self.assertEqual(response.data['gender']['name'], 'F')
        
        # Проверяем, что данные действительно обновились в базе
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        
        self.assertEqual(self.user.first_name, 'Петр')
        self.assertEqual(self.user.last_name, 'Петров')
        self.assertEqual(self.user.email, 'petrov@example.com')
        self.assertEqual(self.user.username, 'petrov@example.com')
        self.assertEqual(self.profile.phone, '+7 999 987-65-43')
        self.assertEqual(self.profile.gender, 'female')
        self.assertEqual(self.profile.birth_date.strftime('%d.%m.%Y'), '15.05.1995')
    
    def test_update_user_with_M_F_gender(self):
        """Тест обновления информации о пользователе с гендером в формате M/F"""
        update_data = {
            'first_name': 'Алексей',
            'gender': 'M',
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Алексей')
        self.assertEqual(response.data['gender']['id'], 1)
        self.assertEqual(response.data['gender']['name'], 'M')
        
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.gender, 'male')
        
        # Проверяем смену на F
        update_data = {
            'gender': 'F',
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['gender']['id'], 2)
        self.assertEqual(response.data['gender']['name'], 'F')
        
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.gender, 'female')
    
    def test_invalid_date_format(self):
        """Тест обработки неверного формата даты"""
        update_data = {
            'date': '1995-05-15'  # Неверный формат, ожидается дд.мм.гггг
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Invalid date format')
    
    def test_unauthorized_access(self):
        """Тест доступа без аутентификации"""
        # Создаем новый клиент без аутентификации
        client = APIClient()
        
        response = client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        update_data = {'first_name': 'Неавторизован'}
        response = client.post(
            self.url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) 