from django.urls import path
from app.api import views
# from .views import login_api

urlpatterns = [
    path("login/", views.login_api, name="api_login"),
]
