from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import OrderSerializer, OrderItemSerializer
from ..models import Order, OrderItem
from ..utils import Cart
from rest_framework.views import APIView
from django.conf import settings
from masterclasses.models import Event


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="List all orders for the current user",
        responses={
            200: openapi.Response(
                description="List of orders",
                schema=OrderSerializer(many=True)
            )
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new order",
        request_body=OrderSerializer,
        responses={
            201: openapi.Response(
                description="Order created successfully",
                schema=OrderSerializer
            ),
            400: "Bad Request"
        }
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Get a specific order",
        responses={
            200: openapi.Response(
                description="Order details",
                schema=OrderSerializer
            ),
            404: "Not Found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update an order",
        request_body=OrderSerializer,
        responses={
            200: openapi.Response(
                description="Order updated successfully",
                schema=OrderSerializer
            ),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update an order",
        request_body=OrderSerializer,
        responses={
            200: openapi.Response(
                description="Order partially updated successfully",
                schema=OrderSerializer
            ),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete an order",
        responses={
            204: "No Content",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="List all items in an order",
        responses={
            200: openapi.Response(
                description="List of order items",
                schema=OrderItemSerializer(many=True)
            ),
            404: "Not Found"
        }
    )
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        order = self.get_object()
        items = order.items.all()
        serializer = OrderItemSerializer(items, many=True)
        return Response(serializer.data)


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all order items",
        responses={
            200: openapi.Response(
                description="List of order items",
                schema=OrderItemSerializer(many=True)
            )
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new order item",
        request_body=OrderItemSerializer,
        responses={
            201: openapi.Response(
                description="Order item created successfully",
                schema=OrderItemSerializer
            ),
            400: "Bad Request"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get a specific order item",
        responses={
            200: openapi.Response(
                description="Order item details",
                schema=OrderItemSerializer
            ),
            404: "Not Found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update an order item",
        request_body=OrderItemSerializer,
        responses={
            200: openapi.Response(
                description="Order item updated successfully",
                schema=OrderItemSerializer
            ),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update an order item",
        request_body=OrderItemSerializer,
        responses={
            200: openapi.Response(
                description="Order item partially updated successfully",
                schema=OrderItemSerializer
            ),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete an order item",
        responses={
            204: "No Content",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class CartView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        cart = Cart(request)
        return Response(cart.get_cart_data())

    def post(self, request):
        if request.path.endswith('clear/'):
            cart = Cart(request)
            cart.clear()
            cart = Cart(request)
            return Response(cart.get_cart_data())
        
        cart = Cart(request)
        item_type = request.data.get('type')
        item_id = request.data.get('id')
        quantity = int(request.data.get('quantity', 1))
        
        if not item_type or not item_id:
            return Response(
                {'error': 'Type and id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if item_type not in ['event', 'certificate']:
            return Response(
                {'error': 'Invalid item type'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if item_type == 'event':
            try:
                event = Event.objects.get(id=item_id)
                if event.get_remaining_seats() < quantity:
                    return Response(
                        {'error': 'Not enough seats available'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Event.DoesNotExist:
                return Response(
                    {'error': 'Event not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        if cart.add(item_type, item_id, quantity):
            return Response(cart.get_cart_data())
        else:
            return Response(
                {'error': 'Failed to add item to cart'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def put(self, request):
        cart = Cart(request)
        
        # Handle promo code update
        if 'promo_code' in request.data:
            cart.set_promo_code(request.data['promo_code'])
            return Response(cart.get_cart_data())
        
        # Handle item quantity update
        item_type = request.data.get('type')
        item_id = request.data.get('id')
        quantity = int(request.data.get('quantity', 0))
        
        if not item_type or not item_id:
            return Response(
                {'error': 'Type and id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if item_type == 'event':
            try:
                event = Event.objects.get(id=item_id)
                if event.get_remaining_seats() < quantity:
                    return Response(
                        {'error': 'Not enough seats available'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Event.DoesNotExist:
                return Response(
                    {'error': 'Event not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        cart.update(item_type, item_id, quantity)
        return Response(cart.get_cart_data())

    def delete(self, request):
        cart = Cart(request)
        item_type = request.data.get('type')
        item_id = request.data.get('id')
        
        if not item_type or not item_id:
            return Response(
                {'error': 'Type and id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        cart.remove(item_type, item_id)
        return Response(cart.get_cart_data()) 