from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from ..models import MasterClass


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
            duration=60
        )
        
        self.masterclass2 = MasterClass.objects.create(
            name='Test Masterclass 2',
            short_description='Test Description 2',
            start_price=2000.00,
            final_price=2000.00,  # No discount
            age_restriction=12,
            duration=90
        )
        
        self.masterclass3 = MasterClass.objects.create(
            name='Test Masterclass 3',
            short_description='Test Description 3',
            start_price=3000.00,
            final_price=2500.00,  # Has discount
            age_restriction=16,
            duration=120
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