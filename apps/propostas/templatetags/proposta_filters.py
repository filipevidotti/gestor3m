import re

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def limpar_md(texto):
    """Remove markdown e converte em HTML com parágrafos."""
    if not texto:
        return ""
    # Converte **bold** em <strong>
    texto = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', texto)
    # Remove *italic*
    texto = re.sub(r'\*(.+?)\*', r'<em>\1</em>', texto)
    # Remove ## headers
    texto = re.sub(r'^#{1,3}\s*(.+)$', r'<strong>\1</strong>', texto, flags=re.MULTILINE)
    # Converte line breaks
    texto = texto.replace('\n', '<br>')
    return mark_safe(texto)
