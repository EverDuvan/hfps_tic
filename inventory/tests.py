"""
Tests for the inventory application.

Covers services (business logic), model properties, and basic view access.
"""
import datetime
from django.test import TestCase, Client as TestClient
from django.contrib.auth.models import User
from django.utils import timezone

from .models import (
    Equipment, Peripheral, Maintenance, MaintenanceSchedule,
    Area, CostCenter, PeripheralType,
)
from .services import (
    sync_maintenance_to_schedule,
    reduce_peripheral_stock,
    reduce_peripheral_stock_floor,
    get_dashboard_stats,
    get_lifespan_expired_queryset,
    get_low_stock_peripherals,
    get_warranty_expired,
)


class SyncMaintenanceToScheduleTest(TestCase):
    """Test sync_maintenance_to_schedule service."""

    def setUp(self):
        self.area = Area.objects.create(name='Test Area')
        self.equipment = Equipment.objects.create(
            serial_number='SN-001', type='PC', brand='Dell', model='OptiPlex',
            status='ACTIVE', area=self.area
        )
        self.user = User.objects.create_user('tech', 'tech@test.com', 'pass123')

    def test_creates_completed_schedule_when_none_exists(self):
        """When no schedule exists for the month, a new COMPLETED entry is created."""
        m = Maintenance.objects.create(
            equipment=self.equipment, date=datetime.date(2026, 3, 15),
            maintenance_type='PREVENTIVE', performed_by=self.user,
            description='Test maintenance'
        )
        sync_maintenance_to_schedule(m)

        schedule = MaintenanceSchedule.objects.get(equipment=self.equipment)
        self.assertEqual(schedule.status, 'COMPLETED')
        self.assertEqual(schedule.scheduled_date, datetime.date(2026, 3, 15))

    def test_marks_pending_schedule_as_completed(self):
        """When a PENDING schedule exists for the month, it gets marked COMPLETED."""
        MaintenanceSchedule.objects.create(
            equipment=self.equipment,
            scheduled_date=datetime.date(2026, 3, 1),
            status='PENDING'
        )
        m = Maintenance.objects.create(
            equipment=self.equipment, date=datetime.date(2026, 3, 20),
            maintenance_type='CORRECTIVE', performed_by=self.user,
            description='Test'
        )
        sync_maintenance_to_schedule(m)

        schedule = MaintenanceSchedule.objects.get(equipment=self.equipment)
        self.assertEqual(schedule.status, 'COMPLETED')
        self.assertEqual(schedule.scheduled_date, datetime.date(2026, 3, 20))

    def test_no_duplicate_schedule_created(self):
        """If a schedule already exists for that exact date, don't create another."""
        MaintenanceSchedule.objects.create(
            equipment=self.equipment,
            scheduled_date=datetime.date(2026, 3, 15),
            status='COMPLETED'
        )
        m = Maintenance.objects.create(
            equipment=self.equipment, date=datetime.date(2026, 3, 15),
            maintenance_type='PREVENTIVE', performed_by=self.user,
            description='Test'
        )
        sync_maintenance_to_schedule(m)

        self.assertEqual(MaintenanceSchedule.objects.filter(equipment=self.equipment).count(), 1)


class ReducePeripheralStockTest(TestCase):
    """Test stock reduction services."""

    def setUp(self):
        self.ptype = PeripheralType.objects.create(name='Mouse')
        self.peripheral = Peripheral.objects.create(
            type=self.ptype, brand='Logitech', model='M100',
            serial_number='P-001', quantity=10, min_stock_level=2
        )

    def test_reduce_stock_success(self):
        success, remaining = reduce_peripheral_stock(self.peripheral, 3)
        self.assertTrue(success)
        self.assertEqual(remaining, 7)
        self.peripheral.refresh_from_db()
        self.assertEqual(self.peripheral.quantity, 7)

    def test_reduce_stock_insufficient(self):
        success, remaining = reduce_peripheral_stock(self.peripheral, 15)
        self.assertFalse(success)
        self.assertEqual(remaining, 10)  # unchanged
        self.peripheral.refresh_from_db()
        self.assertEqual(self.peripheral.quantity, 10)

    def test_reduce_stock_floor_sufficient(self):
        remaining = reduce_peripheral_stock_floor(self.peripheral, 3)
        self.assertEqual(remaining, 7)

    def test_reduce_stock_floor_insufficient_floors_to_zero(self):
        remaining = reduce_peripheral_stock_floor(self.peripheral, 15)
        self.assertEqual(remaining, 0)
        self.peripheral.refresh_from_db()
        self.assertEqual(self.peripheral.quantity, 0)


