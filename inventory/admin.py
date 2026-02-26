from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Area, Equipment, Peripheral, Maintenance, Handover, CostCenter, Client, Technician, PeripheralType, HandoverPeripheral, EquipmentRound, OwnershipType
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .utils import export_to_excel

def export_as_excel_action(modeladmin, request, queryset):
    return export_to_excel(queryset, modeladmin, request)
export_as_excel_action.short_description = "Exportar a Excel"

@admin.register(OwnershipType)
class OwnershipTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    actions = [export_as_excel_action]

@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')
    actions = [export_as_excel_action]

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'identification', 'email', 'area')
    search_fields = ('name', 'identification')
    list_filter = ('area',)
    actions = [export_as_excel_action]

@admin.register(Technician)
class TechnicianAdmin(BaseUserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'is_active')
    # Use default UserAdmin logic but focused on this proxy


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'brand', 'model', 'type', 'area', 'status', 'os_user')
    list_filter = ('type', 'status', 'area', 'brand')
    search_fields = ('serial_number', 'brand', 'model', 'os_user')
    fieldsets = (
        (None, {
            'fields': ('serial_number', 'type', 'brand', 'model', 'area', 'status')
        }),
        ('Detalles Técnicos', {
            'fields': ('processor', 'ram', 'storage', 'operating_system', 'os_user', 'voltage', 'amperage', 'screen_size')
        }),
        ('Fechas', {
            'fields': ('purchase_date', 'warranty_expiry', 'lifespan_years')
        }),
    )
    actions = [export_as_excel_action]

@admin.register(PeripheralType)
class PeripheralTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Peripheral)
class PeripheralAdmin(admin.ModelAdmin):
    list_display = ('type', 'brand', 'model', 'quantity', 'area', 'connected_to', 'status')
    list_filter = ('type', 'status', 'area')
    search_fields = ('serial_number', 'brand', 'model')
    actions = [export_as_excel_action]

@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'date', 'maintenance_type', 'performed_by', 'next_maintenance_date', 'acta_link')
    list_filter = ('maintenance_type', 'date')
    search_fields = ('equipment__serial_number', 'performed_by__username', 'performed_by__first_name', 'performed_by__last_name')
    date_hierarchy = 'date'
    readonly_fields = ('acta_pdf',)
    actions = [export_as_excel_action]
    
    fieldsets = (
        ('Información General', {
            'fields': ('equipment', 'maintenance_type', 'date', 'performed_by', 'next_maintenance_date', 'acta_pdf')
        }),
        ('Tiempos', {
            'fields': ('start_time', 'end_time')
        }),
        ('4. Tipo de Soporte Requerido', {
            'fields': (
                ('type_review', 'type_software_failure'),
                ('type_connection', 'type_updates'),
                ('type_cleaning', 'type_install'),
                ('type_peripheral', 'type_backup')
            )
        }),
        ('5. Actividades de Limpieza S.O.', {
            'fields': (
                ('cleaning_defrag', 'cleaning_cco'),
                ('cleaning_scandisk', 'cleaning_space')
            )
        }),
        ('6. Observaciones', {
            'fields': ('description',)
        }),
        ('7. Etapas Mantenimiento Hardware', {
            'fields': (
                'hw_disassembly', 'hw_power_supply', 'hw_fans', 
                'hw_chassis', 'hw_thermal_paste', 'hw_contacts', 
                'hw_keyboard_mouse', 'hw_screen', 'hw_reassembly'
            )
        }),
    )
    
    def acta_link(self, obj):
        url = reverse('inventory:maintenance_acta', args=[obj.pk])
        return format_html('<a class="button" href="{}" target="_blank">Generar Acta</a>', url)
    acta_link.short_description = "Acta"

class HandoverPeripheralInline(admin.TabularInline):
    model = HandoverPeripheral
    extra = 1

@admin.register(Handover)
class HandoverAdmin(admin.ModelAdmin):
    inlines = [HandoverPeripheralInline]
    list_display = ('date', 'type', 'source_area', 'destination_area', 'technician', 'receiver_name', 'acta_link')
    list_filter = ('type', 'date', 'source_area', 'destination_area')
    search_fields = ('receiver_name', 'technician__username', 'technician__first_name', 'technician__last_name')
    date_hierarchy = 'date'
    readonly_fields = ('acta_pdf',)
    actions = [export_as_excel_action]

    def acta_link(self, obj):
        url = reverse('inventory:handover_acta', args=[obj.pk])
        return format_html('<a class="button" href="{}" target="_blank">Generar Acta</a>', url)
    acta_link.short_description = "Acta"

@admin.register(EquipmentRound)
class EquipmentRoundAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'datetime', 'performed_by', 'general_status', 'powers_on', 'network_status')
    list_filter = ('general_status', 'datetime', 'powers_on', 'monitor_status', 'peripherals_status', 'network_status', 'os_status')
    search_fields = ('equipment__serial_number', 'performed_by__username', 'performed_by__first_name', 'performed_by__last_name', 'observations')
    date_hierarchy = 'datetime'
    actions = [export_as_excel_action]
    
    fieldsets = (
        ('Información General', {
            'fields': ('equipment', 'performed_by', 'datetime')
        }),
        ('Lista de Chequeo', {
            'fields': (
                ('powers_on', 'monitor_status'),
                ('peripherals_status', 'network_status'),
                'os_status'
            )
        }),
        ('Resultado', {
            'fields': ('general_status', 'observations')
        }),
    )
