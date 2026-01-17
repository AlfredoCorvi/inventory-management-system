from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q, F
from decimal import Decimal
from .models import Material, Movimiento, Proveedor
from .forms import EntradaMaterialForm, SalidaMaterialForm
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from datetime import datetime

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

@login_required
@transaction.atomic
def registrar_entrada(request):
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
@transaction.atomic
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

@login_required
def generar_remision_pdf(request, movimiento_id):
    """
    Genera un PDF de remisión/documento para un movimiento específico.
    
    Este tipo de documento es común en operaciones de planta para:
    - Entradas: Comprobar recepción de material del proveedor
    - Salidas: Autorizar la entrega de material a un área/proyecto
    """
    
    movimiento = get_object_or_404(Movimiento, id=movimiento_id)
    
    # Crear el PDF en memoria
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # Contenedor de elementos
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para el título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para subtítulos
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    # ========== ENCABEZADO ==========
    if movimiento.tipo == 'ENTRADA':
        titulo = Paragraph("REMISIÓN DE ENTRADA", title_style)
        subtitulo = Paragraph("Comprobante de Recepción de Material", subtitle_style)
    else:
        titulo = Paragraph("REMISIÓN DE SALIDA", title_style)
        subtitulo = Paragraph("Autorización de Entrega de Material", subtitle_style)
    
    elements.append(titulo)
    elements.append(subtitulo)
    elements.append(Spacer(1, 0.3*inch))
    
    # ========== INFORMACIÓN DEL DOCUMENTO ==========
    info_data = [
        ['Folio:', f'#{movimiento.id:06d}'],
        ['Fecha:', movimiento.fecha.strftime('%d/%m/%Y %H:%M')],
        ['Tipo de Movimiento:', movimiento.get_tipo_display()],
        ['Referencia:', movimiento.referencia],
        ['Registrado por:', movimiento.usuario.get_full_name() or movimiento.usuario.username],
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # ========== INFORMACIÓN DEL MATERIAL ==========
    material_title = Paragraph("<b>DETALLE DEL MATERIAL</b>", styles['Heading2'])
    elements.append(material_title)
    elements.append(Spacer(1, 0.2*inch))
    
    material_data = [
        ['Campo', 'Información'],
        ['Código', movimiento.material.codigo],
        ['Nombre', movimiento.material.nombre],
        ['Descripción', movimiento.material.descripcion],
        ['Unidad de Medida', movimiento.material.get_unidad_medida_display()],
        ['Proveedor', movimiento.material.proveedor.nombre],
    ]
    
    material_table = Table(material_data, colWidths=[2*inch, 4.5*inch])
    material_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
    ]))
    
    elements.append(material_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # ========== MOVIMIENTO ==========
    movimiento_title = Paragraph("<b>INFORMACIÓN DEL MOVIMIENTO</b>", styles['Heading2'])
    elements.append(movimiento_title)
    elements.append(Spacer(1, 0.2*inch))
    
    # Usar color diferente según tipo
    if movimiento.tipo == 'ENTRADA':
        header_color = colors.HexColor('#27ae60')
    else:
        header_color = colors.HexColor('#3498db')
    
    movimiento_data = [
        ['Concepto', 'Valor'],
        ['Cantidad', f"{movimiento.cantidad} {movimiento.material.unidad_medida}"],
        ['Precio Unitario', f"${movimiento.material.precio_unitario:,.2f}"],
        ['Valor Total', f"${movimiento.valor_total:,.2f}"],
        ['Stock Resultante', f"{movimiento.stock_resultante} {movimiento.material.unidad_medida}"],
    ]
    
    movimiento_table = Table(movimiento_data, colWidths=[3*inch, 3.5*inch])
    movimiento_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
    ]))
    
    elements.append(movimiento_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # ========== OBSERVACIONES ==========
    if movimiento.observaciones:
        obs_title = Paragraph("<b>OBSERVACIONES</b>", styles['Heading3'])
        elements.append(obs_title)
        elements.append(Spacer(1, 0.1*inch))
        
        obs_text = Paragraph(movimiento.observaciones, styles['Normal'])
        elements.append(obs_text)
        elements.append(Spacer(1, 0.5*inch))
    else:
        elements.append(Spacer(1, 0.5*inch))
    
    # ========== FIRMAS ==========
    elements.append(Spacer(1, 0.7*inch))
    
    firma_data = [
        ['_________________________', '_________________________'],
        ['Entregó', 'Recibió'],
        ['', ''],
        ['Nombre:', 'Nombre:'],
        ['Firma:', 'Firma:'],
    ]
    
    firma_table = Table(firma_data, colWidths=[3*inch, 3*inch])
    firma_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 0),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 20),
    ]))
    
    elements.append(firma_table)
    
    # ========== FOOTER ==========
    elements.append(Spacer(1, 0.5*inch))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_CENTER
    )
    
    footer_text = f"""
    <i>Documento generado automáticamente por el Sistema de Control de Materiales<br/>
    Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</i>
    """
    footer = Paragraph(footer_text, footer_style)
    elements.append(footer)
    
    # Construir el PDF
    doc.build(elements)
    
    # Obtener el valor del buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Crear la respuesta HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="remision_{movimiento.tipo}_{movimiento.id}.pdf"'
    response.write(pdf)
    
    return response


