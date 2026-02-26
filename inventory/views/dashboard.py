import logging
from datetime import timedelta

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F
from django.utils import timezone

from ..models import Equipment, Maintenance, Handover, Peripheral, MaintenanceSchedule
from ..choices import EQUIPMENT_STATUS_CHOICES, EQUIPMENT_TYPE_CHOICES
from ..services import get_lifespan_expired_queryset

logger = logging.getLogger('inventory')

__all__ = ['dashboard_view']


@login_required
def dashboard_view(request):
    total_equipment = Equipment.objects.count()
    active_equipment = Equipment.objects.filter(status='ACTIVE').count()
    maintenance_count = Maintenance.objects.count()
    
    dashboard_view_handovers = Handover.objects.count()
    
    recent_maintenance = Maintenance.objects.select_related('equipment', 'performed_by').order_by('-date')[:5]
    recent_handovers = Handover.objects.select_related('source_area', 'destination_area', 'client', 'technician').order_by('-date')[:5]
    
    # Chart Data Preparation
    status_dict = dict(EQUIPMENT_STATUS_CHOICES)
    type_dict = dict(EQUIPMENT_TYPE_CHOICES)

    raw_status_data = Equipment.objects.values('status').annotate(count=Count('status'))
    status_data = [{'status': status_dict.get(item['status'], item['status']), 'count': item['count']} for item in raw_status_data]

    raw_type_data = Equipment.objects.values('type').annotate(count=Count('type'))
    type_data = [{'type': type_dict.get(item['type'], item['type']), 'count': item['count']} for item in raw_type_data]

    area_data = list(Equipment.objects.exclude(area__isnull=True).values('area__name').annotate(count=Count('id')).order_by('-count')[:5])

    # Low Stock Alerts
    low_stock_peripherals = Peripheral.objects.filter(quantity__lte=F('min_stock_level'))

    # Expired Alerts
    today = timezone.now().date()
    warranty_expired = Equipment.objects.filter(warranty_expiry__lt=today).exclude(status='RETIRED').order_by('warranty_expiry')
    
    # Calculate lifespan expired using service (cross-database compatible)
    lifespan_expired = get_lifespan_expired_queryset()

    # Upcoming Maintenance Alerts (30 days)
    upcoming_limit = today + timezone.timedelta(days=30)
    
    # 1. From Schedule (Pending)
    upcoming_schedules = MaintenanceSchedule.objects.filter(
        status='PENDING',
        scheduled_date__lte=upcoming_limit
    ).select_related('equipment').order_by('scheduled_date')

    # 2. From Maintenance Records (Next Date)
    upcoming_maintenance_records = Maintenance.objects.filter(
        next_maintenance_date__lte=upcoming_limit
    ).exclude(next_maintenance_date__isnull=True).select_related('equipment').order_by('next_maintenance_date')


    context = {
        'total_equipment': total_equipment,
        'active_equipment': active_equipment,
        'maintenance_count': maintenance_count,
        'handover_count': dashboard_view_handovers,
        'recent_maintenance': recent_maintenance,
        'recent_handovers': recent_handovers,
        'status_data': status_data,
        'type_data': type_data,
        'area_data': area_data,
        'low_stock_peripherals': low_stock_peripherals,
        'warranty_expired': warranty_expired,
        'lifespan_expired': lifespan_expired,
        'upcoming_schedules': upcoming_schedules,
        'upcoming_maintenance_records': upcoming_maintenance_records,
    }
    return render(request, 'inventory/dashboard.html', context)
