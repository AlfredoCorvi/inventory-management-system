# Sistema de Control de Materiales

Sistema web para gestión integral de inventario de materiales en planta industrial, desarrollado con Django y PostgreSQL.

## Características Principales

- **Gestión de Inventario**: Control completo de stock con alertas automáticas de stock mínimo
- **Registro de Movimientos**: Trazabilidad completa de entradas y salidas con auditoría
- **Gestión de Proveedores**: Administración de proveedores y sus materiales
- **Generación de Documentos**: Creación automática de remisiones y reportes en PDF
- **Dashboard Interactivo**: Visualización en tiempo real del estado del inventario
- **Sistema de Alertas**: Notificaciones automáticas cuando el stock está bajo mínimo
- **Validaciones de Negocio**: Prevención de stock negativo y transacciones atómicas
- **API AJAX**: Consulta dinámica de información de materiales
- **Autenticación y Permisos**: Sistema completo de login y control de acceso

## Tecnologías

### Backend
- **Python 3.11**
- **Django 4.2** - Framework web
- **PostgreSQL 18.1** - Base de datos relacional
- **psycopg2** - Adaptador de PostgreSQL

### Frontend
- **Bootstrap 5.3** - Framework CSS
- **Bootstrap Icons** - Iconografía
- **JavaScript Vanilla** - Interactividad

### Librerías Adicionales
- **ReportLab** - Generación de PDFs
- **python-decouple** - Gestión de variables de entorno

## Modelo de Datos
```
┌─────────────────┐
│   Proveedor     │
│  - nombre       │
│  - rfc (unique) │
│  - contacto     │
│  - telefono     │
└────────┬────────┘
         │ 1
         │
         │ N
┌────────▼────────┐         ┌─────────────────┐
│   Material      │         │     Usuario     │
│  - codigo       │         │  (Django Auth)  │
│  - nombre       │         └────────┬────────┘
│  - stock_actual │                  │
│  - stock_minimo │                  │
│  - precio       │                  │
└────────┬────────┘                  │
         │ 1                         │
         │                           │
         │ N                         │ N
      ┌──▼──────────────────────────▼──┐
      │       Movimiento                │
      │  - tipo (ENTRADA/SALIDA)        │
      │  - cantidad                     │
      │  - fecha (auto)                 │
      │  - stock_resultante (auditoría) │
      │  - referencia                   │
      └─────────────────────────────────┘
```

## Instalación

### Prerrequisitos

- Python 3.11+
- PostgreSQL 18.1+
- Git

### 1. Clonar el repositorio
```bash
git clone https://github.com/TU_USUARIO/inventory_management_system.git
cd inventory_management_system
```

### 2. Crear entorno virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar PostgreSQL
```sql
-- En psql como postgres
CREATE DATABASE control_materiales_db;
CREATE USER materiales_user WITH PASSWORD 'tu_password_seguro';
GRANT ALL PRIVILEGES ON DATABASE control_materiales_db TO materiales_user;

-- Conectar a la base de datos
\c control_materiales_db

-- Dar permisos al esquema
GRANT ALL ON SCHEMA public TO materiales_user;
ALTER SCHEMA public OWNER TO materiales_user;

-- Para tests
ALTER USER materiales_user CREATEDB;
```

### 5. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:
```env
# Django
DEBUG=True
SECRET_KEY=tu-secret-key-super-segura-aqui

# PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=control_materiales_db
DB_USER=materiales_user
DB_PASSWORD=tu_password_seguro
DB_HOST=localhost
DB_PORT=5432
```

**Generar SECRET_KEY segura:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 6. Aplicar migraciones
```bash
python manage.py migrate
```

### 7. Crear superusuario
```bash
python manage.py createsuperuser
```

### 8. Ejecutar el servidor
```bash
python manage.py runserver
```

Accede a: `http://127.0.0.1:8000`

## Estructura del Proyecto
```
inventory_management_system/
├── control_materiales/          # Configuración del proyecto
│   ├── settings.py              # Configuración principal
│   ├── urls.py                  # URLs principales
│   └── wsgi.py                  # WSGI para deployment
├── inventario/                  # Aplicación principal
│   ├── models.py                # Modelos de datos
│   ├── views.py                 # Lógica de vistas
│   ├── forms.py                 # Formularios
│   ├── admin.py                 # Configuración del admin
│   ├── urls.py                  # URLs de la app
│   ├── tests.py                 # Suite de tests (29 tests)
│   ├── templates/               # Plantillas HTML
│   │   ├── inventario/
│   │   └── registration/
│   └── static/                  # Archivos estáticos
│       └── inventario/
│           ├── css/             # Estilos personalizados
│           └── js/              # JavaScript
├── .env                         # Variables de entorno (NO en Git)
├── .env.example                 # Ejemplo de variables
├── .gitignore                   # Archivos ignorados por Git
├── requirements.txt             # Dependencias Python
├── manage.py                    # CLI de Django
└── README.md                    # Este archivo
```

