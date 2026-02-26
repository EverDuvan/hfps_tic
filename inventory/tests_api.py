from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from .models import Equipment, Maintenance, Handover, Area, PeripheralType, Peripheral
import datetime

class InventoryAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apiuser', password='apipassword')
        self.client.login(username='apiuser', password='apipassword')
        self.area = Area.objects.create(name='API Area')
        self.equipment = Equipment.objects.create(
            serial_number='API-SN-001',
            type='PC',
            brand='Dell',
            model='API-Model',
            status='ACTIVE',
            area=self.area
        )

    def test_get_equipment_list(self):
        url = '/api/equipment/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if the equipment created in setUp is in the response
        self.assertTrue(any(e['serial_number'] == 'API-SN-001' for e in response.data))

    def test_get_maintenance_list(self):
        Maintenance.objects.create(
            equipment=self.equipment,
            date=datetime.date.today(),
            maintenance_type='PREVENTIVE',
            performed_by=self.user,
            description='API Test Maintenance'
        )
        url = '/api/maintenance/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(m['description'] == 'API Test Maintenance' for m in response.data))

    def test_get_areas_list(self):
        url = '/api/areas/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(a['name'] == 'API Area' for a in response.data))

    def test_unauthenticated_access(self):
        self.client.logout()
        url = '/api/equipment/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
