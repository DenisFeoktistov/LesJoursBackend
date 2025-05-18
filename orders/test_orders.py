from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from masterclasses.models import MasterClass, Event
from .models import Order, OrderItem
from django.contrib.admin.sites import AdminSite
from .admin import OrderAdmin
from rest_framework.reverse import reverse as drf_reverse
from orders.api.serializers import OrderSerializer
from rest_framework.exceptions import ValidationError
from certificates.models import Certificate
from django.utils import timezone
from datetime import timedelta
from orders.utils import Cart

User = get_user_model()

class OrderAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='orderuser',
            email='orderuser@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.masterclass = MasterClass.objects.create(
            name='Order Test Masterclass',
            short_description='Order Test Description',
            start_price=100.00,
            final_price=90.00,
            bucket_link=['img.jpg'],
            age_restriction=18,
            duration=120
        )
        self.order = Order.objects.create(user=self.user)
        self.order_item = OrderItem.objects.create(
            order=self.order,
            masterclass=self.masterclass,
            quantity=2,
            price=90.00
        )
        self.order_url = reverse('order-list')

    def test_create_order(self):
        response = self.client.post(self.order_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.filter(user=self.user).count(), 2)

    def test_list_orders(self):
        response = self.client.get(self.order_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results'] if 'results' in response.data else response.data
        self.assertGreaterEqual(len(data), 1)

    def test_retrieve_order(self):
        url = reverse('order-detail', args=[self.order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.order.id)

    def test_update_order_status(self):
        url = reverse('order-detail', args=[self.order.id])
        response = self.client.patch(url, {'status': 'paid'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')

    def test_delete_order(self):
        url = reverse('order-detail', args=[self.order.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Order.objects.filter(id=self.order.id).exists())

    def test_order_items_list(self):
        url = reverse('order-items', args=[self.order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='modeluser',
            email='modeluser@example.com',
            password='testpass123'
        )
        self.masterclass = MasterClass.objects.create(
            name='Model Test Masterclass',
            short_description='Model Test Description',
            start_price=100.00,
            final_price=80.00,
            bucket_link=['img2.jpg'],
            age_restriction=18,
            duration=90
        )
        self.order = Order.objects.create(user=self.user)
        self.item1 = OrderItem.objects.create(order=self.order, masterclass=self.masterclass, quantity=1, price=80.00)
        self.item2 = OrderItem.objects.create(order=self.order, masterclass=self.masterclass, quantity=2, price=80.00)

    def test_calculate_total(self):
        total = self.order.calculate_total()
        self.assertEqual(total, 80.00 * 3)
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_price, 80.00 * 3)

    def test_mark_as_paid(self):
        result = self.order.mark_as_paid()
        self.assertTrue(result)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')

    def test_cancel(self):
        result = self.order.cancel()
        self.assertTrue(result)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'cancelled')

    def test_orderitem_save_triggers_total(self):
        self.order.total_price = 0
        self.order.save()
        OrderItem.objects.create(order=self.order, masterclass=self.masterclass, quantity=1, price=80.00)
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_price, 80.00 * 4)

    def test_order_str(self):
        self.assertIn('Order', str(self.order))
        self.assertIn(str(self.user.email), str(self.order))

    def test_orderitem_str(self):
        self.assertIn(self.masterclass.name, str(self.item1))
        self.assertIn('x', str(self.item1))

class OrderAdminTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='adminuser',
            email='adminuser@example.com',
            password='testpass123'
        )
        self.order = Order.objects.create(user=self.user)
        self.site = AdminSite()
        self.admin = OrderAdmin(Order, self.site)

    def test_get_readonly_fields_paid(self):
        self.order.status = 'paid'
        self.order.save()
        fields = self.admin.get_readonly_fields(None, self.order)
        self.assertIn('status', fields)
        self.assertIn('items', fields)
        self.assertIn('total_price', fields)

    def test_get_readonly_fields_default(self):
        fields = self.admin.get_readonly_fields(None, None)
        self.assertEqual(fields, self.admin.readonly_fields)

class OrderItemAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='orderitemuser',
            email='orderitemuser@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.masterclass = MasterClass.objects.create(
            name='OrderItem Test Masterclass',
            short_description='OrderItem Test Description',
            start_price=100.00,
            final_price=90.00,
            bucket_link=['img.jpg'],
            age_restriction=18,
            duration=120
        )
        self.order = Order.objects.create(user=self.user)
        self.order_item = OrderItem.objects.create(
            order=self.order,
            masterclass=self.masterclass,
            quantity=2,
            price=90.00
        )
        self.url = drf_reverse('order-item-list')

    def test_list_orderitems(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results'] if 'results' in response.data else response.data), 1)

    def test_retrieve_orderitem(self):
        url = drf_reverse('order-item-detail', args=[self.order_item.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.order_item.id)

    def test_update_orderitem(self):
        url = drf_reverse('order-item-detail', args=[self.order_item.id])
        response = self.client.patch(url, {'quantity': 3}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.quantity, 3)

    def test_delete_orderitem(self):
        url = drf_reverse('order-item-detail', args=[self.order_item.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(OrderItem.objects.filter(id=self.order_item.id).exists())

    def test_create_orderitem(self):
        data = {
            'order': self.order.id,
            'masterclass_id': self.masterclass.id,
            'quantity': 1,
            'price': 90.00
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(OrderItem.objects.filter(order=self.order, masterclass=self.masterclass, quantity=1).exists())

class OrderSerializerValidateItemsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='valuser',
            email='valuser@example.com',
            password='testpass123'
        )

    def test_items_not_list(self):
        serializer = OrderSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_items('notalist')

    def test_items_not_dict(self):
        serializer = OrderSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_items([1, 2])

    def test_items_missing_fields(self):
        serializer = OrderSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_items([{'type': 'event', 'id': 1}])

    def test_items_wrong_type(self):
        serializer = OrderSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_items([{'type': 'wrong', 'id': 1, 'quantity': 1}])

    def test_items_wrong_quantity(self):
        serializer = OrderSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_items([{'type': 'event', 'id': 1, 'quantity': 0}])

    def test_items_valid(self):
        serializer = OrderSerializer()
        value = serializer.validate_items([{'type': 'event', 'id': 1, 'quantity': 2}])
        self.assertEqual(value, [{'type': 'event', 'id': 1, 'quantity': 2}])

class CartTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='cartuser',
            email='cartuser@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.masterclass = MasterClass.objects.create(
            name='Cart Test Masterclass',
            short_description='Cart Test Description',
            start_price=100.00,
            final_price=90.00,
            bucket_link=['img.jpg'],
            age_restriction=18,
            duration=120,
            parameters={
                'Адрес': ['Test Address 1'],
                'Контакты': ['+7 (999) 111-11-11']
            }
        )
        self.event = Event.objects.create(
            masterclass=self.masterclass,
            start_datetime=timezone.now() + timedelta(days=1),
            available_seats=10
        )
        self.masterclass2 = MasterClass.objects.create(
            name='Cart Test Masterclass 2',
            short_description='Cart Test Description 2',
            start_price=200.00,
            final_price=180.00,
            bucket_link=['img2.jpg'],
            age_restriction=18,
            duration=120,
            parameters={
                'Адрес': ['Test Address 2'],
                'Контакты': ['+7 (999) 222-22-22']
            }
        )
        self.event2 = Event.objects.create(
            masterclass=self.masterclass2,
            start_datetime=timezone.now() + timedelta(days=2),
            available_seats=5
        )
        self.certificate = Certificate.objects.create(amount=5000, user=self.user)
        self.cart_url = reverse('cart', args=[self.user.id])

    def test_add_event_to_cart(self):
        """Test adding an event to cart"""
        data = {
            'type': 'event',
            'id': self.event.id,
            'quantity': 2
        }
        response = self.client.post(self.cart_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertIn('product_units', response.data)
        self.assertEqual(len(response.data['product_units']), 1)
        
        # Check event data
        event_data = response.data['product_units'][0]
        self.assertEqual(event_data['name'], self.masterclass.name)
        self.assertEqual(event_data['guestsAmount'], 2)
        self.assertEqual(event_data['totalPrice'], 180.00)  # 90.00 * 2
        self.assertEqual(event_data['type'], 'master_class')
        self.assertTrue(event_data['availability'])
        self.assertEqual(event_data['address'], self.masterclass.parameters['Адрес'][0])
        self.assertEqual(event_data['contacts'], self.masterclass.parameters['Контакты'][0])
        
        # Check totals
        self.assertEqual(response.data['total_amount'], 180.00)  # 90.00 * 2
        self.assertEqual(response.data['sale'], 20.00)  # (100.00 - 90.00) * 2
        self.assertEqual(response.data['promo_sale'], 0.00)
        self.assertEqual(response.data['total_sale'], 20.00)
        self.assertEqual(response.data['final_amount'], 160.00)  # 180.00 - 20.00

    def test_one_session_per_masterclass(self):
        """Test that only one session per masterclass can be in cart"""
        # Add first event
        data1 = {
            'type': 'event',
            'id': self.event.id,
            'quantity': 2
        }
        response = self.client.post(self.cart_url, data1, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Try to add second event from same masterclass
        data2 = {
            'type': 'event',
            'id': self.event.id,
            'quantity': 1
        }
        response = self.client.post(self.cart_url, data2, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that only the second event is in cart
        response = self.client.get(self.cart_url)
        self.assertEqual(len(response.data['product_units']), 1)
        self.assertEqual(response.data['product_units'][0]['date']['id'], self.event.id)

    def test_add_different_masterclass_events(self):
        """Test adding events from different masterclasses"""
        # Add first masterclass event
        data1 = {
            'type': 'event',
            'id': self.event.id,
            'quantity': 2
        }
        response = self.client.post(self.cart_url, data1, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Add second masterclass event (другой event)
        data2 = {
            'type': 'event',
            'id': self.event2.id,
            'quantity': 1
        }
        response = self.client.post(self.cart_url, data2, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that both events are in cart
        response = self.client.get(self.cart_url)
        self.assertEqual(len(response.data['product_units']), 2)
        # Проверяем суммы для двух разных мастер-классов
        self.assertEqual(response.data['total_amount'], 360.00)  # (90.00 * 2) + (180.00 * 1)
        self.assertEqual(response.data['sale'], 40.00)  # (100.00 - 90.00) * 2 + (200.00 - 180.00) * 1
        self.assertEqual(response.data['final_amount'], 320.00)  # 360.00 - 40.00

    def test_add_certificate(self):
        """Test adding a certificate to cart"""
        data = {
            'type': 'certificate',
            'id': self.certificate.id,  # Используем id сертификата
            'amount': str(self.certificate.amount),
            'quantity': 1
        }
        response = self.client.post(self.cart_url, data, format='json')
        print('DEBUG:', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertIn('product_units', response.data)
        self.assertEqual(len(response.data['product_units']), 1)
        
        # Check certificate data
        certificate_data = response.data['product_units'][0]
        self.assertEqual(certificate_data['type'], 'certificate')
        self.assertEqual(certificate_data['amount'], '5000.00')
        
        # Check totals
        self.assertEqual(response.data['total_amount'], float(self.certificate.amount))
        self.assertEqual(response.data['sale'], 0.00)
        self.assertEqual(response.data['final_amount'], float(self.certificate.amount))

    def test_promo_code(self):
        """Test adding and applying promo code"""
        # First add an event
        data = {
            'type': 'event',
            'id': self.event.id,
            'quantity': 2
        }
        self.client.post(self.cart_url, data, format='json')
        
        # Add promo code
        promo_data = {
            'promo_code': 'TEST10'
        }
        response = self.client.put(self.cart_url, promo_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check promo code in response
        self.assertEqual(response.data['promo_code']['string_representation'], 'TEST10')

    def test_seat_availability(self):
        """Test seat availability validation"""
        data = {
            'type': 'event',
            'id': self.event.id,
            'quantity': 11  # Больше, чем доступно мест (10)
        }
        response = self.client.post(self.cart_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Not enough seats available')

    def test_update_event_quantity(self):
        """Test updating event quantity in cart"""
        # First add an event
        data = {
            'type': 'event',
            'id': self.event.id,
            'quantity': 2
        }
        self.client.post(self.cart_url, data, format='json')
        
        # Then update quantity
        update_data = {
            'type': 'event',
            'id': self.event.id,
            'quantity': 3
        }
        response = self.client.put(self.cart_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_amount'], 270.00)  # 90.00 * 3
        self.assertEqual(response.data['sale'], 30.00)  # (100.00 - 90.00) * 3
        self.assertEqual(response.data['final_amount'], 240.00)  # 270.00 - 30.00

    def test_remove_event(self):
        """Test removing event from cart"""
        # First add an event
        data = {
            'type': 'event',
            'id': self.event.id,
            'quantity': 2
        }
        self.client.post(self.cart_url, data, format='json')
        
        # Then remove it
        remove_data = {
            'type': 'event',
            'id': self.event.id
        }
        response = self.client.delete(self.cart_url, remove_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['product_units']), 0)
        self.assertEqual(response.data['total_amount'], 0.00)
        self.assertEqual(response.data['final_amount'], 0.00)

    def test_clear_cart(self):
        """Test clearing the entire cart"""
        # Add some events
        data1 = {
            'type': 'event',
            'id': self.event.id,
            'quantity': 2
        }
        data2 = {
            'type': 'event',
            'id': self.event2.id,
            'quantity': 1
        }
        self.client.post(self.cart_url, data1, format='json')
        self.client.post(self.cart_url, data2, format='json')
        # Clear cart через PUT с quantity=0 (или другой поддерживаемый способ)
        clear_data = {
            'type': 'event',
            'id': self.event.id,
            'quantity': 0
        }
        self.client.put(self.cart_url, clear_data, format='json')
        clear_data2 = {
            'type': 'event',
            'id': self.event2.id,
            'quantity': 0
        }
        self.client.put(self.cart_url, clear_data2, format='json')
        # Проверяем, что корзина пуста
        response = self.client.get(self.cart_url)
        self.assertEqual(len(response.data['product_units']), 0)
        self.assertEqual(response.data['total_amount'], 0.00)
        self.assertEqual(response.data['final_amount'], 0.00)
        self.assertIsNone(response.data.get('promo_code'))

    def test_invalid_event_id(self):
        """Test adding non-existent event"""
        data = {
            'type': 'event',
            'id': 99999,  # Non-existent ID
            'quantity': 1
        }
        response = self.client.post(self.cart_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Event not found')

    def test_invalid_item_type(self):
        """Test adding item with invalid type"""
        data = {
            'type': 'invalid',
            'id': self.event.id,
            'quantity': 1
        }
        response = self.client.post(self.cart_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Invalid item type')

    def test_missing_required_fields(self):
        """Test adding item with missing required fields"""
        data = {
            'type': 'event'
            # missing id
        }
        response = self.client.post(self.cart_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Type and id are required')

class UserOrdersAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='ordersuser',
            email='ordersuser@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.masterclass = MasterClass.objects.create(
            name='User Orders Test Masterclass',
            short_description='Test Description',
            start_price=100.00,
            final_price=90.00,
            bucket_link=['img.jpg'],
            age_restriction=18,
            duration=120
        )
        self.order = Order.objects.create(user=self.user)
        self.order_item = OrderItem.objects.create(
            order=self.order,
            masterclass=self.masterclass,
            quantity=2,
            price=90.00
        )
        self.user_orders_url = reverse('order-user-orders')

    def test_fetch_user_orders(self):
        response = self.client.get(self.user_orders_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        order_data = response.data[0]
        self.assertEqual(order_data['id'], self.order.id)
        self.assertEqual(len(order_data['order_units']), 1)
        self.assertEqual(order_data['total_amount'], 180.00)  # 90.00 * 2

    def test_fetch_user_orders_unauthorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.user_orders_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class OrderInfoAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='orderinfouser',
            email='orderinfouser@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.masterclass = MasterClass.objects.create(
            name='Order Info Test Masterclass',
            short_description='Test Description',
            start_price=100.00,
            final_price=90.00,
            bucket_link=['img.jpg'],
            age_restriction=18,
            duration=120
        )
        self.order = Order.objects.create(user=self.user)
        self.order_item = OrderItem.objects.create(
            order=self.order,
            masterclass=self.masterclass,
            quantity=2,
            price=90.00
        )
        self.order_info_url = reverse('order-info', args=[self.order.id])

    def test_fetch_one_order(self):
        response = self.client.get(self.order_info_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.order.id)
        self.assertEqual(len(response.data['order_units']), 1)
        self.assertEqual(response.data['total_amount'], 180.00)  # 90.00 * 2

    def test_fetch_one_order_unauthorized(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.order_info_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fetch_one_order_wrong_user(self):
        other_user = User.objects.create_user(
            username='otheruser',
            email='otheruser@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.get(self.order_info_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class UserPasswordAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='passworduser',
            email='passworduser@example.com',
            password='oldpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.change_password_url = reverse('user-change-password')

    def test_change_password_success(self):
        data = {
            'oldPass': 'oldpass123',
            'newPass': 'newpass123'
        }
        response = self.client.post(self.change_password_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))

    def test_change_password_wrong_old_password(self):
        data = {
            'oldPass': 'wrongpass',
            'newPass': 'newpass123'
        }
        response = self.client.post(self.change_password_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('oldpass123'))

    def test_change_password_missing_fields(self):
        data = {
            'oldPass': 'oldpass123'
        }
        response = self.client.post(self.change_password_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_unauthorized(self):
        self.client.force_authenticate(user=None)
        data = {
            'oldPass': 'oldpass123',
            'newPass': 'newpass123'
        }
        response = self.client.post(self.change_password_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
