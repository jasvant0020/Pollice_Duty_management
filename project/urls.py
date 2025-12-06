from django.contrib import admin
from django.urls import path
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Login panel pages
    path("", views.login_view, name="login"),
    path("login/", views.login_view, name="login"),

    # GD Munsi Panel Pages
    path('munsi_dashboard/', views.dashboard, name='dashboard'),
    path('police/', views.police_list, name='police_list'),
    path('vvip/', views.vvip_list, name='vvip_list'),
    path('assign_duty/', views.assign_duty, name='assign_duty'),

     # Custom Admin Panel Pages
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage/', views.manage, name='manage'),
    path('police_hierarchy_table/', views.police_hierarchy_table, name='police_hierarchy_table'),
    path('manage_users/', views.manage_users, name='manage_users'),
    path('manage_security_categories/', views.manage_security_categories, name='manage_security_categories'),
    path('manage_vvip/', views.manage_vvip, name='manage_vvip'),
    path('add_vvip/', views.add_vvip, name='add_vvip'),
    path('edit_vvip/<int:vvip_id>/', views.edit_vvip, name='edit_vvip'),
    path('vvip_delete/<int:vvip_id>/', views.delete_vvip, name='delete_vvip'),


    # -------------------------------------------------------
    # UPDATED: Added CRUD URLs for Manage Users functionality
    # -------------------------------------------------------
    path('add_user/', views.add_user, name='add_user'),           
    path('manage_users/edit/<int:user_id>/', views.edit_user, name='edit_user'),  
    path('manage_users/delete/<int:user_id>/', views.delete_user, name='delete_user'), 
    # path('user_list/', views.user_list, name='user_list'),

    # -------------------------------------------------------
    # UPDATED: Added CRUD URLs for Manage Police Categories
    # -------------------------------------------------------
    path('add_security_category/', views.add_security_category, name='add_security_category'),
    path('edit_security_category/<int:category_id>/', views.edit_security_category, name='edit_security_category'),
    path('delete_security_category/<int:category_id>/', views.delete_security_category, name='delete_security_category'),

    # Custom user Panel Pages
    path("user_profile/", views.user_profile, name="user_profile"),
    path("user_assign_duty/", views.user_assign_duty, name="user_assign_duty"),
    path("duty_history/", views.duty_history, name="duty_history"),
    path("request_application_box/", views.request_application_box, name="request_application_box"),  
    path("Notifications/", views.Notifications, name="Notifications"),
    path("attendance_panel/", views.attendance_panel, name="attendance_panel"),
    
    # Firebase push notification 
    path('firebase-messaging-sw.js', views.showFirebaseJS, name="show_firebase_js"),
]
