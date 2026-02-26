"""
Business logic services for the inventory application.

Extracted from views to keep views thin (#11) and enable unit testing (#25).
"""
import calendar
import logging

from django.db.models import Count, F, Q, ExpressionWrapper, DateField
from django.utils import timezone
from datetime import timedelta

from .models import (
    Equipment, Maintenance, Handover, Peripheral,
    MaintenanceSchedule, EquipmentRound, ComponentLog,
)

logger = logging.getLogger('inventory')


# ---------------------------------------------------------------------------
# Maintenance ↔ Schedule synchronization
# ---------------------------------------------------------------------------

def sync_maintenance_to_schedule(maintenance):
    """
    After creating a Maintenance record, sync it with the MaintenanceSchedule.
    - If a PENDING schedule exists for the same equipment/month, mark it COMPLETED.
    - Otherwise, create a new COMPLETED schedule entry.
    """
    try:
        start_of_month = maintenance.date.replace(day=1)
        last_day = calendar.monthrange(maintenance.date.year, maintenance.date.month)[1]
        end_of_month = maintenance.date.replace(day=last_day)

        schedule = MaintenanceSchedule.objects.filter(
            equipment=maintenance.equipment,
            scheduled_date__range=[start_of_month, end_of_month],
            status='PENDING'
        ).first()

        if schedule:
            schedule.status = 'COMPLETED'
            schedule.scheduled_date = maintenance.date
            schedule.save()
        else:
            exists = MaintenanceSchedule.objects.filter(
                equipment=maintenance.equipment,
                scheduled_date=maintenance.date
            ).exists()
            if not exists:
                MaintenanceSchedule.objects.create(
                    equipment=maintenance.equipment,
                    scheduled_date=maintenance.date,
                    status='COMPLETED'
                )
    except Exception as e:
        logger.error(f"Error syncing schedule: {e}")


# ---------------------------------------------------------------------------
# Peripheral stock management
# ---------------------------------------------------------------------------

def reduce_peripheral_stock(peripheral, quantity):
    """
    Reduce peripheral stock by the given quantity.
    Returns (success: bool, remaining_stock: int).
    """
    if peripheral.quantity >= quantity:
        peripheral.quantity -= quantity
        peripheral.save()
        return True, peripheral.quantity
    return False, peripheral.quantity


def reduce_peripheral_stock_floor(peripheral, quantity):
    """
    Reduce peripheral stock by the given quantity, flooring at 0.
    Used by handover (less strict than component log).
    """
    if peripheral.quantity >= quantity:
        peripheral.quantity -= quantity
    else:
        peripheral.quantity = max(0, peripheral.quantity - quantity)
    peripheral.save()
    return peripheral.quantity


# ---------------------------------------------------------------------------
# Dashboard / Reports data computation
# ---------------------------------------------------------------------------

def get_dashboard_stats():
    """Compute the main dashboard KPIs."""
    return {
        'total_equipment': Equipment.objects.count(),
        'active_equipment': Equipment.objects.filter(status='ACTIVE').count(),
        'maintenance_count': Maintenance.objects.count(),
        'handover_count': Handover.objects.count(),
    }


def get_lifespan_expired_queryset(queryset=None):
    """
    Return a queryset of equipment whose lifespan has expired.
    Uses RawSQL for cross-database compatibility (PostgreSQL + SQLite).
    """
    from django.db.models.expressions import RawSQL
    from django.db import connection

    today = timezone.now().date()
    qs = queryset if queryset is not None else Equipment.objects.all()
    qs = qs.exclude(purchase_date__isnull=True).exclude(status='RETIRED').exclude(lifespan_years__isnull=True)

    if connection.vendor == 'sqlite':
        # SQLite: date arithmetic via date() function
        return qs.annotate(
            eol_date=RawSQL(
                "date(purchase_date, '+' || (lifespan_years * 365) || ' days')",
                []
            )
        ).filter(eol_date__lte=str(today))
    else:
        # PostgreSQL / MySQL: interval arithmetic
        return qs.annotate(
            eol_date=ExpressionWrapper(
                F('purchase_date') + timedelta(days=365) * F('lifespan_years'),
                output_field=DateField()
            )
        ).filter(eol_date__lte=today)


def get_low_stock_peripherals():
    """Return peripherals that are at or below their minimum stock level."""
    return Peripheral.objects.filter(quantity__lte=F('min_stock_level'))


def get_warranty_expired(queryset=None):
    """Return active equipment with expired warranties."""
    today = timezone.now().date()
    qs = queryset if queryset is not None else Equipment.objects.all()
    return qs.filter(warranty_expiry__lt=today).exclude(status='RETIRED').order_by('warranty_expiry')
