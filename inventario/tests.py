from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from .models import Proveedor, Material, Movimiento

class ProveedorModelTest(TestCase):
    """Tests para el modelo Proveedor"""
    
    def setUp(self):
        self.proveedor = Proveedor.objects.create(
            nombre="Proveedor Test",
            rfc="TEST123456789",
            contacto="Juan Pérez",
            telefono="5551234567",
            email="test@proveedor.com",
            activo=True
        )
    
    def test_proveedor_creation(self):
        """Test que un proveedor se crea correctamente"""
        self.assertEqual(self.proveedor.nombre, "Proveedor Test")
        self.assertEqual(self.proveedor.rfc, "TEST123456789")
        self.assertTrue(self.proveedor.activo)
    
    def test_proveedor_str(self):
        """Test del método __str__"""
        self.assertEqual(str(self.proveedor), "Proveedor Test")
    
    def test_rfc_unique(self):
        """Test que el RFC es único"""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Proveedor.objects.create(
                nombre="Otro Proveedor",
                rfc="TEST123456789",  # RFC duplicado
                contacto="Test",
                telefono="1234567890"
            )


class MaterialModelTest(TestCase):
    """Tests para el modelo Material"""
    
    def setUp(self):
        self.proveedor = Proveedor.objects.create(
            nombre="Proveedor Test",
            rfc="TEST123456789",
            contacto="Test",
            telefono="1234567890"
        )
        
        self.material = Material.objects.create(
            codigo="MAT001",
            nombre="Tornillo M8",
            descripcion="Tornillo métrico 8mm",
            unidad_medida="PZ",
            stock_actual=Decimal('100.00'),
            stock_minimo=Decimal('20.00'),
            precio_unitario=Decimal('5.50'),
            proveedor=self.proveedor,
            activo=True
        )
    
    def test_material_creation(self):
        """Test que un material se crea correctamente"""
        self.assertEqual(self.material.codigo, "MAT001")
        self.assertEqual(self.material.nombre, "Tornillo M8")
        self.assertEqual(self.material.stock_actual, Decimal('100.00'))
    
    def test_material_str(self):
        """Test del método __str__"""
        self.assertEqual(str(self.material), "MAT001 - Tornillo M8")
    
    def test_esta_bajo_stock_false(self):
        """Test que detecta cuando NO está bajo stock"""
        self.assertFalse(self.material.esta_bajo_stock)
    
    def test_esta_bajo_stock_true(self):
        """Test que detecta cuando SÍ está bajo stock"""
        self.material.stock_actual = Decimal('15.00')
        self.material.save()
        self.assertTrue(self.material.esta_bajo_stock)
    
    def test_valor_inventario(self):
        """Test del cálculo del valor del inventario"""
        valor_esperado = Decimal('100.00') * Decimal('5.50')
        self.assertEqual(self.material.valor_inventario, valor_esperado)
    
    def test_codigo_unique(self):
        """Test que el código es único"""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Material.objects.create(
                codigo="MAT001",  # Código duplicado
                nombre="Otro Material",
                descripcion="Test",
                unidad_medida="KG",
                stock_actual=Decimal('50.00'),
                stock_minimo=Decimal('10.00'),
                precio_unitario=Decimal('10.00'),
                proveedor=self.proveedor
            )
    
    def test_proveedor_protection(self):
        """Test que no se puede eliminar un proveedor con materiales"""
        from django.db.models.deletion import ProtectedError
        with self.assertRaises(ProtectedError):
            self.proveedor.delete()


