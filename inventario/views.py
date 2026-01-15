from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q, F
from decimal import Decimal
from .models import Material, Movimiento, Proveedor
from .forms import EntradaMaterialForm, SalidaMaterialForm

@login_required
def dashboard(request):
    """Vista principal con resumen del inventario"""
    
    # Materiales con stock bajo
    materiales_bajo_stock = Material.objects.filter(
        activo=True,
        stock_actual__lte=F('stock_minimo')
    ).select_related('proveedor')
    
    # Estadísticas generales
    total_materiales = Material.objects.filter(activo=True).count()
    
    # Valor total del inventario
    valor_inventario = Material.objects.filter(activo=True).aggregate(
        total=Sum(F('stock_actual') * F('precio_unitario'))
    )['total'] or 0
    
    # Últimos movimientos
    ultimos_movimientos = Movimiento.objects.select_related(
        'material', 'usuario'
    )[:10]
    
    context = {
        'materiales_bajo_stock': materiales_bajo_stock,
        'total_materiales': total_materiales,
        'valor_inventario': valor_inventario,
        'ultimos_movimientos': ultimos_movimientos,
        'alertas_count': materiales_bajo_stock.count(),
    }
    
    return render(request, 'inventario/dashboard.html', context)


@login_required
def lista_materiales(request):
    """Lista de todos los materiales con filtros"""
    
    materiales = Material.objects.filter(activo=True).select_related('proveedor')
    
    # Búsqueda
    search = request.GET.get('search', '')
    if search:
        materiales = materiales.filter(
            Q(codigo__icontains=search) |
            Q(nombre__icontains=search) |
            Q(descripcion__icontains=search)
        )
    
    # Filtro por proveedor
    proveedor_id = request.GET.get('proveedor', '')
    if proveedor_id:
        materiales = materiales.filter(proveedor_id=proveedor_id)
    
    # Filtro por stock bajo
    solo_bajo_stock = request.GET.get('bajo_stock', '')
    if solo_bajo_stock:
        materiales = materiales.filter(stock_actual__lte=F('stock_minimo'))
    
    proveedores = Proveedor.objects.filter(activo=True)
    
    context = {
        'materiales': materiales,
        'proveedores': proveedores,
        'search': search,
        'proveedor_id': proveedor_id,
        'solo_bajo_stock': solo_bajo_stock,
    }
    
    return render(request, 'inventario/lista_materiales.html', context)


# ============================================
# AQUÍ VIENE LO IMPORTANTE: @transaction.atomic
# ============================================

@login_required
@transaction.atomic  # ← ESTO ES CLAVE
def registrar_entrada(request):
    """
    Registra una entrada de material.
    
    ¿Qué hace @transaction.atomic?
    -----------------------------
    Garantiza que TODAS las operaciones de base de datos dentro de esta función
    se ejecuten como una UNIDAD ATÓMICA:
    
    - Si TODO sale bien → se guarda todo (COMMIT)
    - Si ALGO falla → se deshace todo (ROLLBACK)
    
    En este caso:
    1. Actualizamos el stock del material
    2. Creamos el registro de movimiento
    
    Si falla el paso 2, el paso 1 también se deshace automáticamente.
    Esto evita inconsistencias como "el stock se actualizó pero no hay registro
    del movimiento" o viceversa.
    """
    
    if request.method == 'POST':
        form = EntradaMaterialForm(request.POST)
        
        if form.is_valid():
            material = form.cleaned_data['material']
            cantidad = form.cleaned_data['cantidad']
            referencia = form.cleaned_data['referencia']
            observaciones = form.cleaned_data['observaciones']
            
            # Guardar el stock anterior para auditoría
            stock_anterior = material.stock_actual
            
            # Actualizar stock
            material.stock_actual += cantidad
            material.save()
            
            # Crear registro de movimiento
            Movimiento.objects.create(
                material=material,
                tipo='ENTRADA',
                cantidad=cantidad,
                usuario=request.user,
                referencia=referencia,
                observaciones=observaciones,
                stock_resultante=material.stock_actual
            )
            
            messages.success(
                request, 
                f'Entrada registrada: {cantidad} {material.unidad_medida} de {material.nombre}. '
                f'Stock anterior: {stock_anterior}, Stock actual: {material.stock_actual}'
            )
            
            return redirect('dashboard')
    else:
        form = EntradaMaterialForm()
    
    return render(request, 'inventario/registrar_entrada.html', {'form': form})


