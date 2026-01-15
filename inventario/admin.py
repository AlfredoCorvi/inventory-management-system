from django.contrib import admin
from .models import Proveedor, Material, Movimiento

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'rfc', 'contacto', 'telefono', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre', 'rfc']

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 'nombre', 'stock_actual', 
        'stock_minimo', 'unidad_medida', 'proveedor', 'activo'
    ]
    list_filter = ['unidad_medida', 'proveedor', 'activo']
    search_fields = ['codigo', 'nombre']
    readonly_fields = ['fecha_registro']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('proveedor')

@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = [
        'fecha', 'tipo', 'material', 'cantidad', 
        'stock_resultante', 'usuario', 'referencia'
    ]
    list_filter = ['tipo', 'fecha']
    search_fields = ['material__nombre', 'material__codigo', 'referencia']
    readonly_fields = ['fecha', 'stock_resultante']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('material', 'usuario')