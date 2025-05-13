from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, OrderItemViewSet, CartView

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'orderitems', OrderItemViewSet, basename='orderitem')

urlpatterns = [
    path('', include(router.urls)),
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/clear/', CartView.as_view(), name='cart-clear'),
] 