from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('materiales/', views.lista_materiales, name='lista_materiales'),
    path('materiales/<int:material_id>/', views.detalle_material, name='detalle_material'),
    path('entrada/', views.registrar_entrada, name='registrar_entrada'),
    path('salida/', views.registrar_salida, name='registrar_salida'),
    path('historial/', views.historial_movimientos, name='historial_movimientos'),
    
    # PDFs
    path('pdf/remision/<int:movimiento_id>/', views.generar_remision_pdf, name='generar_remision_pdf'),
    path('pdf/reporte-inventario/', views.generar_reporte_inventario_pdf, name='generar_reporte_inventario_pdf'),
    # AJAX
    path('api/material/<int:material_id>/', views.obtener_info_material, name='obtener_info_material'),
]