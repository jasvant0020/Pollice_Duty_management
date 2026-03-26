from django.contrib import admin
from django.urls import path
from app import views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse
import os


urlpatterns = [
    path('jasvant0020_admin/', admin.site.urls),

    # Login panel pages
    path("", views.login_view, name="login"),
    path("login/", views.login_view, name="login"),
    path('logout/', views.logout_view, name='logout'),

    # GD Munsi Panel urls
    path('munsi_dashboard/', views.munsi_dashboard, name='munsi_dashboard'),
    path('police/', views.police_list, name='police_list'),
    path('vvip/', views.vvip_list, name='vvip_list'),
    path('assign_duty/', views.assign_duty, name='assign_duty'),
    path('munsi_profile/', views.munsi_profile, name='munsi_profile'),
    path('edit_munsi_profile/', views.edit_munsi_profile, name='edit_munsi_profile'),
    path('munsi_assign_duty/', views.munsi_assign_duty, name='munsi_assign_duty'),
    path("munsi_reassign_duty/<uuid:batch_id>/", views.munsi_reassign_duty, name="munsi_reassign_duty"),
    path("munsi_edit_vvip_duty/<uuid:batch_id>/", views.munsi_edit_vvip_duty, name="munsi_edit_vvip_duty"),
    path('munsi_active_duty/', views.munsi_active_duty, name='munsi_active_duty'),
    path('munsi_deactivate_duty_individual/<int:duty_id>/', views.munsi_deactivate_duty_individual, name='munsi_deactivate_duty_individual'),
    path("end-vvip-duty/<uuid:batch_id>/", views.munsi_end_vvip_duty, name="munsi_end_vvip_duty"),
    path("vvip-duty-print/<uuid:batch_id>/", views.munsi_vvip_duty_print, name="munsi_vvip_duty_print"),
    path("munsi_previous_duties/",views.munsi_previous_duties,name="munsi_previous_duties"),
    path("munsi_field_staff_requests/",views.munsi_field_staff_requests,name="munsi_field_staff_requests"),
    path('munsi_approve_request/<int:req_id>/', views.munsi_approve_request, name='munsi_approve_request'),
    path('munsi_reject_request/<int:req_id>/', views.munsi_reject_request, name='munsi_reject_request'),

     # Custom Admin Panel urls
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('profile/', views.profile, name='profile'),
    path("edit_profile/", views.edit_profile, name="edit_profile"),
    path('manage/', views.manage, name='manage'),
    path('police_hierarchy_table/', views.police_hierarchy_table, name='police_hierarchy_table'),
    path('manage_users/', views.manage_users, name='manage_users'),
    path('manage_security_categories/', views.manage_security_categories, name='manage_security_categories'),
    path('manage_vvip/', views.manage_vvip, name='manage_vvip'),
    path('add_vvip/', views.add_vvip, name='add_vvip'),
    path('edit_vvip/<int:vvip_id>/', views.edit_vvip, name='edit_vvip'),

    path('add_security_category/', views.add_security_category, name='add_security_category'),
    path('edit_security_category/<int:category_id>/', views.edit_security_category, name='edit_security_category'),
    path('delete_security_category/<int:category_id>/', views.delete_security_category, name='delete_security_category'),

    path('add_user/', views.add_user, name='add_user'),           
    path('manage_users/edit/<int:user_id>/', views.edit_user, name='edit_user'),  
    path('manage_users/delete/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'), 
    
    # Field staff Panel urls
    path("user_profile/", views.user_profile, name="user_profile"),
    path("edit_user_profile/", views.edit_user_profile, name="edit_user_profile"),
    path("user_assign_duty/", views.user_assign_duty, name="user_assign_duty"),
    path("duty_history/", views.duty_history, name="duty_history"),
    path("request_application_box/", views.request_application_box, name="request_application_box"), 
    path("request_history/", views.request_history, name="request_history"),  
    path("attendance_panel/", views.attendance_panel, name="attendance_panel"),

    #vvip panel urls
    path("vvip_profile/", views.vvip_profile, name="vvip_profile"),
    path("edit_vvip_profile/", views.edit_vvip_profile, name="edit_vvip_profile"),
    path("vvip_assigned_duty/", views.vvip_assigned_duty, name="vvip_assigned_duty"),
    path("vvip_request_history/", views.vvip_request_history, name="vvip_request_history"),
    path("vvip_request_application_box/", views.vvip_request_application_box, name="vvip_request_application_box"),

    #forgot password urls
    path("forgot_password/", views.forgot_password_view, name="forgot_password"),
    path("verify_otp/", views.verify_otp_view, name="verify_otp"),
    path("reset_password/", views.reset_password_view, name="reset_password"),

    #verify email
    path("send-email-otp/", views.send_email_otp, name="send_email_otp"),
    path("verify-email-otp/", views.verify_email_otp, name="verify_email_otp"),

    #centrelize notification url
    path("centrelize_Notifications/", views.centrelize_Notifications, name="centrelize_Notifications"),
    path("mark_notification_read/<int:notification_id>/",views.mark_notification_read,name="mark_notification_read"),
    path("delete_notification/<int:notification_id>/",views.delete_notification,name="delete_notification"),
    path("mark_all_notifications_read/",views.mark_all_notifications_read,name="mark_all_notifications_read"),
    path("delete_all_notifications/",views.delete_all_notifications,name="delete_all_notifications"),

    #centralized notification sending panel
    path("centrelize_notify/",views.centrelize_notify,name="centrelize_notify"),
    path("centrelize-notify-history/", views.centrelize_notify_history, name="centrelize_notify_history"),




    # Firebase push notification
    path("save-fcm-token/", views.save_fcm_token, name="save_fcm_token"),
    
    # # Firebase push notification 
    # path('firebase-messaging-sw.js', views.showFirebaseJS, name="show_firebase_js"),

    #API urls
    path("api/", include("app.api.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

def firebase_sw(request):
    file_path = os.path.join(settings.BASE_DIR, "firebase-messaging-sw.js")
    return FileResponse(open(file_path, "rb"), content_type="application/javascript")

urlpatterns += [
    path("firebase-messaging-sw.js", firebase_sw),
]