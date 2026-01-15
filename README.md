# Sistema de Control de Materiales

Sistema web para gestión de inventario de materiales en planta industrial, desarrollado con Django.

# Características

- Registro de entradas y salidas de materiales
- Control de stock en tiempo real
- Gestión de proveedores
- Generación de documentos (remisiones/facturas) en PDF
- Alertas de stock mínimo
- Historial completo de movimientos
- Reportes y análisis de consumo

## Tecnologías

- Python 3.x
- Django 4.x
- PostgreSQL / SQLite
- ReportLab (generación de PDFs)
- Bootstrap 5 (interfaz)

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/AlfredoCorvi/inventory-management-system
cd inventory-management-system
```

2. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar base de datos:
```bash
python manage.py migrate
python manage.py createsuperuser
```

5. Ejecutar servidor:
```bash
python manage.py runserver
```

# Modelo de Datos

- **Material**: Información del material (código, nombre, stock, precio)
- **Proveedor**: Datos de proveedores
- **Movimiento**: Registro de entradas/salidas con trazabilidad
- **Usuario**: Control de acceso y auditoría

## 🎯 Próximas Mejoras

- [ ] Integración con código de barras
- [ ] Dashboard con gráficas
- [ ] Exportación a Excel
- [ ] API REST
- [ ] Notificaciones por email

# Autor

Desarrollado como proyecto de práctica para entrevista técnica.