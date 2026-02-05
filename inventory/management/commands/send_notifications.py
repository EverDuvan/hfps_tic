from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from inventory.models import MaintenanceSchedule
from django.conf import settings
import math

class Command(BaseCommand):
    help = 'Sends email notifications for pending maintenance scheduled for the current week.'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        self.stdout.write(f"Checking for pending maintenance for TODAY: {today}...")
        
        # Filter schedules for explicit date
        pending = MaintenanceSchedule.objects.filter(
            scheduled_date=today,
            status='PENDING'
        ).select_related('equipment')
        
        if not pending.exists():
            self.stdout.write(self.style.SUCCESS(f"No maintenance scheduled for today ({today})."))
            return

        count = 0
        email_list = []
        
        for item in pending:
            area_name = item.equipment.area.name if item.equipment.area else "Sin Área"
            email_list.append(f"- Equipo: {item.equipment.serial_number} ({area_name})")
            count += 1
            
        subject = f"🔔 Recordatorio: {count} Mantenimientos para HOY ({today})"
        message = f"""Hola Administrador,
        
Tiene {count} mantenimientos programados para el día de hoy ({today}):

{chr(10).join(email_list)}

Por favor, proceda con la ejecución.

Sistema de Gestión de Inventario
"""
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL], # Send to self/admin
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f"Successfully sent notification for {count} items."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send email: {e}"))
