"""
Seed dos templates padrao de checklists, diagnostico e conquistas.
Uso: python manage.py seed_templates
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.checklists.models import (
    ChecklistCategory,
    ChecklistTemplate,
    ChecklistTemplateItem,
)
from apps.clientes.models import EtapaPipeline
from apps.diagnosticos.models import DiagnosticTemplate, DiagnosticQuestion
from apps.gamificacao.models import Achievement
from apps.tarefas.models import TipoTarefa

User = get_user_model()


class Command(BaseCommand):
    help = "Cria templates padrao de checklists, diagnostico, conquistas, etapas e tipos"

    def handle(self, *args, **options):
        self.criar_categorias()
        self.criar_checklists()
        self.criar_diagnostico()
        self.criar_conquistas()
        self.criar_etapas_pipeline()
        self.criar_tipos_tarefa()
        self.stdout.write(self.style.SUCCESS("Seed concluido com sucesso!"))

    def criar_categorias(self):
        cats = [
            ("Documentacao", "clipboard-list", 1),
            ("Conta ML", "shopping-bag", 2),
            ("Anuncios", "tag", 3),
            ("Logistica", "truck", 4),
            ("Atendimento", "message-circle", 5),
            ("Financeiro", "dollar-sign", 6),
            ("Marketing", "megaphone", 7),
            ("Embalagem", "package", 8),
            ("Reputacao", "star", 9),
            ("Produtos", "search", 10),
        ]
        for nome, icone, ordem in cats:
            ChecklistCategory.objects.get_or_create(
                nome=nome, defaults={"icone": icone, "ordem": ordem}
            )
        self.stdout.write(f"  {len(cats)} categorias criadas")

    def criar_checklists(self):
        templates_data = [
            {
                "nome": "Onboarding de Novo Cliente",
                "descricao": "Checklist completo para integrar um novo seller a consultoria 3M",
                "target_audience": "consultant",
                "tipo": "onboarding",
                "icone": "user-plus",
                "itens": [
                    ("Documentacao", "Contrato assinado e arquivado", False, True),
                    ("Documentacao", "Dados da empresa coletados (CNPJ, endereco, contatos)", False, False),
                    ("Documentacao", "Acessos ao Mercado Livre recebidos", False, False),
                    ("Conta ML", "Analisar reputacao atual da conta", False, True),
                    ("Conta ML", "Verificar status de vendedor (Mercado Lider, etc)", False, False),
                    ("Conta ML", "Auditar configuracoes da conta (frete, devolucoes)", False, True),
                    ("Anuncios", "Listar top 10 anuncios por faturamento", False, False),
                    ("Anuncios", "Identificar anuncios com problemas de qualidade", False, True),
                    ("Logistica", "Verificar operacao logistica atual", False, True),
                    ("Logistica", "Avaliar prazo de envio medio", False, False),
                    ("Atendimento", "Verificar tempo medio de resposta", False, False),
                    ("Atendimento", "Auditar qualidade das respostas", False, True),
                    ("Financeiro", "Analisar margem atual dos produtos", False, True),
                ],
            },
            {
                "nome": "Primeira Reuniao",
                "descricao": "Itens a cobrir na reuniao inaugural com o seller",
                "target_audience": "consultant",
                "tipo": "avulso",
                "icone": "video",
                "itens": [
                    ("Documentacao", "Apresentar a metodologia 3M", False, False),
                    ("Documentacao", "Definir metas iniciais (30/60/90 dias)", False, True),
                    ("Conta ML", "Mostrar analise inicial da conta", False, False),
                    ("Anuncios", "Apresentar diagnostico dos anuncios", False, False),
                    ("Anuncios", "Definir prioridades de otimizacao", False, True),
                    ("Logistica", "Alinhar expectativas de prazo", False, False),
                    ("Atendimento", "Estabelecer SLA de atendimento", False, True),
                    ("Financeiro", "Revisar precificacao atual", False, False),
                ],
            },
            {
                "nome": "Acompanhamento Mensal",
                "descricao": "Checklist de revisao mensal do seller",
                "target_audience": "consultant",
                "tipo": "recorrente",
                "icone": "calendar",
                "itens": [
                    ("Conta ML", "Verificar evolucao da reputacao", False, True),
                    ("Conta ML", "Analisar metricas de vendas vs mes anterior", False, True),
                    ("Anuncios", "Revisar performance dos top anuncios", False, False),
                    ("Anuncios", "Verificar novos anuncios criados", False, False),
                    ("Logistica", "Avaliar taxa de atraso no envio", False, False),
                    ("Atendimento", "Verificar reclamacoes do periodo", False, True),
                    ("Financeiro", "Analisar faturamento vs meta", False, True),
                    ("Marketing", "Verificar campanhas ativas", False, False),
                ],
            },
            {
                "nome": "Criacao de Anuncio",
                "descricao": "Checklist para o seller criar anuncios de qualidade",
                "target_audience": "client",
                "tipo": "avulso",
                "icone": "file-plus",
                "itens": [
                    ("Anuncios", "Titulo com palavras-chave relevantes (max 60 chars)", False, True),
                    ("Anuncios", "Fotos profissionais (minimo 6 fotos)", True, False),
                    ("Anuncios", "Descricao completa com especificacoes", False, True),
                    ("Anuncios", "Ficha tecnica preenchida (todos os atributos)", False, False),
                    ("Anuncios", "Preco competitivo (pesquisa de concorrencia feita)", False, True),
                    ("Anuncios", "Frete gratis configurado (se aplicavel)", False, False),
                    ("Anuncios", "Variantes cadastradas corretamente", False, False),
                    ("Anuncios", "Video do produto adicionado", True, False),
                ],
            },
            {
                "nome": "Embalagem e Envio",
                "descricao": "Checklist para o seller garantir qualidade no envio",
                "target_audience": "client",
                "tipo": "recorrente",
                "icone": "package",
                "itens": [
                    ("Embalagem", "Caixa em bom estado e tamanho adequado", True, False),
                    ("Embalagem", "Produto com protecao interna (bolha, papel)", True, False),
                    ("Embalagem", "Cartao de agradecimento incluido", False, False),
                    ("Embalagem", "Etiqueta impressa e legivel", True, False),
                    ("Embalagem", "Lacre de seguranca aplicado", False, False),
                    ("Logistica", "Pedido separado dentro do prazo", False, False),
                    ("Logistica", "Coleta ou postagem agendada", False, False),
                ],
            },
            {
                "nome": "Procura de Produtos",
                "descricao": "Checklist para o seller avaliar novos produtos",
                "target_audience": "client",
                "tipo": "avulso",
                "icone": "search",
                "itens": [
                    ("Produtos", "Produto com demanda comprovada no ML", False, True),
                    ("Produtos", "Analise de concorrencia (preco, frete, reputacao)", False, True),
                    ("Produtos", "Fornecedor confiavel identificado", False, False),
                    ("Produtos", "Margem minima de 30% garantida", False, True),
                    ("Produtos", "Produto sem restricao legal (INMETRO, ANVISA)", False, False),
                    ("Produtos", "Peso/dimensao viavel para frete competitivo", False, False),
                    ("Produtos", "Amostra solicitada ou recebida", False, False),
                ],
            },
        ]

        for tpl_data in templates_data:
            tpl, created = ChecklistTemplate.objects.get_or_create(
                nome=tpl_data["nome"],
                defaults={
                    "descricao": tpl_data["descricao"],
                    "target_audience": tpl_data["target_audience"],
                    "tipo": tpl_data["tipo"],
                    "icone": tpl_data["icone"],
                },
            )
            if created:
                for ordem, (cat_nome, descricao, req_evidence, req_note) in enumerate(
                    tpl_data["itens"], start=1
                ):
                    cat = ChecklistCategory.objects.filter(nome=cat_nome).first()
                    ChecklistTemplateItem.objects.create(
                        template=tpl,
                        category=cat,
                        descricao=descricao,
                        ordem=ordem,
                        requires_evidence=req_evidence,
                        requires_note=req_note,
                    )
        self.stdout.write(f"  {len(templates_data)} templates de checklist criados")

    def criar_diagnostico(self):
        tpl, created = DiagnosticTemplate.objects.get_or_create(
            nome="Diagnostico 360 ML",
            defaults={"descricao": "Diagnostico completo do seller no Mercado Livre"},
        )
        if not created:
            self.stdout.write("  Diagnostico 360 ja existe")
            return

        perguntas = [
            # Reputacao
            ("Reputacao", "Nivel de reputacao atual", "scale_1_10", 2, False),
            ("Reputacao", "Taxa de reclamacoes (%)", "value", 2, True),
            ("Reputacao", "Tempo medio de envio (dias)", "value", 1.5, True),
            ("Reputacao", "Taxa de cancelamento (%)", "value", 1.5, True),
            ("Reputacao", "Mediacao favoravel ao vendedor (%)", "value", 1, False),
            # Anuncios
            ("Anuncios", "Qualidade geral dos titulos", "scale_1_10", 2, False),
            ("Anuncios", "Qualidade das fotos", "scale_1_10", 2, False),
            ("Anuncios", "Completude das fichas tecnicas", "scale_1_10", 1.5, False),
            ("Anuncios", "Uso de video nos anuncios", "scale_1_10", 1, False),
            ("Anuncios", "Competitividade de precos", "scale_1_10", 1.5, False),
            # Logistica
            ("Logistica", "Prazo de envio configurado (dias)", "value", 1.5, True),
            ("Logistica", "Frete gratis nos principais anuncios", "scale_1_10", 1.5, False),
            ("Logistica", "Qualidade da embalagem", "scale_1_10", 1, False),
            # Atendimento
            ("Atendimento", "Tempo medio de resposta (horas)", "value", 2, True),
            ("Atendimento", "Qualidade das respostas", "scale_1_10", 1.5, False),
            ("Atendimento", "Uso de respostas pre-definidas", "scale_1_10", 1, False),
            # Financeiro
            ("Financeiro", "Margem media atual (%)", "value", 1.5, False),
            ("Financeiro", "Faturamento mensal (R$)", "value", 1, False),
            ("Financeiro", "Controle de custos organizado", "scale_1_10", 1, False),
            # Marketing
            ("Marketing", "Uso de Mercado Ads", "scale_1_10", 1, False),
            ("Marketing", "Presenca em redes sociais", "scale_1_10", 0.5, False),
        ]

        for ordem, (cat, texto, tipo, weight, inverted) in enumerate(perguntas, start=1):
            DiagnosticQuestion.objects.create(
                template=tpl,
                categoria=cat,
                texto=texto,
                tipo=tipo,
                weight=weight,
                is_inverted=inverted,
                ordem=ordem,
            )
        self.stdout.write(f"  Diagnostico 360 criado com {len(perguntas)} perguntas")

    def criar_conquistas(self):
        conquistas = [
            # Consultores
            ("Primeiro Checklist", "Complete seu primeiro checklist", "bronze", 10, "checklists_concluidos", 1, "consultor"),
            ("Checklist Master", "Complete 10 checklists", "prata", 50, "checklists_concluidos", 10, "consultor"),
            ("Checklist Expert", "Complete 50 checklists", "ouro", 200, "checklists_concluidos", 50, "consultor"),
            ("Checklist Lenda", "Complete 100 checklists", "diamante", 500, "checklists_concluidos", 100, "consultor"),
            # Sellers
            ("Meu Primeiro Passo", "Complete seu primeiro checklist", "bronze", 10, "checklists_concluidos", 1, "seller"),
            ("Comprometido", "Complete 5 checklists", "prata", 30, "checklists_concluidos", 5, "seller"),
            ("Seller Exemplar", "Complete 20 checklists", "ouro", 100, "checklists_concluidos", 20, "seller"),
            # Tarefas (ambos)
            ("Produtivo", "Conclua 10 tarefas", "bronze", 20, "tarefas_concluidas", 10, "ambos"),
            ("Maquina de Tarefas", "Conclua 50 tarefas", "prata", 100, "tarefas_concluidas", 50, "ambos"),
            ("Imparavel", "Conclua 100 tarefas", "ouro", 250, "tarefas_concluidas", 100, "ambos"),
            # Streak
            ("Constancia", "Mantenha 7 dias de sequencia", "bronze", 30, "streak_dias", 7, "ambos"),
            ("Disciplinado", "Mantenha 30 dias de sequencia", "prata", 150, "streak_dias", 30, "ambos"),
            ("Inabalavel", "Mantenha 90 dias de sequencia", "diamante", 500, "streak_dias", 90, "ambos"),
            # Pontos
            ("Iniciante", "Acumule 100 pontos", "bronze", 0, "total_pontos", 100, "ambos"),
            ("Veterano", "Acumule 1000 pontos", "prata", 0, "total_pontos", 1000, "ambos"),
            ("Elite", "Acumule 5000 pontos", "ouro", 0, "total_pontos", 5000, "ambos"),
            ("Lendario", "Acumule 10000 pontos", "diamante", 0, "total_pontos", 10000, "ambos"),
        ]

        for nome, desc, tipo, recomp, campo, valor, publico in conquistas:
            Achievement.objects.get_or_create(
                nome=nome,
                defaults={
                    "descricao": desc,
                    "tipo": tipo,
                    "pontos_recompensa": recomp,
                    "criterio_campo": campo,
                    "criterio_valor": valor,
                    "publico": publico,
                },
            )
        self.stdout.write(f"  {len(conquistas)} conquistas criadas")

    def criar_etapas_pipeline(self):
        etapas = [
            ("Onboarding", "#3b82f6", 1),
            ("Diagnostico", "#8b5cf6", 2),
            ("Treinamento", "#f59e0b", 3),
            ("Acompanhamento", "#10b981", 4),
            ("Full", "#25d366", 5),
        ]
        for nome, cor, ordem in etapas:
            EtapaPipeline.objects.get_or_create(
                nome=nome, defaults={"cor": cor, "ordem": ordem}
            )
        self.stdout.write(f"  {len(etapas)} etapas de pipeline criadas")

    def criar_tipos_tarefa(self):
        tipos = [
            ("Cadastro Anuncios", "tag", "#3b82f6"),
            ("Promocoes", "percent", "#f59e0b"),
            ("Verificar Full", "truck", "#10b981"),
            ("Embalagem", "package", "#8b5cf6"),
            ("Atendimento", "message-circle", "#ec4899"),
            ("Outro", "clipboard", "#6b7280"),
        ]
        for nome, icone, cor in tipos:
            TipoTarefa.objects.get_or_create(
                nome=nome, defaults={"icone": icone, "cor": cor}
            )
        self.stdout.write(f"  {len(tipos)} tipos de tarefa criados")
