"""how_late_is_muni URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
"""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from website import views

urlpatterns = [
    path('', views.index, name='index'),
    path('arrivals/buckets', views.get_arrival_buckets),
    path('routes', views.routes),
    path('stops', views.stops)
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
