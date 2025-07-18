
from django.contrib import admin
from .models import JobOffer, StatusMessageTemplate, Candidatura

@admin.register(JobOffer)
class JobOfferAdmin(admin.ModelAdmin):
    list_display = ['title', 'company_name', 'created_by', 'is_active', 'created_at']
    list_filter = ['is_active', 'modality']
    search_fields = ['title', 'company_name', 'created_by__username']

@admin.register(StatusMessageTemplate)
class StatusMessageTemplateAdmin(admin.ModelAdmin):
    list_display = ['user', 'estado']
    search_fields = ['user__username', 'estado']

@admin.register(Candidatura)
class CandidaturaAdmin(admin.ModelAdmin):
    list_display = ('user', 'offer', 'estado', 'updated_at')
    list_filter = ('estado',)


