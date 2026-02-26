from rest_framework import viewsets, permissions
from .models import Equipment, Maintenance, Handover, Area
from .serializers import EquipmentSerializer, MaintenanceSerializer, HandoverSerializer, AreaSerializer

class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.select_related('area', 'ownership').all().order_by('-created_at')
    serializer_class = EquipmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'type', 'area', 'ip_address']
    search_fields = ['serial_number', 'brand', 'model']

class MaintenanceViewSet(viewsets.ModelViewSet):
    queryset = Maintenance.objects.select_related('equipment', 'performed_by').all().order_by('-date')
    serializer_class = MaintenanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['maintenance_type', 'performed_by', 'equipment']

class HandoverViewSet(viewsets.ModelViewSet):
    queryset = Handover.objects.select_related(
        'source_area', 'destination_area', 'client', 'technician'
    ).prefetch_related('equipment', 'peripherals').all().order_by('-date')
    serializer_class = HandoverSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['type', 'technician', 'client', 'source_area', 'destination_area']

class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects.all().order_by('name')
    serializer_class = AreaSerializer
    permission_classes = [permissions.IsAuthenticated]
