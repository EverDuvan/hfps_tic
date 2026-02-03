from django.shortcuts import get_object_or_404
from django.http import HttpResponse, FileResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Maintenance, Handover, Equipment, Peripheral, Area, CostCenter
from .utils import generate_maintenance_pdf, generate_handover_pdf, export_to_excel
from django.apps import apps
from django.shortcuts import render, redirect
from .forms import MaintenanceForm
from django.db.models import Count, Q

@login_required
def maintenance_acta_view(request, pk):
    maintenance = get_object_or_404(Maintenance, pk=pk)
    pdf_content = generate_maintenance_pdf(maintenance)
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="acta_mantenimiento_{pk}.pdf"'
    return response

@login_required
def handover_acta_view(request, pk):
    handover = get_object_or_404(Handover, pk=pk)
    pdf_content = generate_handover_pdf(handover)
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="acta_entrega_{pk}.pdf"'
    return response

@login_required
def export_data_view(request, model_name):
    try:
        model = apps.get_model('inventory', model_name)
    except LookupError:
        return HttpResponse("Model not found", status=404)
    
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
    
    # Recent activity
    recent_maintenance = Maintenance.objects.order_by('-date')[:5]
    recent_handovers = Handover.objects.order_by('-date')[:5]
    
    context = {
        'total_equipment': total_equipment,
        'active_equipment': active_equipment,
        'maintenance_count': maintenance_count,
        'recent_maintenance': recent_maintenance,
        'recent_handovers': recent_handovers,
    }
    return render(request, 'inventory/dashboard.html', context)

@login_required
def equipment_list_view(request):
    query = request.GET.get('q', '')
    equipments = Equipment.objects.all()
    
    if query:
        equipments = equipments.filter(
            Q(serial_number__icontains=query) | 
            Q(brand__icontains=query) | 
            Q(model__icontains=query) |
            Q(type__icontains=query)
        )
        
    return render(request, 'inventory/equipment_list.html', {'equipments': equipments, 'search_query': query})

@login_required
def maintenance_create_view(request):
    if request.method == 'POST':
        form = MaintenanceForm(request.POST, request.FILES)
        if form.is_valid():
            maintenance = form.save(commit=False)
            # If performed_by not in form, set to user
            if not maintenance.performed_by:
                maintenance.performed_by = request.user
            maintenance.save()
            return redirect('equipment_list')
    else:
        form = MaintenanceForm()
        # Pre-fill performed_by if it's in the form fields, otherwise handled in save
        if 'performed_by' in form.fields:
            form.fields['performed_by'].initial = request.user
            
    return render(request, 'inventory/maintenance_form.html', {'form': form})
