from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MasterClassViewSet, EventViewSet, ProductUnitListView

router = DefaultRouter()
router.register(r'masterclasses', MasterClassViewSet)
router.register(r'events', EventViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('product_unit/list/', ProductUnitListView.as_view(), name='product-unit-list'),
] 