from django.urls import path
from . import views

urlpatterns = [
    path('ofertas/', views.job_offer_list, name='job_offer_list'),
    path('oferta/<int:offer_id>/', views.job_offer_detail, name='job_offer_detail'),
    path('oferta/<int:offer_id>/postular/', views.apply_to_offer, name='apply_to_offer'),
    
    
    # Headhunter URLs
    path('headhunter/', views.headhunter_dashboard, name='headhunter_dashboard'),
    path('headhunter/crear/', views.create_offer, name='create_offer'),
    path('headhunter/oferta/<int:offer_id>/candidaturas/', views.offer_applications,name='offer_applications'),
    path('headhunter/candidatura/<int:candidature_id>/update/',views.cambiar_estado_candidatura,name='cambiar_estado_candidatura'),
    path('mensaje/<int:offer_id>', views.message, name='message'),
    
]