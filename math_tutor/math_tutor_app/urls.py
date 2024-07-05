from django.urls import path
from math_tutor_app import views

urlpatterns = [
    path("", views.home, name="home"),
]