import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


def _notificar_multicanal(notificacao, user, cliente=None):
    """Tenta enviar notificação por WhatsApp e e-mail."""
    telefone = ""
    email = ""

    # Busca telefone/email do destinatário ou do cliente associado
    if hasattr(user, "telefone") and user.telefone:
        telefone = user.telefone
    if user.email:
        email = user.email

    # Se for notificação sobre um cliente seller, usa dados do seller
    if cliente and hasattr(cliente, "usuario") and cliente.usuario:
        seller = cliente.usuario
        if seller.telefone:
            telefone = seller.telefone
        if seller.email:
            email = seller.email

    notificacao.enviar_multicanal(telefone=telefone, email=email)


@shared_task
def verificar_tarefas_atrasadas():
    """Tarefas com prazo vencido → marca atrasado + notifica multi-canal."""
    from apps.notificacoes.models import Notificacao
    from apps.tarefas.models import Tarefa

    hoje = timezone.localdate()
    tarefas = Tarefa.objects.filter(
        prazo__lt=hoje,
        status__in=[Tarefa.Status.PENDENTE, Tarefa.Status.EM_ANDAMENTO],
    ).select_related("responsavel", "cliente")

    count = 0
    for tarefa in tarefas:
        tarefa.status = Tarefa.Status.ATRASADO
        tarefa.save(update_fields=["status", "updated_at"])

        ja_notificado = Notificacao.objects.filter(
            destinatario=tarefa.responsavel,
            tipo=Notificacao.Tipo.TAREFA_ATRASADA,
            link__contains=f"/tarefas/{tarefa.pk}/",
            lida=False,
        ).exists()

        if not ja_notificado:
            notif = Notificacao.objects.create(
                destinatario=tarefa.responsavel,
                tipo=Notificacao.Tipo.TAREFA_ATRASADA,
                titulo=f"Tarefa atrasada: {tarefa.descricao[:80]}",
                mensagem=(
                    f"A tarefa do cliente {tarefa.cliente} estava prevista "
                    f"para {tarefa.prazo:%d/%m/%Y} e ainda nao foi concluida."
                ),
                link=f"/tarefas/{tarefa.pk}/",
            )
            _notificar_multicanal(notif, tarefa.responsavel)
            count += 1

    logger.info("verificar_tarefas_atrasadas: %d notificacoes criadas", count)
    return count


@shared_task
def verificar_inadimplencia():
    """Pagamentos atrasados → notifica gestores multi-canal."""
    from apps.accounts.models import User
    from apps.financeiro.models import Pagamento
    from apps.notificacoes.models import Notificacao

    hoje = timezone.localdate()
    pagamentos_pendentes = Pagamento.objects.filter(
        status=Pagamento.Status.PENDENTE,
    ).select_related("contrato__cliente")

    pagamentos_atrasados = []
    for pag in pagamentos_pendentes:
        try:
            dia = min(pag.contrato.dia_vencimento, 28)
            data_vencimento = pag.mes_referencia.replace(day=dia)
        except ValueError:
            data_vencimento = pag.mes_referencia
        if data_vencimento < hoje:
            pagamentos_atrasados.append((pag, data_vencimento))

    if not pagamentos_atrasados:
        return 0

    gestores = User.objects.filter(role=User.Role.GESTOR, is_active=True)
    count = 0

    for pag, data_vencimento in pagamentos_atrasados:
        pag.status = Pagamento.Status.ATRASADO
        pag.save(update_fields=["status", "updated_at"])

        for gestor in gestores:
            ja_notificado = Notificacao.objects.filter(
                destinatario=gestor,
                tipo=Notificacao.Tipo.INADIMPLENCIA,
                link__contains=f"/financeiro/contratos/{pag.contrato.pk}/",
                lida=False,
            ).exists()

            if not ja_notificado:
                notif = Notificacao.objects.create(
                    destinatario=gestor,
                    tipo=Notificacao.Tipo.INADIMPLENCIA,
                    titulo=f"Inadimplencia: {pag.contrato.cliente}",
                    mensagem=(
                        f"O pagamento de {pag.mes_referencia:%m/%Y} do cliente "
                        f"{pag.contrato.cliente} (R$ {pag.valor}) esta atrasado "
                        f"desde {data_vencimento:%d/%m/%Y}."
                    ),
                    link=f"/financeiro/contratos/{pag.contrato.pk}/",
                )
                _notificar_multicanal(notif, gestor)
                count += 1

    logger.info("verificar_inadimplencia: %d notificacoes criadas", count)
    return count


