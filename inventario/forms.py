from django import forms
from .models import Material, Movimiento

class EntradaMaterialForm(forms.Form):
    material = forms.ModelChoiceField(
        queryset=Material.objects.filter(activo=True),
        label="Material",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    cantidad = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        label="Cantidad",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    referencia = forms.CharField(
        max_length=100,
        label="Referencia (Orden de Compra, Factura, etc.)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    observaciones = forms.CharField(
        required=False,
        label="Observaciones",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

class SalidaMaterialForm(forms.Form):
    material = forms.ModelChoiceField(
        queryset=Material.objects.filter(activo=True),
        label="Material",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    cantidad = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        label="Cantidad",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    referencia = forms.CharField(
        max_length=100,
        label="Referencia (Requisición, Área, etc.)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    observaciones = forms.CharField(
        required=False,
        label="Observaciones",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostrar solo materiales con stock disponible
        self.fields['material'].queryset = Material.objects.filter(
            activo=True,
            stock_actual__gt=0
        )