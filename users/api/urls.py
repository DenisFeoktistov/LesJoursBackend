from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserProfileViewSet, RegistrationView, LoginView,
    RefreshTokenView, UserInfoView, LastSeenView,
    ChangePasswordView
)
from .wishlist_views import WishlistView

router = DefaultRouter()
router.register(r'profiles', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('wishlist/<int:id>/', WishlistView.as_view(), name='wishlist'),
    path('wishlist/<int:id>/<int:product_id>/', WishlistView.as_view(), name='wishlist-item'),
    path('token/refresh/', RefreshTokenView.as_view(), name='token-refresh'),
    path('user_info/<int:id>/', UserInfoView.as_view(), name='user-info'),
    path('last_seen/<int:id>/', LastSeenView.as_view(), name='last-seen'),
    path('change_pwd_lk/<int:id>/', ChangePasswordView.as_view(), name='change-password'),
] 