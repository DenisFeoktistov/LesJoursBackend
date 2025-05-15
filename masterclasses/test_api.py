from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from .models import MasterClass, Event
from django.contrib.auth import get_user_model

User = get_user_model()


class MasterClassAPITest(TestCase):
    def setUp(self):
        # Clean up any existing data
        MasterClass.objects.all().delete()
        Event.objects.all().delete()
        
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.masterclass_data = {
            'name': 'Test Masterclass',
            'short_description': 'Test Description',
            'long_description': 'Test Long Description',
            'price': {
                'start_price': 100.00,
                'final_price': 90.00
            },
            'bucket_link': ['image1.jpg', 'image2.jpg'],
            'age_restriction': 18,
            'duration': 120,
            'parameters': {
                'Адрес': ['г. Москва, Климентовский переулок, 6'],
                'Контакты': ['+7 (983) 285-83-99'],
                'Возраст': ['12+'],
                'Продолжительность': ['2 часа'],
                'Материалы включены': ['Да'],
                'Подходит для новичков': ['Да'],
                'Количество участников': ['8']
            },
            'details': [
                'Сборка бенто-торта',
                'Выравнивание кремом',
                'Декорирование на ваш вкус'
            ]
        }
        self.masterclass = MasterClass.objects.create(
            name=self.masterclass_data['name'],
            short_description=self.masterclass_data['short_description'],
            long_description=self.masterclass_data['long_description'],
            start_price=self.masterclass_data['price']['start_price'],
            final_price=self.masterclass_data['price']['final_price'],
            bucket_link=self.masterclass_data['bucket_link'],
            age_restriction=self.masterclass_data['age_restriction'],
            duration=self.masterclass_data['duration'],
            parameters=self.masterclass_data['parameters'],
            details=self.masterclass_data['details']
        )
        self.url = reverse('masterclass-list')

    def test_create_masterclass(self):
        # Create a new masterclass with a different name to avoid slug conflict
        new_masterclass_data = self.masterclass_data.copy()
        new_masterclass_data['name'] = 'Another Test Masterclass'
        response = self.client.post(self.url, new_masterclass_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MasterClass.objects.count(), 2)
        self.assertEqual(MasterClass.objects.get(name='Another Test Masterclass').slug, 'another-test-masterclass')

    def test_list_masterclasses(self):
        # Delete any existing masterclasses to ensure clean state
        MasterClass.objects.all().delete()
        # Create a single masterclass for testing
        MasterClass.objects.create(
            name=self.masterclass_data['name'],
            short_description=self.masterclass_data['short_description'],
            start_price=self.masterclass_data['price']['start_price'],
            final_price=self.masterclass_data['price']['final_price'],
            bucket_link=self.masterclass_data['bucket_link'],
            age_restriction=self.masterclass_data['age_restriction'],
            duration=self.masterclass_data['duration']
        )
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn('in_wishlist', response.data['results'][0])
        self.assertFalse(response.data['results'][0]['in_wishlist'])

    def test_masterclass_in_wishlist(self):
        # Add masterclass to user's wishlist
        self.user.profile.favorite_masterclasses.add(self.masterclass)
        
        # Test list endpoint
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['results'][0]['in_wishlist'])
        
        # Test detail endpoint
        detail_url = reverse('masterclass-detail', args=[self.masterclass.id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['in_wishlist'])

    def test_masterclass_not_in_wishlist(self):
        # Ensure masterclass is not in wishlist
        self.user.profile.favorite_masterclasses.remove(self.masterclass)
        
        # Test list endpoint
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['results'][0]['in_wishlist'])
        
        # Test detail endpoint
        detail_url = reverse('masterclass-detail', args=[self.masterclass.id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['in_wishlist'])

    def test_unauthenticated_user_wishlist(self):
        # Test as unauthenticated user
        self.client.force_authenticate(user=None)
        
        # Test list endpoint
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['results'][0]['in_wishlist'])
        
        # Test detail endpoint
        detail_url = reverse('masterclass-detail', args=[self.masterclass.id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['in_wishlist'])

    def test_retrieve_masterclass(self):
        url = reverse('masterclass-detail', args=[self.masterclass.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.masterclass.name)
        self.assertIn('in_wishlist', response.data)
        self.assertFalse(response.data['in_wishlist'])

    def test_update_masterclass(self):
        url = reverse('masterclass-detail', args=[self.masterclass.id])
        updated_data = self.masterclass_data.copy()
        updated_data['name'] = 'Updated Masterclass'
        response = self.client.put(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Masterclass')
        self.assertIn('in_wishlist', response.data)

    def test_delete_masterclass(self):
        url = reverse('masterclass-detail', args=[self.masterclass.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(MasterClass.objects.count(), 0)

    def test_masterclass_events(self):
        url = reverse('masterclass-events', args=[self.masterclass.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_masterclass_duplicate_slug(self):
        # Try to create a masterclass with the same name (slug conflict)
        duplicate_data = self.masterclass_data.copy()
        duplicate_data['name'] = self.masterclass_data['name']  # Same name
        response = self.client.post(self.url, duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('slug', response.data)

    def test_create_masterclass_missing_required(self):
        # Missing name
        data = self.masterclass_data.copy()
        data.pop('name')
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)

    def test_create_masterclass_invalid_price(self):
        data = self.masterclass_data.copy()
        data['name'] = 'Unique Name for Invalid Price'
        data['price'] = {'start_price': -10, 'final_price': 90.00}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', response.data)
        self.assertIn('start_price', response.data['price'])

    def test_partial_update_masterclass(self):
        url = reverse('masterclass-detail', args=[self.masterclass.id])
        response = self.client.patch(url, {'short_description': 'Partially updated', 'price': {'start_price': 100.00, 'final_price': 90.00}}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.masterclass.refresh_from_db()
        self.assertEqual(self.masterclass.short_description, 'Partially updated')
        self.assertIn('in_wishlist', response.data)

    def test_filter_masterclasses(self):
        response = self.client.get(self.url + '?age_restriction=18')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)
        self.assertIn('in_wishlist', response.data['results'][0])

    def test_unauthenticated_access(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(self.url, self.masterclass_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_masterclass_events_with_events(self):
        # Add an event to the masterclass
        Event.objects.create(
            masterclass=self.masterclass,
            start_datetime=timezone.now(),
            available_seats=5
        )
        url = reverse('masterclass-events', args=[self.masterclass.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_toggle_wishlist_add(self):
        # Test adding to wishlist
        url = reverse('masterclass-toggle-wishlist', args=[self.masterclass.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['in_wishlist'])
        self.assertEqual(response.data['message'], 'Masterclass added to wishlist')
        
        # Verify it's actually in the wishlist
        self.assertTrue(self.masterclass in self.user.profile.favorite_masterclasses.all())

    def test_toggle_wishlist_remove(self):
        # First add to wishlist
        self.user.profile.favorite_masterclasses.add(self.masterclass)
        
        # Test removing from wishlist
        url = reverse('masterclass-toggle-wishlist', args=[self.masterclass.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['in_wishlist'])
        self.assertEqual(response.data['message'], 'Masterclass removed from wishlist')
        
        # Verify it's actually removed from wishlist
        self.assertFalse(self.masterclass in self.user.profile.favorite_masterclasses.all())

    def test_toggle_wishlist_unauthenticated(self):
        # Test as unauthenticated user
        self.client.force_authenticate(user=None)
        url = reverse('masterclass-toggle-wishlist', args=[self.masterclass.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_toggle_wishlist_nonexistent(self):
        # Test with non-existent masterclass
        url = reverse('masterclass-toggle-wishlist', args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class EventAPITest(TestCase):
    def setUp(self):
        # Clean up any existing data
        MasterClass.objects.all().delete()
        Event.objects.all().delete()
        
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.masterclass = MasterClass.objects.create(
            name='Test Masterclass',
            short_description='Test Description',
            start_price=100.00,
            final_price=90.00,
            duration=120
        )
        
        self.start_time = timezone.now()
        self.event_data = {
            'masterclass': self.masterclass.id,
            'start_datetime': self.start_time,
            'available_seats': 10
        }
        self.event = Event.objects.create(
            masterclass=self.masterclass,
            start_datetime=self.start_time,
            available_seats=10
        )
        self.url = reverse('event-list')

    def test_list_events(self):
        # Delete any existing events to ensure clean state
        Event.objects.all().delete()
        # Create a single event for testing
        event = Event.objects.create(
            masterclass=self.masterclass,
            start_datetime=self.start_time,
            available_seats=10
        )
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_event(self):
        new_event_data = self.event_data.copy()
        new_event_data['start_datetime'] = self.start_time + timedelta(hours=2)
        response = self.client.post(self.url, new_event_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Event.objects.count(), 2)

    def test_retrieve_event(self):
        url = reverse('event-detail', args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['available_seats'], self.event.available_seats)

    def test_update_event(self):
        url = reverse('event-detail', args=[self.event.id])
        updated_data = self.event_data.copy()
        updated_data['available_seats'] = 5
        response = self.client.put(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['available_seats'], 5)

    def test_partial_update_event(self):
        url = reverse('event-detail', args=[self.event.id])
        response = self.client.patch(url, {'available_seats': 7}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.event.refresh_from_db()
        self.assertEqual(self.event.available_seats, 7)

    def test_delete_event(self):
        url = reverse('event-detail', args=[self.event.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Event.objects.count(), 0) 