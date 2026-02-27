import os
import datetime
import logging

from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.apps import apps
from django.conf import settings
from django.utils import timezone

from fpdf import FPDF

from ..utils import export_to_excel
from ..models import Equipment, Maintenance, Handover

logger = logging.getLogger('inventory')

__all__ = [
    'maintenance_acta_view', 'handover_acta_view', 'export_data_view',
    'export_equipment_history_pdf',
]


@login_required
def maintenance_acta_view(request, pk):
    from ..utils import generate_maintenance_pdf
    maintenance = get_object_or_404(Maintenance, pk=pk)
    
    if maintenance.acta_pdf:
        from django.http import FileResponse
        return FileResponse(maintenance.acta_pdf, as_attachment=False, filename=f"acta_mantenimiento_{pk}.pdf")
    
    # Fallback if PDF not generated yet
    pdf_content = generate_maintenance_pdf(maintenance)
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="acta_mantenimiento_{pk}.pdf"'
    return response


@login_required
def handover_acta_view(request, pk):
    from ..utils import generate_handover_pdf
    handover = get_object_or_404(Handover, pk=pk)
    
    if handover.acta_pdf:
        from django.http import FileResponse
        return FileResponse(handover.acta_pdf, as_attachment=False, filename=f"acta_entrega_{pk}.pdf")

    pdf_content = generate_handover_pdf(handover)
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="acta_entrega_{pk}.pdf"'
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

    # Apply filters based on model name
    if model_name == 'equipment':
        query = request.GET.get('q', '')
        area_id = request.GET.get('area', '')
        status = request.GET.get('status', '')
        eq_type = request.GET.get('type', '')
        ownership = request.GET.get('ownership', '')

        if query:
            queryset = queryset.filter(
                Q(serial_number__icontains=query) | 
                Q(brand__icontains=query) | 
                Q(model__icontains=query) |
                Q(ip_address__icontains=query)
            )
        if area_id:
            queryset = queryset.filter(area_id=area_id)
        if status:
            queryset = queryset.filter(status=status)
        if eq_type:
            queryset = queryset.filter(type=eq_type)
        if ownership:
            queryset = queryset.filter(ownership_type=ownership)
            
    elif model_name == 'maintenance':
        date_start = request.GET.get('date_start', '')
        date_end = request.GET.get('date_end', '')
        m_type = request.GET.get('type', '')
        
        if date_start:
            queryset = queryset.filter(date__gte=date_start)
        if date_end:
            queryset = queryset.filter(date__lte=date_end)
        if m_type:
            queryset = queryset.filter(maintenance_type=m_type)
            
    elif model_name == 'handover':
        date_start = request.GET.get('date_start', '')
        date_end = request.GET.get('date_end', '')
        area_id = request.GET.get('area', '')
        
        if date_start:
            queryset = queryset.filter(date__date__gte=date_start)
        if date_end:
            queryset = queryset.filter(date__date__lte=date_end)
        if area_id:
            queryset = queryset.filter(Q(source_area_id=area_id) | Q(destination_area_id=area_id))
            
    elif model_name == 'peripheral':
        query = request.GET.get('q', '')
        if query:
            queryset = queryset.filter(
                Q(serial_number__icontains=query) | 
                Q(brand__icontains=query) | 
                Q(model__icontains=query) |
                Q(type__name__icontains=query)
            )

    class DummyAdmin:
        pass
    dummy_admin = DummyAdmin()
    dummy_admin.model = model
    
    return export_to_excel(queryset, dummy_admin, request)


