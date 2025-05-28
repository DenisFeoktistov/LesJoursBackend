from django.conf import settings
import json
from decimal import Decimal
from masterclasses.models import MasterClass, Event
from certificates.models import Certificate
from django.utils import timezone
from users.models import UserProfile
from orders.models import Cart as DB_Cart, CartItem as DB_CartItem

class Cart:
    def __init__(self, request):
        self.request = request
        self.user = request.user if request.user.is_authenticated else None
        if self.user:
            self.cart_obj, _ = DB_Cart.objects.get_or_create(user=self.user)
            self.is_authenticated = True
        else:
            self.cart = request.session.get('cart', {})
            self.is_authenticated = False

    def add(self, item_type, item_id, quantity=1, user=None):
        if self.is_authenticated:
            if item_type == 'event':
                try:
                    event = Event.objects.get(id=item_id)
                    cart_item, created = DB_CartItem.objects.get_or_create(cart=self.cart_obj, event=event, certificate=None)
                    cart_item.quantity = quantity
                    cart_item.save()
                except Event.DoesNotExist:
                    return False
            elif item_type == 'certificate':
                try:
                    certificate = Certificate.objects.get(id=item_id)
                    cart_item, created = DB_CartItem.objects.get_or_create(cart=self.cart_obj, event=None, certificate=certificate)
                    cart_item.quantity = quantity
                    cart_item.save()
                except Certificate.DoesNotExist:
                    return False
            return True
        else:
            # Старая логика для анонимных
            if item_type == 'event':
                try:
                    event = Event.objects.get(id=item_id)
                    item_key = f"{item_type}_{item_id}_{event.start_datetime.isoformat()}"
                    self.cart[item_key] = {
                        'type': item_type,
                        'id': item_id,
                        'quantity': quantity,
                        'user': user.id if user else None
                    }
                except Event.DoesNotExist:
                    return False
            else:
                item_key = f"{item_type}_{item_id}"
                if item_key in self.cart:
                    self.cart[item_key]['quantity'] += quantity
                else:
                    self.cart[item_key] = {
                        'type': item_type,
                        'id': item_id,
                        'quantity': quantity,
                        'user': user.id if user else None
                    }
            self.save()
            return True

    def remove(self, item_type, item_id):
        if self.is_authenticated:
            if item_type == 'event':
                DB_CartItem.objects.filter(cart=self.cart_obj, event_id=item_id).delete()
            elif item_type == 'certificate':
                DB_CartItem.objects.filter(cart=self.cart_obj, certificate_id=item_id).delete()
        else:
            for key, item in list(self.cart.items()):
                if item['type'] == item_type and str(item['id']) == str(item_id):
                    del self.cart[key]
            self.save()

    def update(self, item_type, item_id, quantity):
        if self.is_authenticated:
            if item_type == 'event':
                DB_CartItem.objects.filter(cart=self.cart_obj, event_id=item_id).update(quantity=quantity)
            elif item_type == 'certificate':
                DB_CartItem.objects.filter(cart=self.cart_obj, certificate_id=item_id).update(quantity=quantity)
        else:
            for key, item in self.cart.items():
                if item['type'] == item_type and str(item['id']) == str(item_id):
                    if quantity > 0:
                        self.cart[key]['quantity'] = quantity
                    else:
                        del self.cart[key]
            self.save()

    def clear(self):
        if self.is_authenticated:
            self.cart_obj.items.all().delete()
        else:
            self.cart = {}
            self.save()

    def save(self):
        if not self.is_authenticated:
            self.request.session['cart'] = self.cart
            self.request.session.modified = True

    def set_promo_code(self, promo_code):
        if self.is_authenticated:
            # Можно реализовать поле promo_code в Cart, если нужно
            pass
        else:
            self.cart['promo_code'] = promo_code
            self.save()

    def get_promo_code(self):
        if self.is_authenticated:
            # Можно реализовать поле promo_code в Cart, если нужно
            return None
        return self.cart.get('promo_code')

    def get_items(self):
        items = []
        if self.is_authenticated:
            for cart_item in self.cart_obj.items.all():
                if cart_item.event:
                    event = cart_item.event
                    masterclass = event.masterclass
                    guests_amount = cart_item.quantity
                    availability = event.get_remaining_seats() >= guests_amount
                    params = masterclass.parameters
                    address = ''
                    contacts = ''
                    if isinstance(params, dict):
                        if 'parameters' in params and isinstance(params['parameters'], dict):
                            address = params['parameters'].get('Адрес', [''])
                            if address and isinstance(address, list):
                                address = address[0]
                            contacts = params['parameters'].get('Контакты', [''])
                            if contacts and isinstance(contacts, list):
                                contacts = contacts[0]
                        else:
                            address = params.get('Адрес', [''])
                            if isinstance(address, list):
                                address = address[0]
                            contacts = params.get('Контакты', [''])
                            if isinstance(contacts, list):
                                contacts = contacts[0]
                    bucket_links = masterclass.bucket_link
                    if isinstance(bucket_links, str):
                        bucket_links = [{'url': bucket_links}]
                    elif isinstance(bucket_links, list):
                        if all(isinstance(x, dict) and 'url' in x for x in bucket_links):
                            bucket_links = bucket_links
                        elif all(isinstance(x, str) for x in bucket_links):
                            bucket_links = [{'url': x} for x in bucket_links]
                        else:
                            bucket_links = [{'url': str(x)} for x in bucket_links]
                    else:
                        bucket_links = [{'url': str(bucket_links)}]
                    items.append({
                        'id': event.id,
                        'name': masterclass.name,
                        'in_wishlist': False,
                        'availability': availability,
                        'bucket_link': bucket_links,
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
                        'type': 'event'
                    })
                elif cart_item.certificate:
                    certificate = cart_item.certificate
                    items.append({
                        'type': 'certificate',
                        'amount': str(certificate.amount),
                        'quantity': cart_item.quantity
                    })
        else:
            for item_data in self.cart.values():
                if isinstance(item_data, dict) and item_data.get('type') == 'event':
                    try:
                        event = Event.objects.get(id=item_data['id'])
                        masterclass = event.masterclass
                        guests_amount = item_data['quantity']
                        availability = event.get_remaining_seats() >= guests_amount
                        params = masterclass.parameters
                        address = ''
                        contacts = ''
                        if isinstance(params, dict):
                            if 'parameters' in params and isinstance(params['parameters'], dict):
                                address = params['parameters'].get('Адрес', [''])
                                if address and isinstance(address, list):
                                    address = address[0]
                                contacts = params['parameters'].get('Контакты', [''])
                                if contacts and isinstance(contacts, list):
                                    contacts = contacts[0]
                            else:
                                address = params.get('Адрес', [''])
                                if isinstance(address, list):
                                    address = address[0]
                                contacts = params.get('Контакты', [''])
                                if isinstance(contacts, list):
                                    contacts = contacts[0]
                        bucket_links = masterclass.bucket_link
                        if isinstance(bucket_links, str):
                            bucket_links = [{'url': bucket_links}]
                        elif isinstance(bucket_links, list):
                            if all(isinstance(x, dict) and 'url' in x for x in bucket_links):
                                bucket_links = bucket_links
                            elif all(isinstance(x, str) for x in bucket_links):
                                bucket_links = [{'url': x} for x in bucket_links]
                            else:
                                bucket_links = [{'url': str(x)} for x in bucket_links]
                        else:
                            bucket_links = [{'url': str(bucket_links)}]
                        items.append({
                            'id': event.id,
                            'name': masterclass.name,
                            'in_wishlist': False,
                            'availability': availability,
                            'bucket_link': bucket_links,
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
                            'type': 'event'
                        })
                    except Event.DoesNotExist:
                        continue
                elif isinstance(item_data, dict) and item_data.get('type') == 'certificate':
                    try:
                        certificate = Certificate.objects.get(id=item_data['id'])
                        items.append({
                            'type': 'certificate',
                            'amount': str(certificate.amount),
                            'quantity': item_data['quantity']
                        })
                    except Certificate.DoesNotExist:
                        items.append({
                            'type': 'certificate',
                            'amount': str(item_data['id']),
                            'quantity': item_data['quantity']
                        })
        return items

    def get_cart_data(self):
        return {
            'id': 0,
            'promo_code': {'string_representation': self.get_promo_code()} if self.get_promo_code() else None,
            'product_units': self.get_items(),
            'is_update': False,
            'total_amount': float(self.get_total_amount()),
            'sale': float(self.get_sale()),
            'promo_sale': float(self.get_promo_sale()),
            'total_sale': float(self.get_total_sale()),
            'final_amount': float(self.get_final_amount())
        }

    def get_total_amount(self):
        total = Decimal('0')
        if self.is_authenticated:
            for cart_item in self.cart_obj.items.all():
                if cart_item.event:
                    total += cart_item.event.masterclass.final_price * cart_item.quantity
                elif cart_item.certificate:
                    total += cart_item.certificate.amount * cart_item.quantity
        else:
            for item in self.cart.values():
                if isinstance(item, dict) and item.get('type') == 'event':
                    event = Event.objects.get(id=item['id'])
                    total += event.masterclass.final_price * item['quantity']
                elif isinstance(item, dict) and item.get('type') == 'certificate':
                    try:
                        certificate = Certificate.objects.get(id=item['id'])
                        amount = certificate.amount
                    except Certificate.DoesNotExist:
                        amount = Decimal(item['id'])
                    total += amount * item['quantity']
        return total

    def get_sale(self):
        total = Decimal('0')
        if self.is_authenticated:
            for cart_item in self.cart_obj.items.all():
                if cart_item.event:
                    event = cart_item.event
                    if event.masterclass.start_price and event.masterclass.final_price:
                        total += (event.masterclass.start_price - event.masterclass.final_price) * cart_item.quantity
        else:
            for item in self.cart.values():
                if isinstance(item, dict) and item.get('type') == 'event':
                    event = Event.objects.get(id=item['id'])
                    if event.masterclass.start_price and event.masterclass.final_price:
                        total += (event.masterclass.start_price - event.masterclass.final_price) * item['quantity']
        return total

    def get_promo_sale(self):
        # Оставим как есть, если нужно — доработаем
        return Decimal('0')

    def get_total_sale(self):
        return self.get_sale() + self.get_promo_sale()

    def get_final_amount(self):
        return self.get_total_amount() - self.get_total_sale() 