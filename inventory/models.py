from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.utils import timezone
from .utils import generate_maintenance_pdf, generate_handover_pdf

class CostCenter(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Código"))
    name = models.CharField(max_length=100, verbose_name=_("Nombre"))

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        verbose_name = _("Centro de Costos")
        verbose_name_plural = _("Centros de Costos")

class Area(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Nombre"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Descripción"))
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Centro de Costos"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Área")
        verbose_name_plural = _("Áreas")
class Client(models.Model):
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
    class Meta:
        proxy = True
        verbose_name = _("Ingeniero / Técnico")
        verbose_name_plural = _("Ingenieros / Técnicos")

class Equipment(models.Model):
    TYPE_CHOICES = [
        ('PC', 'PC de Escritorio'),
        ('LAPTOP', 'Portátil'),
        ('AIO', 'All-in-One'),
        ('SERVER', 'Servidor'),
        ('PRINTER', 'Impresora'),
        ('SCANNER', 'Escáner'),
        ('OTHER', 'Otro'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Activo'),
        ('MAINTENANCE', 'En Mantenimiento'),
        ('RETIRED', 'Dado de Baja'),
        ('aSTOCK', 'En Stock'),
    ]

    serial_number = models.CharField(max_length=100, unique=True, verbose_name=_("Número de Serie"))
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name=_("Tipo"))
    brand = models.CharField(max_length=100, verbose_name=_("Marca"))
    model = models.CharField(max_length=100, verbose_name=_("Modelo"))
    operating_system = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Sistema Operativo"))
    processor = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Procesador"))
    ram = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("RAM"))
    storage = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Almacenamiento"))
    voltage = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Voltaje"))
    amperage = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Amperaje"))
    os_user = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Usuario SO"))
    screen_size = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Tamaño Pantalla"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', verbose_name=_("Estado"))
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipments', verbose_name=_("Área"))
    purchase_date = models.DateField(blank=True, null=True, verbose_name=_("Fecha de Compra"))
    warranty_expiry = models.DateField(blank=True, null=True, verbose_name=_("Vencimiento de Garantía"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_type_display()} - {self.brand} {self.model} ({self.serial_number})"

    class Meta:
        verbose_name = _("Equipo")
        verbose_name_plural = _("Equipos")

class Peripheral(models.Model):
    TYPE_CHOICES = [
        ('MONITOR', 'Monitor'),
        ('KEYBOARD', 'Teclado'),
        ('MOUSE', 'Mouse'),
        ('HEADSET', 'Diadema/Audífonos'),
        ('WEBCAM', 'Cámara Web'),
        ('OTHER', 'Otro'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Activo'),
        ('FAULTY', 'Dañado'),
        ('RETIRED', 'Dado de Baja'),
        ('STOCK', 'En Stock'),
    ]

    serial_number = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Número de Serie")) # Some peripherals don't have serials
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name=_("Tipo"))
    brand = models.CharField(max_length=100, verbose_name=_("Marca"))
    model = models.CharField(max_length=100, verbose_name=_("Modelo"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', verbose_name=_("Estado"))
    connected_to = models.ForeignKey(Equipment, on_delete=models.SET_NULL, null=True, blank=True, related_name='peripherals', verbose_name=_("Conectado a"))
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='peripherals', verbose_name=_("Área"))
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.brand} {self.model}"

    class Meta:
        verbose_name = _("Periférico")
        verbose_name_plural = _("Periféricos")

class Maintenance(models.Model):
    TYPE_CHOICES = [
        ('PREVENTIVE', 'Preventivo'),
        ('CORRECTIVE', 'Correctivo'),
    ]

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenances', verbose_name=_("Equipo"))
    date = models.DateField(default=timezone.now, verbose_name=_("Fecha"))
    maintenance_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name=_("Tipo de Mantenimiento"))
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

    def save(self, *args, **kwargs):
        # Determine if we need to generate the PDF
        should_generate_pdf = not self.acta_pdf
        
        # Save first to get ID
        super().save(*args, **kwargs)
        
        if should_generate_pdf:
            pdf_content = generate_maintenance_pdf(self)
            # Save the file. content.save() calls model.save(), so we must prevent infinite recursion if possible,
            # but FileField.save() sets the field and saves the model.
            # To be safe, we can check if the field is already set to this filename, but filename generation uses ID.
            filename = f'acta_mantenimiento_{self.id}.pdf'
            
            # Using save=False on the field save would prevent recursion but might not persist the field change to DB depending on storage.
            # However, standard practice to avoid recursion loop with FileField save is tricky. 
            # Better approach: save the file content to the field, then save the model with update_fields.
            self.acta_pdf.save(filename, ContentFile(pdf_content), save=False)
            super().save(update_fields=['acta_pdf'])

    def __str__(self):
        return f"{self.get_maintenance_type_display()} - {self.equipment} - {self.date}"

    class Meta:
        verbose_name = _("Mantenimiento")
        verbose_name_plural = _("Mantenimientos")

class Handover(models.Model):
    TYPE_CHOICES = [
        ('ASSIGNMENT', 'Asignación'),
        ('RETURN', 'Devolución'),
        ('TRANSFER', 'Traslado'),
    ]

    date = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha y Hora"))
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name=_("Tipo de Entrega"))
    equipment = models.ManyToManyField(Equipment, blank=True, related_name='handovers', verbose_name=_("Equipos"))
    peripherals = models.ManyToManyField(Peripheral, blank=True, related_name='handovers', verbose_name=_("Periféricos"))
    source_area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='handovers_from', verbose_name=_("Área Origen"))
    destination_area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='handovers_to', verbose_name=_("Área Destino"))
    technician = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_("Técnico Responsable"))
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Cliente / Funcionario"))
    receiver_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Nombre quien recibe (Opcional)"))
    observations = models.TextField(blank=True, null=True, verbose_name=_("Observaciones"))
    acta_pdf = models.FileField(upload_to='handover_actas/', blank=True, null=True, verbose_name=_("Acta de Entrega PDF"))

    def save(self, *args, **kwargs):
        should_generate_pdf = not self.acta_pdf
        super().save(*args, **kwargs)
        if should_generate_pdf:
            pdf_content = generate_handover_pdf(self)
            self.acta_pdf.save(f'acta_entrega_{self.id}.pdf', ContentFile(pdf_content), save=False)
            super().save(update_fields=['acta_pdf'])

    def __str__(self):
        return f"{self.get_type_display()} - {self.date.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = _("Entrega / Acta")
        verbose_name_plural = _("Entregas / Actas")