@shared_task
def verificar_clientes_sem_reuniao():
    """Clientes sem reunião há 30+ dias → notifica consultor multi-canal."""
    from django.db.models import Max, Q

    from apps.clientes.models import Cliente
    from apps.notificacoes.models import Notificacao

    hoje = timezone.localdate()
    limite = hoje - timedelta(days=30)

    clientes = (
        Cliente.objects.filter(status__in=["ativo", "onboarding"])
        .annotate(ultima_reuniao=Max("reunioes__data"))
        .filter(Q(ultima_reuniao__isnull=True) | Q(ultima_reuniao__lt=limite))
        .select_related("consultor")
    )

    count = 0
    for cliente in clientes:
        ja_notificado = Notificacao.objects.filter(
            destinatario=cliente.consultor,
            tipo=Notificacao.Tipo.SEM_REUNIAO,
            link__contains=f"/clientes/{cliente.pk}/",
            lida=False,
        ).exists()

        if not ja_notificado:
            if cliente.ultima_reuniao:
                msg = (
                    f"O cliente {cliente} nao tem reuniao ha mais de 30 dias. "
                    f"Ultima reuniao: {cliente.ultima_reuniao:%d/%m/%Y}."
                )
            else:
                msg = f"O cliente {cliente} ainda nao teve nenhuma reuniao registrada."

            notif = Notificacao.objects.create(
                destinatario=cliente.consultor,
                tipo=Notificacao.Tipo.SEM_REUNIAO,
                titulo=f"Sem reuniao: {cliente}",
                mensagem=msg,
                link=f"/clientes/{cliente.pk}/",
            )
            _notificar_multicanal(notif, cliente.consultor)
            count += 1

    logger.info("verificar_clientes_sem_reuniao: %d notificacoes criadas", count)
    return count


@shared_task
def verificar_diagnosticos_pendentes():
    """Clientes sem diagnóstico → notifica consultor multi-canal."""
    from django.db.models import Count

    from apps.clientes.models import Cliente
    from apps.notificacoes.models import Notificacao

    clientes = (
        Cliente.objects.filter(status__in=["ativo", "onboarding"])
        .annotate(total_diagnosticos=Count("diagnosticos"))
        .filter(total_diagnosticos=0)
        .select_related("consultor")
    )

    count = 0
    for cliente in clientes:
        ja_notificado = Notificacao.objects.filter(
            destinatario=cliente.consultor,
            tipo=Notificacao.Tipo.DIAGNOSTICO_PENDENTE,
            link__contains=f"/clientes/{cliente.pk}/",
            lida=False,
        ).exists()

        if not ja_notificado:
            notif = Notificacao.objects.create(
                destinatario=cliente.consultor,
                tipo=Notificacao.Tipo.DIAGNOSTICO_PENDENTE,
                titulo=f"Diagnostico pendente: {cliente}",
                mensagem=(
                    f"O cliente {cliente} ainda nao possui nenhum diagnostico "
                    f"registrado. Agende e realize o diagnostico inicial."
                ),
                link=f"/clientes/{cliente.pk}/",
            )
            _notificar_multicanal(notif, cliente.consultor)
            count += 1

    logger.info("verificar_diagnosticos_pendentes: %d notificacoes criadas", count)
    return count


