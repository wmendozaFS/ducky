# jobs/admin.py
from django.contrib import admin
from .models import JobOffer, StatusMessageTemplate, Candidatura, AgendaAccion # Asegúrate de importar todos tus modelos

# Inline para ver Candidaturas directamente en la página de JobOffer
class CandidaturaInline(admin.TabularInline): # admin.StackedInline ofrece un layout diferente
    model = Candidatura
    extra = 0 # No mostrar formularios vacíos adicionales por defecto
    fields = ('offer','user', 'fecha_aplicacion', 'estado', 'mensaje_personalizado', 'updated_at') # CORREGIDO: 'message_personalizado'
    readonly_fields = ('user', 'fecha_aplicacion', 'updated_at') # Campos que no se pueden editar directamente aquí
    can_delete = False # O True si quieres permitir eliminar candidaturas desde la oferta

# 1. Personalización para JobOffer
@admin.register(JobOffer)
class JobOfferAdmin(admin.ModelAdmin):
    # CORREGIDO: Añadido 'updated_at' al list_display y readonly_fields según tu modelo de JobOffer
    list_display = ['title', 'company_name', 'location', 'modality', 'created_by', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'modality', 'created_at', 'company_name']
    search_fields = ['title', 'company_name', 'location', 'description', 'created_by__username']
    ordering = ('-created_at',) # Ordenar por fecha de creación descendente por defecto
    readonly_fields = ('created_by', 'created_at', 'updated_at') # Campos que no deberían ser editables después de la creación

    # Agrupar campos en la página de edición
    fieldsets = (
        (None, { # Sección general
            'fields': ('title', 'description', 'salary', 'modality', 'is_active')
        }),
        ('Información de la Empresa y Ubicación', { # Sección colapsable para detalles de la empresa
            'fields': ('company_name', 'location'),
            'classes': ('collapse',), # Esto hace que la sección sea colapsable
        }),
        ('Auditoría', { # Sección para campos de auditoría
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    inlines = [CandidaturaInline] # Añadir las candidaturas como inlines

    # Para asignar automáticamente el usuario que crea la oferta si no se especifica
    def save_model(self, request, obj, form, change):
        if not obj.pk: # Si es un nuevo objeto (no una edición)
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# 2. Personalización para StatusMessageTemplate
@admin.register(StatusMessageTemplate)
class StatusMessageTemplateAdmin(admin.ModelAdmin):
    # CORREGIDO: 'mensaje' es el nombre del campo en el modelo, no 'message_content'
    list_display = ['user', 'estado', 'mensaje']
    search_fields = ['user__username', 'estado', 'mensaje']
    # Si quieres que el usuario y el estado sean inmutables una vez creados
    # readonly_fields = ['user', 'estado']


# 3. Personalización para Candidatura
@admin.register(Candidatura)
class CandidaturaAdmin(admin.ModelAdmin):
    # CORREGIDO: 'mensaje_personalizado' es el nombre del campo, no 'message'
    list_display = ('user', 'offer', 'fecha_aplicacion', 'estado', 'mensaje_personalizado', 'updated_at')
    # CORREGIDO: Tus acciones personalizadas usan estados que NO están definidos en CandidatureStatus
    # Debes añadir estos estados a CandidatureStatus en models.py o cambiar los nombres aquí.
    # Por ejemplo, 'revisado', 'entrevista', 'contratado' no existen.
    # Los que sí existen son: 'pendiente', 'aceptado', 'rechazado'.
    list_filter = ('estado', 'fecha_aplicacion', 'offer__title', 'user__username') # Filtros adicionales
    search_fields = ('user__username', 'offer__title', 'mensaje_personalizado') # CORREGIDO: 'mensaje_personalizado'
    ordering = ('-fecha_aplicacion',) # Ordenar por fecha de aplicación descendente
    readonly_fields = ('fecha_aplicacion', 'updated_at') # Campos de solo lectura

    # Si tienes muchos usuarios u ofertas, esto mejora el rendimiento de los selectores
    raw_id_fields = ('user', 'offer') 
    
    # Acciones personalizadas para cambiar el estado de múltiples candidaturas
    # Estas acciones tendrán que usar los CHOICES reales de CandidatureStatus
    actions = ['marcar_como_aceptado', 'marcar_como_rechazado', 'marcar_como_pendiente'] # Usando los CHOICES existentes

    def marcar_como_aceptado(self, request, queryset):
        updated = queryset.update(estado='aceptado')
        self.message_user(request, f"{updated} candidaturas marcadas como 'Aceptado'.", level='success')
    marcar_como_aceptado.short_description = "Marcar candidaturas seleccionadas como 'Aceptado'"

    def marcar_como_rechazado(self, request, queryset):
        updated = queryset.update(estado='rechazado')
        self.message_user(request, f"{updated} candidaturas marcadas como 'Rechazado'.", level='warning')
    marcar_como_rechazado.short_description = "Marcar candidaturas seleccionadas como 'Rechazado'"

    def marcar_como_pendiente(self, request, queryset):
        updated = queryset.update(estado='pendiente')
        self.message_user(request, f"{updated} candidaturas marcadas como 'Pendiente'.", level='info')
    marcar_como_pendiente.short_description = "Marcar candidaturas seleccionadas como 'Pendiente'"


# 4. Personalización para AgendaAccion
@admin.register(AgendaAccion)
class AgendaAccionAdmin(admin.ModelAdmin):
    # CORREGIDO: Los campos 'candidatura' y 'fecha' no existen directamente en AgendaAccion
    # En tu modelo AgendaAccion tienes 'fecha_hora_inicio' y NO tienes un campo 'candidatura' directo.
    # Para 'candidatura', si quieres relacionar AgendaAccion con Candidatura, necesitas añadir una FK en el modelo.
    # Si 'fecha' se refiere a 'fecha_hora_inicio', cámbialo.
    # Si 'notas' se refiere a 'descripcion', cámbialo.

    list_display = ('titulo', 'tipo', 'user', 'oferta', 'fecha_hora_inicio', 'display_descripcion') # Añadido 'display_descripcion'
    list_filter = ('tipo', 'fecha_hora_inicio', 'oferta__title', 'user__username') # CORREGIDO: Usar 'fecha_hora_inicio'
    search_fields = ('titulo', 'descripcion', 'oferta__title', 'user__username') # CORREGIDO: 'descripcion'
    ordering = ('fecha_hora_inicio',) # CORREGIDO: Usar 'fecha_hora_inicio'

    # Método para mostrar una versión corta de la descripción en list_display
    def display_descripcion(self, obj):
        return obj.descripcion[:50] + '...' if len(obj.descripcion) > 50 else obj.descripcion
    display_descripcion.short_description = 'Descripción'

    # Agrupar campos en la página de edición
    fieldsets = (
        (None, {
            'fields': ('titulo', 'tipo', 'user', 'oferta', 'fecha_hora_inicio', 'duracion_minutos', 'descripcion', 'finished', 'fecha_finalizacion')
        }),
    )
    # Si tienes muchas ofertas o candidaturas, esto puede ser útil
    # Si añades candidatura a AgendaAccion, también la pones aquí
    raw_id_fields = ('user', 'oferta') # 'candidatura' si lo añades al modelo