import json
import logging
from types import SimpleNamespace

from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.forms import inlineformset_factory
from django.utils import timezone
from django import forms

from ..models import Equipment, Handover, HandoverPeripheral, Peripheral, Area
from ..forms import HandoverForm
from ..utils import generate_handover_pdf
from ..services import reduce_peripheral_stock_floor

logger = logging.getLogger('inventory')

__all__ = [
    'handover_create_view', 'handover_success_view', 'handover_list_view',
]


@login_required
def handover_create_view(request):
    HandoverPeripheralFormSet = inlineformset_factory(
        Handover, HandoverPeripheral,
        fields=('peripheral', 'quantity'),
        extra=1,
        can_delete=True,
        widgets={
            'peripheral': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'style': 'width: 80px;'}),
        }
    )
    
    if request.method == 'POST':
        form = HandoverForm(request.POST)
        formset = HandoverPeripheralFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            action = request.POST.get('action', 'save')
            
            if action == 'preview':
                handover = form.save(commit=False)
                handover.technician = request.user
                handover.date = timezone.now() 
                
                selected_equipment = form.cleaned_data.get('equipment')
                
                preview_peripherals = []
                for f in formset:
                    if f.cleaned_data and not f.cleaned_data.get('DELETE', False):
                        p = f.cleaned_data.get('peripheral')
                        q = f.cleaned_data.get('quantity')
                        if p and q:
                            preview_peripherals.append(SimpleNamespace(peripheral=p, quantity=q))
                
                pdf_content = generate_handover_pdf(handover, equipment_list=selected_equipment, peripheral_list=preview_peripherals)
                
                response = HttpResponse(pdf_content, content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="vista_previa_acta.pdf"'
                return response
            
            else:
                handover = form.save(commit=False)
                handover.technician = request.user
                handover.save()
                form.save_m2m() 
                
                instances = formset.save(commit=False)
                for instance in instances:
                    instance.handover = handover
                    reduce_peripheral_stock_floor(instance.peripheral, instance.quantity)
                    instance.save()
                
                return redirect('inventory:handover_success', pk=handover.pk)
    else:
        form = HandoverForm()
        formset = HandoverPeripheralFormSet()
    
    equipment_area_map = {e.id: e.area_id for e in Equipment.objects.all() if e.area_id}
    peripheral_area_map = {p.id: p.area_id for p in Peripheral.objects.all() if p.area_id}
    
    context = {
        'form': form, 
        'formset': formset, 
        'title': 'Nueva Entrega / Acta',
        'equipment_area_map': json.dumps(equipment_area_map),
        'peripheral_area_map': json.dumps(peripheral_area_map)
    }
    return render(request, 'inventory/handover_form.html', context)


@login_required
def handover_success_view(request, pk):
    return render(request, 'inventory/handover_success.html', {'pk': pk})


@login_required
def handover_list_view(request):
    date_start = request.GET.get('date_start', '')
    date_end = request.GET.get('date_end', '')
    area_id = request.GET.get('area', '')

    handovers = Handover.objects.all().order_by('-date')
    
    if date_start:
        handovers = handovers.filter(date__date__gte=date_start)
    if date_end:
        handovers = handovers.filter(date__date__lte=date_end)
    if area_id:
        handovers = handovers.filter(Q(source_area_id=area_id) | Q(destination_area_id=area_id))
    paginator = Paginator(handovers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    areas = Area.objects.all()
    
    context = {
        'page_obj': page_obj,
        'handovers': page_obj,
        'areas': areas,
        'current_start': date_start,
        'current_end': date_end,
        'current_area': int(area_id) if area_id.isdigit() else '',
    }
    return render(request, 'inventory/handover_list.html', context)
