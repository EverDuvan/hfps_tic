from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Maintenance, MaintenanceSchedule
from django.utils import timezone

@receiver(post_save, sender=Maintenance)
def sync_maintenance_to_schedule(sender, instance, created, **kwargs):
    """
    When Maintenance is saved, if next_maintenance_date is set,
    create a corresponding MaintenanceSchedule entry.
    """
    if instance.next_maintenance_date:
        MaintenanceSchedule.objects.get_or_create(
            equipment=instance.equipment,
            scheduled_date=instance.next_maintenance_date,
            defaults={'status': 'PENDING'}
        )

@receiver(post_save, sender=MaintenanceSchedule)
@receiver(post_delete, sender=MaintenanceSchedule)
def sync_schedule_to_maintenance(sender, instance, **kwargs):
    """
    When a Schedule is modified (added/removed), update the latest Maintenance
    record's 'next_maintenance_date' to reflect the *next* upcoming schedule.
    """
    equipment = instance.equipment
    
    # Find the latest performed maintenance
    last_maintenance = Maintenance.objects.filter(equipment=equipment).order_by('-date').first()
    
    if last_maintenance:
        # Find the earliest PENDING schedule that is after the maintenance date
        # (or just after today, depending on logic. Let's use after maintenance date for consistency)
        
        # We need schedules in the future relative to the last maintenance
        next_schedule = MaintenanceSchedule.objects.filter(
            equipment=equipment,
            scheduled_date__gt=last_maintenance.date,
            status='PENDING'
        ).order_by('scheduled_date').first()
        
        if next_schedule:
            # Update silence signals to avoid infinite recursion Loop A->B->A
            # We must disconnect or use a flag, but save() usually triggers signals.
            # To avoid recursion: check if value actually changed.
            if last_maintenance.next_maintenance_date != next_schedule.scheduled_date:
                last_maintenance.next_maintenance_date = next_schedule.scheduled_date
                last_maintenance.save(update_fields=['next_maintenance_date'])
        else:
            # If no future schedule found, clear the field?
            # Or keep user manual entry?
            # "Vice versa" implies sync. If I delete the only schedule, next_maintenance should probably be cleared
            # IF checks allow. Let's be safe: if it matched the deleted one, clear it.
            # But simpler: Just sync to the next available.
            if last_maintenance.next_maintenance_date != None:
                 last_maintenance.next_maintenance_date = None
                 last_maintenance.save(update_fields=['next_maintenance_date'])
