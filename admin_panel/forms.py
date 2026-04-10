from django import forms
from core.models import LoteCertificados, SolicitudAcceso, SesionAsistencia, Participante, FirmaInstitucional


class BatchForm(forms.ModelForm):
    class Meta:
        model = LoteCertificados
        fields = ['nombre_lote', 'facultad', 'archivo_excel']
        widgets = {
            'nombre_lote': forms.TextInput(attrs={
                'class': 'w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-unemi-orange focus:border-transparent transition-all duration-300',
                'placeholder': 'Ej: NORMAS ISO'
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


class SolicitudAccesoForm(forms.ModelForm):
    """Formulario de registro con solicitud de acceso - incluye contraseña"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full bg-white dark:bg-[#0B1221] border border-gray-200 dark:border-white/10 rounded-lg px-3.5 py-2.5 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-600 focus:outline-none focus:border-unemi-orange focus:ring-1 focus:ring-unemi-orange transition-colors',
            'placeholder': '••••••••',
            'required': True,
            'minlength': '6',
        }),
        label='Contraseña',
        min_length=6,
    )
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full bg-white dark:bg-[#0B1221] border border-gray-200 dark:border-white/10 rounded-lg px-3.5 py-2.5 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-600 focus:outline-none focus:border-unemi-orange focus:ring-1 focus:ring-unemi-orange transition-colors',
            'placeholder': '••••••••',
            'required': True,
        }),
        label='Confirmar Contraseña',
    )
    
    class Meta:
        model = SolicitudAcceso
        fields = ['nombres', 'apellidos', 'email', 'telefono', 'facultad']
        widgets = {
            'nombres': forms.TextInput(attrs={
                'class': 'w-full bg-white dark:bg-[#0B1221] border border-gray-200 dark:border-white/10 rounded-lg px-3.5 py-2.5 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-600 focus:outline-none focus:border-unemi-orange focus:ring-1 focus:ring-unemi-orange transition-colors',
                'placeholder': 'Tus nombres',
                'required': True
            }),
            'apellidos': forms.TextInput(attrs={
                'class': 'w-full bg-white dark:bg-[#0B1221] border border-gray-200 dark:border-white/10 rounded-lg px-3.5 py-2.5 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-600 focus:outline-none focus:border-unemi-orange focus:ring-1 focus:ring-unemi-orange transition-colors',
                'placeholder': 'Tus apellidos',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full bg-white dark:bg-[#0B1221] border border-gray-200 dark:border-white/10 rounded-lg px-3.5 py-2.5 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-600 focus:outline-none focus:border-unemi-orange focus:ring-1 focus:ring-unemi-orange transition-colors',
                'placeholder': 'correo@ejemplo.com',
                'required': True
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'w-full bg-white dark:bg-[#0B1221] border border-gray-200 dark:border-white/10 rounded-lg px-3.5 py-2.5 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-600 focus:outline-none focus:border-unemi-orange focus:ring-1 focus:ring-unemi-orange transition-colors',
                'placeholder': 'Ej: 0997541322',
                'type': 'tel',
                'inputmode': 'numeric',
                'pattern': '[0-9]{10}',
                'maxlength': '10',
            }),
            'facultad': forms.Select(attrs={
                'class': 'w-full bg-white dark:bg-[#0B1221] border border-gray-200 dark:border-white/10 rounded-lg px-3.5 py-2.5 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-600 focus:outline-none focus:border-unemi-orange focus:ring-1 focus:ring-unemi-orange transition-colors',
                'required': True
            }),
        }
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            # Eliminar espacios o guiones si los hay
            telefono = telefono.replace(' ', '').replace('-', '')
            if not telefono.isdigit():
                raise forms.ValidationError('El teléfono solo debe contener números.')
            if len(telefono) != 10:
                raise forms.ValidationError('El número de teléfono debe tener exactamente 10 dígitos.')
        return telefono
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Las contraseñas no coinciden.')

        return cleaned_data


INPUT_CLASS = 'w-full p-3 rounded-xl bg-gray-50 dark:bg-[#0F163A]/50 border border-gray-200 dark:border-blue-900/30 text-gray-800 dark:text-white font-medium focus:outline-none focus:border-[#F58830] transition-all duration-300'
SELECT_CLASS = INPUT_CLASS


class SesionForm(forms.ModelForm):
    capacidad_ilimitada = forms.BooleanField(
        required=False,
        label='Cupos ilimitados',
        widget=forms.CheckboxInput(attrs={
            'class': 'h-5 w-5 rounded text-[#F58830] focus:ring-[#F58830] border-gray-300',
        }),
    )

    class Meta:
        model = SesionAsistencia
        fields = ['titulo', 'descripcion', 'lugar', 'fecha', 'dia_semana', 'hora_inicio', 'hora_fin', 'capacidad', 'solo_lideres']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ej: Seminario de IA'}),
            'descripcion': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3, 'placeholder': 'Descripción del evento (opcional)'}),
            'lugar': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ej: Auditorio Principal'}),
            'fecha': forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'}),
            'dia_semana': forms.Select(attrs={'class': SELECT_CLASS}),
            'hora_inicio': forms.TimeInput(attrs={'class': INPUT_CLASS, 'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'class': INPUT_CLASS, 'type': 'time'}),
            'capacidad': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': '1', 'placeholder': 'Ej: 100'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['capacidad_ilimitada'].initial = self.instance.capacidad == 0

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('capacidad_ilimitada'):
            cleaned_data['capacidad'] = 0
        elif not cleaned_data.get('capacidad'):
            cleaned_data['capacidad'] = 0  # default ilimitada si no se pone nada
        return cleaned_data


class ParticipanteRegistroForm(forms.ModelForm):
    """Formulario público para registro de participante en sesión."""
    class Meta:
        model = Participante
        fields = ['cedula', 'nombres', 'apellidos', 'email', 'celular']
        widgets = {
            'cedula': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Ej: 0912345678',
                'inputmode': 'numeric',
            }),
            'nombres': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Tus nombres',
                'required': True,
            }),
            'apellidos': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Tus apellidos',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'correo@ejemplo.com',
                'required': True,
            }),
            'celular': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Ej: 0997541322',
                'type': 'tel',
                'inputmode': 'numeric',
                'maxlength': '10',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        cedula = cleaned_data.get('cedula', '').strip()
        email = cleaned_data.get('email', '').strip()
        if not cedula and not email:
            raise forms.ValidationError('Debe proporcionar al menos cédula o correo electrónico.')
        return cleaned_data

class FirmaInstitucionalForm(forms.ModelForm):
    class Meta:
        model = FirmaInstitucional
        fields = ['nombre', 'cargo', 'orden', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Ej: Ph.D. Fabricio Guevara Viejó',
            }),
            'cargo': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Ej: RECTOR UNEMI',
            }),
            'orden': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'min': 0,
                'placeholder': 'Orden de aparición (1, 2, 3...)',
            }),
            'activa': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 rounded text-[#F58830] focus:ring-[#F58830] border-gray-300',
            }),
        }
