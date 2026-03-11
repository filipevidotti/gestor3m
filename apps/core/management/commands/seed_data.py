"""
Popula o banco com dados ficticios para demonstracao.
Cria usuarios (gestor, consultores, sellers), clientes, tarefas,
diagnosticos, planos, reunioes, checklists, contratos, notificacoes, etc.

Uso: python manage.py seed_data
Para limpar e recriar: python manage.py seed_data --reset
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.clientes.models import Cliente, Atividade, EtapaPipeline
from apps.consultores.models import Consultor
from apps.diagnosticos.models import (
    DiagnosticTemplate, Diagnostic, DiagnosticAnswer,
)
from apps.planos.models import PlanoAcao, ItemPlano
from apps.tarefas.models import Tarefa, TipoTarefa
from apps.checklists.models import (
    ChecklistTemplate, ChecklistExecution, ChecklistExecutionItem,
)
from apps.reunioes.models import Reuniao
from apps.treinamentos.models import Treinamento, TreinamentoRealizado
from apps.financeiro.models import Contrato, Pagamento
from apps.notificacoes.models import Notificacao
from apps.gamificacao.models import Score, Streak

User = get_user_model()
now = timezone.now()


class Command(BaseCommand):
    help = "Popula o banco com dados ficticios para demonstracao"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Limpa dados ficticios antes de recriar",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write(self.style.WARNING("Limpando dados ficticios..."))
            self._limpar()

        self.stdout.write("Criando dados ficticios...")
        self._criar_usuarios()
        self._criar_clientes()
        self._criar_treinamentos()
        self._criar_tarefas()
        self._criar_diagnosticos()
        self._criar_planos()
        self._criar_reunioes()
        self._criar_checklists()
        self._criar_contratos()
        self._criar_notificacoes()
        self._criar_atividades()
        self._criar_scores()
        self.stdout.write(self.style.SUCCESS("\nSeed de dados concluido com sucesso!"))
        self._imprimir_credenciais()

    # ── Limpeza ────────────────────────────────────────────
    def _limpar(self):
        Score.objects.all().delete()
        Streak.objects.all().delete()
        Notificacao.objects.all().delete()
        Pagamento.objects.all().delete()
        Contrato.objects.all().delete()
        TreinamentoRealizado.objects.all().delete()
        Treinamento.objects.all().delete()
        ChecklistExecutionItem.objects.all().delete()
        ChecklistExecution.objects.all().delete()
        DiagnosticAnswer.objects.all().delete()
        Diagnostic.objects.all().delete()
        ItemPlano.objects.all().delete()
        PlanoAcao.objects.all().delete()
        Reuniao.objects.all().delete()
        Tarefa.objects.all().delete()
        Atividade.objects.all().delete()
        Cliente.all_objects.all().delete()
        Consultor.objects.all().delete()
        User.objects.filter(username__in=[
            "admin", "consultor1", "consultor2",
            "seller1", "seller2", "seller3", "seller4",
            "seller5", "seller6", "seller7", "seller8",
        ]).delete()
        self.stdout.write("  Dados limpos.")

    # ── Usuarios ───────────────────────────────────────────
    def _criar_usuarios(self):
        # Gestor (admin)
        self.gestor, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@3mconsultoria.com.br",
                "first_name": "Carlos",
                "last_name": "Mendes",
                "role": "gestor",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        self.gestor.set_password("admin123")
        self.gestor.save()

        # Consultores
        consultores_data = [
            ("consultor1", "Fernanda", "Oliveira", "fernanda@3mconsultoria.com.br"),
            ("consultor2", "Rafael", "Santos", "rafael@3mconsultoria.com.br"),
        ]
        self.consultores_users = []
        self.consultores = []
        for username, first, last, email in consultores_data:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first,
                    "last_name": last,
                    "role": "consultor",
                },
            )
            user.set_password("consultor123")
            user.save()
            self.consultores_users.append(user)

            consultor, _ = Consultor.objects.get_or_create(
                usuario=user,
                defaults={
                    "especialidade": random.choice([
                        "Vendas e Ads no Mercado Livre",
                        "Logistica Full e Reputacao",
                    ]),
                    "bio": f"Consultora especialista com 5 anos de experiencia" if first == "Fernanda"
                    else "Consultor focado em crescimento de sellers",
                    "max_clientes": 8,
                },
            )
            self.consultores.append(consultor)

        # Sellers
        sellers_data = [
            ("seller1", "Joao", "Silva", "joao@techstore.com.br"),
            ("seller2", "Maria", "Costa", "maria@modafeminina.com.br"),
            ("seller3", "Pedro", "Almeida", "pedro@casainteligente.com.br"),
            ("seller4", "Ana", "Ferreira", "ana@petshopml.com.br"),
            ("seller5", "Lucas", "Rocha", "lucas@autoparts.com.br"),
            ("seller6", "Juliana", "Martins", "juliana@belezanatural.com.br"),
            ("seller7", "Bruno", "Souza", "bruno@esportemania.com.br"),
            ("seller8", "Camila", "Lima", "camila@brinquedoskids.com.br"),
        ]
        self.sellers = []
        for username, first, last, email in sellers_data:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first,
                    "last_name": last,
                    "role": "seller",
                },
            )
            user.set_password("seller123")
            user.save()
            self.sellers.append(user)

        self.stdout.write(f"  {1 + len(consultores_data) + len(sellers_data)} usuarios criados")

    # ── Clientes ───────────────────────────────────────────
    def _criar_clientes(self):
        etapas = list(EtapaPipeline.objects.all().order_by("ordem"))
        if not etapas:
            self.stdout.write(self.style.WARNING(
                "  Sem etapas de pipeline. Rode seed_templates primeiro!"
            ))

        clientes_data = [
            {
                "empresa": "TechStore Brasil",
                "cnpj": "12.345.678/0001-90",
                "nicho": "Eletronicos",
                "telefone": "(11) 99876-5432",
                "email": "contato@techstore.com.br",
                "ml_nickname": "TECHSTORE_BR",
                "ml_seller_id": "123456789",
                "ml_reputacao": "MercadoLider Gold",
                "tipo_consultoria": "estrategica",
                "status": "ativo",
                "etapa_idx": 4,
                "consultor_idx": 0,
                "seller_idx": 0,
            },
            {
                "empresa": "Moda Feminina ML",
                "cnpj": "23.456.789/0001-01",
                "nicho": "Moda Feminina",
                "telefone": "(21) 98765-4321",
                "email": "contato@modafeminina.com.br",
                "ml_nickname": "MODAFEM_OFICIAL",
                "ml_seller_id": "234567890",
                "ml_reputacao": "MercadoLider",
                "tipo_consultoria": "estrategica",
                "status": "ativo",
                "etapa_idx": 3,
                "consultor_idx": 0,
                "seller_idx": 1,
            },
            {
                "empresa": "Casa Inteligente",
                "cnpj": "34.567.890/0001-12",
                "nicho": "Casa e Decoracao",
                "telefone": "(31) 97654-3210",
                "email": "pedro@casainteligente.com.br",
                "ml_nickname": "CASAINTELIGENTE",
                "ml_seller_id": "345678901",
                "ml_reputacao": "Verde",
                "tipo_consultoria": "operacional",
                "status": "ativo",
                "etapa_idx": 2,
                "consultor_idx": 0,
                "seller_idx": 2,
            },
            {
                "empresa": "PetShop Amigo Fiel",
                "cnpj": "45.678.901/0001-23",
                "nicho": "Pet Shop",
                "telefone": "(41) 96543-2109",
                "email": "ana@petshopml.com.br",
                "ml_nickname": "PETAMIGOFIEL",
                "ml_seller_id": "456789012",
                "ml_reputacao": "MercadoLider",
                "tipo_consultoria": "operacional",
                "status": "ativo",
                "etapa_idx": 3,
                "consultor_idx": 1,
                "seller_idx": 3,
            },
            {
                "empresa": "AutoParts Express",
                "cnpj": "56.789.012/0001-34",
                "nicho": "Autopecas",
                "telefone": "(51) 95432-1098",
                "email": "lucas@autoparts.com.br",
                "ml_nickname": "AUTOPARTS_EXP",
                "ml_seller_id": "567890123",
                "ml_reputacao": "Amarelo",
                "tipo_consultoria": "estrategica",
                "status": "onboarding",
                "etapa_idx": 0,
                "consultor_idx": 1,
                "seller_idx": 4,
            },
            {
                "empresa": "Beleza Natural Cosmeticos",
                "cnpj": "67.890.123/0001-45",
                "nicho": "Beleza e Cosmeticos",
                "telefone": "(61) 94321-0987",
                "email": "juliana@belezanatural.com.br",
                "ml_nickname": "BELEZANATURAL_ML",
                "ml_seller_id": "678901234",
                "ml_reputacao": "MercadoLider Platinum",
                "tipo_consultoria": "estrategica",
                "status": "ativo",
                "etapa_idx": 4,
                "consultor_idx": 1,
                "seller_idx": 5,
            },
            {
                "empresa": "EsporteMania Store",
                "cnpj": "78.901.234/0001-56",
                "nicho": "Esportes e Fitness",
                "telefone": "(71) 93210-9876",
                "email": "bruno@esportemania.com.br",
                "ml_nickname": "ESPORTEMANIA",
                "ml_seller_id": "789012345",
                "ml_reputacao": "Verde",
                "tipo_consultoria": "operacional",
                "status": "pausado",
                "etapa_idx": 2,
                "consultor_idx": 0,
                "seller_idx": 6,
            },
            {
                "empresa": "Brinquedos Kids Fun",
                "cnpj": "89.012.345/0001-67",
                "nicho": "Brinquedos",
                "telefone": "(81) 92109-8765",
                "email": "camila@brinquedoskids.com.br",
                "ml_nickname": "KIDSFUN_ML",
                "ml_seller_id": "890123456",
                "ml_reputacao": "MercadoLider",
                "tipo_consultoria": "operacional",
                "status": "ativo",
                "etapa_idx": 3,
                "consultor_idx": 1,
                "seller_idx": 7,
            },
        ]

        self.clientes = []
        for c in clientes_data:
            etapa = etapas[c["etapa_idx"]] if etapas and c["etapa_idx"] < len(etapas) else None
            cliente, _ = Cliente.objects.get_or_create(
                empresa=c["empresa"],
                defaults={
                    "cnpj": c["cnpj"],
                    "nicho": c["nicho"],
                    "telefone": c["telefone"],
                    "email": c["email"],
                    "ml_nickname": c["ml_nickname"],
                    "ml_seller_id": c["ml_seller_id"],
                    "ml_reputacao": c["ml_reputacao"],
                    "consultor": self.consultores_users[c["consultor_idx"]],
                    "tipo_consultoria": c["tipo_consultoria"],
                    "data_inicio": now.date() - timedelta(days=random.randint(30, 365)),
                    "status": c["status"],
                    "etapa": etapa,
                    "usuario": self.sellers[c["seller_idx"]],
                },
            )
            self.clientes.append(cliente)

        self.stdout.write(f"  {len(self.clientes)} clientes criados")

    # ── Treinamentos ───────────────────────────────────────
    def _criar_treinamentos(self):
        treinamentos_data = [
            ("Otimizacao de Titulos no ML", "seo", "Aprenda a criar titulos que vendem", 45),
            ("Mercado Ads do Zero", "ads", "Configuracao e estrategia de campanhas", 60),
            ("Logistica Full Completa", "full", "Como ativar e operar com Full", 90),
            ("Gestao de Reputacao", "reputacao", "Proteja e melhore sua reputacao", 40),
            ("Catalogo de Produtos", "catalogo", "Ficha tecnica e atributos perfeitos", 35),
            ("Estrategias de Vendas", "vendas", "Tecnicas de conversao e precificacao", 50),
            ("Fotografia de Produtos", "outro", "Fotos que convertem vendas", 30),
            ("Atendimento ao Cliente", "outro", "SAC eficiente no Mercado Livre", 25),
        ]

        self.treinamentos = []
        for titulo, cat, desc, duracao in treinamentos_data:
            t, _ = Treinamento.objects.get_or_create(
                titulo=titulo,
                defaults={
                    "categoria": cat,
                    "descricao": desc,
                    "duracao_minutos": duracao,
                    "conteudo_url": "https://www.youtube.com/watch?v=exemplo",
                },
            )
            self.treinamentos.append(t)

        # Treinamentos realizados
        count = 0
        for cliente in self.clientes:
            if cliente.status in ("ativo", "pausado"):
                qtd = random.randint(2, 5)
                treinos = random.sample(self.treinamentos, min(qtd, len(self.treinamentos)))
                for treino in treinos:
                    TreinamentoRealizado.objects.get_or_create(
                        treinamento=treino,
                        cliente=cliente,
                        defaults={
                            "data": now.date() - timedelta(days=random.randint(5, 120)),
                            "observacoes": "Seller demonstrou bom entendimento do conteudo.",
                        },
                    )
                    count += 1

        self.stdout.write(f"  {len(self.treinamentos)} treinamentos + {count} realizados")

    # ── Tarefas ────────────────────────────────────────────
    def _criar_tarefas(self):
        tipos = list(TipoTarefa.objects.all())
        descricoes = [
            "Otimizar titulos dos 5 anuncios mais vendidos",
            "Responder perguntas pendentes no ML",
            "Configurar frete gratis para anuncios acima de R$79",
            "Atualizar fotos dos produtos com baixa conversao",
            "Criar campanha de Mercado Ads para Black Friday",
            "Verificar estoque e repor produtos esgotados",
            "Analisar concorrentes do nicho",
            "Preparar relatorio semanal de vendas",
            "Configurar variantes nos anuncios principais",
            "Responder reclamacoes abertas no ML",
            "Cadastrar novos produtos no catalogo",
            "Revisar precificacao vs concorrencia",
            "Empacotar pedidos do dia com cartao de agradecimento",
            "Verificar status de envio dos pedidos Full",
            "Criar descricoes detalhadas para novos anuncios",
            "Agendar coleta com transportadora",
            "Auditar qualidade das embalagens",
            "Verificar prazo de postagem dos pedidos atrasados",
            "Analisar metricas de conversao da semana",
            "Testar novo layout de anuncio",
        ]

        statuses = ["pendente", "em_andamento", "concluido", "atrasado"]
        prioridades = ["baixa", "media", "alta", "urgente"]
        count = 0

        for cliente in self.clientes:
            if cliente.status == "encerrado":
                continue
            qtd = random.randint(3, 6)
            for _ in range(qtd):
                status = random.choices(statuses, weights=[30, 25, 35, 10])[0]
                Tarefa.objects.create(
                    cliente=cliente,
                    criado_por=cliente.consultor,
                    responsavel=random.choice([cliente.consultor, cliente.usuario]) if cliente.usuario else cliente.consultor,
                    tipo=random.choice(tipos) if tipos else None,
                    descricao=random.choice(descricoes),
                    prioridade=random.choice(prioridades),
                    prazo=now.date() + timedelta(days=random.randint(-10, 30)),
                    status=status,
                    concluido_em=now - timedelta(days=random.randint(0, 5)) if status == "concluido" else None,
                )
                count += 1

        self.stdout.write(f"  {count} tarefas criadas")

    # ── Diagnosticos ───────────────────────────────────────
    def _criar_diagnosticos(self):
        template = DiagnosticTemplate.objects.filter(nome="Diagnostico 360 ML").first()
        if not template:
            self.stdout.write(self.style.WARNING(
                "  Template de diagnostico nao encontrado. Rode seed_templates primeiro!"
            ))
            return

        perguntas = list(template.perguntas.all().order_by("ordem"))
        count = 0

        for cliente in self.clientes:
            if cliente.status not in ("ativo", "pausado"):
                continue
            # 2-3 meses de diagnostico
            for months_ago in range(random.randint(1, 3)):
                dt = now - timedelta(days=30 * months_ago)
                mes, ano = dt.month, dt.year

                diag, created = Diagnostic.objects.get_or_create(
                    cliente=cliente,
                    mes=mes,
                    ano=ano,
                    template=template,
                    defaults={
                        "executor": cliente.consultor,
                        "status": "completed" if months_ago > 0 else random.choice(["completed", "in_progress"]),
                        "completed_at": dt if months_ago > 0 else None,
                    },
                )
                if created:
                    scores_cat = {}
                    for pergunta in perguntas:
                        if pergunta.tipo == "scale_1_10":
                            val = round(random.uniform(3, 9.5), 1)
                        else:
                            val = round(random.uniform(1, 100), 1)

                        answer = DiagnosticAnswer.objects.create(
                            diagnostic=diag,
                            question=pergunta,
                            value_numeric=Decimal(str(val)),
                        )
                        answer.calcular_score()
                        answer.save()

                        cat = pergunta.categoria
                        if cat not in scores_cat:
                            scores_cat[cat] = []
                        scores_cat[cat].append(float(answer.score))

                    diag.scores_por_categoria = {
                        cat: round(sum(vals) / len(vals), 1)
                        for cat, vals in scores_cat.items()
                    }
                    diag.calcular_score()
                    diag.save()
                    count += 1

        self.stdout.write(f"  {count} diagnosticos criados")

    # ── Planos de Acao ─────────────────────────────────────
    def _criar_planos(self):
        planos_data = [
            ("Plano Estrategico Q1 2026", "estrategico", [
                "Aumentar faturamento em 30% ate marco",
                "Atingir Mercado Lider Gold",
                "Reduzir taxa de reclamacao para < 1%",
                "Implementar Mercado Ads em todos os top anuncios",
                "Treinar equipe em atendimento ao cliente",
            ]),
            ("Plano Semanal - Otimizacao", "semanal", [
                "Otimizar 10 titulos de anuncios",
                "Atualizar fotos de 5 produtos",
                "Responder todas as perguntas pendentes",
                "Revisar precos dos concorrentes",
            ]),
            ("Acoes Diarias - Rotina ML", "diario", [
                "Verificar pedidos e envios pendentes",
                "Responder perguntas e mensagens",
                "Monitorar reputacao e reclamacoes",
            ]),
        ]

        statuses = ["pendente", "em_andamento", "concluido"]
        prioridades = ["baixa", "media", "alta", "urgente"]
        count = 0

        for cliente in self.clientes:
            if cliente.status not in ("ativo",):
                continue
            for titulo, tipo, itens_desc in planos_data:
                plano, created = PlanoAcao.objects.get_or_create(
                    cliente=cliente,
                    titulo=titulo,
                    defaults={
                        "tipo": tipo,
                        "descricao": f"Plano {tipo} para {cliente.empresa}",
                    },
                )
                if created:
                    for desc in itens_desc:
                        ItemPlano.objects.create(
                            plano=plano,
                            descricao=desc,
                            responsavel=random.choice([cliente.consultor, self.gestor]),
                            prioridade=random.choice(prioridades),
                            prazo=now.date() + timedelta(days=random.randint(-5, 45)),
                            status=random.choices(statuses, weights=[25, 35, 40])[0],
                        )
                    count += 1

        self.stdout.write(f"  {count} planos de acao criados")

    # ── Reunioes ───────────────────────────────────────────
    def _criar_reunioes(self):
        tipos = ["diagnostico", "treinamento_full", "treinamento_reputacao",
                 "treinamento_ads", "revisao_mensal", "outro"]
        resumos = [
            "Seller apresentou boa evolucao nas metricas. Definimos proximos passos para otimizacao de anuncios.",
            "Revisamos a reputacao e criamos plano para reduzir reclamacoes. Meta: abaixo de 1% no proximo mes.",
            "Treinamento de Mercado Ads concluido. Seller conseguiu configurar 3 campanhas durante a reuniao.",
            "Diagnostico inicial realizado. Principais pontos de melhoria: fotos, titulos e frete.",
            "Revisao mensal positiva. Faturamento subiu 22% em relacao ao mes anterior.",
            "Alinhamento sobre logistica Full. Seller vai testar com 10 produtos piloto.",
        ]
        count = 0

        for cliente in self.clientes:
            if cliente.status == "encerrado":
                continue
            qtd = random.randint(2, 5)
            for i in range(qtd):
                days_ago = random.randint(1, 90)
                Reuniao.objects.create(
                    cliente=cliente,
                    tipo=random.choice(tipos),
                    data=now - timedelta(days=days_ago, hours=random.randint(0, 8)),
                    duracao_minutos=random.choice([30, 45, 60, 90]),
                    consultor=cliente.consultor,
                    participantes=f"{cliente.consultor.get_full_name()}, {cliente.empresa}",
                    resumo=random.choice(resumos),
                    proximos_passos="1. Implementar acoes combinadas\n2. Acompanhar metricas semanalmente\n3. Agendar proxima reuniao",
                )
                count += 1

        self.stdout.write(f"  {count} reunioes criadas")

    # ── Checklists ─────────────────────────────────────────
    def _criar_checklists(self):
        templates = list(ChecklistTemplate.objects.all())
        if not templates:
            self.stdout.write(self.style.WARNING(
                "  Sem templates de checklist. Rode seed_templates primeiro!"
            ))
            return

        status_choices = ["pending", "conforming", "non_conforming", "not_applicable"]
        count = 0

        for cliente in self.clientes:
            if cliente.status not in ("ativo", "pausado"):
                continue
            qtd = random.randint(1, 3)
            for tpl in random.sample(templates, min(qtd, len(templates))):
                exec_status = random.choice(["completed", "in_progress", "pending"])
                execution, created = ChecklistExecution.objects.get_or_create(
                    template=tpl,
                    cliente=cliente,
                    defaults={
                        "executor": cliente.consultor,
                        "status": exec_status,
                        "started_at": now - timedelta(days=random.randint(1, 30)),
                        "completed_at": now - timedelta(days=random.randint(0, 5)) if exec_status == "completed" else None,
                    },
                )
                if created:
                    tpl_items = list(tpl.itens.all())
                    for item in tpl_items:
                        item_status = random.choices(
                            status_choices,
                            weights=[10, 60, 20, 10],
                        )[0]
                        if exec_status == "pending":
                            item_status = "pending"
                        ChecklistExecutionItem.objects.create(
                            execution=execution,
                            template_item=item,
                            status=item_status,
                            note="Verificado e aprovado" if item_status == "conforming" else "",
                            completed_at=now if item_status != "pending" else None,
                            completed_by=cliente.consultor if item_status != "pending" else None,
                        )
                    if exec_status == "completed":
                        execution.calcular_score()
                        execution.save()
                    count += 1

        self.stdout.write(f"  {count} execucoes de checklist criadas")

    # ── Contratos e Pagamentos ─────────────────────────────
    def _criar_contratos(self):
        planos_contrato = [
            ("Consultoria Estrategica Premium", Decimal("2500.00")),
            ("Consultoria Estrategica", Decimal("1800.00")),
            ("Consultoria Operacional", Decimal("1200.00")),
            ("Consultoria Operacional Basica", Decimal("800.00")),
        ]
        count_c = 0
        count_p = 0

        for cliente in self.clientes:
            if cliente.tipo_consultoria == "estrategica":
                plano_nome, valor = random.choice(planos_contrato[:2])
            else:
                plano_nome, valor = random.choice(planos_contrato[2:])

            contrato, created = Contrato.objects.get_or_create(
                cliente=cliente,
                defaults={
                    "plano": plano_nome,
                    "valor": valor,
                    "dia_vencimento": random.choice([5, 10, 15, 20]),
                    "data_inicio": cliente.data_inicio,
                    "observacoes": "Contrato padrao de consultoria 3M.",
                },
            )
            if created:
                count_c += 1
                # Gerar 3-6 meses de pagamentos
                meses = random.randint(3, 6)
                for m in range(meses):
                    mes_ref = now.date().replace(day=1) - timedelta(days=30 * m)
                    status_pag = random.choices(
                        ["pago", "pendente", "atrasado"],
                        weights=[70, 20, 10],
                    )[0]
                    if m == 0:
                        status_pag = random.choice(["pendente", "pago"])

                    Pagamento.objects.create(
                        contrato=contrato,
                        mes_referencia=mes_ref,
                        valor=valor,
                        status=status_pag,
                        data_pagamento=mes_ref + timedelta(days=random.randint(1, 15)) if status_pag == "pago" else None,
                    )
                    count_p += 1

        self.stdout.write(f"  {count_c} contratos + {count_p} pagamentos criados")

    # ── Notificacoes ───────────────────────────────────────
    def _criar_notificacoes(self):
        notifs = [
            ("tarefa_atrasada", "Tarefa atrasada", "A tarefa 'Otimizar titulos' esta atrasada ha 3 dias."),
            ("inadimplencia", "Pagamento pendente", "O cliente TechStore Brasil esta com pagamento de Fev/2026 pendente."),
            ("reuniao_marcada", "Reuniao agendada", "Reuniao de revisao mensal com Moda Feminina ML amanha as 14h."),
            ("diagnostico_pendente", "Diagnostico pendente", "O diagnostico de Marco/2026 de Casa Inteligente ainda nao foi iniciado."),
            ("sem_reuniao", "Sem reuniao recente", "O cliente PetShop Amigo Fiel nao tem reuniao ha mais de 30 dias."),
            ("geral", "Bem-vindo ao 3M Control", "Seu acesso ao sistema foi configurado. Explore o dashboard!"),
        ]

        count = 0
        all_users = [self.gestor] + self.consultores_users + self.sellers
        for user in all_users:
            qtd = random.randint(1, 4)
            for _ in range(qtd):
                tipo, titulo, msg = random.choice(notifs)
                Notificacao.objects.create(
                    destinatario=user,
                    tipo=tipo,
                    titulo=titulo,
                    mensagem=msg,
                    lida=random.choice([True, False]),
                )
                count += 1

        self.stdout.write(f"  {count} notificacoes criadas")

    # ── Atividades (log) ───────────────────────────────────
    def _criar_atividades(self):
        descricoes_ativ = [
            "Realizou reuniao de alinhamento com o seller",
            "Otimizou 5 titulos de anuncios",
            "Configurou campanha de Mercado Ads",
            "Analisou metricas de reputacao",
            "Criou plano de acao semanal",
            "Enviou relatorio mensal ao seller",
            "Treinou seller sobre logistica Full",
            "Revisou precificacao dos produtos",
            "Identificou 3 novos produtos para catalogo",
            "Resolveu reclamacao critica do cliente",
        ]
        count = 0
        for cliente in self.clientes:
            qtd = random.randint(3, 8)
            for _ in range(qtd):
                Atividade.objects.create(
                    cliente=cliente,
                    descricao=random.choice(descricoes_ativ),
                    autor=cliente.consultor,
                )
                count += 1

        self.stdout.write(f"  {count} atividades registradas")

    # ── Gamificacao (scores) ───────────────────────────────
    def _criar_scores(self):
        categorias = ["checklist", "diagnostico", "tarefa", "reuniao", "bonus"]
        count = 0

        for user in self.consultores_users + self.sellers:
            qtd = random.randint(5, 15)
            for _ in range(qtd):
                Score.objects.create(
                    usuario=user,
                    pontos=random.randint(5, 50),
                    categoria=random.choice(categorias),
                    descricao=f"Pontos por atividade concluida",
                )
                count += 1

            Streak.objects.get_or_create(
                usuario=user,
                defaults={
                    "dias_consecutivos": random.randint(0, 30),
                    "maior_sequencia": random.randint(5, 45),
                    "ultimo_dia": now.date() - timedelta(days=random.randint(0, 3)),
                },
            )

        self.stdout.write(f"  {count} scores + streaks criados")

    # ── Credenciais ────────────────────────────────────────
    def _imprimir_credenciais(self):
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("CREDENCIAIS DE ACESSO"))
        self.stdout.write("=" * 50)
        self.stdout.write(f"\n{'Tipo':<15} {'Usuario':<15} {'Senha':<15} {'Nome'}")
        self.stdout.write("-" * 60)
        self.stdout.write(f"{'GESTOR':<15} {'admin':<15} {'admin123':<15} Carlos Mendes")
        self.stdout.write(f"{'CONSULTOR':<15} {'consultor1':<15} {'consultor123':<15} Fernanda Oliveira")
        self.stdout.write(f"{'CONSULTOR':<15} {'consultor2':<15} {'consultor123':<15} Rafael Santos")
        self.stdout.write(f"{'SELLER':<15} {'seller1':<15} {'seller123':<15} Joao Silva")
        self.stdout.write(f"{'SELLER':<15} {'seller2':<15} {'seller123':<15} Maria Costa")
        self.stdout.write(f"{'SELLER':<15} {'seller3':<15} {'seller123':<15} Pedro Almeida")
        self.stdout.write(f"{'SELLER':<15} {'seller4':<15} {'seller123':<15} Ana Ferreira")
        self.stdout.write(f"{'SELLER':<15} {'seller5':<15} {'seller123':<15} Lucas Rocha")
        self.stdout.write(f"{'SELLER':<15} {'seller6':<15} {'seller123':<15} Juliana Martins")
        self.stdout.write(f"{'SELLER':<15} {'seller7':<15} {'seller123':<15} Bruno Souza")
        self.stdout.write(f"{'SELLER':<15} {'seller8':<15} {'seller123':<15} Camila Lima")
        self.stdout.write("=" * 50)
