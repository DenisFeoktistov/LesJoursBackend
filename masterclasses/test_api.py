from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from .models import MasterClass, Event
from django.contrib.auth import get_user_model
from time import sleep

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
        new_masterclass = MasterClass.objects.get(name='Another Test Masterclass')
        self.assertEqual(new_masterclass.slug, f'another-test-masterclass-{new_masterclass.id}')

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
        detail_url = reverse('masterclass-detail', args=[self.masterclass.slug])
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
        detail_url = reverse('masterclass-detail', args=[self.masterclass.slug])
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
        detail_url = reverse('masterclass-detail', args=[self.masterclass.slug])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['in_wishlist'])

    def test_retrieve_masterclass(self):
        url = reverse('masterclass-detail', args=[self.masterclass.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.masterclass.name)
        self.assertIn('in_wishlist', response.data)
        self.assertFalse(response.data['in_wishlist'])

    def test_update_masterclass(self):
        url = reverse('masterclass-detail', args=[self.masterclass.slug])
        updated_data = self.masterclass_data.copy()
        updated_data['name'] = 'Updated Masterclass'
        response = self.client.put(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Masterclass')
        self.assertIn('in_wishlist', response.data)

    def test_delete_masterclass(self):
        url = reverse('masterclass-detail', args=[self.masterclass.slug])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(MasterClass.objects.count(), 0)

    def test_masterclass_events(self):
        url = reverse('masterclass-events', args=[self.masterclass.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_masterclass_duplicate_slug(self):
        # Try to create a masterclass with the same name (slug conflict)
        duplicate_data = self.masterclass_data.copy()
        duplicate_data['name'] = self.masterclass_data['name']  # Same name
        response = self.client.post(self.url, duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # Should succeed because ID is appended
        self.assertEqual(MasterClass.objects.count(), 2)
        # Verify that slugs are different due to ID
        slugs = MasterClass.objects.values_list('slug', flat=True)
        self.assertEqual(len(set(slugs)), 2)  # All slugs should be unique

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
        url = reverse('masterclass-detail', args=[self.masterclass.slug])
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
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # Should succeed because we allow any access

    def test_masterclass_events_with_events(self):
        # Add an event to the masterclass
        Event.objects.create(
            masterclass=self.masterclass,
            start_datetime=timezone.now(),
            available_seats=5
        )
        url = reverse('masterclass-events', args=[self.masterclass.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_toggle_wishlist_add(self):
        # Test adding to wishlist
        url = reverse('masterclass-toggle-wishlist', args=[self.masterclass.slug])
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
        url = reverse('masterclass-toggle-wishlist', args=[self.masterclass.slug])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['in_wishlist'])
        self.assertEqual(response.data['message'], 'Masterclass removed from wishlist')
        
        # Verify it's actually removed from wishlist
        self.assertFalse(self.masterclass in self.user.profile.favorite_masterclasses.all())

    def test_toggle_wishlist_unauthenticated(self):
        # Test as unauthenticated user
        self.client.force_authenticate(user=None)
        url = reverse('masterclass-toggle-wishlist', args=[self.masterclass.slug])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_toggle_wishlist_nonexistent(self):
        # Test with non-existent masterclass
        url = reverse('masterclass-toggle-wishlist', args=['non-existent-slug'])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_masterclasses_by_ids(self):
        # Create a second masterclass for testing
        second_masterclass = MasterClass.objects.create(
            name='Second Test Masterclass',
            short_description='Another test description',
            start_price=100.00,
            final_price=90.00,
            bucket_link='https://example.com/image2.jpg',
            age_restriction=18,
            duration=120
        )

        # Test with valid IDs
        url = reverse('masterclass-list-masterclasses')
        response = self.client.post(url, {'products': [self.masterclass.id, second_masterclass.id]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertIn('in_wishlist', response.data[0])
        self.assertIn('in_wishlist', response.data[1])
        
        # Verify response format
        first_masterclass = response.data[0]
        self.assertIn('id', first_masterclass)
        self.assertIn('price', first_masterclass)
        self.assertIn('start_price', first_masterclass['price'])
        self.assertIn('final_price', first_masterclass['price'])
        self.assertIn('short_description', first_masterclass)
        self.assertIn('slug', first_masterclass)
        self.assertIn('location', first_masterclass)
        self.assertIn('name', first_masterclass)
        self.assertIn('bucket_link', first_masterclass)

        # Test with empty products list
        response = self.client.post(url, {'products': []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

        # Test with non-existent IDs
        response = self.client.post(url, {'products': [99999, 99998]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        # Test with invalid request format
        response = self.client.post(url, {'invalid_key': [1, 2]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test with string IDs instead of integers
        response = self.client.post(url, {'products': ['1', '2']}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Test with mixed valid and invalid IDs
        response = self.client.post(url, {'products': [self.masterclass.id, 99999]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.masterclass.id)

        # Test with wishlist functionality
        self.user.profile.favorite_masterclasses.add(self.masterclass)
        response = self.client.post(url, {'products': [self.masterclass.id]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data[0]['in_wishlist'])

        # Test with unauthenticated user
        self.client.force_authenticate(user=None)
        response = self.client.post(url, {'products': [self.masterclass.id]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data[0]['in_wishlist'])

    def test_pagination(self):
        """Test that pagination returns correct number of items per page"""
        # Create 15 masterclasses
        for i in range(15):
            MasterClass.objects.create(
                name=f'Test Masterclass {i}',
                short_description=f'Test description {i}',
                start_price=100.00,
                final_price=90.00,
                bucket_link='https://example.com/image.jpg',
                age_restriction=18,
                duration=120
            )

        # Test first page
        url = reverse('masterclass-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 12)  # Should return 12 items
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        expected_count = MasterClass.objects.count()
        self.assertEqual(response.data['count'], expected_count)  # Total count should match

        # Test second page
        response = self.client.get(f"{url}?page=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), expected_count - 12)  # Остаток на второй странице
        self.assertIsNone(response.data['next'])  # No next page
        self.assertIsNotNone(response.data['previous'])  # Should have previous page

    def test_pagination_with_filters(self):
        """Test that pagination works correctly with filters"""
        # Create masterclasses with different prices
        for i in range(15):
            MasterClass.objects.create(
                name=f'Test Masterclass {i}',
                short_description=f'Test description {i}',
                start_price=100.00 + i,
                final_price=90.00 + i,
                bucket_link='https://example.com/image.jpg',
                age_restriction=18,
                duration=120
            )

        # Test pagination with price filter
        url = reverse('masterclass-list')
        response = self.client.get(f"{url}?final_price_min=95&final_price_max=100")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data['results']), 12)  # Should not exceed page size
        self.assertIn('count', response.data)
        self.assertIn('min_price', response.data)
        self.assertIn('max_price', response.data)

    def test_pagination_with_ordering(self):
        """Test that pagination works correctly with ordering"""
        # Create masterclasses with different prices
        for i in range(15):
            MasterClass.objects.create(
                name=f'Test Masterclass {i}',
                short_description=f'Test description {i}',
                start_price=100.00 + i,
                final_price=90.00 + i,
                bucket_link='https://example.com/image.jpg',
                age_restriction=18,
                duration=120
            )

        # Test pagination with ordering
        url = reverse('masterclass-list')
        response = self.client.get(f"{url}?ordering=final_price")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 12)  # First page should have 12 items
        
        # Verify ordering
        prices = [item['price']['final_price'] for item in response.data['results']]
        self.assertEqual(prices, sorted(prices))  # Should be in ascending order

    def test_filter_by_age(self):
        """Тест фильтрации мастер-классов по возрастному ограничению"""
        # Очищаем существующие мастер-классы перед тестом
        MasterClass.objects.all().delete()
        
        # Создаем мастер-классы с разными возрастными ограничениями
        mc1 = MasterClass.objects.create(
            name="МК для детей",
            short_description="Для маленьких",
            age_restriction=6,
            start_price=1000,
            final_price=1000
        )
        mc2 = MasterClass.objects.create(
            name="МК для подростков",
            short_description="Для средних",
            age_restriction=12,
            start_price=2000,
            final_price=2000
        )
        mc3 = MasterClass.objects.create(
            name="МК для старших",
            short_description="Для взрослых",
            age_restriction=16,
            start_price=3000,
            final_price=3000
        )

        # Проверяем фильтр по одному возрасту
        response = self.client.get(reverse('masterclass-list') + '?age=6')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], mc1.id)

        # Проверяем фильтр по нескольким возрастам
        response = self.client.get(reverse('masterclass-list') + '?age=6&age=12')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Сбрасываем между тестами
        self.client = APIClient()

    def test_filter_by_discount(self):
        """Тест фильтрации мастер-классов по наличию скидки"""
        # Очищаем существующие мастер-классы перед тестом
        MasterClass.objects.all().delete()
        
        # Создаем мастер-классы со скидкой и без
        mc1 = MasterClass.objects.create(
            name="МК со скидкой",
            short_description="Со скидкой",
            start_price=2000,
            final_price=1500
        )
        mc2 = MasterClass.objects.create(
            name="МК без скидки",
            short_description="Без скидки",
            start_price=2000,
            final_price=2000
        )

        # Проверяем фильтр по наличию скидки
        response = self.client.get(reverse('masterclass-list') + '?is_sale=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], mc1.id)

        # Проверяем фильтр по отсутствию скидки
        response = self.client.get(reverse('masterclass-list') + '?is_sale=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], mc2.id)
        
        # Сбрасываем между тестами
        self.client = APIClient()

    def test_filter_by_price(self):
        """Тест фильтрации мастер-классов по цене"""
        # Очищаем существующие мастер-классы перед тестом
        MasterClass.objects.all().delete()
        
        # Создаем мастер-классы с разными ценами
        mc1 = MasterClass.objects.create(
            name="МК дешевый",
            short_description="Дешевый",
            start_price=1000,
            final_price=1000
        )
        mc2 = MasterClass.objects.create(
            name="МК средний",
            short_description="Средний",
            start_price=3000,
            final_price=3000
        )
        mc3 = MasterClass.objects.create(
            name="МК дорогой",
            short_description="Дорогой",
            start_price=5000,
            final_price=5000
        )

        # Проверяем фильтр по минимальной цене
        response = self.client.get(reverse('masterclass-list') + '?price_min=2000')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Проверяем фильтр по максимальной цене
        response = self.client.get(reverse('masterclass-list') + '?price_max=4000')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Проверяем фильтр по диапазону цен
        response = self.client.get(reverse('masterclass-list') + '?price_min=2000&price_max=4000')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], mc2.id)
        
        # Сбрасываем между тестами
        self.client = APIClient()

    def test_sorting_options(self):
        """Тест сортировки мастер-классов"""
        # Очищаем существующие мастер-классы перед тестом
        MasterClass.objects.all().delete()
        
        # Создаем мастер-классы с разными параметрами
        mc1 = MasterClass.objects.create(
            name="МК A",
            short_description="Описание A",
            start_price=1000,
            final_price=1000,
            score_product_page=30,  # Низкая популярность
        )
        mc2 = MasterClass.objects.create(
            name="МК B",
            short_description="Описание B",
            start_price=3000,
            final_price=3000,
            score_product_page=70,  # Средняя популярность
        )
        mc3 = MasterClass.objects.create(
            name="МК C",
            short_description="Описание C",
            start_price=5000,
            final_price=5000,
            score_product_page=90,  # Высокая популярность
        )

        # Проверяем сортировку по популярности (score_product_page по убыванию)
        response = self.client.get(reverse('masterclass-list') + '?ordering=popular')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = [item['id'] for item in response.data['results']]
        self.assertEqual(result_ids, [mc3.id, mc2.id, mc1.id])
        
        # Проверяем сортировку по возрастанию цены
        response = self.client.get(reverse('masterclass-list') + '?ordering=min_price')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = [item['id'] for item in response.data['results']]
        self.assertEqual(result_ids, [mc1.id, mc2.id, mc3.id])
        
        # Проверяем сортировку по убыванию цены
        response = self.client.get(reverse('masterclass-list') + '?ordering=max_price')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = [item['id'] for item in response.data['results']]
        self.assertEqual(result_ids, [mc3.id, mc2.id, mc1.id])
        
        # Сбрасываем между тестами
        self.client = APIClient()


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