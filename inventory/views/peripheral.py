import logging

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator

from ..models import Peripheral, Handover
from ..forms import PeripheralForm, PeripheralTypeForm

logger = logging.getLogger('inventory')

__all__ = [
    'peripheral_list_view', 'peripheral_detail_view',
    'peripheral_create_view', 'peripheral_edit_view',
    'peripheral_type_create_view',
]


@login_required
def peripheral_list_view(request):
    query = request.GET.get('q', '')
    peripherals_list = Peripheral.objects.all().order_by('-id')
    
    if query:
        peripherals_list = peripherals_list.filter(
            Q(serial_number__icontains=query) | 
            Q(brand__icontains=query) | 
            Q(model__icontains=query) |
            Q(type__name__icontains=query)
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
            return redirect('inventory:peripheral_list')
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
            return redirect('inventory:peripheral_detail', pk=pk)
    else:
        form = PeripheralForm(instance=peripheral)
    
    return render(request, 'inventory/peripheral_form.html', {'form': form, 'title': f'Editar {peripheral.brand} {peripheral.model}'})


@login_required
def peripheral_type_create_view(request):
    if request.method == 'POST':
        form = PeripheralTypeForm(request.POST)
        if form.is_valid():
            form.save()
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('inventory:peripheral_list')
    else:
        form = PeripheralTypeForm()
    
    return render(request, 'inventory/peripheral_type_form.html', {'form': form})
