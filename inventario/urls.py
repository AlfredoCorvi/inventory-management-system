from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('materiales/', views.lista_materiales, name='lista_materiales'),
    path('materiales/<int:material_id>/', views.detalle_material, name='detalle_material'),
    path('entrada/', views.registrar_entrada, name='registrar_entrada'),
    path('salida/', views.registrar_salida, name='registrar_salida'),
    path('historial/', views.historial_movimientos, name='historial_movimientos'),
]