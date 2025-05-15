from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, OrderItemViewSet
from .cart_views import (
    CartView,
    fetch_product_units,
    update_cart_from_cookies,
    fetch_cart_price,
    promo_auth,
    promo_unauth
)

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='order-item')

urlpatterns = [
    path('', include(router.urls)),
    
    # Cart endpoints
    path('cart/<int:user_id>/', CartView.as_view(), name='cart'),
    path('cart/<int:user_id>/<int:product_unit_id>/<int:guests_amount>/', CartView.as_view(), name='add-to-cart'),
    path('cart/<int:user_id>/<str:product_unit_id>/', CartView.as_view(), name='add-to-cart-certificate'),
    path('cart/<int:user_id>/<int:product_unit_id>/', CartView.as_view(), name='remove-from-cart'),
    
    # Product units
    path('product_unit/list/', fetch_product_units, name='fetch-product-units'),
    
    # Cart sync
    path('cart_list/<int:user_id>/', update_cart_from_cookies, name='update-cart-from-cookies'),
    
    # Price calculation
    path('product_unit/total_amount_list/', fetch_cart_price, name='fetch-cart-price'),
    
    # Promo code
    path('promo/check/<int:user_id>/', promo_auth, name='promo-auth'),
    path('promo/anon_check/', promo_unauth, name='promo-unauth'),
] 