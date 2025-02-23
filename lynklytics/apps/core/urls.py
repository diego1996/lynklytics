from django.urls import path
from . import views

urlpatterns = [
    path('mis-enlaces/', views.my_links, name='my_links'),
    path('enlace/<uuid:pk>/estadisticas/', views.link_stats, name='link_stats'),
    path('estadisticas/', views.global_stats, name='global_stats'),
    path('<str:short_code>/', views.redirect_link, name='redirect_link'),
    path('', views.shorten_url, name='shorten_url'),
]
