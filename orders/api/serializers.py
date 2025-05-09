from rest_framework import serializers
from ..models import Order, OrderItem
from masterclasses.api.serializers import MasterClassSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    masterclass = MasterClassSerializer(read_only=True)
    masterclass_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'masterclass', 'masterclass_id', 'quantity', 'price']
        read_only_fields = ['price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'items', 'status', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['user', 'total_price', 'created_at', 'updated_at']

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