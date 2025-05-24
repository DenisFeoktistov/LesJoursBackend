from django.conf import settings
import json
from decimal import Decimal
from masterclasses.models import MasterClass, Event
from certificates.models import Certificate
from django.utils import timezone
from users.models import UserProfile

class Cart:
    def __init__(self, request):
        self.request = request
        if request.user.is_authenticated:
            self.profile, _ = UserProfile.objects.get_or_create(user=request.user)
            self.cart = self.profile.cart
        else:
            self.cart = {}
            self.profile = None

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
        print(f"[DEBUG] Attempting to remove item - type: {item_type}, id: {item_id}")
        print(f"[DEBUG] Current cart contents: {self.cart}")
        
        if item_type == 'certificate':
            # For certificates, we need to find the one with matching amount
            amount_to_remove = Decimal(str(item_id))
            print(f"[DEBUG] Looking for certificate with amount: {amount_to_remove}")
            
            # Find the first certificate with matching amount
            for key, item in list(self.cart.items()):
                if item['type'] == 'certificate':
                    try:
                        # For authenticated users, get amount from Certificate model
                        if self.request.user.is_authenticated:
                            certificate = Certificate.objects.get(id=item['id'])
                            item_amount = certificate.amount
                        else:
                            # For anonymous users, amount is stored directly in id
                            item_amount = Decimal(str(item['id']))
                            
                        print(f"[DEBUG] Comparing amounts: {item_amount} == {amount_to_remove}")
                        if item_amount == amount_to_remove:
                            print(f"[DEBUG] Found matching certificate: {key}")
                            del self.cart[key]
                            self.save()
                            print(f"[DEBUG] Certificate removed. New cart contents: {self.cart}")
                            return
                    except (Certificate.DoesNotExist, ValueError) as e:
                        print(f"[DEBUG] Error processing certificate: {e}")
                        continue
            
            print(f"[DEBUG] No certificate found with amount {amount_to_remove}")
        else:
            # For other items (like events), use the original logic
            item_key = f"{item_type}_{item_id}"
            if item_key in self.cart:
                print(f"[DEBUG] Found item to remove: {self.cart[item_key]}")
                del self.cart[item_key]
                self.save()
                print(f"[DEBUG] Item removed. New cart contents: {self.cart}")
            else:
                print(f"[DEBUG] Item not found in cart")

    def update(self, item_type, item_id, quantity):
        item_key = f"{item_type}_{item_id}"
        if item_key in self.cart:
            if quantity > 0:
                self.cart[item_key]['quantity'] = quantity
            else:
                del self.cart[item_key]
            self.save()

    def clear(self):
        self.cart = {}
        self.save()

    def save(self):
        if self.profile:
            self.profile.cart = self.cart
            self.profile.save()

    def set_promo_code(self, promo_code):
        if 'promo_code' not in self.cart:
            self.cart['promo_code'] = {}
        self.cart['promo_code'] = promo_code
        self.save()

    def get_promo_code(self):
        return self.cart.get('promo_code')

    def get_total_amount(self):
        """Get total amount without any discounts"""
        total = Decimal('0')
        for item in self.cart.values():
            if isinstance(item, dict) and item.get('type') == 'event':
                event = Event.objects.get(id=item['id'])
                total += event.masterclass.final_price * item['quantity']
            elif isinstance(item, dict) and item.get('type') == 'certificate':
                # Для авторизованных пользователей ищем сертификат по id
                try:
                    certificate = Certificate.objects.get(id=item['id'])
                    amount = certificate.amount
                except Certificate.DoesNotExist:
                    # Для анонимных пользователей используем id как сумму
                    amount = Decimal(item['id'])
                total += amount * item['quantity']
        return total

    def get_sale(self):
        """Get total sale amount"""
        total = Decimal('0')
        for item in self.cart.values():
            if isinstance(item, dict) and item.get('type') == 'event':
                event = Event.objects.get(id=item['id'])
                if event.masterclass.start_price and event.masterclass.final_price:
                    total += (event.masterclass.start_price - event.masterclass.final_price) * item['quantity']
        return total

    def get_promo_sale(self):
        """Get total promo sale amount"""
        if not self.get_promo_code():
            return Decimal('0')
            
        total = Decimal('0')
        for item in self.cart.values():
            if isinstance(item, dict) and item.get('type') == 'event':
                event = Event.objects.get(id=item['id'])
                # Пример: 10% скидка по промокоду
                if self.get_promo_code() == 'TEST10':
                    total += event.masterclass.final_price * item['quantity'] * Decimal('0.10')
        return total

    def get_total_sale(self):
        """Get total sale amount including promo sales"""
        return self.get_sale() + self.get_promo_sale()

    def get_final_amount(self):
        """Get final amount after all discounts"""
        return self.get_total_amount() - self.get_total_sale()

    def get_items(self):
        items = []
        for item_key, item_data in self.cart.items():
            if isinstance(item_data, dict) and item_data.get('type') == 'event':
                try:
                    event = Event.objects.get(id=item_data['id'])
                    masterclass = event.masterclass
                    params = masterclass.parameters
                    address = ''
                    contacts = ''
                    if isinstance(params, dict):
                        # Вложенная структура
                        if 'parameters' in params and isinstance(params['parameters'], dict):
                            address = params['parameters'].get('Адрес', [''])
                            if address and isinstance(address, list):
                                address = address[0]
                            contacts = params['parameters'].get('Контакты', [''])
                            if contacts and isinstance(contacts, list):
                                contacts = contacts[0]
                        # Плоская структура
                        elif 'Адрес' in params:
                            address = params['Адрес']
                            if isinstance(address, list):
                                address = address[0]
                        if 'Контакты' in params:
                            contacts = params['Контакты']
                            if isinstance(contacts, list):
                                contacts = contacts[0]
                    guests_amount = item_data['quantity']
                    
                    # Check availability
                    availability = event.get_remaining_seats() >= guests_amount
                    
                    # DEBUG: логируем значение и тип bucket_link в файл
                    with open('debug_bucket_links.log', 'a', encoding='utf-8') as f:
                        f.write(f"bucket_links: {repr(masterclass.bucket_link)} type: {type(masterclass.bucket_link)}\n")
                    # Корректная обработка bucket_link
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
                        'in_wishlist': False,  # TODO: Implement wishlist functionality
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
                        'type': 'master_class'
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
                    # For anonymous users, use the ID as the amount
                    items.append({
                        'type': 'certificate',
                        'amount': str(item_data['id']),
                        'quantity': item_data['quantity']
                    })
        return items

    def get_cart_data(self):
        """Get complete cart data in the required format"""
        return {
            'id': 0,  # Not used as per requirements
            'promo_code': {'string_representation': self.get_promo_code()} if self.get_promo_code() else None,
            'product_units': self.get_items(),
            'is_update': False,  # TODO: Implement update flag logic
            'total_amount': float(self.get_total_amount()),
            'sale': float(self.get_sale()),
            'promo_sale': float(self.get_promo_sale()),
            'total_sale': float(self.get_total_sale()),
            'final_amount': float(self.get_final_amount())
        } 