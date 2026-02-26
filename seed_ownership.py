import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hfps_tic.settings")
django.setup()

from inventory.models import Equipment, OwnershipType

def run():
    # Setup base ownership types
    owned, _ = OwnershipType.objects.get_or_create(name="Propio (Institución)")
    rented, _ = OwnershipType.objects.get_or_create(name="Alquilado / Leasing")
    comodato, _ = OwnershipType.objects.get_or_create(name="Comodato")
    
    # Migrate existing data
    equipments = Equipment.objects.all()
    updated = 0
    for eq in equipments:
        if eq.ownership_type == 'OWNED':
            eq.ownership = owned
        elif eq.ownership_type == 'RENTED':
            eq.ownership = rented
        elif eq.ownership_type == 'COMMODATUM': # In case it was already saved somehow natively
            eq.ownership = comodato
        else:
            eq.ownership = owned
        eq.save()
        updated += 1
        
    print(f"Data migration complete. Updated {updated} records.")

if __name__ == "__main__":
    run()
