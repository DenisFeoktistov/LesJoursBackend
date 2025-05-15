from django.conf import settings
import json
from decimal import Decimal
from masterclasses.models import MasterClass, Event
from certificates.models import Certificate
from django.utils import timezone

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        self.promo_code = self.session.get('promo_code')

    def add(self, item_type, item_id, quantity=1, user=None):
        if item_type == 'event':
            try:
                event = Event.objects.get(id=item_id)
                masterclass_id = event.masterclass.id
                
                # Check seat availability
                if event.get_remaining_seats() < quantity:
                    return False
                
                # Check if there's already a session for this masterclass in cart
                for key, item in self.cart.items():
                    if item['type'] == 'event':
                        existing_event = Event.objects.get(id=item['id'])
                        if existing_event.masterclass.id == masterclass_id:
                            # Remove existing session for this masterclass
                            del self.cart[key]
                            break
                
                # Add the new event session
                item_key = f"{item_type}_{item_id}"
                self.cart[item_key] = {
                    'type': item_type,
                    'id': item_id,
                    'quantity': quantity,
                    'user': user.id if user else None
                }
            except Event.DoesNotExist:
                return False
        else:
            # For certificates, use the amount as the ID for anonymous users
            item_key = f"{item_type}_{item_id}"
            if item_key in self.cart:
                self.cart[item_key]['quantity'] += quantity
            else:
                self.cart[item_key] = {
                    'type': item_type,
                    'id': item_id,  # This will be the amount for anonymous users
                    'quantity': quantity,
                    'user': user.id if user else None
                }
        self.save()
        return True

    def remove(self, item_type, item_id):
        item_key = f"{item_type}_{item_id}"
        if item_key in self.cart:
            del self.cart[item_key]
            self.save()

    def update(self, item_type, item_id, quantity):
        item_key = f"{item_type}_{item_id}"
        if item_key in self.cart:
            if quantity > 0:
                self.cart[item_key]['quantity'] = quantity
            else:
                del self.cart[item_key]
            self.save()

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.session.pop('promo_code', None)
        self.save()

    def save(self):
        self.session.modified = True

    def set_promo_code(self, promo_code):
        self.session['promo_code'] = promo_code
        self.promo_code = promo_code
        self.save()

    def get_promo_code(self):
        return self.promo_code

    def get_total_amount(self):
        """Calculate total amount before any discounts"""
        total = Decimal('0.00')
        for item_key, item_data in self.cart.items():
            if item_data['type'] == 'event':
                try:
                    event = Event.objects.get(id=item_data['id'])
                    total += event.masterclass.start_price * item_data['quantity']
                except Event.DoesNotExist:
                    continue
            elif item_data['type'] == 'certificate':
                try:
                    certificate = Certificate.objects.get(id=item_data['id'])
                    total += certificate.amount * item_data['quantity']
                except Certificate.DoesNotExist:
                    continue
        return total

    def get_sale(self):
        """Calculate sale from masterclass discounts"""
        sale = Decimal('0.00')
        for item_key, item_data in self.cart.items():
            if item_data['type'] == 'event':
                try:
                    event = Event.objects.get(id=item_data['id'])
                    sale += (event.masterclass.start_price - event.masterclass.final_price) * item_data['quantity']
                except Event.DoesNotExist:
                    continue
        return sale

    def get_promo_sale(self):
        """Calculate sale from promo code"""
        if not self.promo_code:
            return Decimal('0.00')
            
        # Example promo code logic - you should implement your own
        if self.promo_code == 'TEST10':
            return self.get_total_amount() * Decimal('0.10')  # 10% discount
        elif self.promo_code == 'TEST20':
            return self.get_total_amount() * Decimal('0.20')  # 20% discount
        return Decimal('0.00')

    def get_total_sale(self):
        """Calculate total sale (masterclass + promo)"""
        return self.get_sale() + self.get_promo_sale()

    def get_final_amount(self):
        """Calculate final amount after all discounts"""
        return self.get_total_amount() - self.get_total_sale()

    def get_items(self):
        items = []
        for item_key, item_data in self.cart.items():
            if item_data['type'] == 'event':
                try:
                    event = Event.objects.get(id=item_data['id'])
                    masterclass = event.masterclass
                    address = masterclass.parameters.get('Адрес', [''])[0]
                    contacts = masterclass.parameters.get('Контакты', [''])[0]
                    guests_amount = item_data['quantity']
                    
                    # Check availability
                    availability = event.get_remaining_seats() >= guests_amount
                    
                    items.append({
                        'id': event.id,
                        'name': masterclass.name,
                        'in_wishlist': False,  # TODO: Implement wishlist functionality
                        'availability': availability,
                        'bucket_link': [{'url': url} for url in masterclass.bucket_link],
                        'slug': masterclass.slug,
                        'guestsAmount': guests_amount,
                        'totalPrice': float(masterclass.final_price * guests_amount),
                        'date': {
                            'id': event.id,
                            'start_datetime': event.start_datetime.isoformat(),
                            'end_datetime': event.end_datetime.isoformat()
                        },
                        'address': address,
                        'contacts': contacts,
                        'type': 'master_class'
                    })
                except Event.DoesNotExist:
                    continue
            elif item_data['type'] == 'certificate':
                try:
                    if item_data.get('user'):
                        certificate = Certificate.objects.get(id=item_data['id'])
                        items.append({
                            'type': 'certificate',
                            'amount': str(certificate.amount),
                            'quantity': item_data['quantity']
                        })
                    else:
                        # For anonymous users, use the ID as the amount
                        items.append({
                            'type': 'certificate',
                            'amount': str(item_data['id']),
                            'quantity': item_data['quantity']
                        })
                except Certificate.DoesNotExist:
                    continue
        return items

    def get_cart_data(self):
        """Get complete cart data in the required format"""
        return {
            'id': 0,  # Not used as per requirements
            'promo_code': {'string_representation': self.promo_code} if self.promo_code else None,
            'product_units': self.get_items(),
            'is_update': False,  # TODO: Implement update flag logic
            'total_amount': float(self.get_total_amount()),
            'sale': float(self.get_sale()),
            'promo_sale': float(self.get_promo_sale()),
            'total_sale': float(self.get_total_sale()),
            'final_amount': float(self.get_final_amount())
        } 