class MovimientoModelTest(TestCase):
    """Tests para el modelo Movimiento"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.proveedor = Proveedor.objects.create(
            nombre="Proveedor Test",
            rfc="TEST123456789",
            contacto="Test",
            telefono="1234567890"
        )
        
        self.material = Material.objects.create(
            codigo="MAT001",
            nombre="Tornillo M8",
            descripcion="Test",
            unidad_medida="PZ",
            stock_actual=Decimal('100.00'),
            stock_minimo=Decimal('20.00'),
            precio_unitario=Decimal('5.50'),
            proveedor=self.proveedor
        )
    
    def test_movimiento_entrada_creation(self):
        """Test crear un movimiento de entrada"""
        movimiento = Movimiento.objects.create(
            material=self.material,
            tipo='ENTRADA',
            cantidad=Decimal('50.00'),
            usuario=self.user,
            referencia='OC-001',
            observaciones='Compra mensual',
            stock_resultante=Decimal('150.00')
        )
        
        self.assertEqual(movimiento.tipo, 'ENTRADA')
        self.assertEqual(movimiento.cantidad, Decimal('50.00'))
        self.assertEqual(movimiento.stock_resultante, Decimal('150.00'))
    
    def test_movimiento_salida_creation(self):
        """Test crear un movimiento de salida"""
        movimiento = Movimiento.objects.create(
            material=self.material,
            tipo='SALIDA',
            cantidad=Decimal('30.00'),
            usuario=self.user,
            referencia='REQ-001',
            observaciones='Producción',
            stock_resultante=Decimal('70.00')
        )
        
        self.assertEqual(movimiento.tipo, 'SALIDA')
        self.assertEqual(movimiento.cantidad, Decimal('30.00'))
    
    def test_valor_total(self):
        """Test del cálculo del valor total del movimiento"""
        movimiento = Movimiento.objects.create(
            material=self.material,
            tipo='ENTRADA',
            cantidad=Decimal('10.00'),
            usuario=self.user,
            referencia='TEST',
            stock_resultante=Decimal('110.00')
        )
        
        valor_esperado = Decimal('10.00') * Decimal('5.50')
        self.assertEqual(movimiento.valor_total, valor_esperado)
    
    def test_material_protection(self):
        """Test que no se puede eliminar un material con movimientos"""
        Movimiento.objects.create(
            material=self.material,
            tipo='ENTRADA',
            cantidad=Decimal('10.00'),
            usuario=self.user,
            referencia='TEST',
            stock_resultante=Decimal('110.00')
        )
        
        from django.db.models.deletion import ProtectedError
        with self.assertRaises(ProtectedError):
            self.material.delete()


class RegistrarEntradaViewTest(TestCase):
    """Tests para la vista de registrar entrada"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.proveedor = Proveedor.objects.create(
            nombre="Proveedor Test",
            rfc="TEST123456789",
            contacto="Test",
            telefono="1234567890"
        )
        
        self.material = Material.objects.create(
            codigo="MAT001",
            nombre="Tornillo M8",
            descripcion="Test",
            unidad_medida="PZ",
            stock_actual=Decimal('100.00'),
            stock_minimo=Decimal('20.00'),
            precio_unitario=Decimal('5.50'),
            proveedor=self.proveedor
        )
        
        self.url = reverse('registrar_entrada')
    
    def test_view_requiere_login(self):
        """Test que la vista requiere autenticación"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Redirect a login
        self.assertIn('/accounts/login/', response.url)
    
    def test_view_accesible_con_login(self):
        """Test que usuario logueado puede acceder"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventario/registrar_entrada.html')
    
    def test_registrar_entrada_incrementa_stock(self):
        """Test CRÍTICO: Entrada incrementa stock correctamente"""
        self.client.login(username='testuser', password='testpass123')
        
        stock_inicial = self.material.stock_actual
        cantidad_entrada = Decimal('50.00')
        
        response = self.client.post(self.url, {
            'material': self.material.id,
            'cantidad': cantidad_entrada,
            'referencia': 'OC-TEST-001',
            'observaciones': 'Test de entrada'
        })
        
        # Verificar redirect
        self.assertEqual(response.status_code, 302)
        
        # Recargar material desde BD
        self.material.refresh_from_db()
        
        # Verificar que el stock aumentó
        self.assertEqual(
            self.material.stock_actual,
            stock_inicial + cantidad_entrada
        )
    
    def test_registrar_entrada_crea_movimiento(self):
        """Test que se crea el registro de movimiento"""
        self.client.login(username='testuser', password='testpass123')
        
        movimientos_antes = Movimiento.objects.count()
        
        self.client.post(self.url, {
            'material': self.material.id,
            'cantidad': Decimal('25.00'),
            'referencia': 'OC-TEST-002',
            'observaciones': 'Test'
        })
        
        movimientos_despues = Movimiento.objects.count()
        
        # Verificar que se creó un movimiento
        self.assertEqual(movimientos_despues, movimientos_antes + 1)
        
        # Verificar el movimiento creado
        movimiento = Movimiento.objects.latest('fecha')
        self.assertEqual(movimiento.tipo, 'ENTRADA')
        self.assertEqual(movimiento.cantidad, Decimal('25.00'))
        self.assertEqual(movimiento.material, self.material)
        self.assertEqual(movimiento.usuario, self.user)


