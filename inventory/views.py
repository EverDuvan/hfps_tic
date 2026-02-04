from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, FileResponse, Http404
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Maintenance, Handover, Equipment, Peripheral, Area, CostCenter
from .utils import generate_maintenance_pdf, generate_handover_pdf, export_to_excel
from django.apps import apps
from .forms import MaintenanceForm, EquipmentForm, AreaForm, CostCenterForm, CustomUserCreationForm, PeripheralForm, HandoverForm, ClientForm
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.core.paginator import Paginator

@login_required
def maintenance_acta_view(request, pk):
    maintenance = get_object_or_404(Maintenance, pk=pk)
    
    if maintenance.acta_pdf:
        return FileResponse(maintenance.acta_pdf, as_attachment=True, filename=f"acta_mantenimiento_{pk}.pdf")
    
    # Fallback if PDF not generated yet
    pdf_content = generate_maintenance_pdf(maintenance)
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="acta_mantenimiento_{pk}.pdf"'
    return response

@login_required
def handover_acta_view(request, pk):
    handover = get_object_or_404(Handover, pk=pk)
    
    if handover.acta_pdf:
        return FileResponse(handover.acta_pdf, as_attachment=True, filename=f"acta_entrega_{pk}.pdf")

    pdf_content = generate_handover_pdf(handover)
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="acta_entrega_{pk}.pdf"'
    return response

@login_required
def export_data_view(request, model_name):
    allowed_models = ['equipment', 'peripheral', 'maintenance', 'handover', 'client', 'area', 'costcenter']
    if model_name.lower() not in allowed_models:
        raise Http404("Invalid model for export")

    try:
        model = apps.get_model('inventory', model_name)
    except LookupError:
        raise Http404("Model not found")
    
    queryset = model.objects.all()
    # Create a dummy ModelAdmin-like object or just pass a simple object with model._meta
    class DummyAdmin:
        pass
    dummy_admin = DummyAdmin()
    dummy_admin.model = model
    
    return export_to_excel(queryset, dummy_admin, request)

@login_required
def dashboard_view(request):
    total_equipment = Equipment.objects.count()
    active_equipment = Equipment.objects.filter(status='ACTIVE').count()
    maintenance_count = Maintenance.objects.count()
    
    recent_maintenance = Maintenance.objects.order_by('-date')[:5]
    recent_handovers = Handover.objects.order_by('-date')[:5]
    
    # Chart Data
    status_data = list(Equipment.objects.values('status').annotate(count=Count('status')))
    type_data = list(Equipment.objects.values('type').annotate(count=Count('type')))
    area_data = list(Equipment.objects.exclude(area__isnull=True).values('area__name').annotate(count=Count('id')).order_by('-count')[:5])

    context = {
        'total_equipment': total_equipment,
        'active_equipment': active_equipment,
        'maintenance_count': maintenance_count,
        'recent_maintenance': recent_maintenance,
        'recent_handovers': recent_handovers,
        'status_data': status_data,
        'type_data': type_data,
        'area_data': area_data,
    }
    return render(request, 'inventory/dashboard.html', context)

