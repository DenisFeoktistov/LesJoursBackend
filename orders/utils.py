from django.conf import settings
import json
from decimal import Decimal
from masterclasses.models import MasterClass
from certificates.models import Certificate

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, item_type, item_id, quantity=1):
        item_key = f"{item_type}_{item_id}"
        if item_key in self.cart:
            self.cart[item_key]['quantity'] += quantity
        else:
            self.cart[item_key] = {
                'type': item_type,
                'id': item_id,
                'quantity': quantity
            }
        self.save()

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
        self.save()

    def save(self):
        self.session.modified = True

    def get_total_price(self):
        total = Decimal('0.00')
        for item_key, item_data in self.cart.items():
            if item_data['type'] == 'masterclass':
                try:
                    masterclass = MasterClass.objects.get(id=item_data['id'])
                    total += masterclass.final_price * item_data['quantity']
                except MasterClass.DoesNotExist:
                    continue
            elif item_data['type'] == 'certificate':
                try:
                    certificate = Certificate.objects.get(id=item_data['id'])
                    total += certificate.amount * item_data['quantity']
                except Certificate.DoesNotExist:
                    continue
        return total

    def get_items(self):
        items = []
        for item_key, item_data in self.cart.items():
            if item_data['type'] == 'masterclass':
                try:
                    masterclass = MasterClass.objects.get(id=item_data['id'])
                    items.append({
                        'type': 'masterclass',
                        'id': masterclass.id,
                        'name': masterclass.name,
                        'price': masterclass.final_price,
                        'quantity': item_data['quantity'],
                        'total': masterclass.final_price * item_data['quantity']
                    })
                except MasterClass.DoesNotExist:
                    continue
            elif item_data['type'] == 'certificate':
                try:
                    certificate = Certificate.objects.get(id=item_data['id'])
                    items.append({
                        'type': 'certificate',
                        'id': certificate.id,
                        'name': f'Certificate {certificate.code}',
                        'price': certificate.amount,
                        'quantity': item_data['quantity'],
                        'total': certificate.amount * item_data['quantity']
                    })
                except Certificate.DoesNotExist:
                    continue
        return items 