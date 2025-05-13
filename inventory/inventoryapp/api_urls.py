from django.urls import path
from .api_views import InventoryAPI, AdminAPI

urlpatterns = [
    path('inventory/', InventoryAPI.as_view(), name='api_inventory'),
    path('admins/', AdminAPI.as_view(), name='api_admins'),
]
