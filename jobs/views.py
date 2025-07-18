from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .decorators import headhunter_required
from .models import JobOffer, Candidatura, StatusMessageTemplate
from .forms import JobOfferForm, CandidatureStatusForm, CambiarEstadoCandidaturaForm, StatusMessageTemplateForm
from django.contrib import messages
from django.core.mail import send_mail



@login_required
@headhunter_required
def create_offer(request):
    if not request.user.groups.filter(name='headhunter').exists():
        messages.error(request, "Solo los headhunters pueden crear ofertas.")
        return redirect('home')

    if request.method == 'POST':
        form = JobOfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.created_by = request.user
            offer.save()
            messages.success(request, "Oferta creada correctamente.")
            return redirect('job_offer_list')  
    else:
        form = JobOfferForm()

    return render(request, 'jobs/create_offer.html', {'form': form})

def job_offer_list(request):
    is_headhunter = request.user.groups.filter(name='headhunter').exists()
    is_candidate = request.user.groups.filter(name='candidate').exists()
    if is_headhunter:
        offers = JobOffer.objects.filter(created_by=request.user).order_by('-created_at')
    elif is_candidate:
        offers = JobOffer.objects.all().order_by('-created_at')
    else:
        offers = JobOffer.objects.filter(is_active=True).order_by('-created_at')

    return render(request, 'jobs/job_offer_list.html', {'offers': offers})
   


def job_offer_detail(request, offer_id):
    offer = get_object_or_404(JobOffer, id=offer_id)
    return render(request, 'jobs/job_offer_detail.html', {'offer': offer})


@login_required
def apply_to_offer(request, offer_id):
    offer = get_object_or_404(JobOffer, id=offer_id)
    # Evita duplicados
    existing = Candidatura.objects.filter(offer=offer, user=request.user).exists()
    if not existing:
        Candidatura.objects.create(offer=offer, user=request.user, estado='pendiente')
        messages.success(request, 'Has postulado correctamente.')
        return redirect('job_offer_detail', offer_id=offer.id)

    return render(request, 'jobs/apply_to_offer.html', {'offer': offer})

@login_required
@headhunter_required
def headhunter_dashboard(request):
    if not request.user.groups.filter(name='headhunter').exists():
        messages.error(request, "Acceso restringido al rol headhunter.")
        return redirect('home')

    offers = JobOffer.objects.filter(created_by=request.user)
    candidaturas = Candidatura.objects.filter(offer__in=offers).select_related('offer', 'user')

    if request.method == 'POST':
        candidature_id = request.POST.get('candidature_id')
        candidatura = get_object_or_404(Candidatura, id=candidature_id)
        form = CandidatureStatusForm(request.POST, instance=candidatura)

        if form.is_valid():
            form.save()

            # Enviar email al candidato
            estado_humano = candidatura.get_estado_display()
            asunto = f"Actualización de tu candidatura a {candidatura.offer.title}"
            mensaje = f"""
Hola {candidatura.user.first_name or candidatura.user.username},

Tu candidatura para el puesto '{candidatura.offer.title}' ha sido actualizada al estado: {estado_humano}.

Gracias por usar nuestra plataforma OpenToJob.

Un saludo,  
El equipo de OpenToJob
"""
            send_mail(
                subject=asunto,
                message=mensaje,
                from_email=None,
                recipient_list=[candidatura.user.email],
                fail_silently=True,
            )
            return redirect('headhunter_dashboard')

    else:
        forms_dict = {c.id: CandidatureStatusForm(instance=c) for c in candidaturas}
    return render(request, 'jobs/headhunter_dashboard.html', {
        'candidaturas': candidaturas,
        'forms_dict': forms_dict,
    })
@login_required
@headhunter_required
def editar_plantilla_estado(request, estado):
    if not request.user.groups.filter(name='headhunter').exists():
        messages.error(request, "Acceso restringido al rol headhunter.")
        return redirect('home')
    template, created = StatusMessageTemplate.objects.get_or_create(
        user=request.user,
        estado=estado
    )
    
    if request.method == 'POST':
        form = StatusMessageTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            return redirect('mis_plantillas_estado')
    else:
        form = StatusMessageTemplateForm(instance=template)
        
    return render(request, 'jobs/editar_plantilla.html', {'form': form, 'estado': estado})
@login_required
def offer_applications(request, offer_id):
    offer = get_object_or_404(JobOffer, id=offer_id, created_by=request.user)
    applications = offer.applications.all()
    return render(request, 'jobs/offer_applications.html', {
        'offer': offer,
        'applications': applications
    })

@login_required
@headhunter_required
def cambiar_estado_candidatura(request, candidature_id):
    if not request.user.groups.filter(name='headhunter').exists():
        messages.error(request, "Acceso restringido al rol headhunter.")
        return redirect('home')
 
    candidatura = get_object_or_404(Candidatura, id=candidature_id)

    if request.method == 'POST':
        form = CambiarEstadoCandidaturaForm(request.POST, instance=candidatura)
        if form.is_valid():
            form.save()
            return redirect('job_offer_detail', offer_id=candidatura.offer.pk)
    else:
        # Cargar mensaje por defecto desde plantilla si existe
        try:
            plantilla = StatusMessageTemplate.objects.get(
                user=request.user,
                estado=candidatura.estado
            )
            default_message = plantilla.mensaje
        except StatusMessageTemplate.DoesNotExist:
            default_message = ''
        
        form = CambiarEstadoCandidaturaForm(
            instance=candidatura,
            initial={'mensaje_personalizado': default_message}
        )
    print("Renderizando template con formulario")
    return render(
        request,
        'jobs/cambiar_estado_candidatura.html',
        {'form': form, 'candidatura': candidatura}
    )

@login_required
def candidature_list(request):
    candidatures = Candidatura.objects.all()
    return render(request, 'jobs/candidature_list.html', {'candidatures': candidatures},)


@login_required
@headhunter_required
def headhunter_offer_list(request):
    if not request.user.groups.filter(name='headhunter').exists():
        messages.error(request, "Acceso restringido al rol headhunter.")
        return redirect('home')
    elif request.user.is_candidate:
        offers = JobOffer.objects.all().order_by('-created_at')
    else:
        offers = JobOffer.objects.filter(created_by=request.user)
        return render(request, 'jobs/headhunter_offer_list.html', {'offers': offers})

@login_required
def message(request, offer_id):
    return render(request, 'jobs/message.html' , {'offer_id': offer_id})