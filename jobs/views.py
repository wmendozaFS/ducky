# jobs/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse # Import HttpResponse for the edit form content
from django.utils.decorators import method_decorator
from datetime import timedelta # Necesario para calcular 'end' en eventos de calendario
from django.views.decorators.http import require_GET, require_POST # Importar para decoradores de método HTTP

# Importa tus modelos y formularios
from .models import JobOffer, Candidatura, AgendaAccion, StatusMessageTemplate

# Corregido 'CandidatureStatusForm' a 'CandidaturaStatusForm'
from .forms import JobOfferForm, CandidaturaForm, AgendaAccionForm, CandidaturaStatusForm 

# Importa tus decoradores personalizados y Mixins
from .decorators import headhunter_required, HeadhunterRequiredMixin 

# --- Vistas del Dashboard del Headhunter y Gestión de Ofertas ---

# Usamos HeadhunterRequiredMixin directamente en lugar del decorador para CBV ---
# --- Vistas para la Gestión de Ofertas (Headhunter) ---
class HeadhunterDashboardView(HeadhunterRequiredMixin, ListView):
    """
    Muestra el panel de control del headhunter con las candidaturas
    de las ofertas que ha creado.
    """
    model = Candidatura
    template_name = 'jobs/headhunter_dashboard.html'
    context_object_name = 'candidaturas'

    def get_queryset(self):
        # Filtra candidaturas de ofertas creadas por el headhunter actual
        return Candidatura.objects.filter(offer__created_by=self.request.user).order_by('-updated_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_headhunter'] = True 
        return context

class CreateOfferView(HeadhunterRequiredMixin, CreateView):
    """
    Permite a un headhunter crear una nueva oferta de empleo.
    """
    model = JobOffer
    form_class = JobOfferForm
    template_name = 'jobs/create_offer.html'
    success_url = reverse_lazy('headhunter_dashboard')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, '¡Oferta de empleo creada exitosamente!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_headhunter'] = True 
        return context