@login_required
@transaction.atomic  # ← Igual aquí
def registrar_salida(request):
    """
    Registra una salida de material.
    
    IMPORTANTE: Aquí añadimos validación de negocio para evitar stock negativo.
    """
    
    if request.method == 'POST':
        form = SalidaMaterialForm(request.POST)
        
        if form.is_valid():
            material = form.cleaned_data['material']
            cantidad = form.cleaned_data['cantidad']
            referencia = form.cleaned_data['referencia']
            observaciones = form.cleaned_data['observaciones']
            
            # VALIDACIÓN CRÍTICA: Verificar stock disponible
            if material.stock_actual < cantidad:
                messages.error(
                    request,
                    f'Stock insuficiente. Disponible: {material.stock_actual} '
                    f'{material.unidad_medida}, Solicitado: {cantidad} {material.unidad_medida}'
                )
                return render(request, 'inventario/registrar_salida.html', {'form': form})
            
            # Guardar stock anterior
            stock_anterior = material.stock_actual
            
            # Actualizar stock
            material.stock_actual -= cantidad
            material.save()
            
            # Crear registro de movimiento
            Movimiento.objects.create(
                material=material,
                tipo='SALIDA',
                cantidad=cantidad,
                usuario=request.user,
                referencia=referencia,
                observaciones=observaciones,
                stock_resultante=material.stock_actual
            )
            
            # Alerta si quedó bajo stock mínimo
            if material.esta_bajo_stock:
                messages.warning(
                    request,
                    f'¡ALERTA! El material {material.nombre} está por debajo del stock mínimo. '
                    f'Actual: {material.stock_actual}, Mínimo: {material.stock_minimo}'
                )
            else:
                messages.success(
                    request,
                    f'Salida registrada: {cantidad} {material.unidad_medida} de {material.nombre}. '
                    f'Stock anterior: {stock_anterior}, Stock actual: {material.stock_actual}'
                )
            
            return redirect('dashboard')
    else:
        form = SalidaMaterialForm()
    
    return render(request, 'inventario/registrar_salida.html', {'form': form})


@login_required
def historial_movimientos(request):
    """Historial completo de movimientos con filtros"""
    
    movimientos = Movimiento.objects.select_related('material', 'usuario')
    
    # Filtro por tipo
    tipo = request.GET.get('tipo', '')
    if tipo:
        movimientos = movimientos.filter(tipo=tipo)
    
    # Filtro por material
    material_id = request.GET.get('material', '')
    if material_id:
        movimientos = movimientos.filter(material_id=material_id)
    
    # Filtro por fechas
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    if fecha_desde:
        movimientos = movimientos.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        movimientos = movimientos.filter(fecha__lte=fecha_hasta)
    
    materiales = Material.objects.filter(activo=True)
    
    context = {
        'movimientos': movimientos[:100],  # Limitar a 100 para performance
        'materiales': materiales,
        'tipo': tipo,
        'material_id': material_id,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    
    return render(request, 'inventario/historial_movimientos.html', context)


@login_required
def detalle_material(request, material_id):
    """Vista detallada de un material con su historial"""
    
    material = get_object_or_404(Material, id=material_id)
    
    # Últimos 20 movimientos del material
    movimientos = material.movimientos.select_related('usuario')[:20]
    
    # Estadísticas del material
    total_entradas = material.movimientos.filter(tipo='ENTRADA').aggregate(
        total=Sum('cantidad')
    )['total'] or 0
    
    total_salidas = material.movimientos.filter(tipo='SALIDA').aggregate(
        total=Sum('cantidad')
    )['total'] or 0
    
    context = {
        'material': material,
        'movimientos': movimientos,
        'total_entradas': total_entradas,
        'total_salidas': total_salidas,
    }
    
    return render(request, 'inventario/detalle_material.html', context)