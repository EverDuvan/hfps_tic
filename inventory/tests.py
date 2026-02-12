from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Equipment, Area, CostCenter, Maintenance

class EquipmentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.cc = CostCenter.objects.create(code='CC-001', name='Administracion')
        self.area = Area.objects.create(name='Recursos Humanos', cost_center=self.cc)
        
    def test_create_equipment(self):
        eq = Equipment.objects.create(
            serial_number='TEST-SN-123',
            type='PC',
            brand='Lenovo',
            model='ThinkCentre',
            status='ACTIVE',
            area=self.area
        )
        self.assertEqual(eq.serial_number, 'TEST-SN-123')
        self.assertEqual(str(eq), 'PC de Escritorio - Lenovo ThinkCentre (TEST-SN-123)')
        self.assertTrue(eq.history.exists()) # Check if history was created upon creation

class DashboardViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_login(self.user)
        
    def test_dashboard_status_code(self):
        response = self.client.get(reverse('inventory:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/dashboard.html')

class MaintenancePDFTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tech', password='password')
        self.client.force_login(self.user)
        self.eq = Equipment.objects.create(
            serial_number='MANT-TEST', type='PRINTER', brand='HP', model='LaserJet'
        )
        
    def test_maintenance_creation_generates_pdf(self):
        # Create maintenance via model directly to check save method logic
        # Or better yet, test the view if possible, but save() logic is in model.
        m = Maintenance.objects.create(
            equipment=self.eq,
            maintenance_type='PREVENTIVE',
            description='Test maintenance',
            performed_by=self.user
        )
        
        # Check if PDF field is populated
        self.assertTrue(m.acta_pdf)
        self.assertTrue(m.acta_pdf.name.endswith('.pdf'))
