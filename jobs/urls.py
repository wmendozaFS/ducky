from django.urls import path
from . import views

urlpatterns = [
    # URLs para ofertas de empleo (accesibles por candidatos y headhunters)
    path('ofertas/', views.JobOfferList.as_view(), name='job_offer_list'),
    path('oferta/<int:offer_id>/', views.JobOfferDetailView.as_view(), name='job_offer_detail'),
    path('oferta/<int:offer_id>/postular/', views.apply_to_offer, name='apply_to_offer'),
    path('oferta/crear/', views.CreateOfferView.as_view(), name='create_offer'), # Solo headhunters
    path('oferta/<int:offer_id>/editar/', views.EditOfferView.as_view(), name='edit_offer'),
    path('candidato/dashboard/', views.candidate_dashboard, name='candidate_dashboard'),

    # URLs para el dashboard y gestión de headhunters
    path('headhunter/', views.HeadhunterDashboardView.as_view(), name='headhunter_dashboard'),
    path('headhunter/oferta/<int:offer_id>/candidaturas/', views.OfferApplicationsView.as_view(), name='offer_applications'),
    path('headhunter/candidatura/<int:candidature_id>/update/', views.cambiar_estado_candidatura, name='cambiar_estado_candidatura'),
    
    # URLs para la agenda del headhunter
    path('headhunter/agenda/', views.agenda, name='agenda'),
    path('headhunter/api/acciones/', views.api_acciones_headhunter, name='api_acciones_headhunter'),
    path('headhunter/crear-accion-ajax/', views.crear_accion_ajax, name='crear_accion_ajax'),
    path('headhunter/agenda/editar-accion-ajax/<int:accion_id>/', views.editar_accion_ajax, name='editar_accion_ajax'), # Añadido
    path('headhunter/agenda/eliminar-accion-ajax/<int:accion_id>/', views.eliminar_accion_ajax, name='eliminar_accion_ajax'), # Añadido

    # URL para el historial de acciones de una oferta (si es necesaria)
    # path('oferta/<int:offer_id>/historial-acciones/', views.historial_acciones, name='historial_acciones'), # Ejemplo, si la usas
    # URL para agregar acción a una oferta específica (si es necesaria)
    # path('oferta/<int:oferta_id>/agregar-accion/', views.agregar_accion, name='agregar_accion'), # Ejemplo, si la usas
]