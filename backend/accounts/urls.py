from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("csrf/", views.csrf, name="csrf"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.client_login, name="login"),
    path("logout/", views.client_logout, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
