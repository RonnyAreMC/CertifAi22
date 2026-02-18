from django import forms
from core.models import LoteCertificados


class BatchForm(forms.ModelForm):
    class Meta:
        model = LoteCertificados
        fields = ['nombre_lote', 'facultad', 'archivo_excel']
        widgets = {
            'nombre_lote': forms.TextInput(attrs={
                'class': 'w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-unemi-orange focus:border-transparent transition-all duration-300',
                'placeholder': 'Ej: Seminario de Inteligencia Artificial 2024'
            }),
            'facultad': forms.Select(attrs={
                'class': 'w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-unemi-orange focus:border-transparent transition-all duration-300'
            }),
            'archivo_excel': forms.FileInput(attrs={
                'class': 'hidden',
                'id': 'file-upload',
                'accept': '.xlsx, .xls, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel'
            }),
        }
