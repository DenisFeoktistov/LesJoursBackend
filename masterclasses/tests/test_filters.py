from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from ..models import MasterClass
from django.utils import timezone


class MasterClassFilterTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create test masterclasses with different prices and age restrictions
        self.masterclass1 = MasterClass.objects.create(
            name='Test Masterclass 1',
            short_description='Test Description 1',
            start_price=1000.00,
            final_price=800.00,  # Has discount
            age_restriction=6,
            duration=60,
            score_product_page=50,
            created_at=timezone.now() - timezone.timedelta(days=2)
        )
        
        self.masterclass2 = MasterClass.objects.create(
            name='Test Masterclass 2',
            short_description='Test Description 2',
            start_price=2000.00,
            final_price=2000.00,  # No discount
            age_restriction=12,
            duration=90,
            score_product_page=80,
            created_at=timezone.now() - timezone.timedelta(days=1)
        )
        
        self.masterclass3 = MasterClass.objects.create(
            name='Test Masterclass 3',
            short_description='Test Description 3',
            start_price=3000.00,
            final_price=2500.00,  # Has discount
            age_restriction=16,
            duration=120,
            score_product_page=30,
            created_at=timezone.now()
        )
        
        self.url = reverse('masterclass-list')

    def test_price_range_filter(self):
        # Test min_price filter (final_price >= 2000)
        response = self.client.get(f'{self.url}?min_price=2000')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # 2000 и 2500
        
        # Test max_price filter (final_price <= 2000)
        response = self.client.get(f'{self.url}?max_price=2000')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # 800 и 2000
        
        # Test both min_price and max_price (2000 <= final_price <= 2500)
        response = self.client.get(f'{self.url}?min_price=2000&max_price=2500')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # 2000 и 2500

    def test_discount_filter(self):
        # Test has_discount=true (final_price < start_price)
        response = self.client.get(f'{self.url}?has_discount=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # 800 и 2500
        
        # Test has_discount=false (final_price >= start_price)
        response = self.client.get(f'{self.url}?has_discount=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # 2000

    def test_age_restrictions_filter(self):
        # Test single age restriction
        response = self.client.get(f'{self.url}?age_restrictions=6+')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test multiple age restrictions
        response = self.client.get(f'{self.url}?age_restrictions=6+,12+')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Test all age restrictions
        response = self.client.get(f'{self.url}?age_restrictions=6+,12+,16+')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_combined_filters(self):
        # Test combination of price range and discount
        response = self.client.get(f'{self.url}?min_price=2000&has_discount=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # только 2500
        
        # Test combination of price range and age restrictions
        response = self.client.get(f'{self.url}?max_price=2000&age_restrictions=6+,12+')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # 800 и 2000
        
        # Test all filters combined
        response = self.client.get(f'{self.url}?min_price=2000&max_price=3000&has_discount=true&age_restrictions=12+,16+')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # только 2500

    def test_invalid_filters(self):
        # Test invalid price values (ожидаем 400)
        response = self.client.get(f'{self.url}?min_price=invalid')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid age restriction (ожидаем 200 и 0 результатов)
        response = self.client.get(f'{self.url}?age_restrictions=invalid')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
        
        # Test invalid has_discount value (ожидаем 200 и все объекты)
        response = self.client.get(f'{self.url}?has_discount=invalid')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_sort_by_price_descending(self):
        response = self.client.get(f'{self.url}?ordering=-final_price')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['id'], self.masterclass3.id)  # Highest price
        self.assertEqual(results[1]['id'], self.masterclass2.id)
        self.assertEqual(results[2]['id'], self.masterclass1.id)  # Lowest price

    def test_sort_by_age_ascending(self):
        response = self.client.get(f'{self.url}?ordering=age_restriction')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['id'], self.masterclass1.id)  # Age 6
        self.assertEqual(results[1]['id'], self.masterclass2.id)  # Age 12
        self.assertEqual(results[2]['id'], self.masterclass3.id)  # Age 16

    def test_sort_by_popularity_descending(self):
        response = self.client.get(f'{self.url}?ordering=-score_product_page')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['id'], self.masterclass2.id)  # Score 80
        self.assertEqual(results[1]['id'], self.masterclass1.id)  # Score 50
        self.assertEqual(results[2]['id'], self.masterclass3.id)  # Score 30

    def test_sort_by_creation_date_descending(self):
        response = self.client.get(f'{self.url}?ordering=-created_at')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['id'], self.masterclass3.id)  # Most recent
        self.assertEqual(results[1]['id'], self.masterclass2.id)
        self.assertEqual(results[2]['id'], self.masterclass1.id)  # Oldest

    def test_sort_by_multiple_fields(self):
        # Sort by price descending and then by age ascending
        response = self.client.get(f'{self.url}?ordering=-final_price,age_restriction')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 3)
        # First sort by price (descending)
        self.assertEqual(results[0]['id'], self.masterclass3.id)  # Highest price
        self.assertEqual(results[1]['id'], self.masterclass2.id)
        self.assertEqual(results[2]['id'], self.masterclass1.id)  # Lowest price

    def test_invalid_sort_field(self):
        response = self.client.get(f'{self.url}?ordering=invalid_field')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return results in default order (by created_at descending)
        results = response.data['results']
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['id'], self.masterclass3.id)  # Most recent

    def test_list_response_format(self):
        # Create 15 masterclasses to test pagination
        for i in range(4, 16):
            MasterClass.objects.create(
                name=f'Test Masterclass {i}',
                short_description=f'Test Description {i}',
                start_price=1000.00 + i * 100,
                final_price=800.00 + i * 100,
                age_restriction=16,
                duration=60
            )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response format
        self.assertIn('count', response.data)
        self.assertIn('min_price', response.data)
        self.assertIn('max_price', response.data)
        self.assertIn('results', response.data)
        
        # Verify count is total number of items
        self.assertEqual(response.data['count'], 15)
        
        # Verify min and max prices
        self.assertEqual(response.data['min_price'], 800.00)
        self.assertEqual(response.data['max_price'], 2500.00)  # Updated to match actual value
        
        # Verify results are limited to 12 items
        self.assertEqual(len(response.data['results']), 12)
        
        # Verify results are ordered by created_at descending
        results = response.data['results']
        self.assertEqual(results[0]['name'], 'Test Masterclass 15')
        self.assertEqual(results[11]['name'], 'Test Masterclass 4') 