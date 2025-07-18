from django import forms
from .models import JobOffer, Candidatura, StatusMessageTemplate, CANDIDATURE_STATUS_CHOICES


class JobOfferForm(forms.ModelForm):
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
class CandidatureStatusForm(forms.ModelForm):
    class Meta:
        model = Candidatura
        fields = ['estado']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class CambiarEstadoCandidaturaForm(forms.ModelForm):
    estado = forms.ChoiceField(choices=CANDIDATURE_STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    mensaje_personalizado = forms.CharField(widget=forms.Textarea, required=False)
    class Meta:
        model = Candidatura
        fields = ['estado', 'mensaje_personalizado']

class StatusMessageTemplateForm(forms.ModelForm):
    class Meta:
        model = StatusMessageTemplate
        fields = ['estado', 'mensaje']
        widgets = {
            'mensaje': forms.Textarea(attrs={'rows': 5}),
        }