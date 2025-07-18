from django.db import models
from django.contrib.auth.models import User

CANDIDATURE_STATUS_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('aceptado', 'Aceptado'),
    ('rechazado', 'Rechazado'),
]
# Oferta de empleo creada por un headhunter
class JobOffer(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_offers')
    company_name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100, blank=True)
    modality = models.CharField(
        max_length=20,
        choices=[
            ('remote', 'Remote'),
            ('onsite', 'On Site'),
            ('hybrid', 'Hybrid')
        ],
        default='onsite'
    )
    salary = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100, blank=True)
    requirements = models.TextField(blank=True)
    benefits = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"{self.title} at {self.company_name}"

# Candidatura de un usuario a una oferta
# Propuesta de modelo Candidatura unificado
class Candidatura(models.Model):
    offer = models.ForeignKey(JobOffer, on_delete=models.CASCADE, related_name='candidaturas')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='candidaturas_usuario') # Cambié related_name para evitar conflicto si hay otro 'candidaturas'
    estado = models.CharField(max_length=20, choices=CANDIDATURE_STATUS_CHOICES, default='pendiente')
    mensaje_inicial = models.TextField(blank=True) # Mensaje de la aplicación inicial
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('offer', 'user') # Asegura una única aplicación por oferta y usuario

    def __str__(self):
        return f"{self.user.username} - {self.offer.title} ({self.estado})"

class StatusMessageTemplate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="status_templates")
    estado = models.CharField(max_length=20, choices=CANDIDATURE_STATUS_CHOICES, default='pendiente')
    mensaje = models.TextField()

    class Meta:
        unique_together = ('user', 'estado')

    def __str__(self):
        return f"{self.user.username} - {self.estado}"
    


class AccionOferta(models.Model):
    TIPO_ACCION_CHOICES = [
        ('llamada', 'Llamada'),
        ('entrevista', 'Entrevista'),
        ('nota', 'Nota Interna'),
        ('seguimiento', 'Seguimiento'),
        ('otro', 'Otro'),
    ]

   
    oferta = models.ForeignKey(JobOffer, on_delete=models.CASCADE, related_name='acciones')
    fecha = models.DateTimeField()
    tipo = models.CharField(max_length=20, choices=TIPO_ACCION_CHOICES)
    descripcion = models.TextField()
    realizada_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='acciones_realizadas')

class AgendaAccion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agenda_acciones_creadas')
    oferta = models.ForeignKey(JobOffer, null=True, blank=True, on_delete=models.SET_NULL, related_name='agenda_acciones_oferta')
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    fecha = models.DateField()
    hora = models.TimeField()
    duracion_minutos = models.PositiveIntegerField(default=30)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['fecha']),
            models.Index(fields=['oferta']),
        ]

    def __str__(self):
        return f"{self.titulo} ({self.fecha} {self.hora})"
