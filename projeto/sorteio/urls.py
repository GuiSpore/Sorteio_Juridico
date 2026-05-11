from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('painel-juiz/', views.painel_juiz, name='painel_juiz'),
    path('painel-assessor/', views.painel_assessor, name='painel_assessor'),
]