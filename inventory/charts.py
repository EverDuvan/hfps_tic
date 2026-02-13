import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
from .choices import EQUIPMENT_TYPE_CHOICES, MAINTENANCE_TYPE_CHOICES, EQUIPMENT_STATUS_CHOICES

def get_chart_buffer():
    """Helper to get a BytesIO buffer of the current plot."""
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    plt.close()
    return buf

def generate_equipment_by_type_chart(data):
    """
    Generates a bar chart for equipment by type.
    data: list of dicts [{'type': 'PC', 'count': 10}, ...]
    """
    if not data:
        return None
    
    types = [dict(EQUIPMENT_TYPE_CHOICES).get(item['type'], item['type']) for item in data]
    counts = [item['count'] for item in data]
    
    plt.figure(figsize=(6, 4))
    bars = plt.bar(types, counts, color='#2c3e50')
    
    plt.title('Equipos por Tipo')
    plt.xlabel('Tipo')
    plt.ylabel('Cantidad')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    return get_chart_buffer()

def generate_maintenance_by_type_chart(data):
    """
    Generates a bar chart for maintenance by type.
    data: list of dicts [{'maintenance_type': 'PREVENTIVE', 'count': 5}, ...]
    """
    if not data:
        return None
        
    types = [dict(MAINTENANCE_TYPE_CHOICES).get(item['maintenance_type'], item['maintenance_type']) for item in data]
    counts = [item['count'] for item in data]
    
    plt.figure(figsize=(6, 4))
    bars = plt.bar(types, counts, color='#2980b9')
    
    plt.title('Mantenimientos por Tipo')
    plt.xlabel('Tipo')
    plt.ylabel('Cantidad')
    plt.tight_layout()
    
    return get_chart_buffer()

def generate_equipment_status_chart(data):
    """
    Generates a pie chart for equipment status.
    data: list of dicts [{'status': 'ACTIVE', 'count': 20}, ...]
    """
    if not data:
        return None
        
    labels = [dict(EQUIPMENT_STATUS_CHOICES).get(item['status'], item['status']) for item in data]
    counts = [item['count'] for item in data]
    
    plt.figure(figsize=(5, 5))
    plt.pie(counts, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#27ae60', '#e74c3c', '#f39c12', '#95a5a6'])
    plt.title('Estado de Equipos')
    plt.tight_layout()
    
    return get_chart_buffer()

def generate_handover_by_type_chart(data):
    """
    Generates a bar chart for handovers by type.
    data: list of dicts [{'type': 'ASSIGNMENT', 'count': 5}, ...]
    """
    if not data:
        return None
    
    # Import locally to avoid circular imports if necessary, or rely on existing imports
    from .choices import HANDOVER_TYPE_CHOICES
    
    types = [dict(HANDOVER_TYPE_CHOICES).get(item['type'], item['type']) for item in data]
    counts = [item['count'] for item in data]
    
    plt.figure(figsize=(6, 4))
    bars = plt.bar(types, counts, color='#8e44ad')
    
    plt.title('Entregas por Tipo')
    plt.xlabel('Tipo')
    plt.ylabel('Cantidad')
    plt.tight_layout()
    
    return get_chart_buffer()

def generate_handover_by_area_chart(data):
    """
    Generates a horizontal bar chart for handovers by destination area.
    data: list of dicts [{'destination_area__name': 'HR', 'count': 5}, ...]
    """
    if not data:
        return None
        
    areas = [item['destination_area__name'] or 'N/A' for item in data]
    counts = [item['count'] for item in data]
    
    plt.figure(figsize=(6, 4))
    bars = plt.barh(areas, counts, color='#d35400')
    
    plt.title('Entregas por Área Destino')
    plt.xlabel('Cantidad')
    plt.tight_layout()
    
    return get_chart_buffer()
