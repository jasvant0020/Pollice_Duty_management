from django.contrib import admin
from django.urls import path
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # GD Munsi Panel Pages
    path('', views.dashboard, name='dashboard'),
    path('police/', views.police_list, name='police_list'),
    path('vvip/', views.vvip_list, name='vvip_list'),
    path('duty/assign/', views.assign_duty, name='assign_duty'),
     # Custom Admin Panel Pages
    path('admin_base/', views.admin_base, name='admin_base'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    # path('admin-panel/manage-users/', views.manage_users, name='manage_users'),
    # path('admin-panel/manage-police-categories/', views.manage_police_categories, name='manage_police_categories'),
    # path('admin-panel/manage-vvip-categories/', views.manage_vvip_categories, name='manage_vvip_categories'), 
    # path("dashboard/", views.user_dashboard, name="user_dashboard"),
    # Custom user Panel Pages
    path("user_dashboard/", views.user_base, name="user_base"),
    path("user_assign_duty/", views.user_assign_duty, name="user_assign_duty"),
    path("request_application_box/", views.request_application_box, name="request_application_box"),
    path("duty_history/", views.duty_history, name="duty_history"),
    path("Notifications/", views.Notifications, name="Notifications"),
    path("attendance_panel/", views.attendance_panel, name="attendance_panel"),
    path("user_profile/", views.user_profile, name="user_profile"),


    path('firebase-messaging-sw.js',views.showFirebaseJS,name="show_firebase_js"),
]
