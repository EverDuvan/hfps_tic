import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hfps_tic.settings')
django.setup()

from inventory.models import Area, Equipment, MaintenanceSchedule

def run():
    with open('data.tsv', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_area = None

    for line in lines[1:]:  # Skip header
        line = line.strip('\n')
        if not line.strip():
            continue
        
        parts = line.split('\t')
        
        # If the first part has text and doesn't start with space/tab in original line, it's an area.
        # But wait, we stripped \n, let's check if parts[0] is not empty.
        
        # When splitting by tab:
        # "ADMINISTRACION DEL TALENTO HUMANO\tMXL..." -> parts[0]="ADMINISTRACION DEL TALENTO HUMANO", parts[1]="MXL..."
        # "\tHFPS5370\t\t4/2/2026..." -> parts[0]="", parts[1]="HFPS5370"
        
        if parts[0].strip():
            area_name = parts[0].strip()
            # Find or create area
            current_area, _ = Area.objects.get_or_create(name=area_name)
            serial = parts[1].strip() if len(parts) > 1 else ""
            estado = parts[2].strip() if len(parts) > 2 else ""
            date_str = parts[3].strip() if len(parts) > 3 else ""
        else:
            serial = parts[1].strip() if len(parts) > 1 else ""
            estado = parts[2].strip() if len(parts) > 2 else ""
            date_str = parts[3].strip() if len(parts) > 3 else ""

        if not serial:
            continue
            
        # Parse date
        scheduled_date = None
        if date_str:
            try:
                scheduled_date = datetime.strptime(date_str, "%d/%m/%Y").date()
            except ValueError:
                pass

        # Create or update Equipment
        eq, created = Equipment.objects.get_or_create(
            serial_number=serial,
            defaults={
                'type': 'PC',  # Default type
                'brand': 'Genérico',
                'model': 'Genérico',
            }
        )
        # Update specified fields
        eq.operating_system = "Windows 11"
        eq.processor = "Intel Core i5"
        if current_area:
            eq.area = current_area
            
        eq.save()
        
        # Update MaintenanceSchedule
        if scheduled_date:
            ms_status = 'COMPLETED' if estado.upper() == 'REALIZADO' else 'PENDING'
            
            # Look like schedule_date is what we want
            ms, ms_created = MaintenanceSchedule.objects.get_or_create(
                equipment=eq,
                scheduled_date=scheduled_date,
                defaults={'status': ms_status}
            )

    print("Import completed successfully.")

if __name__ == '__main__':
    run()
