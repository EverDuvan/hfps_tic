from datetime import time
import openpyxl
from django.http import HttpResponse
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import io
from django.utils import timezone

def export_to_excel(queryset, model_admin, request):
    meta = model_admin.model._meta
    field_names = [field.name for field in meta.fields]

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={meta.verbose_name_plural}.xlsx'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = str(meta.verbose_name_plural)[:31]

    # Header
    ws.append(field_names)

    # Data
    for obj in queryset:
        row = []
        for field in field_names:
            value = getattr(obj, field)
            if value and hasattr(value, 'isoformat'): # Handle dates
                value = value.isoformat()
            if isinstance(value, time):
                value = value.strftime('%H:%M')
            row.append(str(value) if value is not None else '')
        ws.append(row)

    wb.save(response)
    return response

class PDF(FPDF):
    pass
    # Custom header/footer moved inside generation function for flexibility with this specific form

def draw_checked_box(pdf, checked, label):
    # Helper to draw a checkbox [X] Label
    pdf.set_font("Arial", size=8)
    x = pdf.get_x()
    y = pdf.get_y()
    pdf.rect(x, y, 4, 4)
    if checked:
        pdf.text(x+1, y+3, "X")
    pdf.set_xy(x + 5, y)
    pdf.cell(40, 4, label)
    pdf.ln(5)

