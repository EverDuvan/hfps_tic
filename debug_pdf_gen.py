import os
import django
from django.conf import settings

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hfps_tic.settings')
django.setup()

from fpdf import FPDF
from inventory.charts import generate_equipment_by_type_chart
from inventory.models import Equipment
import datetime

# Mock data
equipments = Equipment.objects.all()
equipment_by_type = list(equipments.values('type').annotate(count=django.db.models.Count('type')))

print("Generating chart...")
chart_buffer = generate_equipment_by_type_chart(equipment_by_type)
print(f"Chart buffer generated: {type(chart_buffer)}")

# PDF generation logic from views.py (simplified)
class PDF(FPDF):
    def header(self):
        # Logo
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'hfps.jpg')
        if os.path.exists(logo_path):
            try:
                self.image(logo_path, 10, 8, 33)
            except Exception as e:
                print(f"Error loading logo: {e}")
            
        self.set_font('helvetica', 'B', 15)
        self.cell(80) # Move to right
        self.cell(30, 10, 'Reporte de Gestion', 0, 1, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}/{{nb}}', 0, 0, 'C')

try:
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font('helvetica', '', 12)
    
    pdf.cell(0, 10, f'Fecha de generacion: {datetime.date.today()}', 0, 1)
    
    # Add chart
    if chart_buffer:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            tmp.write(chart_buffer.getvalue())
            tmp_path = tmp.name
        
        print(f"Adding image from {tmp_path}")
        pdf.image(tmp_path, x=10, y=30, w=100)
        os.unlink(tmp_path)
    
    print("Generating PDF output...")
    pdf_content = pdf.output()
    print(f"PDF content type: {type(pdf_content)}")
    print(f"PDF content length: {len(pdf_content)}")
    
    with open('debug_output.pdf', 'wb') as f:
        f.write(pdf_content)
    print("PDF saved to debug_output.pdf")

except Exception as e:
    import traceback
    traceback.print_exc()
