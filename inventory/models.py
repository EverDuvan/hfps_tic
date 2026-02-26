from django.db import models
from simple_history.models import HistoricalRecords
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.utils import timezone
from .utils import generate_maintenance_pdf, generate_handover_pdf
from .choices import (
    EQUIPMENT_TYPE_CHOICES, EQUIPMENT_STATUS_CHOICES,
    PERIPHERAL_TYPE_CHOICES, PERIPHERAL_STATUS_CHOICES,
    MAINTENANCE_TYPE_CHOICES, HANDOVER_TYPE_CHOICES,
    IP_TYPE_CHOICES, OWNERSHIP_CHOICES
)

class CostCenter(models.Model):
    """Model representing a Cost Center."""
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Código"))
    name = models.CharField(max_length=100, verbose_name=_("Nombre"))

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        verbose_name = _("Centro de Costos")
        verbose_name_plural = _("Centros de Costos")

class Area(models.Model):
    """Model representing an Area within the organization."""
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Nombre"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Descripción"))
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Centro de Costos"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Área")
        verbose_name_plural = _("Áreas")

class Client(models.Model):
    """Model representing a Client or Employee (Funcionario)."""
    name = models.CharField(max_length=100, verbose_name=_("Nombre Completo"))
    identification = models.CharField(max_length=20, unique=True, verbose_name=_("Identificación / Cédula"))
    email = models.EmailField(blank=True, null=True, verbose_name=_("Correo Electrónico"))
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Teléfono"))
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Área"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Cliente / Funcionario")
        verbose_name_plural = _("Clientes / Funcionarios")

class Technician(User):
    """Proxy model for User to distinguish Technicians."""
    class Meta:
        proxy = True
        verbose_name = _("Ingeniero / Técnico")
        verbose_name_plural = _("Ingenieros / Técnicos")

class Equipment(models.Model):
    """Model representing an IT Equipment item."""
    serial_number = models.CharField(max_length=100, unique=True, verbose_name=_("Número de Serie"))
    type = models.CharField(max_length=20, choices=EQUIPMENT_TYPE_CHOICES, verbose_name=_("Tipo"))
    brand = models.CharField(max_length=100, verbose_name=_("Marca"))
    model = models.CharField(max_length=100, verbose_name=_("Modelo"))
    operating_system = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Sistema Operativo"))
    processor = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Procesador"))
    ram = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("RAM"))
    storage = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Almacenamiento"))
    os_user = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Usuario SO"))
    screen_size = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Tamaño Pantalla"))
    status = models.CharField(max_length=20, choices=EQUIPMENT_STATUS_CHOICES, default='ACTIVE', verbose_name=_("Estado"))
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipments', verbose_name=_("Área"))
    purchase_date = models.DateField(blank=True, null=True, verbose_name=_("Fecha de Compra"))
    warranty_expiry = models.DateField(blank=True, null=True, verbose_name=_("Vencimiento de Garantía"))
    lifespan_years = models.PositiveIntegerField(default=5, verbose_name=_("Vida Útil (Años)"))

    @property
    def end_of_life_date(self):
        if self.purchase_date:
            try:
                return self.purchase_date.replace(year=self.purchase_date.year + self.lifespan_years)
            except ValueError: # Handle Feb 29
                return self.purchase_date.replace(year=self.purchase_date.year + self.lifespan_years, day=28)
        return None

    @property
    def is_end_of_life_reached(self):
        eol = self.end_of_life_date
        if eol:
            return eol <= timezone.now().date()
        return False
    
    # New IP Fields
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name=_("Dirección IP"))
    ip_type = models.CharField(max_length=20, choices=IP_TYPE_CHOICES, default='DHCP', verbose_name=_("Tipo de IP"))

    # Electrical Specs
    voltage = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Voltaje"))
    amperage = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Amperaje (A)"))

    # Ownership & Rental Info
    ownership_type = models.CharField(max_length=20, choices=OWNERSHIP_CHOICES, default='OWNED', verbose_name=_("Propiedad"))
    provider_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Proveedor / Empresa"))
    rental_contract_ref = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Ref. Contrato / Ticket"))
    support_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Teléfono Soporte"))

    created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.get_type_display()} - {self.brand} {self.model} ({self.serial_number})"

    class Meta:
        verbose_name = _("Equipo")
        verbose_name_plural = _("Equipos")

class PeripheralType(models.Model):
    """Model for dynamic Peripheral Types."""
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Nombre del Tipo"))
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Tipo de Periférico")
        verbose_name_plural = _("Tipos de Periféricos")