class DashboardStatsTest(TestCase):
    """Test get_dashboard_stats service."""

    def setUp(self):
        self.area = Area.objects.create(name='Test Area')
        Equipment.objects.create(
            serial_number='SN-A', type='PC', brand='Dell', model='XPS',
            status='ACTIVE', area=self.area
        )
        Equipment.objects.create(
            serial_number='SN-B', type='LAPTOP', brand='HP', model='ProBook',
            status='RETIRED', area=self.area
        )

    def test_counts_equipment_correctly(self):
        stats = get_dashboard_stats()
        self.assertEqual(stats['total_equipment'], 2)
        self.assertEqual(stats['active_equipment'], 1)


class LifespanExpiredTest(TestCase):
    """Test get_lifespan_expired_queryset service."""

    def setUp(self):
        self.area = Area.objects.create(name='Test Area')

    def test_expired_equipment_included(self):
        Equipment.objects.create(
            serial_number='OLD-01', type='PC', brand='Dell', model='Old',
            status='ACTIVE', area=self.area,
            purchase_date=datetime.date(2018, 1, 1), lifespan_years=5
        )
        expired = get_lifespan_expired_queryset()
        self.assertEqual(expired.count(), 1)

    def test_new_equipment_excluded(self):
        Equipment.objects.create(
            serial_number='NEW-01', type='PC', brand='Dell', model='New',
            status='ACTIVE', area=self.area,
            purchase_date=datetime.date(2025, 1, 1), lifespan_years=5
        )
        expired = get_lifespan_expired_queryset()
        self.assertEqual(expired.count(), 0)

    def test_retired_equipment_excluded(self):
        Equipment.objects.create(
            serial_number='RET-01', type='PC', brand='Dell', model='Retired',
            status='RETIRED', area=self.area,
            purchase_date=datetime.date(2018, 1, 1), lifespan_years=5
        )
        expired = get_lifespan_expired_queryset()
        self.assertEqual(expired.count(), 0)


class LowStockPeripheralsTest(TestCase):
    """Test get_low_stock_peripherals service."""

    def setUp(self):
        self.ptype = PeripheralType.objects.create(name='Teclado')

    def test_below_min_stock_included(self):
        Peripheral.objects.create(
            type=self.ptype, brand='HP', model='KB', serial_number='K-01',
            quantity=1, min_stock_level=5
        )
        low = get_low_stock_peripherals()
        self.assertEqual(low.count(), 1)

    def test_above_min_stock_excluded(self):
        Peripheral.objects.create(
            type=self.ptype, brand='HP', model='KB', serial_number='K-02',
            quantity=10, min_stock_level=5
        )
        low = get_low_stock_peripherals()
        self.assertEqual(low.count(), 0)


class ViewAccessTest(TestCase):
    """Test that key views require login and respond correctly."""

    def setUp(self):
        self.client = TestClient()
        self.user = User.objects.create_user('testuser', 'test@test.com', 'pass123')

    def test_dashboard_requires_login(self):
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)  # redirect to login

    def test_dashboard_accessible_when_logged_in(self):
        self.client.login(username='testuser', password='pass123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_support_page_is_public(self):
        response = self.client.get('/support/')
        self.assertEqual(response.status_code, 200)

    def test_manual_page_is_public(self):
        response = self.client.get('/manual/')
        self.assertEqual(response.status_code, 200)

    def test_privacy_page_is_public(self):
        response = self.client.get('/privacy/')
        self.assertEqual(response.status_code, 200)

    def test_equipment_list_requires_login(self):
        response = self.client.get('/inventory/')
        self.assertEqual(response.status_code, 302)

    def test_maintenance_list_requires_login(self):
        response = self.client.get('/maintenance/')
        self.assertEqual(response.status_code, 302)
