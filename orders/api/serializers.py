from rest_framework import serializers
from ..models import Order, OrderItem
from masterclasses.models import MasterClass
from certificates.models import Certificate
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class OrderItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='masterclass.name', read_only=True)
    bucket_link = serializers.SerializerMethodField()
    slug = serializers.CharField(source='masterclass.slug', read_only=True)
    price = serializers.SerializerMethodField(read_only=True)
    guestsAmount = serializers.IntegerField(source='quantity', read_only=True)
    totalPrice = serializers.SerializerMethodField(read_only=True)
    date = serializers.SerializerMethodField(read_only=True)
    address = serializers.SerializerMethodField()
    contacts = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField(read_only=True)
    masterclass_id = serializers.PrimaryKeyRelatedField(
        queryset=MasterClass.objects.all(), source='masterclass', write_only=True, required=False
    )

    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'masterclass', 'masterclass_id', 'name', 'bucket_link', 'slug', 'price',
            'guestsAmount', 'totalPrice', 'date', 'address', 'contacts', 'type', 'quantity', 'price'
        ]
        extra_kwargs = {
            'order': {'write_only': True, 'required': True},
            'masterclass': {'read_only': True},
            'quantity': {'required': True},
            'price': {'required': False},
        }

    def create(self, validated_data):
        return OrderItem.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.price = validated_data.get('price', instance.price)
        instance.save()
        return instance

    def get_bucket_link(self, obj):
        if obj.masterclass:
            bucket_links = obj.masterclass.bucket_link
            if isinstance(bucket_links, str):
                return [{'url': bucket_links}]
            elif isinstance(bucket_links, list):
                if all(isinstance(x, dict) and 'url' in x for x in bucket_links):
                    return bucket_links
                elif all(isinstance(x, str) for x in bucket_links):
                    return [{'url': x} for x in bucket_links]
                else:
                    return [{'url': str(x)} for x in bucket_links]
            else:
                return [{'url': str(bucket_links)}]
        return []

    def get_price(self, obj):
        return {
            'start_price': float(obj.masterclass.start_price),
            'final_price': float(obj.price)
        }

    def get_totalPrice(self, obj):
        return float(obj.price * obj.quantity)

    def get_date(self, obj):
        event = obj.masterclass.events.first()
        if event:
            return {
                'start_datetime': event.start_datetime.isoformat(),
                'end_datetime': event.end_datetime.isoformat()
            }
        return None

    def get_address(self, obj):
        if obj.masterclass:
            params = obj.masterclass.parameters
            if isinstance(params, dict):
                # Вложенная структура
                if 'parameters' in params and isinstance(params['parameters'], dict):
                    address = params['parameters'].get('Адрес', [''])
                    if address and isinstance(address, list):
                        return address[0]
                # Плоская структура
                elif 'Адрес' in params:
                    address = params['Адрес']
                    if isinstance(address, list):
                        return address[0]
                    return address
        return ''

    def get_contacts(self, obj):
        if obj.masterclass:
            params = obj.masterclass.parameters
            if isinstance(params, dict):
                # Вложенная структура
                if 'parameters' in params and isinstance(params['parameters'], dict):
                    contacts = params['parameters'].get('Контакты', [''])
                    if contacts and isinstance(contacts, list):
                        return contacts[0]
                # Плоская структура
                elif 'Контакты' in params:
                    contacts = params['Контакты']
                    if isinstance(contacts, list):
                        return contacts[0]
                    return contacts
        return ''

    def get_type(self, obj):
        return 'master_class'


class CertificateOrderItemSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['type', 'amount']

    def get_type(self, obj):
        return 'certificate'

    def get_amount(self, obj):
        return str(obj.price)