class RegistrarSalidaViewTest(TestCase):
    """Tests para la vista de registrar salida"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.proveedor = Proveedor.objects.create(
            nombre="Proveedor Test",
            rfc="TEST123456789",
            contacto="Test",
            telefono="1234567890"
        )
        
        self.material = Material.objects.create(
            codigo="MAT001",
            nombre="Tornillo M8",
            descripcion="Test",
            unidad_medida="PZ",
            stock_actual=Decimal('100.00'),
            stock_minimo=Decimal('20.00'),
            precio_unitario=Decimal('5.50'),
            proveedor=self.proveedor
        )
        
        self.url = reverse('registrar_salida')
    
    def test_view_requiere_login(self):
        """Test que la vista requiere autenticación"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
    
    def test_registrar_salida_decrementa_stock(self):
        """Test CRÍTICO: Salida decrementa stock correctamente"""
        self.client.login(username='testuser', password='testpass123')
        
        stock_inicial = self.material.stock_actual
        cantidad_salida = Decimal('30.00')
        
        response = self.client.post(self.url, {
            'material': self.material.id,
            'cantidad': cantidad_salida,
            'referencia': 'REQ-TEST-001',
            'observaciones': 'Test de salida'
        })
        
        self.assertEqual(response.status_code, 302)
        
        self.material.refresh_from_db()
        
        # Verificar que el stock disminuyó
        self.assertEqual(
            self.material.stock_actual,
            stock_inicial - cantidad_salida
        )
    
    def test_no_permite_stock_negativo(self):
        """Test CRÍTICO: No permite salidas que generen stock negativo"""
        self.client.login(username='testuser', password='testpass123')
        
        stock_inicial = self.material.stock_actual
        cantidad_excesiva = Decimal('150.00')  # Más del stock disponible
        
        response = self.client.post(self.url, {
            'material': self.material.id,
            'cantidad': cantidad_excesiva,
            'referencia': 'REQ-TEST-002',
            'observaciones': 'Test'
        })
        
        # Debe quedarse en la misma página (status 200)
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el stock NO cambió
        self.material.refresh_from_db()
        self.assertEqual(self.material.stock_actual, stock_inicial)
    
    def test_alerta_stock_bajo_minimo(self):
        """Test que genera alerta cuando stock queda bajo mínimo"""
        self.client.login(username='testuser', password='testpass123')
        
        # Dejar el stock justo por debajo del mínimo
        cantidad_salida = Decimal('85.00')  # 100 - 85 = 15 (menor que mínimo de 20)
        
        response = self.client.post(self.url, {
            'material': self.material.id,
            'cantidad': cantidad_salida,
            'referencia': 'REQ-TEST-003',
            'observaciones': 'Test'
        }, follow=True)
        
        # Verificar que hay un mensaje de advertencia
        messages = list(response.context['messages'])
        self.assertTrue(any('ALERTA' in str(m) for m in messages))


