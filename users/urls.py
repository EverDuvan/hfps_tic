from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('password_change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    
    # User Management (Admin only)
    path('manage/', views.UserListView.as_view(), name='user_list'),
    path('manage/create/', views.UserCreateView.as_view(), name='user_create'),
    path('manage/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_update'),
]
