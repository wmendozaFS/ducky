# jobs/templatetags/user_tags.py
from django import template
from django.contrib.auth.models import User, Group

register = template.Library()

@register.filter(name='is_in_group')
def is_in_group(user, group_name):
    """
    Comprueba si el usuario pertenece a un grupo específico.
    Uso: {% if request.user|is_in_group:'nombre_del_grupo' %}
    """
    if user.is_authenticated:
        try:
            return user.groups.filter(name=group_name).exists()
        except Group.DoesNotExist:
            return False # El grupo no existe
    return False