@shared_task
def lembrete_reuniao_amanha():
    """Lembra consultor e seller de reunião amanhã — sistema + WhatsApp + e-mail."""
    from apps.core.services.evolution import enviar_mensagem
    from apps.notificacoes.models import Notificacao
    from apps.reunioes.models import Reuniao

    amanha = timezone.localdate() + timedelta(days=1)
    inicio = timezone.make_aware(
        timezone.datetime.combine(amanha, timezone.datetime.min.time())
    )
    fim = inicio + timedelta(days=1)

    reunioes = Reuniao.objects.filter(
        data__gte=inicio,
        data__lt=fim,
    ).select_related("cliente", "consultor", "cliente__usuario")

    count = 0
    for reuniao in reunioes:
        # Notifica consultor
        ja_notificado = Notificacao.objects.filter(
            destinatario=reuniao.consultor,
            tipo=Notificacao.Tipo.REUNIAO_MARCADA,
            link__contains=f"/reunioes/{reuniao.pk}/",
            lida=False,
        ).exists()

        if not ja_notificado:
            notif = Notificacao.objects.create(
                destinatario=reuniao.consultor,
                tipo=Notificacao.Tipo.REUNIAO_MARCADA,
                titulo=f"Reuniao amanha: {reuniao.cliente}",
                mensagem=(
                    f"Voce tem uma reuniao de {reuniao.get_tipo_display()} "
                    f"com {reuniao.cliente} amanha as {reuniao.data:%H:%M}."
                ),
                link=f"/reunioes/{reuniao.pk}/",
            )
            _notificar_multicanal(notif, reuniao.consultor)
            count += 1

        # Envia WhatsApp direto pro seller (se tem telefone)
        seller = getattr(reuniao.cliente, "usuario", None)
        if seller and seller.telefone:
            texto = (
                f"Ola {seller.first_name}! 👋\n\n"
                f"Lembrete: amanha ({amanha:%d/%m/%Y}) as {reuniao.data:%H:%M} "
                f"temos uma reuniao de *{reuniao.get_tipo_display()}*.\n\n"
                f"Consultor: {reuniao.consultor.get_full_name()}\n\n"
                f"Ate amanha! 🚀\n_3M Consultoria_"
            )
            enviar_mensagem(seller.telefone, texto)

    logger.info("lembrete_reuniao_amanha: %d notificacoes criadas", count)
    return count


# =============================================
# NOVAS TASKS
# =============================================


@shared_task
def resumo_semanal_seller():
    """Toda segunda-feira: envia resumo da semana pro seller via WhatsApp."""
    from apps.checklists.models import ChecklistExecution
    from apps.clientes.models import Cliente
    from apps.core.services.evolution import enviar_mensagem
    from apps.tarefas.models import Tarefa

    hoje = timezone.localdate()
    inicio_semana = hoje - timedelta(days=7)

    clientes = Cliente.objects.filter(
        status="ativo",
    ).select_related("usuario")

    count = 0
    for cliente in clientes:
        seller = getattr(cliente, "usuario", None)
        if not seller or not seller.telefone:
            continue

        tarefas_concluidas = Tarefa.objects.filter(
            cliente=cliente,
            status="concluido",
            updated_at__date__gte=inicio_semana,
        ).count()
        tarefas_total = Tarefa.objects.filter(
            cliente=cliente,
            status__in=["pendente", "em_andamento", "concluido", "atrasado"],
        ).count()
        checklists_feitos = ChecklistExecution.objects.filter(
            cliente=cliente,
            status="completed",
            updated_at__date__gte=inicio_semana,
        ).count()

        texto = (
            f"Ola {seller.first_name}! 📊\n\n"
            f"*Resumo da semana:*\n"
            f"✅ Tarefas concluidas: {tarefas_concluidas}/{tarefas_total}\n"
            f"📋 Checklists finalizados: {checklists_feitos}\n\n"
        )

        if tarefas_total > 0 and tarefas_concluidas / tarefas_total >= 0.8:
            texto += "Otimo desempenho! Continue assim! 🏆\n"
        elif tarefas_concluidas == 0:
            texto += "Vamos retomar as atividades? Sua evolucao depende de voce! 💪\n"
        else:
            texto += "Bom trabalho! Vamos manter o ritmo! 🚀\n"

        texto += "\n_3M Consultoria_"

        if enviar_mensagem(seller.telefone, texto):
            count += 1

    logger.info("resumo_semanal_seller: %d mensagens enviadas", count)
    return count


@shared_task
def recalcular_benchmarks():
    """Recalcula benchmarks de todos os segmentos (semanal)."""
    from apps.diagnosticos.models import BenchmarkSegmento

    BenchmarkSegmento.recalcular_todos()
    logger.info("recalcular_benchmarks: concluido")


