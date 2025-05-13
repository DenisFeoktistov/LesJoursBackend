from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from masterclasses.models import MasterClass
from .models import Order, OrderItem
from django.contrib.admin.sites import AdminSite
from .admin import OrderAdmin
from rest_framework.reverse import reverse as drf_reverse
from orders.api.serializers import OrderSerializer
from rest_framework.exceptions import ValidationError
from certificates.models import Certificate

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
        self.url = drf_reverse('orderitem-list')

    def test_list_orderitems(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results'] if 'results' in response.data else response.data), 1)

    def test_retrieve_orderitem(self):
        url = drf_reverse('orderitem-detail', args=[self.order_item.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.order_item.id)

    def test_update_orderitem(self):
        url = drf_reverse('orderitem-detail', args=[self.order_item.id])
        response = self.client.patch(url, {'quantity': 3}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.quantity, 3)

    def test_delete_orderitem(self):
        url = drf_reverse('orderitem-detail', args=[self.order_item.id])
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

class CartAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='cartuser',
            email='cartuser@example.com',
            password='testpass123'
        )
        self.masterclass = MasterClass.objects.create(
            name='Cart Test Masterclass',
            short_description='Cart Test Description',
            start_price=100.00,
            final_price=90.00,
            bucket_link=['img.jpg'],
            age_restriction=18,
            duration=120
        )
        self.certificate = Certificate.objects.create(
            user=self.user,
            amount=1000.00,
            code='TEST123'
        )
        self.cart_url = reverse('cart')

    def test_get_empty_cart(self):
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['items'], [])
        self.assertEqual(response.data['total_price'], '0.00')

    def test_add_masterclass_to_cart(self):
        data = {
            'type': 'masterclass',
            'id': self.masterclass.id,
            'quantity': 2
        }
        response = self.client.post(self.cart_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['total_price'], '180.00')

    def test_add_certificate_to_cart(self):
        data = {
            'type': 'certificate',
            'id': self.certificate.id,
            'quantity': 1
        }
        response = self.client.post(self.cart_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['total_price'], '1000.00')

    def test_update_cart_item(self):
        # First add an item
        data = {
            'type': 'masterclass',
            'id': self.masterclass.id,
            'quantity': 1
        }
        self.client.post(self.cart_url, data, format='json')

        # Then update it
        update_data = {
            'type': 'masterclass',
            'id': self.masterclass.id,
            'quantity': 3
        }
        response = self.client.put(self.cart_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['total_price'], '270.00')

    def test_remove_cart_item(self):
        # First add an item
        data = {
            'type': 'masterclass',
            'id': self.masterclass.id,
            'quantity': 1
        }
        self.client.post(self.cart_url, data, format='json')

        # Then remove it
        remove_data = {
            'type': 'masterclass',
            'id': self.masterclass.id
        }
        response = self.client.delete(self.cart_url, remove_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 0)
        self.assertEqual(response.data['total_price'], '0.00')

    def test_clear_cart(self):
        # First add some items
        data1 = {
            'type': 'masterclass',
            'id': self.masterclass.id,
            'quantity': 1
        }
        data2 = {
            'type': 'certificate',
            'id': self.certificate.id,
            'quantity': 1
        }
        self.client.post(self.cart_url, data1, format='json')
        self.client.post(self.cart_url, data2, format='json')

        # Then clear the cart
        response = self.client.post(reverse('cart-clear'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 0)
        self.assertEqual(response.data['total_price'], '0.00')

    def test_invalid_item_type(self):
        data = {
            'type': 'invalid',
            'id': 1,
            'quantity': 1
        }
        response = self.client.post(self.cart_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_required_fields(self):
        data = {
            'type': 'masterclass'
            # missing id
        }
        response = self.client.post(self.cart_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
