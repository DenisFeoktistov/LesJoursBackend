from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from orders.utils import Cart
from masterclasses.models import Event
from decimal import Decimal
import json

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
                cart.add('certificate', amount, 1)  # Always add with quantity 1 for certificates
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