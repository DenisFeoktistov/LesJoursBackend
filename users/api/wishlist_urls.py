from django.urls import path
from .wishlist_views import WishlistView

urlpatterns = [
    path('<int:id>/', WishlistView.as_view(), name='wishlist-without-user'),
    path('<int:id>/<int:product_id>/', WishlistView.as_view(), name='wishlist-item-without-user'),
] 