@login_required
def export_equipment_history_pdf(request, pk):
    """Generate a PDF with equipment specs + full history (Hoja de Vida)."""
    equipment = get_object_or_404(Equipment, pk=pk)

    # --- Collect events (same logic as equipment_history_view) ---
    events = []
    events.append({
        'type': 'Registro Inicial',
        'date': equipment.created_at,
        'description': 'Equipo dado de alta en el sistema.',
        'user': '-',
    })
    for m in equipment.maintenances.all().order_by('-date'):
        sort_dt = timezone.datetime.combine(m.date, timezone.datetime.min.time())
        if timezone.is_aware(equipment.created_at):
            sort_dt = timezone.make_aware(sort_dt, timezone.get_current_timezone())
        events.append({
            'type': f'Mant. {m.get_maintenance_type_display()}',
            'date': sort_dt,
            'description': m.description or '-',
            'user': m.performed_by.username if m.performed_by else 'N/A',
        })
    for h in equipment.handovers.all().order_by('-date'):
        dest = h.destination_area.name if h.destination_area else 'N/A'
        client = h.client.name if h.client else (h.receiver_name or 'N/A')
        events.append({
            'type': f'Acta: {h.get_type_display()}',
            'date': h.date,
            'description': f'{dest} — Asignado a: {client}',
            'user': h.technician.username if h.technician else 'N/A',
        })
    for r in equipment.rounds.all().order_by('-datetime'):
        events.append({
            'type': f'Ronda: {r.get_general_status_display()}',
            'date': r.datetime,
            'description': r.observations or 'Revisión técnica de rutina.',
            'user': r.performed_by.username if r.performed_by else 'N/A',
        })
    for c in equipment.component_logs.all().order_by('-date'):
        events.append({
            'type': f'{c.get_action_type_display()}: {c.component_name}',
            'date': c.date,
            'description': c.description or '-',
            'user': c.performed_by.username if c.performed_by else 'N/A',
        })
    events.sort(key=lambda x: x['date'], reverse=True)

    # --- Build PDF ---
    class PDF(FPDF):
        def header(self):
        # Add Logo
            from inventory.models import SystemSettings
            sys_settings = SystemSettings.load()
            if sys_settings and sys_settings.logo and os.path.exists(sys_settings.logo.path):
                logo_path = sys_settings.logo.path
            else:
                logo_path = os.path.join(settings.BASE_DIR, 'inventory', 'static', 'img', 'hfps.jpg')
                if not os.path.exists(logo_path):
                    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'hfps.jpg')
            if os.path.exists(logo_path):
                self.image(logo_path, 10, 8, 33)
                # A4 width is 210mm. 210 - 10 (margin) - 33 (width) = 167
                self.image(logo_path, 167, 8, 33)
            self.set_font('Arial', 'B', 14)
            self.cell(80)
            self.cell(30, 10, 'Hoja de Vida del Equipo', 0, 1, 'C')
            self.set_font('Arial', '', 9)
            self.cell(80)
            self.cell(30, 5, f'Generado: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
            self.ln(15)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', 0, 0, 'C')

    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # --- Equipment Specs ---
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '1. Información del Equipo', 0, 1, 'L', fill=True)
    pdf.ln(3)

    def spec_row(label, value):
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(50, 7, label, 0, 0)
        pdf.set_font('Arial', '', 9)
        pdf.cell(0, 7, str(value or '-'), 0, 1)

    spec_row('Serial:', equipment.serial_number)
    spec_row('Tipo:', equipment.get_type_display())
    spec_row('Marca / Modelo:', f'{equipment.brand} {equipment.model}')
    spec_row('Estado:', equipment.get_status_display())
    spec_row('Área:', equipment.area.name if equipment.area else '-')
    spec_row('Fecha de Compra:', equipment.purchase_date.strftime('%d/%m/%Y') if equipment.purchase_date else '-')
    spec_row('Garantía Hasta:', equipment.warranty_expiry.strftime('%d/%m/%Y') if equipment.warranty_expiry else '-')
    spec_row('Vida Útil:', f'{equipment.lifespan_years} años' if equipment.lifespan_years else '-')
    eol = equipment.end_of_life_date
    spec_row('Fin Vida Útil:', eol.strftime('%d/%m/%Y') if eol else '-')
    spec_row('Dirección IP:', equipment.ip_address or '-')
    spec_row('Sistema Operativo:', equipment.operating_system or '-')
    spec_row('Procesador:', equipment.processor or '-')
    spec_row('RAM:', equipment.ram or '-')
    spec_row('Almacenamiento:', equipment.storage or '-')
    if hasattr(equipment, 'ownership') and equipment.ownership:
        spec_row('Tipo Propiedad:', str(equipment.ownership))
        spec_row('Proveedor:', equipment.provider_name or '-')
    pdf.ln(5)

    # --- History Table ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2. Historial Cronológico', 0, 1, 'L', fill=True)
    pdf.ln(3)

    # Table header
    pdf.set_font('Arial', 'B', 8)
    pdf.cell(28, 8, 'Fecha', 1)
    pdf.cell(40, 8, 'Evento', 1)
    pdf.cell(82, 8, 'Descripción', 1)
    pdf.cell(30, 8, 'Responsable', 1)
    pdf.ln()

    pdf.set_font('Arial', '', 7)
    for ev in events:
        date_str = ev['date'].strftime('%d/%m/%Y %H:%M') if hasattr(ev['date'], 'strftime') else str(ev['date'])[:16]
        desc = (ev['description'] or '-').replace('\n', ' ')
        if len(desc) > 55:
            desc = desc[:55] + '...'
        ev_type = ev['type'][:22] if len(ev['type']) > 22 else ev['type']

        pdf.cell(28, 7, date_str[:16], 1)
        pdf.cell(40, 7, ev_type, 1)
        pdf.cell(82, 7, desc, 1)
        pdf.cell(30, 7, str(ev['user'] or '-')[:16], 1)
        pdf.ln()

    if not events:
        pdf.set_font('Arial', 'I', 9)
        pdf.cell(0, 10, 'Sin historial registrado.', 0, 1, 'C')

    # --- Footer note ---
    pdf.ln(8)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, 'Documento generado automáticamente por el sistema HFPS TIC.', 0, 1, 'C')

    # Output
    pdf_content = pdf.output(dest='S')
    if isinstance(pdf_content, str):
        pdf_content = pdf_content.encode('latin-1')
    else:
        pdf_content = bytes(pdf_content)

    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="hoja_vida_{equipment.serial_number}.pdf"'
    return response
