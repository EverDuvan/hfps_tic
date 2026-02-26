import json
import logging

from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone

from ..models import Equipment, Maintenance, MaintenanceSchedule, Area
from ..forms import MaintenanceForm
from ..choices import MAINTENANCE_TYPE_CHOICES
from ..services import sync_maintenance_to_schedule

logger = logging.getLogger('inventory')

__all__ = [
    'maintenance_create_view', 'maintenance_success_view',
    'maintenance_list_view', 'maintenance_schedule_view',
    'toggle_schedule_view',
]


@login_required
def maintenance_create_view(request):
    if request.method == 'POST':
        form = MaintenanceForm(request.POST)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.performed_by = request.user
            maintenance.save()
            
            # Sync with schedule via service layer
            sync_maintenance_to_schedule(maintenance)

            return redirect('inventory:maintenance_success', pk=maintenance.pk)
    else:
        form = MaintenanceForm()
            
    return render(request, 'inventory/maintenance_form.html', {'form': form})


@login_required
def maintenance_success_view(request, pk):
    return render(request, 'inventory/maintenance_success.html', {'pk': pk})


@login_required
def maintenance_list_view(request):
    date_start = request.GET.get('date_start', '')
    date_end = request.GET.get('date_end', '')
    m_type = request.GET.get('type', '')

    maintenances = Maintenance.objects.all().order_by('-date')
    
    if date_start:
        maintenances = maintenances.filter(date__gte=date_start)
    if date_end:
        maintenances = maintenances.filter(date__lte=date_end)
    if m_type:
        maintenances = maintenances.filter(maintenance_type=m_type)
    paginator = Paginator(maintenances, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'maintenances': page_obj,
        'maintenance_types': MAINTENANCE_TYPE_CHOICES,
        'current_start': date_start,
        'current_end': date_end,
        'current_type': m_type,
    }
    return render(request, 'inventory/maintenance_list.html', context)


@login_required
def maintenance_schedule_view(request):
    year = int(request.GET.get('year', timezone.now().year))
    
    weeks = [1, 2, 3, 4]
    months = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]
    
    equipments = Equipment.objects.all().select_related('area').order_by('area__name', 'serial_number')
    
    area_id = request.GET.get('area')
    if area_id:
        equipments = equipments.filter(area_id=area_id)

    schedules = MaintenanceSchedule.objects.filter(scheduled_date__year=year)
    
    schedule_map = {}
    for s in schedules:
        day = s.scheduled_date.day
        month = s.scheduled_date.month
        
        if day <= 7: v_week = 1
        elif day <= 14: v_week = 2
        elif day <= 21: v_week = 3
        else: v_week = 4
        
        schedule_map[(s.equipment_id, month, v_week)] = {
            'status': s.status,
            'day': day,
            'date': s.scheduled_date.strftime('%Y-%m-%d')
        }
    
    for eq in equipments:
        eq.schedule_row = []
        for m_num, m_name in months:
            month_weeks = []
            for w in weeks:
                data = schedule_map.get((eq.id, m_num, w), None)
                month_weeks.append({'month': m_num, 'week': w, 'data': data})
            eq.schedule_row.append({'month': m_name, 'weeks': month_weeks})
            
    current_actual_years = timezone.now().year
    start_year = current_actual_years
    available_years = range(start_year, start_year + 21)

    areas = Area.objects.all()

    context = {
        'year': year,
        'months': months,
        'equipments': equipments,
        'weeks': weeks,
        'available_years': available_years,
        'areas': areas,
        'current_area': int(area_id) if area_id and area_id.isdigit() else None,
    }
    return render(request, 'inventory/maintenance_schedule.html', context)


@login_required
def toggle_schedule_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            equipment_id = data.get('equipment_id')
            date_str = data.get('date')
            
            if not date_str:
                 return JsonResponse({'error': 'Date required'}, status=400)

            schedule = MaintenanceSchedule.objects.filter(
                equipment_id=equipment_id, scheduled_date=date_str
            ).first()
            
            if schedule:
                schedule.delete()
                return JsonResponse({'status': 'removed'})
            else:
                MaintenanceSchedule.objects.create(
                    equipment_id=equipment_id, scheduled_date=date_str, status='PENDING'
                )
                return JsonResponse({'status': 'added', 'state': 'PENDING'})
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)
