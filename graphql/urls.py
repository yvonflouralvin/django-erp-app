from django.urls import path, include 
from .views import graphQL
from rest_framework.routers import DefaultRouter

urlpatterns = [
    path('<model>', graphQL, name="graph-ql")
]
 