@login_required
def generar_reporte_inventario_pdf(request):
    """
    Genera un reporte completo del inventario actual en PDF.
    """
    
    materiales = Material.objects.filter(activo=True).select_related('proveedor')
    
    # Crear el PDF en memoria
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # ========== TÍTULO ==========
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    titulo = Paragraph("REPORTE DE INVENTARIO", title_style)
    fecha = Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
                      ParagraphStyle('Subtitle', parent=styles['Normal'], 
                                   alignment=TA_CENTER, fontSize=10))
    
    elements.append(titulo)
    elements.append(fecha)
    elements.append(Spacer(1, 0.3*inch))
    
    # ========== RESUMEN ==========
    total_materiales = materiales.count()
    materiales_bajo_stock = materiales.filter(stock_actual__lte=F('stock_minimo')).count()
    valor_total = materiales.aggregate(
        total=Sum(F('stock_actual') * F('precio_unitario'))
    )['total'] or 0
    
    resumen_data = [
        ['RESUMEN GENERAL'],
        ['Total de Materiales', str(total_materiales)],
        ['Materiales con Stock Bajo', str(materiales_bajo_stock)],
        ['Valor Total del Inventario', f"${valor_total:,.2f}"],
    ]
    
    resumen_table = Table(resumen_data, colWidths=[4*inch, 2.5*inch])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#ecf0f1')),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(resumen_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # ========== TABLA DE MATERIALES ==========
    detalle_title = Paragraph("<b>DETALLE DE MATERIALES</b>", styles['Heading2'])
    elements.append(detalle_title)
    elements.append(Spacer(1, 0.2*inch))
    
    # Encabezados
    data = [['Código', 'Material', 'Stock', 'Unidad', 'P. Unit.', 'Valor', 'Estado']]
    
    # Datos
    for material in materiales:
        estado = '⚠ BAJO' if material.esta_bajo_stock else '✓ OK'
        data.append([
            material.codigo,
            Paragraph(material.nombre[:30], styles['Normal']),
            f"{material.stock_actual}",
            material.unidad_medida,
            f"${material.precio_unitario:,.2f}",
            f"${material.valor_inventario:,.2f}",
            estado
        ])
    
    tabla_materiales = Table(data, colWidths=[0.8*inch, 2*inch, 0.7*inch, 
                                               0.7*inch, 0.9*inch, 1*inch, 0.7*inch])
    tabla_materiales.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(tabla_materiales)
    
    # Footer
    elements.append(Spacer(1, 0.3*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_CENTER
    )
    footer = Paragraph(
        f"<i>Reporte generado automáticamente - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</i>",
        footer_style
    )
    elements.append(footer)
    
    # Construir PDF
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_inventario_{datetime.now().strftime("%Y%m%d")}.pdf"'
    response.write(pdf)
    
    return response