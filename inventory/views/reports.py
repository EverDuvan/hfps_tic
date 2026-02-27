import datetime
import tempfile
import os
import logging
from datetime import timedelta

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, F
from django.utils import timezone

from fpdf import FPDF

from ..models import Equipment, Maintenance, Handover, Peripheral, EquipmentRound, ComponentLog
from ..choices import MAINTENANCE_TYPE_CHOICES
from ..services import get_lifespan_expired_queryset
from ..charts import (
    generate_equipment_by_type_chart, 
    generate_maintenance_by_type_chart, 
    generate_equipment_status_chart,
    generate_handover_by_type_chart,
    generate_handover_by_area_chart,
    generate_round_status_chart
)

logger = logging.getLogger('inventory')

__all__ = ['reports_dashboard_view', 'export_report_pdf']


@login_required
def reports_dashboard_view(request):
    # 1. Date Filtering
    today = timezone.now().date()
    start_str = request.GET.get('start_date', '')
    end_str = request.GET.get('end_date', '')
    
    if not start_str:
        start_date = today.replace(month=1, day=1)
    else:
        try:
            start_date = datetime.datetime.strptime(start_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = today.replace(month=1, day=1)
            
    if not end_str:
        end_date = today
    else:
        try:
            end_date = datetime.datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            end_date = today

    # 2. Main QuerySets
    maintenances = Maintenance.objects.filter(date__range=[start_date, end_date])
    handovers = Handover.objects.filter(date__date__range=[start_date, end_date])
    rounds = EquipmentRound.objects.filter(datetime__date__range=[start_date, end_date])
    equipments = Equipment.objects.all()

    # 3. KPIs
    total_equipment = equipments.count()
    active_equipment = equipments.filter(status='ACTIVE').count()
    maintenance_count = maintenances.count()
    handover_count = handovers.count()
    round_count = rounds.count()
    
    # 4. Charts Data
    eq_by_type = list(equipments.values('type').annotate(count=Count('type')).order_by('-count'))
    m_by_type = list(maintenances.values('maintenance_type').annotate(count=Count('id')))
    top_techs = list(maintenances.values('performed_by__username').annotate(count=Count('id')).order_by('-count')[:5])
    eq_by_status = list(equipments.values('status').annotate(count=Count('status')))
    handover_by_type = list(handovers.values('type').annotate(count=Count('type')))
    handover_by_area = list(handovers.values('destination_area__name').annotate(count=Count('destination_area')).order_by('-count')[:5])
    round_by_status = list(rounds.values('general_status').annotate(count=Count('id')))

    # 5. Actionable Lists
    limit_date = today + datetime.timedelta(days=90)
    warranty_expiring = equipments.filter(warranty_expiry__range=[today, limit_date]).order_by('warranty_expiry')
    low_stock_peripherals = Peripheral.objects.filter(quantity__lte=F('min_stock_level'))
    warranty_expired = equipments.filter(warranty_expiry__lt=today).exclude(status='RETIRED').order_by('warranty_expiry')
    
    # Calculate lifespan expired using service (cross-database compatible)
    lifespan_expired = get_lifespan_expired_queryset(equipments)

    context = {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'total_equipment': total_equipment,
        'active_equipment': active_equipment,
        'maintenance_count': maintenance_count,
        'handover_count': handover_count,
        'eq_by_type': eq_by_type,
        'm_by_type': m_by_type,
        'top_techs': top_techs,
        'eq_by_status': eq_by_status,
        'warranty_expiring': warranty_expiring,
        'low_stock_peripherals': low_stock_peripherals,
        'warranty_expired': warranty_expired,
        'lifespan_expired': lifespan_expired,
        'handover_by_type': handover_by_type,
        'handover_by_area': handover_by_area,
        'round_count': round_count,
        'round_by_status': round_by_status,
    }
    return render(request, 'inventory/reports_dashboard.html', context)


@login_required
def export_report_pdf(request):
    # 1. Date Filtering (Same logic as dashboard)
    today = timezone.now().date()
    start_str = request.GET.get('start_date', '')
    end_str = request.GET.get('end_date', '')
    
    if not start_str:
        start_date = today.replace(month=1, day=1)
    else:
        try:
            start_date = datetime.datetime.strptime(start_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = today.replace(month=1, day=1)
            
    if not end_str:
        end_date = today
    else:
        try:
            end_date = datetime.datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            end_date = today

    # 2. Fetch Data
    maintenances = Maintenance.objects.filter(date__range=[start_date, end_date])
    handovers = Handover.objects.filter(date__date__range=[start_date, end_date])
    rounds = EquipmentRound.objects.filter(datetime__date__range=[start_date, end_date])
    component_logs = ComponentLog.objects.filter(date__date__range=[start_date, end_date])
    equipments = Equipment.objects.all()
    
    total_equipment = equipments.count()
    active_equipment = equipments.filter(status='ACTIVE').count()
    maintenance_count = maintenances.count()
    handover_count = handovers.count()
    round_count = rounds.count()
    
    limit_date = today + datetime.timedelta(days=90)
    warranty_expiring = equipments.filter(warranty_expiry__range=[today, limit_date]).order_by('warranty_expiry')
    low_stock_peripherals = Peripheral.objects.filter(quantity__lte=F('min_stock_level'))
    warranty_expired = equipments.filter(warranty_expiry__lt=today).exclude(status='RETIRED').order_by('warranty_expiry')
    
    lifespan_expired = get_lifespan_expired_queryset(equipments)
    
    # Data for Charts
    eq_by_type_data = list(equipments.values('type').annotate(count=Count('type')).order_by('-count'))
    m_by_type_data = list(maintenances.values('maintenance_type').annotate(count=Count('id')))
    eq_by_status_data = list(equipments.values('status').annotate(count=Count('status')))
    h_by_type_data = list(handovers.values('type').annotate(count=Count('type')))
    h_by_area_data = list(handovers.values('destination_area__name').annotate(count=Count('destination_area')).order_by('-count')[:5])
    round_by_status_data = list(rounds.values('general_status').annotate(count=Count('id')))
    
    critical_equipments = Equipment.objects.annotate(
        maint_count=Count('maintenances', filter=Q(maintenances__in=maintenances))
    ).filter(maint_count__gt=0).order_by('-maint_count')[:5]

    # 3. Generate PDF
    class PDF(FPDF):
        def header(self):
            from django.conf import settings
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
                
            self.set_font('Arial', 'B', 15)
            self.cell(80)
            self.cell(30, 10, 'Reporte de Gestión', 0, 1, 'C')
            
            self.set_font('Arial', '', 10)
            self.cell(80)
            self.cell(30, 5, f'Generado el: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
            self.ln(20)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', 0, 0, 'C')

    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # --- Period Info ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f'Periodo del Reporte: {start_date.strftime("%d/%m/%Y")} al {end_date.strftime("%d/%m/%Y")}', 0, 1, 'L')
    pdf.ln(5)
    
    # --- Executive Summary ---
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '1. Resumen Ejecutivo', 0, 1, 'L', fill=True)
    pdf.ln(2)
    
    pdf.set_font('Arial', '', 11)
    col_width = 45
    
    pdf.cell(col_width, 10, 'Total Equipos:', 0, 0)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(col_width, 10, str(total_equipment), 0, 0)
    
    pdf.set_font('Arial', '', 11)
    pdf.cell(col_width, 10, 'Mantenimientos:', 0, 0)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(col_width, 10, str(maintenance_count), 0, 1)
    
    pdf.set_font('Arial', '', 11)
    pdf.cell(col_width, 10, 'Equipos Activos:', 0, 0)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(col_width, 10, str(active_equipment), 0, 0)
    
    pdf.set_font('Arial', '', 11)
    pdf.cell(col_width, 10, 'Entregas:', 0, 0)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(col_width, 10, str(handover_count), 0, 1)
    
    pdf.set_font('Arial', '', 11)
    pdf.cell(col_width, 10, 'Rondas Realizadas:', 0, 0)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(col_width, 10, str(round_count), 0, 1)
    pdf.ln(5)
    
    # --- Top 5 Critical Equipments ---
    if critical_equipments.exists():
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(220, 50, 50)
        pdf.cell(0, 10, 'Top 5 Equipos Críticos (Mayor nro. de mantenimientos)', 0, 1, 'L', fill=False)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(40, 8, 'Serial', 1)
        pdf.cell(70, 8, 'Equipo', 1)
        pdf.cell(40, 8, 'Mantenimientos', 1, 0, 'C')
        pdf.ln()
        
        pdf.set_font('Arial', '', 9)
        for eq in critical_equipments:
            pdf.cell(40, 8, str(eq.serial_number), 1)
            pdf.cell(70, 8, f"{eq.brand} {eq.model}"[:40], 1)
            
            pdf.set_text_color(220, 50, 50)
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(40, 8, str(eq.maint_count), 1, 0, 'C')
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Arial', '', 9)
            pdf.ln()
        pdf.ln(5)
    
    # --- Low Stock Alerts ---
    if low_stock_peripherals.exists():
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(220, 50, 50)
        pdf.cell(0, 10, '1.1 Alertas de Stock Bajo', 0, 1, 'L', fill=False)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(90, 8, 'Periférico', 1)
        pdf.cell(25, 8, 'Stock', 1)
        pdf.cell(25, 8, 'Mínimo', 1)
        pdf.cell(40, 8, 'Área', 1)
        pdf.ln()
        
        pdf.set_font('Arial', '', 9)
        for p in low_stock_peripherals:
            p_name = f"{p.type.name} - {p.brand} {p.model}"
            pdf.cell(90, 8, p_name[:50], 1)
            
            if p.quantity == 0:
                pdf.set_text_color(220, 50, 50)
                pdf.set_font('Arial', 'B', 9)
            
            pdf.cell(25, 8, str(p.quantity), 1)
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Arial', '', 9)
            
            pdf.cell(25, 8, str(p.min_stock_level), 1)
            area_name = p.area.name if p.area else "-"
            pdf.cell(40, 8, area_name[:20], 1)
            pdf.ln()
        pdf.ln(5)

    # --- Charts Section ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '2. Gráficos Estadísticos', 0, 1, 'L', fill=True)
    pdf.ln(2)
    
    temp_files = []
    
    def add_chart_to_pdf(pdf_obj, chart_func, data, title, x, y, w, h):
        buf = chart_func(data)
        if buf:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                tmp.write(buf.read())
                tmp_path = tmp.name
                temp_files.append(tmp_path)
            
            pdf_obj.image(tmp_path, x=x, y=y, w=w, h=h)
            return True
        return False

    current_y = pdf.get_y()
    
    add_chart_to_pdf(pdf, generate_equipment_by_type_chart, eq_by_type_data, "Equipos por Tipo", 10, current_y, 90, 60)
    add_chart_to_pdf(pdf, generate_equipment_status_chart, eq_by_status_data, "Estado Equipos", 110, current_y, 70, 70)
    
    pdf.set_y(current_y + 75)
    
    if maintenance_count > 0:
        current_y = pdf.get_y()
        add_chart_to_pdf(pdf, generate_maintenance_by_type_chart, m_by_type_data, "Mantenimientos", 50, current_y, 110, 70)
        pdf.set_y(current_y + 75)

    if handover_count > 0:
        current_y = pdf.get_y()
        if current_y > 200:
             pdf.add_page()
             current_y = pdf.get_y()
             
        add_chart_to_pdf(pdf, generate_handover_by_type_chart, h_by_type_data, "Entregas por Tipo", 10, current_y, 90, 60)
        add_chart_to_pdf(pdf, generate_handover_by_area_chart, h_by_area_data, "Entregas por Área", 110, current_y, 90, 60)
        pdf.set_y(current_y + 75)
        
    if round_count > 0:
        current_y = pdf.get_y()
        if current_y > 200:
             pdf.add_page()
             current_y = pdf.get_y()
        add_chart_to_pdf(pdf, generate_round_status_chart, round_by_status_data, "Estado de Rondas", 60, current_y, 90, 90)
        pdf.set_y(current_y + 95)
    
    pdf.ln(5)

    # --- Maintenance Summary Table ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '3. Actividad por Técnico (Top 5)', 0, 1, 'L', fill=True)
    pdf.ln(2)
    
    top_techs = list(maintenances.values('performed_by__username').annotate(count=Count('id')).order_by('-count')[:5])
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(80, 8, 'Técnico', 1)
    pdf.cell(40, 8, 'Mantenimientos', 1)
    pdf.ln()
    
    pdf.set_font('Arial', '', 10)
    if top_techs:
        for tech in top_techs:
            username = tech['performed_by__username']
            pdf.cell(80, 8, str(username).title(), 1)
            pdf.cell(40, 8, str(tech['count']), 1)
            pdf.ln()
    else:
        pdf.cell(120, 8, 'Sin actividad registrada.', 1)
        pdf.ln()
    pdf.ln(5)

    # --- Warranty Alerts ---
    if warranty_expiring.exists():
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(220, 50, 50)
        pdf.cell(0, 10, '4. Alertas de Garantía (Próximos 90 días)', 0, 1, 'L', fill=False)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(40, 8, 'Fecha Vence', 1)
        pdf.cell(50, 8, 'Serial', 1)
        pdf.cell(60, 8, 'Equipo', 1)
        pdf.cell(40, 8, 'Área', 1)
        pdf.ln()
        
        pdf.set_font('Arial', '', 9)
        for w in warranty_expiring:
            pdf.cell(40, 8, w.warranty_expiry.strftime('%Y-%m-%d'), 1)
            pdf.cell(50, 8, str(w.serial_number), 1)
            pdf.cell(60, 8, f"{w.brand} {w.model}"[:30], 1)
            area_name = w.area.name if w.area else "-"
            pdf.cell(40, 8, area_name[:20], 1)
            pdf.ln()
            
    # --- Expired Warranty ---
    if warranty_expired.exists():
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(220, 20, 60)
        pdf.cell(0, 10, '4.1 Garantías Vencidas', 0, 1, 'L', fill=False)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(40, 8, 'Fecha Vence', 1)
        pdf.cell(50, 8, 'Serial', 1)
        pdf.cell(60, 8, 'Equipo', 1)
        pdf.cell(40, 8, 'Área', 1)
        pdf.ln()
        
        pdf.set_font('Arial', '', 9)
        for w in warranty_expired:
            pdf.cell(40, 8, w.warranty_expiry.strftime('%Y-%m-%d'), 1)
            pdf.cell(50, 8, str(w.serial_number), 1)
            pdf.cell(60, 8, f"{w.brand} {w.model}"[:30], 1)
            area_name = w.area.name if w.area else "-"
            pdf.cell(40, 8, area_name[:20], 1)
            pdf.ln()

    # --- Expired Lifespan ---
    if lifespan_expired:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(220, 20, 60)
        pdf.cell(0, 10, '4.2 Vida Útil Vencida', 0, 1, 'L', fill=False)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(40, 8, 'Fin Vida Útil', 1)
        pdf.cell(50, 8, 'Serial', 1)
        pdf.cell(60, 8, 'Equipo', 1)
        pdf.cell(40, 8, 'Área', 1)
        pdf.ln()
        
        pdf.set_font('Arial', '', 9)
        for e in lifespan_expired:
            eol_date = e.end_of_life_date
            eol_str = eol_date.strftime('%Y-%m-%d') if eol_date else "N/A"
            pdf.cell(40, 8, eol_str, 1)
            pdf.cell(50, 8, str(e.serial_number), 1)
            pdf.cell(60, 8, f"{e.brand} {e.model}"[:30], 1)
            area_name = e.area.name if e.area else "-"
            pdf.cell(40, 8, area_name[:20], 1)
            pdf.ln()
            
    # --- Detailed Maintenance Log ---
    if maintenances.exists():
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, '5. Detalle de Mantenimientos Realizados', 0, 1, 'L', fill=True)
        pdf.ln(2)
        
        pdf.set_font('Arial', 'B', 8)
        pdf.cell(25, 8, 'Fecha', 1)
        pdf.cell(30, 8, 'Serial', 1)
        pdf.cell(35, 8, 'Equipo', 1)
        pdf.cell(30, 8, 'Tipo', 1)
        pdf.cell(35, 8, 'Técnico', 1)
        pdf.cell(35, 8, 'Descripción', 1)
        pdf.ln()
        
        pdf.set_font('Arial', '', 8)
        for m in maintenances.select_related('equipment', 'performed_by'):
            pdf.cell(25, 8, m.date.strftime('%Y-%m-%d'), 1)
            pdf.cell(30, 8, m.equipment.serial_number[:15], 1)
            pdf.cell(35, 8, f"{m.equipment.brand} {m.equipment.model}"[:20], 1)
            
            m_type_label = dict(MAINTENANCE_TYPE_CHOICES).get(m.maintenance_type, m.maintenance_type)
            pdf.cell(30, 8, str(m_type_label)[:15], 1)
            
            tech_name = m.performed_by.username if m.performed_by else "N/A"
            pdf.cell(35, 8, tech_name[:18], 1)
            
            desc = m.description.replace('\n', ' ')[:20] + "..." if len(m.description) > 20 else m.description
            pdf.cell(35, 8, desc, 1)
            pdf.ln()
            
    # --- Detailed Handover Log ---
    if handovers.exists():
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, '6. Detalle de Entregas (Actas)', 0, 1, 'L', fill=True)
        pdf.ln(2)
        
        pdf.set_font('Arial', 'B', 8)
        pdf.cell(25, 8, 'Fecha', 1)
        pdf.cell(60, 8, 'Equipos (Serials)', 1)
        pdf.cell(35, 8, 'Origen', 1)
        pdf.cell(35, 8, 'Destino', 1)
        pdf.cell(30, 8, 'Tipo', 1)
        pdf.ln()
        
        pdf.set_font('Arial', '', 7)
        for h in handovers.select_related('source_area', 'destination_area').prefetch_related('equipment'):
            h_date = h.date.strftime('%Y-%m-%d') if hasattr(h.date, 'strftime') else str(h.date)[:10]
            
            eq_list = [f"{e.serial_number} ({e.brand})" for e in h.equipment.all()]
            eq_str = ", ".join(eq_list)
            
            pdf.cell(25, 8, h_date, 1)
            pdf.cell(60, 8, eq_str[:45], 1)
            
            source = h.source_area.name if h.source_area else "N/A"
            dest = h.destination_area.name if h.destination_area else "N/A"
            
            pdf.cell(35, 8, source[:20], 1)
            pdf.cell(35, 8, dest[:20], 1)
            pdf.cell(30, 8, h.get_type_display()[:15], 1)
            pdf.ln()

    # --- Detailed Rounds Log ---
    if rounds.exists():
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, '7. Súper-Detalle de Rondas de Inspección', 0, 1, 'L', fill=True)
        pdf.ln(2)
        
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(0, 6, 'Leyenda Puntos: (B = Bien / OK), (R = Regular / !), (M = Malo / X), (N/A = No Aplica)', 0, 1, 'L')
        pdf.ln(2)
        
        pdf.set_font('Arial', 'B', 7)
        pdf.cell(18, 8, 'Fecha', 1)
        pdf.cell(30, 8, 'Equipo (Serial)', 1)
        pdf.cell(12, 8, 'Físico', 1, 0, 'C')
        pdf.cell(12, 8, 'Energ', 1, 0, 'C')
        pdf.cell(12, 8, 'Pant', 1, 0, 'C')
        pdf.cell(12, 8, 'Peri', 1, 0, 'C')
        pdf.cell(12, 8, 'Red', 1, 0, 'C')
        pdf.cell(12, 8, 'OS', 1, 0, 'C')
        pdf.cell(20, 8, 'Estado Gral.', 1)
        pdf.cell(50, 8, 'Observaciones', 1)
        pdf.ln()
        
        pdf.set_font('Arial', '', 6)
        
        def check_to_initial(val):
            maps = {'PASS': 'B', 'WARN': 'R', 'FAIL': 'M', 'NA': 'N/A'}
            return maps.get(val, val)
            
        for r in rounds.select_related('equipment', 'performed_by'):
            r_date = r.datetime.strftime('%Y-%m-%d %H:%M')
            pdf.cell(18, 8, r_date[:10], 1)
            pdf.cell(30, 8, str(r.equipment.serial_number)[:18], 1)
            
            pdf.cell(12, 8, check_to_initial(r.hw_status), 1, 0, 'C')
            pdf.cell(12, 8, check_to_initial(r.powers_on), 1, 0, 'C')
            pdf.cell(12, 8, check_to_initial(r.monitor_status), 1, 0, 'C')
            pdf.cell(12, 8, check_to_initial(r.peripherals_status), 1, 0, 'C')
            pdf.cell(12, 8, check_to_initial(r.network_status), 1, 0, 'C')
            pdf.cell(12, 8, check_to_initial(r.os_status), 1, 0, 'C')
            
            status_map = {'GOOD': 'Bueno', 'REGULAR': 'Regular', 'BAD': 'Malo'}
            g_status = status_map.get(r.general_status, r.general_status)
            pdf.cell(20, 8, g_status[:10], 1)
            
            obs = r.observations.replace('\n', ' ')[:45] + "..." if r.observations and len(r.observations) > 45 else (r.observations or "-")
            pdf.cell(50, 8, obs, 1)
            pdf.ln()

    # --- Component Audit Log ---
    if component_logs.exists():
        pdf.add_page()
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, '8. Auditoría de Componentes y Piezas (Hoja de Vida)', 0, 1, 'L', fill=True)
        pdf.ln(2)
        
        pdf.set_font('Arial', 'B', 8)
        pdf.cell(25, 8, 'Fecha', 1)
        pdf.cell(30, 8, 'Acción', 1)
        pdf.cell(35, 8, 'Equipo (Serial)', 1)
        pdf.cell(50, 8, 'Pieza / Periférico', 1)
        pdf.cell(15, 8, 'Cant.', 1, 0, 'C')
        pdf.cell(35, 8, 'Técnico', 1)
        pdf.ln()
        
        pdf.set_font('Arial', '', 7)
        for c in component_logs.select_related('equipment', 'performed_by'):
            c_date = c.date.strftime('%Y-%m-%d %H:%M')
            pdf.cell(25, 8, c_date[:16], 1)
            pdf.cell(30, 8, c.get_action_type_display()[:15], 1)
            pdf.cell(35, 8, c.equipment.serial_number[:18], 1)
            
            piece_name = c.component_name[:35] if c.component_name else "N/A"
            pdf.cell(50, 8, piece_name, 1)
            pdf.cell(15, 8, str(c.quantity), 1, 0, 'C')
            tech = c.performed_by.username if c.performed_by else "N/A"
            pdf.cell(35, 8, tech[:18], 1)
            pdf.ln()

    # --- Descriptive Footer Note ---
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(100, 100, 100)
    conclusion_text = (
        "Nota: Este reporte gerencial ha sido generado automáticamente por el sistema HFPS TIC. "
        "Las estadísticas presentadas brindan un panorama integral que incluye alertas de stock, "
        "el Top 5 de equipos con mayor tasa de falla (mantenimientos), la auditoría de piezas de hardware reemplazadas (Hoja de Vida), "
        "entregas formales y el súper-detalle del estado de los equipos durante las rondas técnicas. "
        "Se recomienda la revisión periódica de los equipos reportados con advertencias o fallas en las rondas, "
        "y evaluar el reemplazo definitivo del Top 5 de equipos problemáticos para optimizar el presupuesto IT."
    )
    pdf.multi_cell(0, 5, conclusion_text)
    pdf.set_text_color(0, 0, 0)
    
    # Output
    pdf_content = pdf.output(dest='S')
    if isinstance(pdf_content, str):
        pdf_content = pdf_content.encode('latin-1')
    else:
        pdf_content = bytes(pdf_content)
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="reporte_inventario_{start_date}_{end_date}.pdf"'
    
    # Clean up temp files
    for tf in temp_files:
        try:
            os.unlink(tf)
        except OSError:
            pass
    
    return response
