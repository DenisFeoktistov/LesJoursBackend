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
def fetch_product_units(request):
    """Get product units information"""
    try:
        data = json.loads(request.body)
        product_unit_list = data.get('product_unit_list', [])
        result = []
        
        for unit in product_unit_list:
            if unit.startswith('certificate_'):
                # Handle certificate
                amount = unit.split('_')[1]
                result.append({
                    'type': 'certificate',
                    'amount': amount
                })
            else:
                # Handle masterclass event
                event_id, guests_amount, _ = unit.split('_')
                event = Event.objects.get(id=event_id)
                masterclass = event.masterclass
                address = masterclass.parameters.get('Адрес', [''])[0]
                contacts = masterclass.parameters.get('Контакты', [''])[0]
                
                result.append({
                    'id': event.id,
                    'name': masterclass.name,
                    'in_wishlist': False,
                    'availability': event.get_remaining_seats() >= int(guests_amount),
                    'bucket_link': [{'url': url} for url in masterclass.bucket_link],
                    'slug': masterclass.slug,
                    'guestsAmount': int(guests_amount),
                    'totalPrice': float(masterclass.final_price * int(guests_amount)),
                    'date': {
                        'id': event.id,
                        'start_datetime': event.start_datetime.isoformat(),
                        'end_datetime': event.end_datetime.isoformat()
                    },
                    'address': address,
                    'contacts': contacts,
                    'type': 'master_class'
                })
        
        return Response(result)
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
@permission_classes([permissions.AllowAny])
def fetch_cart_price(request):
    """Get cart price information"""
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
            'total_amount': float(cart.get_total_amount()),
            'sale': float(cart.get_sale()),
            'promo_sale': float(cart.get_promo_sale()),
            'total_sale': float(cart.get_total_sale()),
            'final_amount': float(cart.get_final_amount())
        }
        
        # Clear temporary cart
        cart.clear()
        
        return Response(result)
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