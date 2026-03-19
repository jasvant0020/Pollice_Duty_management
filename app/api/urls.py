from django.urls import path
from app.api import views
# from .views import login_api

urlpatterns = [
    path("login/", views.login_api, name="api_login"),
    path("logout/", views.logout_api),
    path("update-location/", views.update_staff_location, name="update_location"),
]
