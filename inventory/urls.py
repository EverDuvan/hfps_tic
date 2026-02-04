from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='home'),
    path('acta/maintenance/<int:pk>/', views.maintenance_acta_view, name='maintenance_acta'),
    path('acta/handover/<int:pk>/', views.handover_acta_view, name='handover_acta'),
    path('export/<str:model_name>/', views.export_data_view, name='export_data'),
    
    # Frontend URLs
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('inventory/', views.equipment_list_view, name='equipment_list'),
    path('inventory/new/', views.equipment_create_view, name='equipment_create'),
    path('inventory/area/new/', views.area_create_view, name='area_create'),
    path('inventory/costcenter/new/', views.cost_center_create_view, name='cost_center_create'),
    path('maintenance/new/', views.maintenance_create_view, name='maintenance_create'),
    path('users/', views.user_list_view, name='user_list'),
    path('users/new/', views.user_create_view, name='user_create'),
]
