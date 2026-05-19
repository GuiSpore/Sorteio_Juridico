from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('painel-magistrado/', views.painel_magistrado, name='painel_magistrado'),
    path('painel-assessor/', views.painel_assessor, name='painel_assessor'),
]