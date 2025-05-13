from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from ..models import MasterClass, Event
from django.utils.text import slugify


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'masterclass', 'start_datetime', 'end_datetime', 'available_seats', 'created_at']
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
    slug = serializers.CharField(
        required=False,
        validators=[UniqueValidator(queryset=MasterClass.objects.all())],
    )

    class Meta:
        model = MasterClass
        fields = [
            'id', 'name', 'slug', 'short_description',
            'bucket_link', 'age_restriction', 'duration',
            'created_at', 'updated_at', 'events', 'location', 'price',
            'in_wishlist'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at', 'in_wishlist']

    def get_bucket_link(self, obj):
        return [{"url": url} for url in obj.bucket_link]

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