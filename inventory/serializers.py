from rest_framework import serializers
from .models import Equipment, Maintenance, Handover, Area

class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ['id', 'name', 'cost_center']

class EquipmentSerializer(serializers.ModelSerializer):
    area_name = serializers.CharField(source='area.name', read_only=True)
    
    class Meta:
        model = Equipment
        fields = [
            'id', 'serial_number', 'type', 'brand', 'model', 'status',
            'area', 'area_name', 'ip_address', 'ip_type', 'mac_address',
            'hostname', 'purchase_date', 'warranty_expiry', 'lifespan_years',
            'processor', 'ram', 'storage', 'os', 'os_version',
            'created_at', 'updated_at',
        ]

class MaintenanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maintenance
        fields = [
            'id', 'equipment', 'maintenance_type', 'date', 'description',
            'performed_by', 'next_maintenance_date', 'start_time', 'end_time',
        ]

class HandoverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Handover
        fields = [
            'id', 'type', 'date', 'source_area', 'destination_area',
            'client', 'technician', 'receiver_name', 'observations',
        ]

