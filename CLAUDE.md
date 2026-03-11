# 3M Control - Sistema de Gestao de Consultoria

## Projeto
- **Produto**: 3M Control
- **Empresa**: 3M Consultoria (www.3mconsultoria.com.br)
- **Stack**: Django 5.1 + Django Ninja + PostgreSQL + Celery + Redis
- **Frontend**: Tailwind CSS (CDN) + Flowbite + HTMX + Alpine.js + Chart.js
- **Python**: 3.12 | **Virtualenv**: `venv/`

## Comandos Rapidos
```bash
source venv/bin/activate
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
celery -A config worker -l info
```

## Arquitetura

### Estrutura de Diretorio
```
gestor3m/
  config/settings/{base,local,production}.py
  apps/{core,accounts,clientes,consultores,diagnosticos,planos,
        tarefas,checklists,reunioes,treinamentos,financeiro,
        dashboard,notificacoes}/
  templates/{base.html, components/, <app>/}
  static/{css,js,img}
```

### Apps e Responsabilidades
| App | Descricao | Models Principais |
|-----|-----------|-------------------|
| core | BaseModel, ActiveManager, decorators | BaseModel (abstract) |
| accounts | Auth, perfis, roles | User (gestor/consultor/seller) |
| clientes | Gestao de sellers | Cliente, Atividade |
| consultores | Equipe consultoria | Consultor |
| diagnosticos | Diagnostico 360 | Diagnostico (mensal + score) |
| planos | Planos de acao | PlanoAcao, ItemPlano |
| tarefas | Controle execucao | Tarefa |
| checklists | Checklists recorrentes | ChecklistTemplate, ChecklistExecucao, ChecklistItem |
| reunioes | Registro reunioes | Reuniao |
| treinamentos | Biblioteca conteudo | Treinamento, TreinamentoRealizado |
| financeiro | Contratos/pagamentos | Contrato, Pagamento |
| dashboard | Paineis | (sem model proprio) |
| notificacoes | Alertas automaticos | Notificacao |

### Roles e Permissoes
- **Gestor**: acesso total
- **Consultor**: acesso aos seus clientes e tarefas
- **Seller**: acesso ao proprio painel (tarefas, reunioes, treinamentos, evolucao)

### Decorators de Permissao (apps/core/decorators.py)
- `@gestor_required` - Apenas gestor
- `@consultor_required` - Gestor + consultor
- `@seller_required` - Todos autenticados
- `@role_required("gestor", "consultor")` - Custom

## Padroes de Codigo

### Models
- Todos herdam de `BaseModel` (created_at, updated_at, is_active)
- Usar `ActiveManager` como manager default quando precisar de soft delete
- TextChoices para campos com opcoes fixas
- db_table explicita, verbose_name em pt-BR

### Views
- Function-Based Views (FBV) com decorators
- Filtrar queryset por role do usuario
- Usar `select_related` e `prefetch_related`
- Retornar partials HTMX quando `request.htmx`

### Templates
- Estender `base.html` (layout com sidebar)
- Componentes reutilizaveis em `templates/components/`
- HTMX para interacoes sem reload
- Alpine.js para estado local (toggles, tabs)

### URLs
- Cada app tem `app_name` definido
- URLs para sub-recursos: `<app>/cliente/<int:cliente_pk>/`
- Nomes consistentes: listar, detalhe, criar, editar, excluir

### API (Django Ninja)
- Definir routers em `apps/<app>/api.py`
- Registrar no `config/api.py`
- Schemas em `apps/<app>/schemas.py`

## Design System - 3M Control

### Marca
- Gradiente oficial: `linear-gradient(135deg, #8C103C, #D83341, #FE8103)`
- Logos em `static/img/`: logo-branca.png (dark), logo-preta.png (light), logo-original.png
- Dark/Light mode com toggle (Alpine.js + localStorage, dark por padrao)

### Cores da Marca
- Brand Dark: #8C103C (vinho)
- Brand Red: #D83341 (vermelho)
- Brand Orange: #FE8103 (laranja — CTA principal)

### Cores do Sistema
- Primary-500: #FE8103 (alias do brand-orange para CTAs)
- Dark: #0F172A (fundo dark mode)
- Dark-100: #1E293B (cards dark mode)
- Dark-200: #334155 (bordas/hover dark mode)
- Danger: #EF4444
- Warning: #FE8103
- Success: #22C55E

### Dark/Light Mode
- Body: `bg-gray-50 dark:bg-dark`
- Cards: `bg-white dark:bg-dark-100`
- Bordas: `border-gray-200 dark:border-gray-700/50`
- Texto titulo: `text-gray-900 dark:text-white`
- Texto corpo: `text-gray-700 dark:text-gray-200`
- Texto secundario: `text-gray-500 dark:text-gray-400`
- Inputs: `bg-gray-50 dark:bg-dark border-gray-200 dark:border-gray-700`

### Fontes
- Headings: Red Hat Display (bold/extrabold)
- Body: Inter (regular/medium)

### Componentes
- Cards: `bg-white dark:bg-dark-100 rounded-xl border border-gray-200 dark:border-gray-700/50`
- Botoes primarios: `bg-brand-orange hover:bg-brand-orange/90 text-white rounded-lg`
- Botao gradiente: `bg-gradient-to-r from-brand-dark via-brand-red to-brand-orange`
- Inputs: `bg-gray-50 dark:bg-dark border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-brand-orange`
- Status badges: `rounded-full px-2.5 py-0.5 text-xs font-medium`
- Link ativo sidebar: `bg-brand-orange/10 text-brand-orange`

## Skills Disponiveis

### Workflow
- `/brainstorm` - Design antes de codar (features novas, 4+ arquivos)
- `/plan` - Criar plano de implementacao
- `/verify` - Verificacao de qualidade

### Desenvolvimento
- `agente-frontend` - Templates Tailwind+HTMX+Flowbite
- `agente-testes` - Testes de models, views, permissoes
- `agente-revisor` - Revisao de codigo

### Design
- `designer-3m` - Design system da 3M Consultoria
- `ui-ux-pro-max` - Design intelligence avancado
- `code-review` - Revisao de seguranca e qualidade

### Meta
- `skill-creator` - Criar novos skills (TDD)
- `using-superpowers` - Guia do sistema de skills
