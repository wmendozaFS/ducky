from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy

def headhunter_required1(view_func):
    """
    Decorador para verificar si el usuario está logueado y pertenece al grupo 'headhunter'.
    """
    def check_user(user):
        return user.is_authenticated and user.groups.filter(name='headhunter').exists()

    return user_passes_test(check_user, login_url='/accounts/login/')(view_func)



def role_required(role_name):
    def check_role(user):
        return user.is_authenticated and getattr(user, 'role', None) == role_name
    return user_passes_test(check_role)


# Decorador para funciones de vista
def headhunter_required(function):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Redirigir a login si no está autenticado
            return redirect(f"{reverse_lazy('login')}?next={request.path}")
        if not request.user.groups.filter(name='headhunter').exists():
            # Redirigir a alguna página de "acceso denegado" o a la home si no es headhunter
            # Puedes personalizar esta redirección (ej. a una 403.html)
            return redirect(reverse_lazy('job_offer_list')) # O a una página de error
        return function(request, *args, **kwargs)
    return wrapper

# Mixin para Class-Based Views (CBVs)
class HeadhunterRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission() # Usa el comportamiento por defecto de AccessMixin para no autenticados
        if not request.user.groups.filter(name='headhunter').exists():
            return redirect(reverse_lazy('job_offer_list')) # Redirige si no es headhunter
        return super().dispatch(request, *args, **kwargs)