from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from ..models import MasterClass, Event
from django.utils.text import slugify


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'masterclass', 'start_datetime', 'end_datetime', 'available_seats', 'created_at']
        read_only_fields = ['created_at', 'end_datetime']


class MasterClassSerializer(serializers.ModelSerializer):
    events = EventSerializer(many=True, read_only=True)
    bucket_link = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    slug = serializers.CharField(
        required=False,
        validators=[UniqueValidator(queryset=MasterClass.objects.all())],
    )

    class Meta:
        model = MasterClass
        fields = [
            'id', 'title', 'slug', 'description', 'start_price', 'final_price',
            'bucket_link', 'age_restriction', 'duration',
            'created_at', 'updated_at', 'events', 'price'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']

    def validate_start_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Start price must be non-negative.")
        return value

    def validate_final_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Final price must be non-negative.")
        return value

    def get_bucket_link(self, obj):
        return [{"url": url} for url in obj.bucket_list]

    def get_price(self, obj):
        return {
            "start_price": obj.start_price,
            "final_price": obj.final_price
        }

    def validate(self, data):
        # Check for duplicate slug generated from title
        title = data.get('title', None)
        if title:
            slug = slugify(title)
            qs = MasterClass.objects.filter(slug=slug)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({'slug': 'A masterclass with this slug already exists.'})
        return data 