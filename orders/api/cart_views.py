from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from ..utils import Cart
from masterclasses.models import Event
from certificates.models import Certificate
from decimal import Decimal
import json
from django.db import transaction
from orders.models import Order, OrderItem
from orders.utils import Cart
from orders.api.serializers import OrderSerializer

User = get_user_model()

class CartView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, user_id):
        """Get cart contents for a user"""
        try:
            user = get_object_or_404(User, id=user_id)
            cart = Cart(request)
            return Response(cart.get_cart_data())
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, user_id, product_unit_id=None, guests_amount=None):
        """Add item to cart"""
        try:
            user = get_object_or_404(User, id=user_id)
            cart = Cart(request)
            data = request.data
            item_type = data.get('type')
            item_id = data.get('id')
            quantity = int(data.get('quantity', 1))

            if not item_type or not item_id:
                return Response({'error': 'Type and id are required'}, status=status.HTTP_400_BAD_REQUEST)

            if item_type not in ['event', 'certificate']:
                return Response({'error': 'Invalid item type'}, status=status.HTTP_400_BAD_REQUEST)

            if item_type == 'event':
                try:
                    event = Event.objects.get(id=item_id)
                    # Check total seats including those already in cart
                    cart_quantity = 0
                    for item in cart.cart.values():
                        if item['type'] == 'event' and str(item['id']) == str(item_id):
                            cart_quantity += item.get('quantity', 0)
                    if event.get_remaining_seats() < cart_quantity + quantity:
                        return Response({'error': 'Not enough seats available'}, status=status.HTTP_400_BAD_REQUEST)
                except Event.DoesNotExist:
                    return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
                cart.add('event', item_id, quantity)
            elif item_type == 'certificate':
                amount = data.get('amount', item_id)
                if request.user.is_authenticated:
                    certificate = Certificate.objects.create(user=request.user, amount=Decimal(amount), code='AUTO')
                    cart.add('certificate', certificate.id, quantity, user=request.user)
                else:
                    cart.add('certificate', amount, quantity)
            return Response(cart.get_cart_data())
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, user_id):
        """Update item quantity or promo code in cart"""
        try:
            user = get_object_or_404(User, id=user_id)
            cart = Cart(request)
            data = request.data
            if 'promo_code' in data:
                cart.set_promo_code(data['promo_code'])
                return Response(cart.get_cart_data())
            item_type = data.get('type')
            item_id = data.get('id')
            quantity = int(data.get('quantity', 0))
            if not item_type or not item_id:
                return Response({'error': 'Type and id are required'}, status=status.HTTP_400_BAD_REQUEST)
            if item_type not in ['event', 'certificate']:
                return Response({'error': 'Invalid item type'}, status=status.HTTP_400_BAD_REQUEST)
            if item_type == 'event':
                try:
                    event = Event.objects.get(id=item_id)
                    cart_quantity = 0
                    for item in cart.cart.values():
                        if item['type'] == 'event' and str(item['id']) == str(item_id):
                            cart_quantity += item.get('quantity', 0)
                    if event.get_remaining_seats() - cart_quantity < quantity:
                        return Response({'error': 'Not enough seats available'}, status=status.HTTP_400_BAD_REQUEST)
                except Event.DoesNotExist:
                    return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
            cart.update(item_type, item_id, quantity)
            return Response(cart.get_cart_data())
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user_id, product_unit_id=None):
        """Remove item from cart"""
        try:
            user = get_object_or_404(User, id=user_id)
            cart = Cart(request)
            data = request.data
            item_type = data.get('type')
            item_id = data.get('id')
            if not item_type or not item_id:
                return Response({'error': 'Type and id are required'}, status=status.HTTP_400_BAD_REQUEST)
            if item_type == 'certificate':
                # Для анонимных ищем по amount, для аутентифицированных по id Certificate
                if request.user.is_authenticated:
                    cart.remove('certificate', item_id)
                else:
                    cart.remove('certificate', item_id)
            else:
                cart.remove(item_type, item_id)
            return Response(cart.get_cart_data())
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def update_cart_from_cookies(request, user_id):
    """Update cart from cookies"""
    try:
        data = json.loads(request.body)
        product_unit_list = data.get('product_unit_list', [])
        cart = Cart(request)
        
        # Clear existing cart
        cart.clear()
        
        # If product_unit_list is ["false"], just return empty list
        if len(product_unit_list) == 1 and product_unit_list[0] == "false":
            return Response([])
        
        # Add items from cookies
        for unit in product_unit_list:
            if unit.startswith('certificate_'):
                amount = unit.split('_')[1]
                if request.user.is_authenticated:
                    certificate = Certificate.objects.create(user=request.user, amount=Decimal(amount), code='AUTO')
                    cart.add('certificate', certificate.id, user=request.user)
                else:
                    cart.add('certificate', amount)
            else:
                event_id, guests_amount, _ = unit.split('_')
                cart.add('event', event_id, int(guests_amount))
        
        return Response(product_unit_list)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def promo_auth(request, user_id):
    """Check promo code for authenticated user"""
    try:
        data = json.loads(request.body)
        promo_str = data.get('promo', '')
        
        cart = Cart(request)
        cart.set_promo_code(promo_str)
        
        return Response({
            'final_amount': float(cart.get_final_amount()),
            'message': 'Промокод успешно применен' if cart.get_promo_sale() > 0 else 'Промокод недействителен',
            'status': cart.get_promo_sale() > 0,
            'promo_sale': float(cart.get_promo_sale())
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def promo_unauth(request):
    """Check promo code for unauthenticated user"""
    try:
        data = json.loads(request.body)
        product_unit_list = data.get('product_unit_list', [])
        promo_str = data.get('promo', '')
        
        cart = Cart(request)
        if promo_str:
            cart.set_promo_code(promo_str)
        
        # Add items to cart temporarily
        for unit in product_unit_list:
            if unit.startswith('certificate_'):
                amount = unit.split('_')[1]
                if request.user.is_authenticated:
                    certificate = Certificate.objects.create(user=request.user, amount=Decimal(amount), code='AUTO')
                    cart.add('certificate', certificate.id, user=request.user)
                else:
                    cart.add('certificate', amount)
            else:
                event_id, guests_amount, _ = unit.split('_')
                cart.add('event', event_id, int(guests_amount))
        
        result = {
            'final_amount': float(cart.get_final_amount()),
            'message': 'Промокод успешно применен' if cart.get_promo_sale() > 0 else 'Промокод недействителен',
            'status': cart.get_promo_sale() > 0,
            'promo_sale': float(cart.get_promo_sale())
        }
        
        # Clear temporary cart
        cart.clear()
        
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CheckoutOrderView(APIView):
    """
    View for checking out an order.
    Accepts user information and cart data, creates an order and returns order details.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        try:
            # Validate user_id matches authenticated user
            if str(request.user.id) != str(user_id):
                return Response(
                    {'error': 'User ID mismatch'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Validate request data
            user_info = request.data.get('user', {})
            if not user_info:
                return Response(
                    {'error': 'User information is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cart_data = request.data.get('cart', {})
            if not cart_data:
                return Response(
                    {'error': 'Cart data is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get cart from session
            cart = Cart(request)
            if not cart.cart:
                return Response(
                    {'error': 'Cart is empty'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate cart items availability
            for item in cart.get_items():
                if item['type'] == 'master_class' and not item['availability']:
                    return Response(
                        {'error': f"Not enough seats available for {item['name']}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Create order in transaction
            with transaction.atomic():
                # Create order
                order = Order.objects.create(
                    user=request.user,
                    total_price=cart.get_final_amount()
                )

                # Create order items
                for item in cart.get_items():
                    if item['type'] == 'master_class':
                        event = get_object_or_404(Event, id=item['date']['id'])
                        # Update available seats
                        event.available_seats -= item['guestsAmount']
                        event.save()
                        # Create order item
                        OrderItem.objects.create(
                            order=order,
                            masterclass=event.masterclass,
                            quantity=item['guestsAmount'],
                            price=event.masterclass.final_price
                        )
                    elif item['type'] == 'certificate':
                        amount = Decimal(item['amount'])
                        OrderItem.objects.create(
                            order=order,
                            masterclass=None,
                            quantity=item['quantity'],
                            price=amount
                        )

                # Clear cart after successful order creation
                cart.clear()

                # Return order details
                response_data = OrderSerializer(order).data
                return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            ) 