class Peripheral(models.Model):
    """Model representing a Peripheral (Keyboard, Mouse, etc.). Acts as a Product/SKU."""
    serial_number = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Número de Serie")) 
    
    # REMOVED OLD TYPE (Char)
    # type = models.CharField(max_length=20, choices=PERIPHERAL_TYPE_CHOICES, verbose_name=_("Tipo (Legacy)"), blank=True, null=True)
    
    # Final type field - Non-nullable
    type = models.ForeignKey(PeripheralType, on_delete=models.PROTECT, verbose_name=_("Tipo"))
    
    brand = models.CharField(max_length=100, verbose_name=_("Marca"))
    model = models.CharField(max_length=100, verbose_name=_("Modelo"))
    status = models.CharField(max_length=20, choices=PERIPHERAL_STATUS_CHOICES, default='ACTIVE', verbose_name=_("Estado"))
    # Quantity for stock tracking
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("Cantidad / Stock"))
    min_stock_level = models.PositiveIntegerField(default=0, verbose_name=_("Stock Mínimo (Alerta)"))
    
    connected_to = models.ForeignKey(Equipment, on_delete=models.SET_NULL, null=True, blank=True, related_name='peripherals', verbose_name=_("Conectado a"))
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='peripherals', verbose_name=_("Área"))
    
    def __str__(self):
        return f"{self.type.name} - {self.brand} {self.model} ({self.quantity})"

    class Meta:
        verbose_name = _("Periférico")
        verbose_name_plural = _("Periféricos")

class HandoverPeripheral(models.Model):
    """Through model for Handover-Peripheral relationship with quantity."""
    handover = models.ForeignKey('Handover', on_delete=models.CASCADE)
    peripheral = models.ForeignKey(Peripheral, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("Cantidad Entregada"))

    def __str__(self):
        return f"{self.quantity} x {self.peripheral}"

class Maintenance(models.Model):
    """Model representing a Maintenance record (Preventive or Corrective)."""
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenances', verbose_name=_("Equipo"))
    date = models.DateField(default=timezone.now, verbose_name=_("Fecha"))
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPE_CHOICES, verbose_name=_("Tipo de Mantenimiento"))
    description = models.TextField(verbose_name=_("Descripción del Trabajo"))
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_("Realizado por"))
    next_maintenance_date = models.DateField(blank=True, null=True, verbose_name=_("Próximo Mantenimiento"))
    acta_pdf = models.FileField(upload_to='maintenance_actas/', blank=True, null=True, verbose_name=_("Acta PDF"))

    # Time Fields
    start_time = models.TimeField(blank=True, null=True, verbose_name=_("Hora Inicio"))
    end_time = models.TimeField(blank=True, null=True, verbose_name=_("Hora Final"))

    # Section 4: Type of Support
    type_review = models.BooleanField(default=False, verbose_name=_("Revisión Equipo"))
    type_software_failure = models.BooleanField(default=False, verbose_name=_("Fallas Software"))
    type_connection = models.BooleanField(default=False, verbose_name=_("Problemas Conexión"))
    type_updates = models.BooleanField(default=False, verbose_name=_("Actualizaciones (Win10)"))
    type_cleaning = models.BooleanField(default=False, verbose_name=_("Limpieza Equipo"))
    type_install = models.BooleanField(default=False, verbose_name=_("Instalación Software"))
    type_peripheral = models.BooleanField(default=False, verbose_name=_("Falla Periféricos"))
    type_backup = models.BooleanField(default=False, verbose_name=_("Copia Seguridad"))

    # Section 5: OS Cleaning
    cleaning_defrag = models.BooleanField(default=False, verbose_name=_("Desfragmentación Disco"))
    cleaning_cco = models.BooleanField(default=False, verbose_name=_("Ejecución C-Cleaner"))
    cleaning_scandisk = models.BooleanField(default=False, verbose_name=_("ScanDisk"))
    cleaning_space = models.BooleanField(default=False, verbose_name=_("Liberación Espacio"))

    # Section 7: Hardware Stages
    hw_disassembly = models.BooleanField(default=False, verbose_name=_("Retiro equipo / Desmontaje"))
    hw_power_supply = models.BooleanField(default=False, verbose_name=_("Limpieza Fuente Poder"))
    hw_fans = models.BooleanField(default=False, verbose_name=_("Limpieza Ventiladores"))
    hw_chassis = models.BooleanField(default=False, verbose_name=_("Limpieza Chasis/Cubiertas"))
    hw_thermal_paste = models.BooleanField(default=False, verbose_name=_("Crema Disipadora"))
    hw_contacts = models.BooleanField(default=False, verbose_name=_("Limpiador Contactos"))
    hw_keyboard_mouse = models.BooleanField(default=False, verbose_name=_("Limpieza Teclado/Mouse"))
    hw_screen = models.BooleanField(default=False, verbose_name=_("Limpieza Pantalla"))
    hw_reassembly = models.BooleanField(default=False, verbose_name=_("Ensamble y Pruebas"))
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        # Determine if we need to generate the PDF
        should_generate_pdf = not self.acta_pdf
        
        # Save first to get ID
        super().save(*args, **kwargs)
        
        if should_generate_pdf:
            pdf_content = generate_maintenance_pdf(self)
            filename = f'acta_mantenimiento_{self.id}.pdf'
            
            # Save the file content to the field, then save the model with update_fields.
            self.acta_pdf.save(filename, ContentFile(pdf_content), save=False)
            super().save(update_fields=['acta_pdf'])

    def __str__(self):
        return f"{self.get_maintenance_type_display()} - {self.equipment} - {self.date}"

    class Meta:
        verbose_name = _("Mantenimiento")
        verbose_name_plural = _("Mantenimientos")

