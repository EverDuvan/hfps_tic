import logging

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test

from ..models import Area, CostCenter
from ..forms import AreaForm, CostCenterForm, ClientForm

logger = logging.getLogger('inventory')

__all__ = [
    'area_create_view', 'area_list_view', 'area_edit_view',
    'cost_center_create_view', 'cost_center_list_view', 'cost_center_edit_view',
    'client_create_view',
    'user_list_view', 'user_create_view',
    'support_view', 'manual_view', 'privacy_policy_view',
]


@login_required
def area_create_view(request):
    if request.method == 'POST':
        form = AreaForm(request.POST)
        if form.is_valid():
            form.save()
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('inventory:dashboard')
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
            return redirect('inventory:area_list')
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
            return redirect('inventory:dashboard')
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
            return redirect('inventory:cost_center_list')
    else:
        form = CostCenterForm(instance=cost_center)
    
    return render(request, 'inventory/cost_center_form.html', {'form': form, 'title': f'Editar C.C.: {cost_center.code}'})


@login_required
def client_create_view(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('inventory:dashboard')
    else:
        form = ClientForm()
    
    return render(request, 'inventory/client_form.html', {'form': form})


# User management is handled by the 'users' app.
# These redirects keep backward compatibility with templates using inventory:user_list/user_create.
@login_required
@user_passes_test(lambda u: u.is_staff)
def user_list_view(request):
    return redirect('users:user_list')


@login_required
@user_passes_test(lambda u: u.is_staff)
def user_create_view(request):
    return redirect('users:user_create')


# Public informational pages (no login required)
def support_view(request):
    return render(request, 'inventory/support.html')

def manual_view(request):
    return render(request, 'inventory/manual.html')

def privacy_policy_view(request):
    return render(request, 'inventory/privacy.html')
