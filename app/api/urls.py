from django.urls import path
from app.api import views
# from .views import login_api

urlpatterns = [
    path("login/", views.login_api, name="api_login"),
    path("logout/", views.logout_api),
    path("update_staff_location/", views.update_staff_location, name="update_location"),
    path("staff-locations/<uuid:batch_id>/", views.get_staff_locations),
    path("update-vvip-location/", views.update_vvip_location),
]