class Handover(models.Model):
    """Model representing an Equipment Handover (Acta de Entrega)."""
    date = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha y Hora"))
    type = models.CharField(max_length=20, choices=HANDOVER_TYPE_CHOICES, verbose_name=_("Tipo de Entrega"))
    equipment = models.ManyToManyField(Equipment, blank=True, related_name='handovers', verbose_name=_("Equipos"))
    # Updated to use custom through model
    peripherals = models.ManyToManyField(Peripheral, blank=True, related_name='handovers', verbose_name=_("Periféricos"), through='HandoverPeripheral')
    source_area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='handovers_from', verbose_name=_("Área Origen"))
    destination_area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='handovers_to', verbose_name=_("Área Destino"))
    technician = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_("Técnico Responsable"))
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Cliente / Funcionario"))
    receiver_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Nombre quien recibe (Opcional)"))
    observations = models.TextField(blank=True, null=True, verbose_name=_("Observaciones"))
    acta_pdf = models.FileField(upload_to='handover_actas/', blank=True, null=True, verbose_name=_("Acta de Entrega PDF"))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_type_display()} - {self.date.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = _("Entrega / Acta")
        verbose_name_plural = _("Entregas / Actas")

class MaintenanceSchedule(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('COMPLETED', 'Realizado'),
        ('CANCELLED', 'Cancelado'),
    ]

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='schedules')
    scheduled_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('equipment', 'scheduled_date')
        verbose_name = "Cronograma de Mantenimiento"
        verbose_name_plural = "Cronogramas de Mantenimiento"

    def __str__(self):
        return f"{self.equipment} - {self.scheduled_date}"

class EquipmentRound(models.Model):
    """Model representing an Equipment Round (Ronda de Equipos) check."""
    
    STATUS_CHOICES = [
        ('GOOD', 'Bueno'),
        ('REGULAR', 'Regular'),
        ('BAD', 'Malo'),
    ]

    CHECK_CHOICES = [
        ('PASS', '✅ Bien'),
        ('WARN', '⚠️ Regular'),
        ('FAIL', '❌ Malo'),
        ('NA', '➖ No Aplica'),
    ]

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='rounds', verbose_name=_("Equipo"))
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_("Realizada por"))
    datetime = models.DateTimeField(default=timezone.now, verbose_name=_("Fecha y Hora"))
    
    # Checklist fields (Professional)
    hw_status = models.CharField(max_length=10, choices=CHECK_CHOICES, default='PASS', verbose_name=_("Estado Físico / Chasis"))
    powers_on = models.CharField(max_length=10, choices=CHECK_CHOICES, default='PASS', verbose_name=_("Encendido / Energía"))
    monitor_status = models.CharField(max_length=10, choices=CHECK_CHOICES, default='PASS', verbose_name=_("Pantalla / Monitor"))
    peripherals_status = models.CharField(max_length=10, choices=CHECK_CHOICES, default='PASS', verbose_name=_("Teclado y Mouse"))
    network_status = models.CharField(max_length=10, choices=CHECK_CHOICES, default='PASS', verbose_name=_("Conectividad / Red"))
    os_status = models.CharField(max_length=10, choices=CHECK_CHOICES, default='PASS', verbose_name=_("Sistema Operativo / Software"))
    
    # New additions
    cables_status = models.CharField(max_length=10, choices=CHECK_CHOICES, default='PASS', verbose_name=_("Organización de Cables"))
    cleanliness_status = models.CharField(max_length=10, choices=CHECK_CHOICES, default='PASS', verbose_name=_("Limpieza del Puesto"))
    ups_status = models.CharField(max_length=10, choices=CHECK_CHOICES, default='NA', verbose_name=_("Estado de UPS / Regulador"))
    printer_status = models.CharField(max_length=10, choices=CHECK_CHOICES, default='NA', verbose_name=_("Impresora / Escáner"))
    
    general_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='GOOD', verbose_name=_("Estado General"))
    observations = models.TextField(blank=True, null=True, verbose_name=_("Observaciones"))
    
    history = HistoricalRecords()

    def __str__(self):
        return f"Ronda {self.equipment} - {self.datetime.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = _("Ronda de Equipo")
        verbose_name_plural = _("Rondas de Equipos")
        ordering = ['-datetime']


