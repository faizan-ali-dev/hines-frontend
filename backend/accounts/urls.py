from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("sign-up/", views.sign_up, name="signup"),
    path("client-login/", views.client_login, name="login"),
    path("sign-out/", views.client_logout, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/demo/", views.demo_dashboard, name="demo-dashboard"),
    path("dashboard/client/", views.client_dashboard, name="client-dashboard"),
]
