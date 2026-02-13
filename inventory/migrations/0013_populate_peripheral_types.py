from django.db import migrations

def populate_types(apps, schema_editor):
    Peripheral = apps.get_model('inventory', 'Peripheral')
    PeripheralType = apps.get_model('inventory', 'PeripheralType')
    
    # We need access to choices to get display name? 
    # Can't easily import from apps unless we import the module directly.
    # Let's try to just use the raw value as name for now, or capitalizing it.
    
    for p in Peripheral.objects.all():
        if p.type:
            # Clean up: capitalize
            name = p.type.replace('_', ' ').title()
            ptype, _ = PeripheralType.objects.get_or_create(name=name)
            p.peripheral_type = ptype
            p.save()

class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0012_peripheraltype_peripheral_quantity_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_types),
    ]
