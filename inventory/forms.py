from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Maintenance, Equipment, Area, CostCenter, Peripheral, Handover, Client
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    is_staff = forms.BooleanField(required=False, label="¿Es Administrador?", help_text="Marcar si el usuario puede gestionar otros usuarios y configuraciones.")
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = self.cleaned_data['is_staff']
        if commit:
            user.save()
        return user

class CostCenterForm(forms.ModelForm):
    class Meta:
        model = CostCenter
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
             if hasattr(self.fields[field], 'widget') and hasattr(self.fields[field].widget, 'attrs'):
                self.fields[field].widget.attrs.update({'class': 'form-control'})

class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = '__all__'
        widgets = {
             'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
             if hasattr(self.fields[field], 'widget') and hasattr(self.fields[field].widget, 'attrs'):
                self.fields[field].widget.attrs.update({'class': 'form-control'})

class MaintenanceForm(forms.ModelForm):
    class Meta:
        model = Maintenance
        fields = '__all__'
        exclude = ['date', 'acta_pdf', 'performed_by'] # performed_by is usually auto-set to logged user, but for the form we might let them choose or default.
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'next_maintenance_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add custom classes for styling if needed, e.g.
        for field in self.fields:
            if isinstance(self.fields[field].widget, (forms.TextInput, forms.Textarea, forms.Select, forms.TimeInput, forms.DateInput)):
                self.fields[field].widget.attrs.update({'class': 'form-control'})
class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = '__all__'
        exclude = ['created_at', 'updated_at']
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'warranty_expiry': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if isinstance(self.fields[field].widget, forms.Select):
                self.fields[field].widget.attrs.update({'class': 'form-select'})
            elif isinstance(self.fields[field].widget, (forms.TextInput, forms.Textarea, forms.TimeInput, forms.DateInput, forms.NumberInput, forms.EmailInput)):
                self.fields[field].widget.attrs.update({'class': 'form-control'})

class PeripheralForm(forms.ModelForm):
    class Meta:
        model = Peripheral
        fields = '__all__'
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'connected_to': forms.Select(attrs={'class': 'form-select'}), # Searchable via JS ideally, but select for now
            'area': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if hasattr(self.fields[field], 'widget') and hasattr(self.fields[field].widget, 'attrs'):
                # Add form-control class to all inputs
                current_classes = self.fields[field].widget.attrs.get('class', '')
                if 'form-select' not in current_classes:
                    self.fields[field].widget.attrs['class'] = (current_classes + ' form-control').strip()

                if 'form-select' not in current_classes:
                    self.fields[field].widget.attrs['class'] = (current_classes + ' form-control').strip()

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = '__all__'
        widgets = {
            'area': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if hasattr(self.fields[field], 'widget') and hasattr(self.fields[field].widget, 'attrs'):
                current_classes = self.fields[field].widget.attrs.get('class', '')
                if 'form-select' not in current_classes:
                    self.fields[field].widget.attrs['class'] = (current_classes + ' form-control').strip()

class HandoverForm(forms.ModelForm):
    class Meta:
        model = Handover
        fields = ['client', 'source_area', 'destination_area', 'equipment', 'peripherals', 'receiver_name', 'observations', 'type']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'source_area': forms.Select(attrs={'class': 'form-select'}),
            'destination_area': forms.Select(attrs={'class': 'form-select'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'equipment': forms.SelectMultiple(attrs={'class': 'form-select', 'style': 'height: 200px;'}),
            'peripherals': forms.SelectMultiple(attrs={'class': 'form-select', 'style': 'height: 200px;'}),
            'observations': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'receiver_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'equipment': 'Equipos (Mantenga presionado Ctrl para seleccionar varios)',
            'peripherals': 'Periféricos (Mantenga presionado Ctrl para seleccionar varios)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: Filter querysets to show helpful text
        # self.fields['equipment'].queryset = Equipment.objects.filter(status='ACTIVE') 
        # But keeping all is safer for flexibility
        pass

