from django.urls import path
from . import views

urlpatterns = [
    path('nasa_rss/', views.proxy_nasa_rss, name='nasa_rss'),
    path('nasa_youtube/', views.proxy_nasa_youtube, name='nasa_youtube')
]