from django.urls import path

from web import views


urlpatterns = [
    path("", views.hand_list, name="hand_list"),
    path("hands/new/", views.hand_create, name="hand_create"),
    path("hands/<int:pk>/", views.hand_detail, name="hand_detail"),
]