@shared_task
def alerta_plano_atrasado():
    """Verifica itens de plano de ação atrasados e notifica responsável."""
    from apps.notificacoes.models import Notificacao
    from apps.planos.models import ItemPlano

    hoje = timezone.localdate()
    itens = ItemPlano.objects.filter(
        prazo__lt=hoje,
        status__in=["pendente", "em_andamento"],
    ).select_related("plano__cliente", "responsavel")

    count = 0
    for item in itens:
        if not item.responsavel:
            continue

        ja_notificado = Notificacao.objects.filter(
            destinatario=item.responsavel,
            tipo=Notificacao.Tipo.TAREFA_ATRASADA,
            link__contains=f"/planos/{item.plano.pk}/",
            lida=False,
        ).exists()

        if not ja_notificado:
            notif = Notificacao.objects.create(
                destinatario=item.responsavel,
                tipo=Notificacao.Tipo.TAREFA_ATRASADA,
                titulo=f"Plano atrasado: {item.descricao[:60]}",
                mensagem=(
                    f"O item '{item.descricao[:80]}' do plano '{item.plano.titulo}' "
                    f"(cliente {item.plano.cliente}) venceu em {item.prazo:%d/%m/%Y}."
                ),
                link=f"/planos/{item.plano.pk}/",
            )
            _notificar_multicanal(notif, item.responsavel)
            count += 1

    logger.info("alerta_plano_atrasado: %d notificacoes criadas", count)
    return count


@shared_task
def alerta_cliente_parado_pipeline():
    """Clientes na mesma etapa do pipeline há 30+ dias → notifica consultor."""
    from apps.clientes.models import Cliente
    from apps.notificacoes.models import Notificacao

    hoje = timezone.localdate()
    limite = hoje - timedelta(days=30)

    clientes = Cliente.objects.filter(
        status__in=["ativo", "onboarding"],
        etapa__isnull=False,
        updated_at__date__lt=limite,
    ).select_related("consultor", "etapa")

    count = 0
    for cliente in clientes:
        ja_notificado = Notificacao.objects.filter(
            destinatario=cliente.consultor,
            tipo=Notificacao.Tipo.SEM_REUNIAO,
            link__contains=f"/clientes/{cliente.pk}/",
            lida=False,
        ).exists()

        if not ja_notificado:
            notif = Notificacao.objects.create(
                destinatario=cliente.consultor,
                tipo=Notificacao.Tipo.SEM_REUNIAO,
                titulo=f"Cliente parado: {cliente}",
                mensagem=(
                    f"O cliente {cliente} esta na etapa '{cliente.etapa}' "
                    f"ha mais de 30 dias. Considere avançar ou agendar reuniao."
                ),
                link=f"/clientes/{cliente.pk}/",
            )
            _notificar_multicanal(notif, cliente.consultor)
            count += 1

    logger.info("alerta_cliente_parado_pipeline: %d notificacoes criadas", count)
    return count


@shared_task
def gerar_relatorios_mensais():
    """Gera relatórios mensais automaticamente no dia 1 de cada mês (mês anterior)."""
    from django.core.files.base import ContentFile

    from apps.clientes.models import Cliente
    from apps.relatorios.models import RelatorioMensal
    from apps.relatorios.utils import coletar_dados_mensal, gerar_pdf

    hoje = timezone.localdate()
    # Gera do mês anterior
    if hoje.month == 1:
        mes, ano = 12, hoje.year - 1
    else:
        mes, ano = hoje.month - 1, hoje.year

    clientes = Cliente.objects.filter(status="ativo")
    count = 0

    for cliente in clientes:
        rel, created = RelatorioMensal.objects.get_or_create(
            cliente=cliente, mes=mes, ano=ano,
        )
        if not created and rel.arquivo:
            continue  # Já gerado

        dados = coletar_dados_mensal(cliente, mes, ano)
        rel.dados = dados

        pdf = gerar_pdf(dados)
        if pdf:
            filename = f"relatorio_{cliente.empresa}_{mes:02d}_{ano}.pdf"
            rel.arquivo.save(filename, ContentFile(pdf.read()), save=False)

        rel.save()
        count += 1

    logger.info("gerar_relatorios_mensais: %d relatorios gerados", count)
    return count