def generate_maintenance_pdf(m):
    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", size=8)
    
    # --- Header ---
    # Widths: Logo area, Title, Code block
    # Approximating roughly: 30, 110, 50
    
    start_y = pdf.get_y()
    
    # Logo Placeholder
    pdf.cell(30, 20, "HFPS", border=1, align='C') 
    
    # Title
    current_x = pdf.get_x()
    current_y = pdf.get_y()
    pdf.set_xy(current_x, start_y)
    pdf.set_font("Arial", 'B', 10)
    pdf.multi_cell(110, 10, "MANTENIMIENTO PREVENTIVO Y CORRECTIVO \nEQUIPOS DE COMPUTO", border=1, align='C')
    
    # Code block
    current_x += 110
    pdf.set_xy(current_x, start_y)
    pdf.set_font("Arial", size=8)
    
    # Nested cells for code block
    pdf.cell(50, 5, "Código: FR-GT-03 Versión: 01", border=1, ln=1)
    pdf.set_x(current_x)
    
    # Date logic
    date_str = m.date.strftime('%Y-%m-%d')
    day = m.date.day
    month = m.date.month
    year = m.date.year
    
    pdf.cell(50, 5, "Fecha de elaboración:", border=1, ln=1)
    pdf.set_x(current_x)
    pdf.cell(16, 5, "DD", border=1, align='C')
    pdf.cell(17, 5, "MM", border=1, align='C')
    pdf.cell(17, 5, "AAAA", border=1, ln=1, align='C')
    pdf.set_x(current_x)
    pdf.cell(16, 5, str(day), border=1, align='C')
    pdf.cell(17, 5, str(month), border=1, align='C')
    pdf.cell(17, 5, str(year), border=1, ln=1, align='C')
    
    pdf.set_y(start_y + 20)
    pdf.ln(2)

    # --- 1. DATOS DEL EQUIPO ---
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 5, "1. DATOS DEL EQUIPO", border=1, ln=1, fill=True)
    
    pdf.set_font("Arial", size=8)
    pdf.cell(30, 5, "Propiedad:", border=1)
    pdf.cell(30, 5, "HFPS", border=1)
    pdf.cell(30, 5, "Tipo adquisición:", border=1)
    pdf.cell(30, 5, "Propio", border=1)
    pdf.cell(20, 5, "Estado:", border=1)
    pdf.cell(50, 5, m.equipment.get_status_display(), border=1, ln=1)
    
    pdf.cell(30, 5, "No. Serie (S/N):", border=1)
    pdf.cell(60, 5, m.equipment.serial_number, border=1)
    pdf.cell(30, 5, "Nombre Equipo:", border=1)
    pdf.cell(70, 5, f"{m.equipment.brand} {m.equipment.model}", border=1, ln=1)
    
    pdf.cell(30, 5, "NomUsuarioSO:", border=1)
    pdf.cell(60, 5, m.equipment.os_user or "", border=1)
    pdf.cell(100, 5, "", border=1, ln=1) # Empty space filler

    pdf.ln(2)

    # --- 2. INFORMACION CENTRO DE COSTOS ---
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 5, "2. INFORMACION CENTRO DE COSTOS", border=1, ln=1, fill=True)
    
    area = m.equipment.area
    cc = area.cost_center if area and area.cost_center else None
    
    pdf.set_font("Arial", size=8)
    pdf.cell(40, 5, "Centro De Costos:", border=1)
    pdf.cell(150, 5, f"{cc.code} - {cc.name}" if cc else "N/A", border=1, ln=1)
    
    pdf.cell(40, 5, "Ubicación Predeterminada:", border=1)
    pdf.cell(150, 5, area.name if area else "N/A", border=1, ln=1)
    
    pdf.cell(40, 5, "Nombre Proceso/Área:", border=1)
    pdf.cell(150, 5, area.description or area.name if area else "", border=1, ln=1)

    pdf.ln(2)

    # --- 3. CONFIGURACION DEL EQUIPO ---
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 5, "3. CONFIGURACION DEL EQUIPO", border=1, ln=1, fill=True)
    
    pdf.set_font("Arial", size=8)
    # Row 1
    pdf.cell(30, 5, "Tipo de Equipo:", border=1)
    pdf.cell(40, 5, m.equipment.get_type_display(), border=1)
    pdf.cell(20, 5, "Marca:", border=1)
    pdf.cell(40, 5, m.equipment.brand, border=1)
    pdf.cell(20, 5, "Modelo:", border=1)
    pdf.cell(40, 5, m.equipment.model, border=1, ln=1)
    
    # Row 2
    pdf.cell(30, 5, "Voltaje:", border=1)
    pdf.cell(40, 5, m.equipment.voltage or "", border=1)
    pdf.cell(20, 5, "Amperaje:", border=1)
    pdf.cell(40, 5, m.equipment.amperage or "", border=1)
    pdf.cell(20, 5, "Sist. Operativo:", border=1)
    pdf.cell(40, 5, m.equipment.operating_system or "", border=1, ln=1)
    
    # Row 3
    pdf.cell(40, 5, "Tamaño Pantalla (AiO/Laptop):", border=1)
    pdf.cell(150, 5, m.equipment.screen_size or "", border=1, ln=1)
    
    pdf.ln(2)

    # --- 4. TIPO DE SOPORTE REQUERIDO ---
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 5, "4. TIPO DE SOPORTE REQUERIDO", border=1, ln=1, fill=True)
    
    # Grid of checkboxes. 4 columns.
    pdf.set_font("Arial", size=8)
    pdf.cell(47, 5, f"[ {'X' if m.type_review else ' '} ] REVISIÓN DE EQUIPO", border=1)
    pdf.cell(47, 5, f"[ {'X' if m.type_software_failure else ' '} ] FALLAS CON SOFTWARE", border=1)
    pdf.cell(47, 5, f"[ {'X' if m.type_connection else ' '} ] PROBLEMAS CONEXIÓN", border=1)
    pdf.cell(49, 5, f"[ {'X' if m.type_updates else ' '} ] ACTUALIZACIONES WIN10", border=1, ln=1)

    pdf.cell(47, 5, f"[ {'X' if m.type_cleaning else ' '} ] LIMPIEZA EQUIPO", border=1)
    pdf.cell(47, 5, f"[ {'X' if m.type_install else ' '} ] INSTALACIÓN SOFTWARE", border=1)
    pdf.cell(47, 5, f"[ {'X' if m.type_peripheral else ' '} ] FALLA PERIFÉRICOS", border=1)
    pdf.cell(49, 5, f"[ {'X' if m.type_backup else ' '} ] COPIA SEGURIDAD", border=1, ln=1)

    pdf.ln(2)
    
    # --- 5. ACTIVIDADES DE LIMPIEZA AL S.O. ---
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 5, "5. ACTIVIDADES DE LIMPIEZA AL SISTEMA OPERATIVO", border=1, ln=1, fill=True)
    
    pdf.set_font("Arial", size=8)
    pdf.cell(95, 5, f"[ {'X' if m.cleaning_defrag else ' '} ] DESFRAGMENTACIÓN DISCO DURO", border=1)
    pdf.cell(95, 5, f"[ {'X' if m.cleaning_cco else ' '} ] EJECUCIÓN C-CLEANER", border=1, ln=1)
    pdf.cell(95, 5, f"[ {'X' if m.cleaning_scandisk else ' '} ] SCANDISK", border=1)
    pdf.cell(95, 5, f"[ {'X' if m.cleaning_space else ' '} ] LIBERACIÓN DE ESPACIO", border=1, ln=1)

    pdf.ln(2)

    # --- 6. OBSERVACIONES ---
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 5, "6. OBSERVACIONES DEL EQUIPO ANTES DEL MANTENIMIENTO", border=1, ln=1, fill=True)
    pdf.set_font("Arial", size=8)
    pdf.multi_cell(0, 5, m.description or "N/A", border=1)
    
    pdf.ln(2)

    # --- 7. ETAPAS DEL MANTENIMIENTO HARDWARE ---
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 5, "7. ETAPAS DEL MANTENIMIENTO DEL HARDWARE", border=1, ln=1, fill=True)
    
    pdf.set_font("Arial", size=8)
    # List of hardware tasks
    hw_tasks = [
        ("Retiro del equipo / Desmontaje", m.hw_disassembly),
        ("Limpieza Fuente de Poder", m.hw_power_supply),
        ("Limpieza Ventiladores", m.hw_fans),
        ("Limpieza Chasis y Cubiertas", m.hw_chassis),
        ("Uso Crema Disipadora", m.hw_thermal_paste),
        ("Uso Limpiador Contactos", m.hw_contacts),
        ("Limpieza Teclado y Mouse", m.hw_keyboard_mouse),
        ("Limpieza Monitor/Pantalla", m.hw_screen),
        ("Ensamble y Pruebas", m.hw_reassembly)
    ]
    
    for task, checked in hw_tasks:
        pdf.cell(95, 5, task, border=1)
        pdf.cell(20, 5, "REALIZADO" if checked else "N/A", border=1, align='C', ln=1)

    pdf.ln(5)
    
    # --- FOOTER / SIGNATURES ---
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(40, 5, "ESTADO FINAL:", border=1)
    pdf.set_font("Arial", size=9)
    pdf.cell(150, 5, "EQUIPO EN FUNCIONAMIENTO" if m.equipment.status == 'ACTIVE' else m.equipment.get_status_display(), border=1, ln=1)
    
    start_time = m.start_time.strftime('%H:%M') if m.start_time else "  :  "
    end_time = m.end_time.strftime('%H:%M') if m.end_time else "  :  "
    
    pdf.cell(40, 5, "HORA INICIO:", border=1)
    pdf.cell(55, 5, start_time, border=1)
    pdf.cell(40, 5, "HORA FINAL:", border=1)
    pdf.cell(55, 5, end_time, border=1, ln=1)
    
    pdf.ln(10)
    
    # Signatures
    y_sig = pdf.get_y()
    
    # User / Received By
    pdf.line(10, y_sig + 15, 90, y_sig + 15)
    pdf.set_xy(10, y_sig + 16)
    pdf.cell(80, 5, "NOMBRE USUARIO / RECIBIDO POR", align='C', ln=1)
    
    # Technician
    pdf.line(110, y_sig + 15, 190, y_sig + 15)
    pdf.set_xy(110, y_sig + 16)
    tech_name = m.performed_by.get_full_name() if m.performed_by else "TÉCNICO"
    pdf.cell(80, 5, tech_name, align='C', ln=1)
    pdf.set_x(110)
    pdf.cell(80, 5, "SOPORTE TÉCNICO - TIC", align='C', ln=1)

    output = io.BytesIO()
    pdf.output(output)
    return output.getvalue()

