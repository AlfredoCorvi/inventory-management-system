from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Proveedor(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    rfc = models.CharField(max_length=13, unique=True, verbose_name="RFC")
    contacto = models.CharField(max_length=100, verbose_name="Contacto")
    telefono = models.CharField(max_length=15, verbose_name="Teléfono")
    email = models.EmailField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Material(models.Model):
    UNIDADES = [
        ('PZ', 'Piezas'),
        ('KG', 'Kilogramos'),
        ('LT', 'Litros'),
        ('MT', 'Metros'),
        ('M2', 'Metros cuadrados'),
        ('CJ', 'Cajas'),
    ]
    
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    descripcion = models.TextField(verbose_name="Descripción")
    unidad_medida = models.CharField(
        max_length=3, 
        choices=UNIDADES,
        verbose_name="Unidad de medida"
    )
    stock_actual = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Stock actual"
    )
    stock_minimo = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Stock mínimo"
    )
    precio_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Precio unitario"
    )
    proveedor = models.ForeignKey(
        Proveedor, 
        on_delete=models.PROTECT,
        related_name='materiales'
    )
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"
        ordering = ['codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    @property
    def esta_bajo_stock(self):
        return self.stock_actual <= self.stock_minimo
    
    @property
    def valor_inventario(self):
        return self.stock_actual * self.precio_unitario


class Movimiento(models.Model):
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
    ]
    
    material = models.ForeignKey(
        Material, 
        on_delete=models.PROTECT,
        related_name='movimientos'
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    referencia = models.CharField(
        max_length=100,
        verbose_name="Referencia (OC, Requisición, etc.)"
    )
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    
    # Para calcular el stock después del movimiento
    stock_resultante = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Stock después del movimiento"
    )
    
    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.tipo} - {self.material.codigo} - {self.cantidad}"
    
    @property
    def valor_total(self):
        return self.cantidad * self.material.precio_unitario