@login_required
def equipment_list_view(request):
    query = request.GET.get('q', '')
    equipments_list = Equipment.objects.all().order_by('-created_at')
    
    if query:
        equipments_list = equipments_list.filter(
            Q(serial_number__icontains=query) | 
            Q(brand__icontains=query) | 
            Q(model__icontains=query) |
            Q(ip_address__icontains=query)
        )
    
    paginator = Paginator(equipments_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    return render(request, 'inventory/equipment_list.html', {'page_obj': page_obj, 'search_query': query})

@login_required
def maintenance_create_view(request):
    if request.method == 'POST':
        form = MaintenanceForm(request.POST)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.performed_by = request.user
            maintenance.save()
            return redirect('inventory:equipment_list') # Redirect to list or detail
    else:
        form = MaintenanceForm()
        if request.user.is_authenticated:
            form.fields['performed_by'].initial = request.user
            
    return render(request, 'inventory/maintenance_form.html', {'form': form})

@login_required
def equipment_create_view(request):
    if request.method == 'POST':
        form = EquipmentForm(request.POST) 
        if form.is_valid():
            form.save()
            return redirect('equipment_list')
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
            return redirect('equipment_detail', pk=pk)
    else:
        form = EquipmentForm(instance=equipment)
    
    return render(request, 'inventory/equipment_form.html', {'form': form, 'title': f'Editar {equipment.serial_number}'})

@login_required
def area_create_view(request):
    if request.method == 'POST':
        form = AreaForm(request.POST)
        if form.is_valid():
            form.save()
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
    else:
        form = AreaForm()
    
    return render(request, 'inventory/area_form.html', {'form': form})

@login_required
def area_list_view(request):
    areas = Area.objects.all().order_by('name')
    return render(request, 'inventory/area_list.html', {'areas': areas})

@login_required
def area_edit_view(request, pk):
    area = get_object_or_404(Area, pk=pk)
    if request.method == 'POST':
        form = AreaForm(request.POST, instance=area)
        if form.is_valid():
            form.save()
            return redirect('area_list')
    else:
        form = AreaForm(instance=area)
    
    return render(request, 'inventory/area_form.html', {'form': form, 'title': f'Editar Área: {area.name}'})

@login_required
def cost_center_create_view(request):
    if request.method == 'POST':
        form = CostCenterForm(request.POST)
        if form.is_valid():
            form.save()
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
    else:
        form = CostCenterForm()
    
    return render(request, 'inventory/cost_center_form.html', {'form': form})

@login_required
def cost_center_list_view(request):
    cost_centers = CostCenter.objects.all().order_by('code')
    return render(request, 'inventory/cost_center_list.html', {'cost_centers': cost_centers})

@login_required
def cost_center_edit_view(request, pk):
    cost_center = get_object_or_404(CostCenter, pk=pk)
    if request.method == 'POST':
        form = CostCenterForm(request.POST, instance=cost_center)
        if form.is_valid():
            form.save()
            return redirect('cost_center_list')
    else:
        form = CostCenterForm(instance=cost_center)
    
    return render(request, 'inventory/cost_center_form.html', {'form': form, 'title': f'Editar C.C.: {cost_center.code}'})

@login_required
@user_passes_test(lambda u: u.is_staff)
def user_list_view(request):
    users = User.objects.all().order_by('username')
    return render(request, 'inventory/user_list.html', {'users': users})

@login_required
@user_passes_test(lambda u: u.is_staff)
def user_create_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'inventory/user_form.html', {'form': form})

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
def peripheral_list_view(request):
    query = request.GET.get('q', '')
    peripherals_list = Peripheral.objects.all().order_by('-id')
    
    if query:
        peripherals_list = peripherals_list.filter(
            Q(serial_number__icontains=query) | 
            Q(brand__icontains=query) | 
            Q(model__icontains=query) |
            Q(type__icontains=query)
        )

    paginator = Paginator(peripherals_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'inventory/peripheral_list.html', {'page_obj': page_obj, 'search_query': query})

@login_required
def peripheral_detail_view(request, pk):
    peripheral = get_object_or_404(Peripheral, pk=pk)
    handovers = Handover.objects.filter(peripherals=peripheral).order_by('-date')
    
    context = {
        'peripheral': peripheral,
        'handovers': handovers,
    }
    return render(request, 'inventory/peripheral_detail.html', context)

@login_required
def peripheral_create_view(request):
    if request.method == 'POST':
        form = PeripheralForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('peripheral_list')
    else:
        form = PeripheralForm()
    
    return render(request, 'inventory/peripheral_form.html', {'form': form, 'title': 'Nuevo Periférico'})

@login_required
def peripheral_edit_view(request, pk):
    peripheral = get_object_or_404(Peripheral, pk=pk)
    if request.method == 'POST':
        form = PeripheralForm(request.POST, instance=peripheral)
        if form.is_valid():
            form.save()
            return redirect('peripheral_detail', pk=pk)
    else:
        form = PeripheralForm(instance=peripheral)
    
    return render(request, 'inventory/peripheral_form.html', {'form': form, 'title': f'Editar {peripheral.brand} {peripheral.model}'})
    return render(request, 'inventory/peripheral_form.html', {'form': form, 'title': f'Editar {peripheral.brand} {peripheral.model}'})

@login_required
def client_create_view(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
    else:
        form = ClientForm()
    
    return render(request, 'inventory/client_form.html', {'form': form})

@login_required
def handover_create_view(request):
    if request.method == 'POST':
        form = HandoverForm(request.POST)
        if form.is_valid():
            # Check if it's a preview or save
            action = request.POST.get('action', 'save')
            
            if action == 'preview':
                # Create a temporary instance without saving
                handover = form.save(commit=False)
                handover.technician = request.user
                handover.date = timezone.now() # Manually set date for preview since auto_now_add won't trigger yet
                
                # Get selected M2M objects directly from cleaned_data
                selected_equipment = form.cleaned_data.get('equipment')
                selected_peripherals = form.cleaned_data.get('peripherals')
                
                # Generate PDF with these explicitly provided lists
                pdf_content = generate_handover_pdf(handover, equipment_list=selected_equipment, peripheral_list=selected_peripherals)
                
                response = HttpResponse(pdf_content, content_type='application/pdf')
                # inline = open in browser, attachment = download
                response['Content-Disposition'] = 'inline; filename="vista_previa_acta.pdf"'
                return response
            
            else:
                # Save action
                handover = form.save(commit=False)
                handover.technician = request.user
                handover.save()
                form.save_m2m() 
                return redirect('handover_acta', pk=handover.pk)
    else:
        form = HandoverForm()
    
    return render(request, 'inventory/handover_form.html', {'form': form, 'title': 'Nueva Entrega / Acta'})
