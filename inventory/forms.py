from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Maintenance, Equipment, Area, CostCenter
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
        exclude = ['date', 'acta_pdfPerformed_by'] # performed_by is usually auto-set to logged user, but for the form we might let them choose or default.
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
            if isinstance(self.fields[field].widget, (forms.TextInput, forms.Textarea, forms.Select, forms.TimeInput, forms.DateInput, forms.NumberInput, forms.EmailInput)):
                self.fields[field].widget.attrs.update({'class': 'form-control'})
