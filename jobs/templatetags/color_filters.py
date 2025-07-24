from django import template

register = template.Library()

@register.filter
def color_clase(tipo):
    """
    Devuelve una clase CSS de Bootstrap basada en el tipo de actividad.
    """
    return {
        'entrevista': 'bg-primary',
        'llamada': 'bg-success',
        'recordatorio': 'bg-warning',
        'entrega': 'bg-danger',
        'otro': 'bg-secondary'
    }.get(tipo, 'bg-light')