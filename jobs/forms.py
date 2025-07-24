# jobs/forms.py

from django import forms
from .models import (
    JobOffer,
    Candidatura,
    StatusMessageTemplate,
    AgendaAccion # Asegúrate que este modelo esté importado
)
from django.utils import timezone 


class JobOfferForm(forms.ModelForm):
    """
    Formulario para crear y editar ofertas de empleo.
    """
    class Meta:
        model = JobOffer
        fields = [
            'title',
            'company_name',
            'description',
            'location',
            'modality',
            'salary',
            'category',
            'requirements',
            'benefits',
            'is_active',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título del puesto'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la empresa'}),
            'description': forms.Textarea(attrs={'rows': 8, 'class': 'form-control', 'placeholder': 'Descripción detallada del puesto...'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Barcelona, Remoto, Madrid'}),
            'modality': forms.Select(attrs={'class': 'form-select'}),
            'salary': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 30000-40000 EUR/año o Negociable'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Desarrollo Software, Marketing, Ventas'}),
            'requirements': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'Requisitos necesarios (uno por línea o separados por comas)'}),
            'benefits': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'Beneficios ofrecidos (seguro, días libres, etc.)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CandidaturaForm(forms.ModelForm):
    """
    Formulario para que un candidato se postule a una oferta.
    Ahora usa 'mensaje_personalizado' del modelo Candidatura.
    """
    class Meta:
        model = Candidatura
        # >>> CAMBIADO a 'mensaje_personalizado' para que coincida con tu models.py
        fields = ['mensaje_personalizado'] 
        widgets = {
            'mensaje_personalizado': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'Comparte un mensaje o carta de presentación...'}),
        }


class CandidaturaStatusForm(forms.ModelForm):
    """
    Formulario para que un headhunter cambie el estado de una candidatura.
    """
    class Meta:
        model = Candidatura
        fields = ['estado']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }


class StatusMessageTemplateForm(forms.ModelForm):
    """
    Formulario para gestionar plantillas de mensajes de estado.
    """
    class Meta:
        model = StatusMessageTemplate
        fields = ['estado', 'mensaje']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'mensaje': forms.Textarea(attrs={'rows': 8, 'class': 'form-control', 'placeholder': 'Cuerpo del mensaje...'}),
        }


class AgendaAccionForm(forms.ModelForm):
    """
    Formulario para crear y editar acciones en la agenda del headhunter.
    Ahora usa 'fecha_hora_inicio' para coincidir con tu models.py.
    """
    # >>> CAMBIADO a 'fecha_hora_inicio'
    fecha_hora_inicio = forms.DateTimeField( 
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label='Fecha y Hora de Inicio' # Ajustado el label para ser más claro
    )

    class Meta:
        model = AgendaAccion
        # --- CAMBIO IMPORTANTE AQUÍ ---
        # Añadir 'candidatura' a la lista de campos para que el formulario lo maneje.
        fields = ['oferta', 'candidatura', 'tipo', 'titulo', 'descripcion', 'fecha_hora_inicio', 'duracion_minutos']
        widgets = {
            'oferta': forms.Select(attrs={'class': 'form-select'}),
            'candidatura': forms.Select(attrs={'class': 'form-select'}), # Widget para el campo candidatura
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Entrevista con Juan Pérez'}),
            'descripcion': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Notas o detalles de la acción...'}),
            # 'fecha_hora_inicio' ya tiene un widget explícito arriba
            'duracion_minutos': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Duración en minutos (ej: 30, 60)'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)

        if self.user and self.user.groups.filter(name='headhunter').exists():
            # Filtra las ofertas creadas por el headhunter actual
            self.fields['oferta'].queryset = JobOffer.objects.filter(created_by=self.user).order_by('title')
            
            # Filtra las candidaturas relacionadas con las ofertas del headhunter actual
            self.fields['candidatura'].queryset = Candidatura.objects.filter(
                offer__created_by=self.user
            ).select_related('user', 'offer').order_by('user__username', 'offer__title')
            
            # Si se está editando una acción y ya tiene una candidatura, su oferta ya debería estar en el queryset
            # No se necesita un 'pass' explícito aquí, el queryset ya las incluye si el user es el creador.
        else:
            # Si no es un headhunter, los querysets deben estar vacíos para evitar la exposición de datos
            self.fields['oferta'].queryset = JobOffer.objects.none()
            self.fields['candidatura'].queryset = Candidatura.objects.none()

    # Validaciones personalizadas
    def clean_fecha_hora_inicio(self): 
        fecha_accion = self.cleaned_data['fecha_hora_inicio']
        # Si se está creando una nueva acción y la fecha es en el pasado
        if self.instance.pk is None and fecha_accion < timezone.now():
            raise forms.ValidationError("La fecha y hora de la acción no pueden ser en el pasado.")
        return fecha_accion

    def clean_duracion_minutos(self):
        duracion = self.cleaned_data['duracion_minutos']
        if duracion <= 0:
            raise forms.ValidationError("La duración debe ser un número positivo.")
        if duracion > 480: # 8 horas
            raise forms.ValidationError("La duración máxima permitida es de 8 horas.")
        return duracion

    def clean(self):
        cleaned_data = super().clean()
        oferta = cleaned_data.get('oferta')
        candidatura = cleaned_data.get('candidatura')

        # Regla: Si se selecciona una candidatura, debe pertenecer a la oferta seleccionada (si ambas están presentes)
        if oferta and candidatura and candidatura.offer != oferta:
            self.add_error('candidatura', "La candidatura seleccionada no pertenece a la oferta especificada.")
        
        # Lógica para manejar la relación entre oferta y candidatura en el formulario
        # Si no se selecciona oferta, pero sí candidatura, la oferta de la candidatura se puede inferir
        if not oferta and candidatura:
            cleaned_data['oferta'] = candidatura.offer # Asigna la oferta de la candidatura
        
        # Si no hay ni oferta ni candidatura, considera si es un error.
        # En tu modelo, ambos son `null=True, blank=True`, así que por defecto no es un error.
        # Si necesitas que al menos uno esté presente, añade una validación aquí.
        if not oferta and not candidatura:
             self.add_error(None, "Una acción debe estar asociada a una oferta o a una candidatura (o a ambas).")


        return cleaned_data