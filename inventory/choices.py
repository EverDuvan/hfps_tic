from django.utils.translation import gettext_lazy as _

EQUIPMENT_TYPE_CHOICES = [
    ('PC', 'PC de Escritorio'),
    ('LAPTOP', 'Portátil'),
    ('AIO', 'All-in-One'),
    ('SERVER', 'Servidor'),
    ('PRINTER', 'Impresora'),
    ('SCANNER', 'Escáner'),
    ('OTHER', 'Otro'),
]

EQUIPMENT_STATUS_CHOICES = [
    ('ACTIVE', 'Activo'),
    ('MAINTENANCE', 'En Mantenimiento'),
    ('RETIRED', 'Dado de Baja'),
    ('aSTOCK', 'En Stock'),
]

PERIPHERAL_TYPE_CHOICES = [
    ('MONITOR', 'Monitor'),
    ('KEYBOARD', 'Teclado'),
    ('MOUSE', 'Mouse'),
    ('HEADSET', 'Diadema/Audífonos'),
    ('WEBCAM', 'Cámara Web'),
    ('OTHER', 'Otro'),
]

PERIPHERAL_STATUS_CHOICES = [
    ('ACTIVE', 'Activo'),
    ('FAULTY', 'Dañado'),
    ('RETIRED', 'Dado de Baja'),
    ('STOCK', 'En Stock'),
]

MAINTENANCE_TYPE_CHOICES = [
    ('PREVENTIVE', 'Preventivo'),
    ('CORRECTIVE', 'Correctivo'),
]

HANDOVER_TYPE_CHOICES = [
    ('ASSIGNMENT', 'Asignación'),
    ('RETURN', 'Devolución'),
    ('TRANSFER', 'Traslado'),
]

IP_TYPE_CHOICES = [
    ('DHCP', 'DHCP'),
    ('STATIC', 'Estática'),
]
