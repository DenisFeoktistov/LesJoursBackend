from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from masterclasses.models import MasterClass, Event
from certificates.models import Certificate
from decimal import Decimal
import json

User = get_user_model()

class CartAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a masterclass
        self.masterclass = MasterClass.objects.create(
            name='Test Masterclass',
            slug='test-masterclass',
            start_price=Decimal('1000.00'),
            final_price=Decimal('800.00'),
            parameters={
                'Адрес': ['Test Address'],
                'Контакты': ['+7 (999) 999-99-99']
            }
        )
        
        # Create an event
        self.event = Event.objects.create(
            masterclass=self.masterclass,
            start_datetime='2024-04-01T14:00:00Z',
            end_datetime='2024-04-01T16:00:00Z',
            available_seats=10
        )
        
        # Create a certificate
        self.certificate = Certificate.objects.create(
            user=self.user,
            amount=Decimal('5000.00'),
            code='TESTCODE123'
        )

    def test_fetch_cart(self):
        """Test fetching cart contents"""
        url = reverse('cart', kwargs={'user_id': self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('product_units', response.data)
        self.assertIn('total_amount', response.data)

    def test_add_to_cart_masterclass(self):
        """Test adding masterclass to cart"""
        url = reverse('cart', kwargs={'user_id': self.user.id})
        data = {
            'type': 'event',
            'id': self.event.id,
            'quantity': 2
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['product_units']), 1)
        self.assertEqual(response.data['product_units'][0]['guestsAmount'], 2)

    def test_add_to_cart_certificate(self):
        """Test adding certificate to cart"""
        url = reverse('cart', kwargs={'user_id': self.user.id})
        data = {
            'type': 'certificate',
            'id': '5000',
            'amount': '5000'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['product_units']), 1)
        self.assertEqual(response.data['product_units'][0]['amount'], '5000')

    def test_remove_from_cart_masterclass(self):
        """Test removing masterclass from cart"""
        # First add to cart
        add_url = reverse('cart', kwargs={'user_id': self.user.id})
        add_data = {
            'type': 'event',
            'id': self.event.id,
            'quantity': 2
        }
        self.client.post(add_url, add_data)
        
        # Then remove
        remove_data = {
            'type': 'event',
            'id': self.event.id
        }
        response = self.client.delete(add_url, remove_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['product_units']), 0)

    def test_remove_from_cart_certificate(self):
        """Test removing certificate from cart"""
        # First add to cart
        add_url = reverse('cart', kwargs={'user_id': self.user.id})
        add_data = {
            'type': 'certificate',
            'id': '5000',
            'amount': '5000'
        }
        self.client.post(add_url, add_data)
        
        # Then remove
        remove_data = {
            'type': 'certificate',
            'id': '5000'
        }
        response = self.client.delete(add_url, remove_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['product_units']), 0)

    def test_fetch_product_units(self):
        """Test fetching product units information"""
        url = reverse('fetch-product-units')
        data = {
            'product_unit_list': [
                f'{self.event.id}_2_guests',
                'certificate_5000'
            ]
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['type'], 'master_class')
        self.assertEqual(response.data[1]['type'], 'certificate')

    def test_update_cart_from_cookies(self):
        """Test updating cart from cookies"""
        url = reverse('update-cart-from-cookies', kwargs={'user_id': self.user.id})
        data = {
            'product_unit_list': [
                f'{self.event.id}_2_guests',
                'certificate_5000'
            ]
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_fetch_cart_price(self):
        """Test fetching cart price information"""
        url = reverse('fetch-cart-price')
        data = {
            'product_unit_list': [
                f'{self.event.id}_2_guests',
                'certificate_5000'
            ],
            'promo': 'TEST10'
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_amount', response.data)
        self.assertIn('sale', response.data)
        self.assertIn('promo_sale', response.data)
        self.assertIn('total_sale', response.data)
        self.assertIn('final_amount', response.data)

    def test_promo_auth(self):
        """Test promo code check for authenticated user"""
        self.client.force_authenticate(user=self.user)
        url = reverse('promo-auth', kwargs={'user_id': self.user.id})
        data = {'promo': 'TEST10'}
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('final_amount', response.data)
        self.assertIn('message', response.data)
        self.assertIn('status', response.data)
        self.assertIn('promo_sale', response.data)

    def test_promo_unauth(self):
        """Test promo code check for unauthenticated user"""
        url = reverse('promo-unauth')
        data = {
            'product_unit_list': [
                f'{self.event.id}_2_guests',
                'certificate_5000'
            ],
            'promo': 'TEST10'
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('final_amount', response.data)
        self.assertIn('message', response.data)
        self.assertIn('status', response.data)
        self.assertIn('promo_sale', response.data) 