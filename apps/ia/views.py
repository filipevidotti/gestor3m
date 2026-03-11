from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from apps.core.decorators import consultor_required

from .models import InsightIA


@consultor_required
def listar_insights(request):
    """Lista insights do consultor logado."""
    insights = InsightIA.objects.filter(consultor=request.user, lido=False)
    # Usado principalmente via HTMX no painel Meu Dia
    from django.template.loader import render_to_string
    html = render_to_string("ia/partials/lista_insights.html", {"insights": insights}, request=request)
    return HttpResponse(html)


@consultor_required
def marcar_lido(request, pk):
    """Marca insight como lido (HTMX)."""
    if request.method == "POST":
        insight = get_object_or_404(InsightIA, pk=pk, consultor=request.user)
        insight.lido = True
        insight.save(update_fields=["lido", "updated_at"])
        return HttpResponse("")
    return HttpResponse(status=405)
