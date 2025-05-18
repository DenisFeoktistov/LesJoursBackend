from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, OrderItemViewSet, UserPasswordViewSet
from .cart_views import (
    CartView,
    update_cart_from_cookies,
    promo_auth,
    promo_unauth,
    CheckoutOrderView
)

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='order-item')
router.register(r'user', UserPasswordViewSet, basename='user')
router.register(r'user-password', UserPasswordViewSet, basename='user-password')

urlpatterns = [
    path('', include(router.urls)),
    
    # Cart endpoints
    path('cart/<int:user_id>/', CartView.as_view(), name='cart'),
    path('cart/<int:user_id>/<int:product_unit_id>/<int:guests_amount>/', CartView.as_view(), name='add-to-cart'),
    path('cart/<int:user_id>/<str:product_unit_id>/', CartView.as_view(), name='add-to-cart-certificate'),
    path('cart/<int:user_id>/<int:product_unit_id>/', CartView.as_view(), name='remove-from-cart'),
    
    # Cart sync
    path('cart_list/<int:user_id>/', update_cart_from_cookies, name='update-cart-from-cookies'),
    
    # Promo code
    path('promo/check/<int:user_id>/', promo_auth, name='promo-auth'),
    path('promo/anon_check/', promo_unauth, name='promo-unauth'),

    path('checkout/<int:user_id>/', CheckoutOrderView.as_view(), name='checkout-order'),
] 