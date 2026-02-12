from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from inventory.models import Equipment, Maintenance
from django.contrib.auth.models import User
from datetime import timedelta

class Command(BaseCommand):
    help = 'Sends email alerts for upcoming maintenance and expiring warranties'

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # 1. Check Maintenance (Preventive) due in 3 days
        maintenance_window = today + timedelta(days=3)
        # Assuming we check `next_maintenance_date` field in Maintenance model
        # or we check `MaintenanceSchedule` if present. 
        # The model Maintenance has 'next_maintenance_date'.
        
        upcoming_maintenance = Maintenance.objects.filter(
            next_maintenance_date=maintenance_window
        )
        
        if upcoming_maintenance.exists():
            self.stdout.write(f"Found {upcoming_maintenance.count()} upcoming maintenances.")
            
            message = "Los siguientes equipos requieren mantenimiento pronto:\n\n"
            for m in upcoming_maintenance:
                message += f"- {m.equipment} (Serial: {m.equipment.serial_number}): {m.next_maintenance_date}\n"
            
            # Send to all staff/technicians
            recipients = User.objects.filter(is_staff=True).values_list('email', flat=True)
            recipients = [email for email in recipients if email]
            
            if recipients:
                send_mail(
                    'Alerta de Mantenimiento HFPS',
                    message,
                    'admin@hfps.com',
                    recipients,
                    fail_silently=False,
                )
                self.stdout.write("Maintenance emails sent.")
                
        # 2. Check Warranty Expiry due in 30 days
        warranty_window = today + timedelta(days=30)
        expiring_warranty = Equipment.objects.filter(
            warranty_expiry=warranty_window
        )
        
        if expiring_warranty.exists():
            self.stdout.write(f"Found {expiring_warranty.count()} warranties expiring in 30 days.")
            
            message = "Las garantías de los siguientes equipos vencen en 30 días:\n\n"
            for e in expiring_warranty:
                message += f"- {e.brand} {e.model} (Serial: {e.serial_number}): Vence {e.warranty_expiry}\n"
            
            recipients = User.objects.filter(is_staff=True).values_list('email', flat=True)
            recipients = [email for email in recipients if email]
            
            if recipients:
                send_mail(
                    'Alerta de Vencimiento de Garantía HFPS',
                    message,
                    'admin@hfps.com',
                    recipients,
                    fail_silently=False,
                )
                self.stdout.write("Warranty emails sent.")
