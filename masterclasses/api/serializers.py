from rest_framework import serializers
from ..models import MasterClass, Event


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'masterclass', 'start_datetime', 'end_datetime', 'available_seats', 'created_at']
        read_only_fields = ['created_at']


class MasterClassSerializer(serializers.ModelSerializer):
    events = EventSerializer(many=True, read_only=True)
    discounted_price = serializers.SerializerMethodField()

    class Meta:
        model = MasterClass
        fields = [
            'id', 'title', 'slug', 'description', 'price', 'discount',
            'discounted_price', 'age_restriction', 'cover_image',
            'created_at', 'updated_at', 'events'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']

    def get_discounted_price(self, obj):
        return obj.get_discounted_price() 