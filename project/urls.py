"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
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
]
