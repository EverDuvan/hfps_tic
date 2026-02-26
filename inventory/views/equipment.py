import logging
from urllib.parse import urlencode

from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils import timezone

import qrcode
import openpyxl

from ..models import Equipment, Maintenance, Handover, Area, ComponentLog, EquipmentRound
from ..forms import EquipmentForm, ExcelImportForm, ComponentLogForm
from ..choices import EQUIPMENT_STATUS_CHOICES, EQUIPMENT_TYPE_CHOICES, OWNERSHIP_CHOICES

logger = logging.getLogger('inventory')

__all__ = [
    'equipment_list_view', 'equipment_create_view', 'equipment_edit_view',
    'equipment_detail_view', 'equipment_retire_view', 'equipment_history_view',
    'generate_qr_view', 'import_equipment_view',
    'component_log_create_view',
    'equipment_round_list_view', 'equipment_round_create_view',
]


@login_required
def generate_qr_view(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    
    url = request.build_absolute_uri(reverse('inventory:equipment_detail', args=[pk]))
    
    params = {
        'serial': equipment.serial_number,
        'model': f"{equipment.brand} {equipment.model}",
        'type': equipment.get_type_display(),
        'area': equipment.area.name if equipment.area else 'N/A',
        'status': equipment.get_status_display()
    }
    
    full_url = f"{url}?{urlencode(params)}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(full_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    return response


@login_required
def import_equipment_view(request):
    if request.method == 'POST':
        form = ExcelImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                wb = openpyxl.load_workbook(request.FILES['excel_file'])
                ws = wb.active
                
                imported_count = 0
                errors = []
                
                for index, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                    serial = str(row[0]).strip() if row[0] else None
                    if not serial: continue
                    
                    eq_type = str(row[1]).upper() if row[1] else 'PC'
                    brand = str(row[2]).strip() if row[2] else 'Genérico'
                    model = str(row[3]).strip() if row[3] else 'Genérico'
                    area_name = str(row[4]).strip() if row[4] else None
                    status = str(row[5]).upper() if row[5] else 'ACTIVE'
                    
                    area = None
                    if area_name:
                        area, _ = Area.objects.get_or_create(name=area_name)
                    
                    obj, created = Equipment.objects.update_or_create(
                        serial_number=serial,
                        defaults={
                            'type': eq_type,
                            'brand': brand,
                            'model': model,
                            'area': area,
                            'status': status
                        }
                    )
                    imported_count += 1
                
                return render(request, 'inventory/import_success.html', {'count': imported_count})
            
            except Exception as e:
                form.add_error(None, f"Error procesando el archivo: {str(e)}")
    else:
        form = ExcelImportForm()
        
    return render(request, 'inventory/import_form.html', {'form': form, 'title': 'Importar Equipos'})


@login_required
def equipment_list_view(request):
    query = request.GET.get('q', '')
    area_id = request.GET.get('area', '')
    status = request.GET.get('status', '')
    eq_type = request.GET.get('type', '')
    ownership = request.GET.get('ownership', '')
    
    equipments_list = Equipment.objects.all().order_by('-created_at')
    
    if query:
        equipments_list = equipments_list.filter(
            Q(serial_number__icontains=query) | 
            Q(brand__icontains=query) | 
            Q(model__icontains=query) |
            Q(ip_address__icontains=query)
        )
    
    if area_id:
        equipments_list = equipments_list.filter(area_id=area_id)
    if status:
        equipments_list = equipments_list.filter(status=status)
    if eq_type:
        equipments_list = equipments_list.filter(type=eq_type)
    if ownership:
        equipments_list = equipments_list.filter(ownership_type=ownership)
    
    paginator = Paginator(equipments_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    areas = Area.objects.all()
        
    context = {
        'page_obj': page_obj, 
        'search_query': query,
        'areas': areas,
        'status_choices': EQUIPMENT_STATUS_CHOICES,
        'type_choices': EQUIPMENT_TYPE_CHOICES,
        'ownership_choices': OWNERSHIP_CHOICES,
        'current_area': int(area_id) if area_id.isdigit() else '',
        'current_status': status,
        'current_type': eq_type,
        'current_ownership': ownership,
    }
    return render(request, 'inventory/equipment_list.html', context)


@login_required
def equipment_create_view(request):
    if request.method == 'POST':
        form = EquipmentForm(request.POST) 
        if form.is_valid():
            form.save()
            return redirect('inventory:equipment_list')
    else:
        form = EquipmentForm()
    
    return render(request, 'inventory/equipment_form.html', {'form': form, 'title': 'Nuevo Equipo'})


@login_required
def equipment_edit_view(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    if request.method == 'POST':
        form = EquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            form.save()
            return redirect('inventory:equipment_detail', pk=pk)
    else:
        form = EquipmentForm(instance=equipment)
    
    return render(request, 'inventory/equipment_form.html', {'form': form, 'title': f'Editar {equipment.serial_number}'})


@login_required
def equipment_detail_view(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    maintenances = Maintenance.objects.filter(equipment=equipment).order_by('-date')
    handovers = Handover.objects.filter(equipment=equipment).order_by('-date')
    
    context = {
        'equipment': equipment,
        'maintenances': maintenances,
        'handovers': handovers,
    }
    return render(request, 'inventory/equipment_detail.html', context)


@login_required
def equipment_retire_view(request, pk):
    """Retire (dar de baja) an equipment — POST only."""
    equipment = get_object_or_404(Equipment, pk=pk)
    if request.method == 'POST':
        equipment.status = 'RETIRED'
        equipment.save()
        messages.success(request, f'El equipo {equipment.serial_number} ha sido dado de baja exitosamente.')
    return redirect('inventory:equipment_detail', pk=pk)


@login_required
def equipment_round_list_view(request):
    date_start = request.GET.get('date_start', '')
    date_end = request.GET.get('date_end', '')
    equipment_query = request.GET.get('q', '')

    rounds = EquipmentRound.objects.all().order_by('-datetime')
    
    if date_start:
        rounds = rounds.filter(datetime__date__gte=date_start)
    if date_end:
        rounds = rounds.filter(datetime__date__lte=date_end)
    if equipment_query:
        rounds = rounds.filter(
            Q(equipment__serial_number__icontains=equipment_query) | 
            Q(equipment__brand__icontains=equipment_query) | 
            Q(equipment__model__icontains=equipment_query)
        )

    paginator = Paginator(rounds, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'rounds': page_obj,
        'current_start': date_start,
        'current_end': date_end,
        'search_query': equipment_query,
    }
    return render(request, 'inventory/equipment_round_list.html', context)


@login_required
def equipment_round_create_view(request):
    from ..forms import EquipmentRoundForm
    if request.method == 'POST':
        form = EquipmentRoundForm(request.POST)
        if form.is_valid():
            round_obj = form.save(commit=False)
            round_obj.performed_by = request.user
            round_obj.save()
            return redirect('inventory:equipment_round_list')
    else:
        form = EquipmentRoundForm()
    
    return render(request, 'inventory/equipment_round_form.html', {'form': form, 'title': 'Nueva Ronda de Equipos'})


@login_required
def component_log_create_view(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    
    if request.method == 'POST':
        form = ComponentLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.equipment = equipment
            log.performed_by = request.user
            
            # Stock reduction logic
            if log.peripheral and log.action_type in ['ADDED', 'REPLACED']:
                if log.peripheral.quantity >= log.quantity:
                    log.peripheral.quantity -= log.quantity
                    log.peripheral.save()
                    
                    if not log.component_name:
                        log.component_name = str(log.peripheral)
                else:
                    messages.error(request, f"No hay suficiente stock para el periférico seleccionado. Stock actual: {log.peripheral.quantity}")
                    return render(request, 'inventory/component_log_form.html', {'form': form, 'equipment': equipment})
            
            # Require component_name if no peripheral
            if not log.peripheral and not log.component_name:
                messages.error(request, "Debe ingresar una Descripción de Pieza manual si no selecciona una del inventario.")
                return render(request, 'inventory/component_log_form.html', {'form': form, 'equipment': equipment})

            log.save()
            messages.success(request, f"¡Cambio de componente '{log.component_name}' registrado exitosamente!")
            return redirect('inventory:equipment_history', pk=equipment.pk)
    else:
        form = ComponentLogForm()
    
    context = {
        'form': form,
        'equipment': equipment,
    }
    return render(request, 'inventory/component_log_form.html', context)


@login_required
def equipment_history_view(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    
    events = []
    
    # 1. Registration
    events.append({
        'type': 'entry',
        'date': equipment.created_at,
        'title': 'Registro Inicial',
        'description': f'Equipo dado de alta en el sistema.',
        'icon': 'fa-plus-circle',
        'color': 'primary'
    })
    
    # 2. Maintenances
    for m in equipment.maintenances.all():
        sort_dt = timezone.datetime.combine(m.date, timezone.datetime.min.time())
        if timezone.is_aware(equipment.created_at):
            sort_dt = timezone.make_aware(sort_dt, timezone.get_current_timezone())
            
        events.append({
            'type': 'maintenance',
            'date': sort_dt,
            'title': f'Mantenimiento {m.get_maintenance_type_display()}',
            'description': m.description,
            'user': m.performed_by.username if m.performed_by else 'N/A',
            'icon': 'fa-tools',
            'color': 'info'
        })
        
    # 3. Handovers
    for h in equipment.handovers.all():
        dest = h.destination_area.name if h.destination_area else 'N/A'
        client = h.client.name if h.client else (h.receiver_name or 'N/A')
        events.append({
            'type': 'handover',
            'date': h.date,
            'title': f'Acta: {h.get_type_display()} a {dest}',
            'description': f'Asignado a: {client}',
            'user': h.technician.username if h.technician else 'N/A',
            'icon': 'fa-exchange-alt',
            'color': 'warning'
        })
        
    # 4. Rounds
    for r in equipment.rounds.all():
        events.append({
            'type': 'round',
            'date': r.datetime,
            'title': f"Ronda: {r.get_general_status_display()}",
            'description': r.observations if r.observations else "Revisión técnica de rutina.",
            'user': r.performed_by.username if r.performed_by else 'N/A',
            'icon': 'fa-clipboard-check',
            'color': 'success' if r.general_status == 'GOOD' else ('warning' if r.general_status == 'REGULAR' else 'danger')
        })
        
    # 5. Component Logs
    for c in equipment.component_logs.all():
        events.append({
            'type': 'component',
            'date': c.date,
            'title': f"{c.get_action_type_display()}: {c.component_name}",
            'description': c.description,
            'user': c.performed_by.username if c.performed_by else 'N/A',
            'icon': 'fa-microchip',
            'color': 'secondary'
        })
        
    # Sort descending
    events.sort(key=lambda x: x['date'], reverse=True)
    
    context = {
        'equipment': equipment,
        'events': events,
    }
    return render(request, 'inventory/equipment_history.html', context)
