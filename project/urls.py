from django.contrib import admin
from django.urls import path
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('police/', views.police_list, name='police_list'),
    path('vvip/', views.vvip_list, name='vvip_list'),
    path('duty/assign/', views.assign_duty, name='assign_duty'),
     # Custom Admin Panel Pages (your dashboard, users, categories)
    path('admin-panel/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/manage-users/', views.manage_users, name='manage_users'),
    path('admin-panel/manage-police-categories/', views.manage_police_categories, name='manage_police_categories'),
    path('admin-panel/manage-vvip-categories/', views.manage_vvip_categories, name='manage_vvip_categories'),
    path("dashboard/", views.user_dashboard, name="user_dashboard"),
]
