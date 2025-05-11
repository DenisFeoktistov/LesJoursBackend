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
            'title': 'Test Masterclass',
            'description': 'Test Description',
            'start_price': 100.00,
            'final_price': 90.00,
            'bucket_list': ['image1.jpg', 'image2.jpg'],
            'age_restriction': 18,
            'duration': 120
        }
        self.masterclass = MasterClass.objects.create(**self.masterclass_data)
        self.url = reverse('masterclass-list')

    def test_create_masterclass(self):
        # Create a new masterclass with a different title to avoid slug conflict
        new_masterclass_data = self.masterclass_data.copy()
        new_masterclass_data['title'] = 'Another Test Masterclass'
        response = self.client.post(self.url, new_masterclass_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MasterClass.objects.count(), 2)
        self.assertEqual(MasterClass.objects.get(title='Another Test Masterclass').slug, 'another-test-masterclass')

    def test_list_masterclasses(self):
        # Delete any existing masterclasses to ensure clean state
        MasterClass.objects.all().delete()
        # Create a single masterclass for testing
        MasterClass.objects.create(**self.masterclass_data)
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_masterclass(self):
        url = reverse('masterclass-detail', args=[self.masterclass.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.masterclass.title)

    def test_update_masterclass(self):
        url = reverse('masterclass-detail', args=[self.masterclass.id])
        updated_data = self.masterclass_data.copy()
        updated_data['title'] = 'Updated Masterclass'
        response = self.client.put(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Masterclass')

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
        # Try to create a masterclass with the same title (slug conflict)
        duplicate_data = self.masterclass_data.copy()
        duplicate_data['title'] = self.masterclass_data['title']  # Same title
        response = self.client.post(self.url, duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('slug', response.data)

    def test_create_masterclass_missing_required(self):
        # Missing title
        data = self.masterclass_data.copy()
        data.pop('title')
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)

    def test_create_masterclass_invalid_price(self):
        data = self.masterclass_data.copy()
        data['title'] = 'Unique Title for Invalid Price'
        data['start_price'] = -10
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('start_price', response.data)

    def test_partial_update_masterclass(self):
        url = reverse('masterclass-detail', args=[self.masterclass.id])
        response = self.client.patch(url, {'description': 'Partially updated'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.masterclass.refresh_from_db()
        self.assertEqual(self.masterclass.description, 'Partially updated')

    def test_filter_masterclasses(self):
        response = self.client.get(self.url + '?age_restriction=18')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_unauthenticated_access(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(self.url, self.masterclass_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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
            title='Test Masterclass',
            description='Test Description',
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