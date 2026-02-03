from django import forms
from .models import Maintenance, Equipment
from django.contrib.auth.models import User

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
