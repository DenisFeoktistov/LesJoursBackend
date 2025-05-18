from django.urls import path
from .views import fetch_cart_price, fetch_product_units

urlpatterns = [
    path('product_unit/total_amount_list/', fetch_cart_price, name='fetch-cart-price'),
    path('product_unit/list/', fetch_product_units, name='fetch-product-units'),
] 