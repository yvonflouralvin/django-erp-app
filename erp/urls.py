"""
URL configuration for erp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib import admin
from django.urls import path, include

from pathlib import Path
import os  
import json


urlpatterns = [
    path('admin/', admin.site.urls), 
    path('apps/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('apps/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 

    path('apps/core/', include("core.urls")),
    path('apps/graphql/', include("graphql.urls")),
]

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Loading Manifest
manifest_file = open("/configs/manifest.json")
manifest = json.load(manifest_file) 
addons = manifest['addons']

for index, app in enumerate(addons):
    urlpatterns.insert(index, path(f'apps/{app['name']}/', include(f'{app['name']}.urls')))