def generate_handover_pdf(handover):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(0, 10, f"Acta de Entrega #{handover.id}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, "Fecha:", 0)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, handover.date.strftime('%Y-%m-%d %H:%M'), ln=True)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, "Tipo:", 0)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, handover.get_type_display(), ln=True)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, "Origen:", 0)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, str(handover.source_area) if handover.source_area else "N/A", ln=True)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, "Destino:", 0)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, str(handover.destination_area) if handover.destination_area else "N/A", ln=True)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, "Recibido por:", 0)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, handover.receiver_name or "N/A", ln=True)

    if handover.client:
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(40, 10, "Cliente:", 0)
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"{handover.client.name} (ID: {handover.client.identification})", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Equipos:", ln=True)
    pdf.set_font("Arial", '', 12)
    for eq in handover.equipment.all():
         pdf.cell(0, 10, f"- {eq}", ln=True)

    if handover.peripherals.count() > 0:
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Periféricos:", ln=True)
        pdf.set_font("Arial", '', 12)
        for p in handover.peripherals.all():
             pdf.cell(0, 10, f"- {p}", ln=True)

    if handover.observations:
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Observaciones:", ln=True)
        pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 10, handover.observations)

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, "Técnico:", 0)
    pdf.set_font("Arial", '', 12)
    tech_name = handover.technician.get_full_name() if handover.technician else "N/A"
    if not tech_name and handover.technician:
        tech_name = handover.technician.username
    pdf.cell(0, 10, tech_name, ln=True)
    
    pdf.ln(20)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Firmas:", ln=True)
    pdf.ln(20)
    pdf.cell(90, 10, "Entregado por: __________________", 0)
    pdf.cell(90, 10, "Recibido por: __________________", ln=True)
    
    output = io.BytesIO()
    pdf.output(output)
    return output.getvalue()
