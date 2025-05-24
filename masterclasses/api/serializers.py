from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from ..models import MasterClass, Event
from django.utils.text import slugify


class EventSerializer(serializers.ModelSerializer):
    occupied_seats = serializers.IntegerField(read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'masterclass', 'start_datetime', 'end_datetime', 'available_seats', 'created_at', 'occupied_seats']
        read_only_fields = ['created_at', 'end_datetime']


class PriceSerializer(serializers.Serializer):
    start_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_start_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Start price must be non-negative.")
        return value

    def validate_final_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Final price must be non-negative.")
        return value


class MasterClassSerializer(serializers.ModelSerializer):
    events = EventSerializer(many=True, read_only=True)
    bucket_link = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    in_wishlist = serializers.SerializerMethodField()
    parameters = serializers.SerializerMethodField()
    details = serializers.SerializerMethodField()
    slug = serializers.CharField(
        required=False,
        validators=[UniqueValidator(queryset=MasterClass.objects.all())],
    )
    score_product_page = serializers.IntegerField(read_only=True)
    occupied_seats = serializers.IntegerField(read_only=True)

    class Meta:
        model = MasterClass
        fields = [
            'id', 'name', 'slug', 'short_description', 'long_description',
            'bucket_link', 'age_restriction', 'duration',
            'created_at', 'updated_at', 'events', 'location', 'price',
            'in_wishlist', 'parameters', 'details', 'score_product_page', 'occupied_seats'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at', 'in_wishlist']

    def get_bucket_link(self, obj):
        return [{"url": obj.bucket_link}]

    def get_price(self, obj):
        return {
            "start_price": obj.start_price,
            "final_price": obj.final_price
        }

    def get_in_wishlist(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj in request.user.profile.favorite_masterclasses.all()
        return False

    def get_parameters(self, obj):
        return obj.parameters

    def get_details(self, obj):
        return obj.details

    def to_internal_value(self, data):
        price_data = data.get('price', {})
        if not price_data:
            raise serializers.ValidationError({'price': 'This field is required and must include start_price and final_price.'})
        start_price = price_data.get('start_price')
        final_price = price_data.get('final_price')
        errors = {}
        if start_price is None:
            errors['start_price'] = 'This field is required.'
        elif float(start_price) < 0:
            errors['start_price'] = 'Start price must be non-negative.'
        if final_price is None:
            errors['final_price'] = 'This field is required.'
        elif float(final_price) < 0:
            errors['final_price'] = 'Final price must be non-negative.'
        if errors:
            raise serializers.ValidationError({'price': errors})
        data = data.copy()
        data['start_price'] = start_price
        data['final_price'] = final_price
        return super().to_internal_value(data)

    def validate(self, data):
        # Check for duplicate slug generated from name
        name = data.get('name', None)
        if name:
            slug = slugify(name)
            qs = MasterClass.objects.filter(slug=slug)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({'slug': 'A masterclass with this slug already exists.'})
        # Explicit price validation
        start_price = data.get('start_price', getattr(self.instance, 'start_price', None))
        final_price = data.get('final_price', getattr(self.instance, 'final_price', None))
        if start_price is not None and start_price < 0:
            raise serializers.ValidationError({'price': {'start_price': 'Start price must be non-negative.'}})
        if final_price is not None and final_price < 0:
            raise serializers.ValidationError({'price': {'final_price': 'Final price must be non-negative.'}})
        return data 

class ProductUnitSerializer(serializers.ModelSerializer):
    in_wishlist = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()
    bucket_link = serializers.SerializerMethodField()
    totalPrice = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    contacts = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    class Meta:
        model = MasterClass
        fields = [
            'id', 'name', 'in_wishlist', 'availability', 'bucket_link',
            'slug', 'totalPrice', 'date', 'address', 'contacts', 'type'
        ]

    def get_in_wishlist(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj in request.user.profile.favorite_masterclasses.all()
        return False

    def get_availability(self, obj):
        # Get the event from context
        event = self.context.get('event')
        if not event:
            return False
        return event.get_remaining_seats() > 0

    def get_bucket_link(self, obj):
        return [{"url": obj.bucket_link}]

    def get_totalPrice(self, obj):
        # Get guests amount from context
        guests_amount = self.context.get('guests_amount', 1)
        return float(obj.final_price * guests_amount)

    def get_date(self, obj):
        # Get the event from context
        event = self.context.get('event')
        if not event:
            return None
        return {
            'id': event.id,
            'start_datetime': event.start_datetime.isoformat(),
            'end_datetime': event.end_datetime.isoformat() if event.end_datetime else None
        }

    def get_address(self, obj):
        try:
            params = obj.parameters
            if isinstance(params, dict):
                # Try nested structure first
                if 'parameters' in params and isinstance(params['parameters'], dict):
                    address = params['parameters'].get('Адрес', [''])
                    if address and isinstance(address, list):
                        return address[0]
                # Try flat structure
                elif 'Адрес' in params:
                    address = params['Адрес']
                    if isinstance(address, list):
                        return address[0]
                    return address
            # Для отладки
            print(f"[DEBUG] parameters for address: {params}")
        except Exception as e:
            print(f"[ERROR] get_address: {e}")
        return ''

    def get_contacts(self, obj):
        try:
            params = obj.parameters
            if isinstance(params, dict):
                # Try nested structure first
                if 'parameters' in params and isinstance(params['parameters'], dict):
                    contacts = params['parameters'].get('Контакты', [''])
                    if contacts and isinstance(contacts, list):
                        return contacts[0]
                # Try flat structure
                elif 'Контакты' in params:
                    contacts = params['Контакты']
                    if isinstance(contacts, list):
                        return contacts[0]
                    return contacts
            # Для отладки
            print(f"[DEBUG] parameters for contacts: {params}")
        except Exception as e:
            print(f"[ERROR] get_contacts: {e}")
        return ''

    def get_type(self, obj):
        return 'master_class' 