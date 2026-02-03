import csv
from django.core.management.base import BaseCommand
from inventory.models import Equipment, Area, CostCenter
from django.utils import timezone

class Command(BaseCommand):
    help = 'Import equipment from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file']
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                count = 0
                for row in reader:
                    # Get or Create Project/Area if needed, or just look it up.
                    # For simplicity, we'll try to find the area by name, or leave null.
                    area_name = row.get('area', '').strip()
                    area = None
                    if area_name:
                        area, _ = Area.objects.get_or_create(name=area_name)
                    
                    serial = row.get('serial_number', '').strip()
                    if not serial:
                        self.stdout.write(self.style.WARNING(f"Skipping row {row}: No serial number"))
                        continue

                    # Map Type display to internal code if possible, or expect internal code.
                    # Simple mapping for common terms
                    type_map = {
                        'PC': 'PC', 'COMPUTADOR': 'PC', 'DESKTOP': 'PC',
                        'LAPTOP': 'LAPTOP', 'PORTATIL': 'LAPTOP',
                        'IMPRESORA': 'PRINTER', 'PRINTER': 'PRINTER',
                        'AIO': 'AIO', 'ALL IN ONE': 'AIO',
                        'MONITOR': 'MONITOR', # Wait, monitor is peripheral? Equipment model has types.
                        'SERVER': 'SERVER',
                        'ESCANER': 'SCANNER', 'SCANNER': 'SCANNER'
                    }
                    
                    m_type_input = row.get('type', 'OTHER').upper()
                    m_type = type_map.get(m_type_input, 'OTHER')

                    obj, created = Equipment.objects.update_or_create(
                        serial_number=serial,
                        defaults={
                            'type': m_type,
                            'brand': row.get('brand', ''),
                            'model': row.get('model', ''),
                            'area': area,
                            'status': row.get('status', 'ACTIVE'),
                            'processor': row.get('processor', ''),
                            'ram': row.get('ram', ''),
                            'storage': row.get('storage', ''),
                            'operating_system': row.get('os', ''),
                            'voltage': row.get('voltage', ''),
                            'amperage': row.get('amperage', ''),
                            'os_user': row.get('os_user', ''),
                            'screen_size': row.get('screen_size', ''),
                        }
                    )
                    
                    action = "Created" if created else "Updated"
                    self.stdout.write(self.style.SUCCESS(f"{action} Equipment: {serial}"))
                    count += 1
                
                self.stdout.write(self.style.SUCCESS(f"Successfully imported {count} items"))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {csv_file_path}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