## 🧪 Testing

El proyecto incluye una suite completa de 29 tests con 93% de cobertura.

### Ejecutar tests
```bash
# Todos los tests
python manage.py test

# Con verbosidad
python manage.py test --verbosity=2

# Mantener BD de test (más rápido)
python manage.py test --keepdb

# Tests específicos
python manage.py test inventario.tests.MaterialModelTest
```

### Cobertura de código
```bash
# Ejecutar con cobertura
coverage run --source='.' manage.py test inventario

# Ver reporte
coverage report

# Generar HTML
coverage html
# Abrir: htmlcov/index.html
```

### Tipos de tests incluidos

- **Tests de Modelos** (14 tests): Validación de datos, constraints, properties
- **Tests de Vistas** (11 tests): Entradas/salidas, validaciones, autenticación
- **Tests de Transacciones** (1 test): Rollback en caso de error
- **Tests de API** (3 tests): Endpoints AJAX

## 📖 Uso

### Panel de Administración

Accede a `/admin/` para gestionar:
- Proveedores
- Materiales
- Ver movimientos (solo lectura)

### Dashboard

Accede a `/inventario/` para:
- Ver resumen del inventario
- Identificar materiales con stock bajo
- Ver últimos movimientos

### Registrar Entrada

`/inventario/entrada/`
- Selecciona material
- Ingresa cantidad recibida
- Especifica referencia (OC, factura)
- El sistema actualiza automáticamente el stock

### Registrar Salida

`/inventario/salida/`
- Selecciona material
- Ingresa cantidad a retirar
- El sistema valida stock disponible
- Genera alerta si queda bajo stock mínimo

### Generar PDFs

- **Remisión individual**: Desde el historial de movimientos
- **Reporte completo**: Desde dashboard o lista de materiales

## Seguridad

### Implementadas

- `@login_required` en todas las vistas
- CSRF protection habilitado
- Validación de formularios server-side
- `on_delete=PROTECT` para prevenir eliminación accidental
- Transacciones atómicas con `@transaction.atomic`


## Decisiones Técnicas Importantes

### ¿Por qué PostgreSQL?

- **Transacciones ACID robustas**: Crítico para inventarios
- **Integridad referencial**: Foreign keys garantizadas por BD
- **Tipos de datos precisos**: `NUMERIC` exacto para dinero
- **Consultas complejas**: JOINs optimizados para reportes
- **Escalabilidad**: Vertical (más común en plantas)

### ¿Por qué `@transaction.atomic`?

Garantiza que las operaciones sean atómicas:
- Si actualizar stock falla → no se crea movimiento
- Si crear movimiento falla → stock no se actualiza
- **Todo o nada** = consistencia de datos

### ¿Por qué guardar `stock_resultante` en Movimiento?

Para auditoría: permite saber el stock exacto en cualquier momento del pasado sin recalcular.

### ¿Por qué `DecimalField` y no `FloatField`?
```python
# Float tiene problemas de precisión
precio = 10.10
total = precio * 3  # 30.299999999999997

# Decimal es exacto
from decimal import Decimal
precio = Decimal('10.10')
total = precio * 3  # 30.30
```

## Funcionalidades Futuras (Roadmap)

- [ ] **Módulo de Producción**: Rastreo de materiales en procesos
- [ ] **Códigos de barras**: Escaneo rápido para entradas/salidas
- [ ] **Dashboard con gráficas**: Visualización de tendencias
- [ ] **Exportación a Excel**: Reportes personalizables
- [ ] **API REST completa**: Para integración con otros sistemas
- [ ] **Notificaciones por email**: Alertas automáticas
- [ ] **Historial de precios**: Tracking de variaciones
- [ ] **Multi-almacén**: Gestión de múltiples ubicaciones

## Contribuir

Este proyecto fue desarrollado como sistema de gestión de inventarios para uso en planta industrial.

### Convenciones de commits
```
feat: nueva funcionalidad
fix: corrección de bugs
refactor: mejora de código sin cambiar funcionalidad
test: agregar o modificar tests
docs: documentación
style: formato, punto y coma faltante, etc.
```

## 📚 Documentación Adicional

- [Django Documentation](https://docs.djangoproject.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Bootstrap Documentation](https://getbootstrap.com/docs/)
- [ReportLab Documentation](https://www.reportlab.com/docs/)


**Nota**: Este sistema está diseñado para uso en ambiente de desarrollo/staging.