class TransactionAtomicTest(TestCase):
    """Tests para verificar @transaction.atomic"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.proveedor = Proveedor.objects.create(
            nombre="Proveedor Test",
            rfc="TEST123456789",
            contacto="Test",
            telefono="1234567890"
        )
        
        self.material = Material.objects.create(
            codigo="MAT001",
            nombre="Tornillo M8",
            descripcion="Test",
            unidad_medida="PZ",
            stock_actual=Decimal('100.00'),
            stock_minimo=Decimal('20.00'),
            precio_unitario=Decimal('5.50'),
            proveedor=self.proveedor
        )
    
    def test_rollback_en_error(self):
        """Test CRÍTICO: Rollback si falla alguna operación"""
        from django.db import transaction
        
        stock_inicial = self.material.stock_actual
        movimientos_iniciales = Movimiento.objects.count()
        
        # Simular una transacción que falla
        try:
            with transaction.atomic():
                # Actualizar stock
                self.material.stock_actual += Decimal('50.00')
                self.material.save()
                
                # Forzar un error antes de crear el movimiento
                raise Exception("Error simulado")
                
                # Este código nunca se ejecuta
                Movimiento.objects.create(
                    material=self.material,
                    tipo='ENTRADA',
                    cantidad=Decimal('50.00'),
                    usuario=self.user,
                    referencia='TEST',
                    stock_resultante=self.material.stock_actual
                )
        except Exception:
            pass
        
        # Recargar desde BD
        self.material.refresh_from_db()
        
        # Verificar ROLLBACK: el stock NO cambió
        self.assertEqual(self.material.stock_actual, stock_inicial)
        
        # Verificar que NO se creó el movimiento
        self.assertEqual(Movimiento.objects.count(), movimientos_iniciales)


class DashboardViewTest(TestCase):
    """Tests para el dashboard"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.proveedor = Proveedor.objects.create(
            nombre="Proveedor Test",
            rfc="TEST123456789",
            contacto="Test",
            telefono="1234567890"
        )
        
        # Material con stock bajo
        self.material_bajo = Material.objects.create(
            codigo="MAT001",
            nombre="Material Bajo Stock",
            descripcion="Test",
            unidad_medida="PZ",
            stock_actual=Decimal('10.00'),
            stock_minimo=Decimal('20.00'),
            precio_unitario=Decimal('5.00'),
            proveedor=self.proveedor
        )
        
        # Material con stock OK
        self.material_ok = Material.objects.create(
            codigo="MAT002",
            nombre="Material Stock OK",
            descripcion="Test",
            unidad_medida="KG",
            stock_actual=Decimal('100.00'),
            stock_minimo=Decimal('20.00'),
            precio_unitario=Decimal('10.00'),
            proveedor=self.proveedor
        )
        
        self.url = reverse('dashboard')
    
    def test_dashboard_requiere_login(self):
        """Test que el dashboard requiere autenticación"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
    
    def test_dashboard_muestra_alertas_stock_bajo(self):
        """Test que el dashboard muestra materiales con stock bajo"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('materiales_bajo_stock', response.context)
        
        # Verificar que detecta el material bajo
        materiales_bajo = response.context['materiales_bajo_stock']
        self.assertEqual(materiales_bajo.count(), 1)
        self.assertEqual(materiales_bajo.first(), self.material_bajo)
    
    def test_dashboard_calcula_valor_inventario(self):
        """Test que calcula correctamente el valor del inventario"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        valor_esperado = (
            Decimal('10.00') * Decimal('5.00') +  # Material bajo
            Decimal('100.00') * Decimal('10.00')  # Material OK
        )
        
        self.assertEqual(
            response.context['valor_inventario'],
            valor_esperado
        )


class APIEndpointTest(TestCase):
    """Tests para el endpoint AJAX"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.proveedor = Proveedor.objects.create(
            nombre="Proveedor Test",
            rfc="TEST123456789",
            contacto="Test",
            telefono="1234567890"
        )
        
        self.material = Material.objects.create(
            codigo="MAT001",
            nombre="Tornillo M8",
            descripcion="Test",
            unidad_medida="PZ",
            stock_actual=Decimal('100.00'),
            stock_minimo=Decimal('20.00'),
            precio_unitario=Decimal('5.50'),
            proveedor=self.proveedor
        )
    
    def test_api_requiere_login(self):
        """Test que el endpoint requiere autenticación"""
        url = reverse('obtener_info_material', args=[self.material.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
    
    def test_api_devuelve_json(self):
        """Test que devuelve JSON con info del material"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('obtener_info_material', args=[self.material.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['codigo'], 'MAT001')
        self.assertEqual(data['stock_actual'], '100.00')
    
    def test_api_material_no_existe(self):
        """Test cuando el material no existe"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('obtener_info_material', args=[99999])
        response = self.client.get(url)
        
        data = response.json()
        self.assertFalse(data['success'])