class EditOfferView(HeadhunterRequiredMixin, UpdateView):
    """
    Permite a un headhunter editar una oferta de empleo que ha creado.
    """
    model = JobOffer
    form_class = JobOfferForm
    template_name = 'jobs/edit_offer.html'
    pk_url_kwarg = 'offer_id' 
    
    def get_queryset(self):
        # Solo permitir editar ofertas creadas por el usuario actual
        return super().get_queryset().filter(created_by=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, '¡Oferta de empleo actualizada exitosamente!')
        return super().form_valid(form)
    
    def get_success_url(self, **kwargs): # Añade **kwargs para compatibilidad con reverse_lazy si es necesario
        # Usar self.object.pk que es el objeto actualizado
        return reverse_lazy('job_offer_detail', kwargs={'offer_id': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_headhunter'] = True 
        return context

# --- Vistas para Listado y Detalle de Ofertas (Públicas) ---

class JobOfferList(ListView):
    """
    Muestra una lista de todas las ofertas de empleo activas.
    Accesible para todos los usuarios.
    """
    template_name = 'jobs/job_offer_list.html'
    model = JobOffer
    context_object_name = 'offers'
    queryset = JobOffer.objects.filter(is_active=True).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_headhunter'] = self.request.user.is_authenticated and \
        self.request.user.groups.filter(name='headhunter').exists()
        return context

class JobOfferDetailView(DetailView):
    """
    Muestra los detalles de una oferta de empleo específica.
    Accesible para todos los usuarios, con contenido condicional.
    """
    model = JobOffer
    template_name = 'jobs/job_offer_detail.html'
    context_object_name = 'offer'
    pk_url_kwarg = 'offer_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user = self.request.user
        offer = self.object

        context['is_headhunter'] = user.is_authenticated and user.groups.filter(name='headhunter').exists()
        context['is_offer_creator'] = user.is_authenticated and offer.created_by == user

        if user.is_authenticated and not context['is_headhunter']:
            user_application = Candidatura.objects.filter(user=user, offer=offer).first()
            context['user_has_applied'] = user_application is not None
            context['user_application'] = user_application

        return context

# --- Vistas de Postulación ---
@login_required
def candidate_dashboard(request):
    candidaturas = Candidatura.objects.filter(user=request.user).select_related('offer')

    return render(request, 'jobs/candidate_dashboard.html', {
        'candidaturas': candidaturas,
    })

@login_required 
def apply_to_offer(request, offer_id):
    """
    Permite a un usuario (candidato) postularse a una oferta de empleo.
    """
    offer = get_object_or_404(JobOffer, id=offer_id, is_active=True)

    if request.user.groups.filter(name='headhunter').exists():
        messages.error(request, 'Los headhunters no pueden postular a ofertas de empleo.')
        return redirect('job_offer_detail', offer_id=offer_id)

    if Candidatura.objects.filter(user=request.user, offer=offer).exists():
        messages.warning(request, 'Ya te has postulado a esta oferta.')
        return redirect('job_offer_detail', offer_id=offer_id)

    if request.method == 'POST':
        form = CandidaturaForm(request.POST)
        if form.is_valid():
            candidatura = form.save(commit=False)
            candidatura.user = request.user
            candidatura.offer = offer
            candidatura.save()
            messages.success(request, '¡Tu postulación ha sido enviada con éxito!')
            return redirect('job_offer_detail', offer_id=offer_id)
    else:
        form = CandidaturaForm()
    
    context = {
        'offer': offer,
        'form': form,
    }
    return render(request, 'jobs/apply_to_offer.html', context)

class OfferApplicationsView(HeadhunterRequiredMixin, DetailView): # Usamos el Mixin
    """
    Muestra las postulaciones para una oferta específica de un headhunter.
    """
    model = JobOffer
    template_name = 'jobs/offer_applications.html'
    context_object_name = 'offer'
    pk_url_kwarg = 'offer_id'

    def get_queryset(self):
        return super().get_queryset().filter(created_by=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['applications'] = self.object.applications.all().order_by('-fecha_aplicacion')
        context['is_headhunter'] = True
        return context

@headhunter_required 
def cambiar_estado_candidatura(request, candidature_id):
    """
    Permite a un headhunter cambiar el estado de una candidatura.
    """
    # Usar get_object_or_404 en lugar de get_object_or_204 si no está importado, o importar get_object_or_204
    candidatura = get_object_or_404(Candidatura, id=candidature_id, offer__created_by=request.user)

    if request.method == 'POST':
        form = CandidaturaStatusForm(request.POST, instance=candidatura)
        if form.is_valid():
            form.save()
            messages.success(request, f'Estado de la candidatura de {candidatura.user.username} actualizado a "{candidatura.get_estado_display()}".')
            return redirect('offer_applications', offer_id=candidatura.offer.id)
    else:
        form = CandidaturaStatusForm(instance=candidatura)
    
    context = {
        'candidatura': candidatura,
        'form': form,
        'is_headhunter': True,
    }
    return render(request, 'jobs/cambiar_estado_candidatura.html', context)

# --- Vistas de Agenda (Solo para Headhunters) ---

@headhunter_required
def agenda(request):
    """
    Muestra la vista de la agenda con FullCalendar para el headhunter.
    """
    # Al instanciar el formulario, pasamos el usuario para que el queryset de oferta/candidatura se filtre correctamente
    form = AgendaAccionForm(user=request.user) 
    context = {
        'form': form,
        'is_headhunter': True,
    }
    return render(request, 'jobs/agenda.html', context)

@headhunter_required
@require_GET
def api_acciones_headhunter(request):
    """
    API endpoint que devuelve las acciones de agenda del headhunter en formato FullCalendar.
    """
    # Filtra las acciones del headhunter actual (el campo 'user' en AgendaAccion)
    acciones = AgendaAccion.objects.filter(user=request.user).select_related('oferta', 'candidatura__user')
    events = []
    for accion in acciones:
        title = f"{accion.get_tipo_display()} - {accion.titulo}" # Usar titulo de la accion, no de la oferta directamente
        if accion.oferta:
            title += f" (Oferta: {accion.oferta.title})"
        if accion.candidatura:
            title += f" (Candidato: {accion.candidatura.user.username})"
        
        events.append({
            'id': accion.id,
            'title': title,
            'start': accion.fecha_hora_inicio.isoformat(), # Usar fecha_hora_inicio del modelo
            # Calcular el 'end' usando la duración. Añadir el timezone.timedelta
            'end': (accion.fecha_hora_inicio + timedelta(minutes=accion.duracion_minutos)).isoformat() if accion.fecha_hora_inicio else None,
            'backgroundColor': color_por_tipo(accion.tipo), # Usar el filtro de color
            'extendedProps': { # Datos adicionales para uso en JS
                'descripcion': accion.descripcion, # Cambiado de 'notes' a 'descripcion'
                'oferta_id': accion.oferta.id if accion.oferta else None, # Asegúrate de que existe oferta antes de acceder a .id
                'candidatura_id': accion.candidatura.id if accion.candidatura else None,
                'tipo': accion.tipo, # Añadido el tipo de acción
                'duracion_minutos': accion.duracion_minutos, # Añadido la duración
            }
        })
    return JsonResponse(events, safe=False)

@headhunter_required
@require_POST
def crear_accion_ajax(request):
    """
    Crea una nueva acción de agenda vía AJAX.
    """
    # Pasar el usuario al formulario para que los querysets de oferta/candidatura se filtren correctamente ---
    form = AgendaAccionForm(request.POST, user=request.user) 
    if form.is_valid():
        accion = form.save(commit=False)
        accion.user = request.user # Asegura que la acción se asigne al usuario actual
        
        # Validar que la oferta seleccionada (si existe) pertenezca al headhunter actual
        if accion.oferta and not JobOffer.objects.filter(id=accion.oferta.id, created_by=request.user).exists():
            return JsonResponse({'status': 'error', 'errors': {'oferta': ['La oferta seleccionada no te pertenece.']}}, status=403)
        
        # Validar que la candidatura seleccionada (si existe) pertenezca a una oferta del headhunter
        if accion.candidatura and not Candidatura.objects.filter(id=accion.candidatura.id, offer__created_by=request.user).exists():
            return JsonResponse({'status': 'error', 'errors': {'candidatura': ['La candidatura seleccionada no está asociada a una de tus ofertas.']}}, status=403)

        accion.save()
        messages.success(request, 'Acción creada exitosamente.')
        return JsonResponse({'status': 'ok'})
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

@headhunter_required
def editar_accion_ajax(request, accion_id):
    """
    Carga el formulario de edición para una acción de agenda (GET)
    y maneja la actualización (POST).
    """
    # Asegúrate de que solo el headhunter que creó la acción (o su oferta) pueda editarla
    accion = get_object_or_404(AgendaAccion, id=accion_id, user=request.user) # Filtro por el user de la acción
    
    if request.method == 'POST':
        # Pasar el usuario al formulario al editar
        form = AgendaAccionForm(request.POST, instance=accion, user=request.user) 
        if form.is_valid():
            # Validar que la oferta seleccionada (si existe) pertenezca al headhunter
            if form.cleaned_data.get('oferta') and not JobOffer.objects.filter(id=form.cleaned_data['oferta'].id, created_by=request.user).exists():
                return JsonResponse({'status': 'error', 'errors': {'oferta': ['La oferta seleccionada no te pertenece.']}}, status=403)
            
            # Validar que la candidatura seleccionada (si existe) pertenezca a una oferta del headhunter
            if form.cleaned_data.get('candidatura') and not Candidatura.objects.filter(id=form.cleaned_data['candidatura'].id, offer__created_by=request.user).exists():
                return JsonResponse({'status': 'error', 'errors': {'candidatura': ['La candidatura seleccionada no está asociada a una de tus ofertas.']}}, status=403)

            form.save()
            messages.success(request, 'Acción actualizada exitosamente.')
            return JsonResponse({'status': 'ok'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    else: # GET request, para cargar el formulario
        # Pasar el usuario al formulario al obtenerlo
        form = AgendaAccionForm(instance=accion, user=request.user) 
        return render(request, 'modals/editar_accion_modal_content.html', {'form': form, 'accion_id': accion_id})

@headhunter_required
@require_POST
def eliminar_accion_ajax(request, accion_id):
    """
    Elimina una acción de agenda vía AJAX.
    """
    # Asegúrate de que solo el headhunter que creó la acción (o su oferta) pueda eliminarla
    accion = get_object_or_404(AgendaAccion, id=accion_id, user=request.user) # Filtro por el user de la acción
    accion.delete()
    messages.success(request, 'Acción eliminada exitosamente.')
    return JsonResponse({'status': 'ok'})


def color_por_tipo(tipo):
    """
    Devuelve el color asociado a un tipo de acción.
    """
    tipo_colores = {
        'entrevista': '#007bff',  # Azul (bg-primary)
        'llamada': '#28a745',     # Verde (bg-success)
        'recordatorio': '#ffc107', # Amarillo (bg-warning)
        'entrega': '#dc3545',     # Rojo (bg-danger)
        'otro': '#6c757d',        # Gris (bg-secondary)
    }
    return tipo_colores.get(tipo, '#6c757d') # Gris por defecto
    