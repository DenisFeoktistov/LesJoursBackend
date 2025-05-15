from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserProfileViewSet
from .wishlist_views import WishlistView

router = DefaultRouter()
router.register(r'profiles', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
    path('wishlist/<int:id>/', WishlistView.as_view(), name='wishlist'),
    path('wishlist/<int:id>/<int:product_id>/', WishlistView.as_view(), name='wishlist-item'),
] 