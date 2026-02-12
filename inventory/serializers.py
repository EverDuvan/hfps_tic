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
        fields = '__all__'

class MaintenanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maintenance
        fields = '__all__'

class HandoverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Handover
        fields = '__all__'