class OrderSerializer(serializers.ModelSerializer):
    order_units = serializers.SerializerMethodField()
    formatted_date = serializers.SerializerMethodField()
    number = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    final_amount = serializers.SerializerMethodField()
    total_sale = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=False, required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    surname = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    patronymic = serializers.CharField(required=False)
    comment = serializers.CharField(required=False)
    telegram = serializers.CharField(required=False)
    address = serializers.SerializerMethodField()
    contacts = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'order_units', 'formatted_date', 'number', 
                 'total_amount', 'final_amount', 'total_sale', 'status',
                 'email', 'phone', 'surname', 'name', 'patronymic', 'comment', 'telegram',
                 'address', 'contacts']

    def get_email(self, obj):
        return obj.email or obj.user.email

    def get_phone(self, obj):
        return obj.phone or (obj.user.phone if hasattr(obj.user, 'phone') else None)

    def get_surname(self, obj):
        return obj.surname or (obj.user.surname if hasattr(obj.user, 'surname') else None)

    def get_name(self, obj):
        return obj.name or (obj.user.name if hasattr(obj.user, 'name') else None)

    def get_telegram(self, obj):
        return obj.telegram or (obj.user.telegram if hasattr(obj.user, 'telegram') else None)

    def get_order_units(self, obj):
        items = []
        logger.info(f"OrderSerializer.get_order_units: order_id={obj.id}, items_count={obj.items.count()}")
        for item in obj.items.all():
            logger.info(f"OrderSerializer.get_order_units: item_id={item.id}, is_certificate={item.is_certificate}, masterclass={item.masterclass}, event={getattr(item, 'event', None)}")
            if item.masterclass is None:
                items.append(CertificateOrderItemSerializer(item).data)
            else:
                items.append(OrderItemSerializer(item).data)
        logger.info(f"OrderSerializer.get_order_units: result_count={len(items)}")
        return items

    def get_formatted_date(self, obj):
        return obj.created_at.strftime('%d.%m.%y')

    def get_number(self, obj):
        return f"{obj.id:06d}"

    def get_total_amount(self, obj):
        """Calculate total amount without any discounts"""
        total = Decimal('0')
        for item in obj.items.all():
            if item.masterclass:
                total += item.masterclass.start_price * item.quantity
            else:
                # For certificates, use the price directly
                total += item.price * item.quantity
        return float(total)

    def get_final_amount(self, obj):
        """Calculate final amount after all discounts"""
        total = Decimal('0')
        for item in obj.items.all():
            if item.masterclass:
                total += item.masterclass.final_price * item.quantity
            else:
                # For certificates, use the price directly
                total += item.price * item.quantity
        return float(total)

    def get_total_sale(self, obj):
        """Calculate total sale amount"""
        total_amount = self.get_total_amount(obj)
        final_amount = self.get_final_amount(obj)
        return float(total_amount - final_amount)

    def get_address(self, obj):
        # Get address from the first masterclass in the order
        for item in obj.items.all():
            if item.masterclass:
                params = item.masterclass.parameters
                if isinstance(params, dict):
                    if 'parameters' in params and isinstance(params['parameters'], dict):
                        address = params['parameters'].get('Адрес', [''])
                        if address and isinstance(address, list):
                            return address[0]
                    elif 'Адрес' in params:
                        address = params['Адрес']
                        if isinstance(address, list):
                            return address[0]
                        return address
        return ''

    def get_contacts(self, obj):
        # Get contacts from the first masterclass in the order
        for item in obj.items.all():
            if item.masterclass:
                params = item.masterclass.parameters
                if isinstance(params, dict):
                    if 'parameters' in params and isinstance(params['parameters'], dict):
                        contacts = params['parameters'].get('Контакты', [''])
                        if contacts and isinstance(contacts, list):
                            return contacts[0]
                    elif 'Контакты' in params:
                        contacts = params['Контакты']
                        if isinstance(contacts, list):
                            return contacts[0]
                        return contacts
        return ''

    def validate_items(self, value):
        """
        Validate the items format and calculate total price
        """
        if not isinstance(value, list):
            raise serializers.ValidationError("Items must be a list")

        total_price = 0
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError("Each item must be a dictionary")
            
            required_fields = ['type', 'id', 'quantity']
            if not all(field in item for field in required_fields):
                raise serializers.ValidationError(f"Each item must contain {required_fields}")
            
            if item['type'] not in ['event', 'certificate']:
                raise serializers.ValidationError("Item type must be either 'event' or 'certificate'")
            
            if not isinstance(item['quantity'], int) or item['quantity'] <= 0:
                raise serializers.ValidationError("Quantity must be a positive integer")

        return value

    def update(self, instance, validated_data):
        status = validated_data.get('status', None)
        if status == 'paid':
            instance.mark_as_paid()
        else:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
        return instance 