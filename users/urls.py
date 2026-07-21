from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ProfileView

router = DefaultRouter()



urlpatterns = [

    path("me/", ProfileView.as_view(), name="me"),

]
                             