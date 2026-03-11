"""Utilitários para parsing de planilhas de anúncios."""

import csv
import io
from decimal import Decimal, InvalidOperation

import openpyxl


def _parse_decimal(value):
    """Converte valor para Decimal, tratando formatos BR."""
    if value is None or str(value).strip() in ("", "-"):
        return Decimal("0")
    s = str(value).strip()
    # Remove R$ e espaços
    s = s.replace("R$", "").replace(" ", "")
    # Se tem ponto e vírgula, formato BR: 1.234,56
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _parse_int(value):
    """Converte valor para int."""
    if value is None or str(value).strip() in ("", "-"):
        return 0
    s = str(value).strip().replace(".", "").replace(",", "")
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return 0


def _str(value):
    """Converte valor para string limpa."""
    if value is None:
        return ""
    return str(value).strip()


def _read_spreadsheet(file_obj):
    """Lê arquivo CSV ou XLSX e retorna lista de dicts."""
    name = file_obj.name.lower()
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return _read_xlsx(file_obj)
    return _read_csv(file_obj)


def _read_xlsx(file_obj):
    """Lê XLSX e retorna lista de dicts."""
    wb = openpyxl.load_workbook(file_obj, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [_str(h).lower() for h in rows[0]]
    result = []
    for row in rows[1:]:
        if not any(row):
            continue
        result.append(dict(zip(headers, row)))
    wb.close()
    return result


def _read_csv(file_obj):
    """Lê CSV e retorna lista de dicts."""
    content = file_obj.read()
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content), delimiter=";")
    result = []
    for row in reader:
        cleaned = {k.strip().lower(): v for k, v in row.items() if k}
        result.append(cleaned)
    return result


# ─── Mapeamento Curva ABC ─────────────────────────────────

# Mapeamento flexível de nomes de coluna
ABC_COLUMN_MAP = {
    "classe": ["classe"],
    "mlb": ["mlb"],
    "sku": ["sku"],
    "titulo": ["título", "titulo"],
    "marca": ["marca"],
    "status": ["status"],
    "tipo": ["tipo"],
    "catalogo": ["catálogo", "catalogo", "cat."],
    "logistica": ["logística", "logistica"],
    "estoque": ["estoque"],
    "preco_atual": ["preço atual", "preco atual", "preço atu", "preco atu", "preço", "preco"],
    "quantidade": ["quantidade", "quantidac", "qtd"],
    "ticket_medio": ["ticket médio", "ticket medio", "ticket méc", "ticket med"],
    "faturamento": ["faturamento", "faturamen"],
    "margem": ["margem"],
    "percentual_total": ["% do total", "% do tota", "% total"],
    "percentual_acumulado": ["% acumulado", "% acumula", "% acum"],
}

METRICAS_COLUMN_MAP = {
    "mlb": ["mlb"],
    "status": ["status"],
    "geral": ["geral"],
    "vendas_30d": ["v.30d", "v30d", "vendas 30d", "vendas30d"],
    "visitas": ["visitas"],
    "conversao": ["conv.", "conv", "conversão", "conversao"],
    "avaliacao": ["aval.", "aval", "avaliação", "avaliacao"],
    "preco": ["preço", "preco"],
    "categoria": ["cat.", "cat", "categoria"],
    "video": ["víd.", "vid.", "vid", "vídeo", "video"],
    "foto": ["fot.", "fot", "foto"],
    "frete": ["frete"],
    "ads": ["ads"],
    "promo": ["promo"],
}

ATUALIZACOES_COLUMN_MAP = {
    "mlb": ["mlb"],
    "titulo": ["título", "titulo"],
    "precisa_foto": ["precisa foto", "foto"],
    "precisa_video": ["precisa vídeo", "precisa video", "vídeo", "video"],
}


def _find_column(row_dict, candidates):
    """Encontra o valor em um dict usando lista de nomes candidatos."""
    for candidate in candidates:
        for key, value in row_dict.items():
            if key.strip().lower() == candidate.strip().lower():
                return value
    return None


def parse_curva_abc(file_obj):
    """Parse planilha de Curva ABC e retorna lista de dicts normalizados."""
    rows = _read_spreadsheet(file_obj)
    result = []
    for row in rows:
        mlb = _str(_find_column(row, ABC_COLUMN_MAP["mlb"]))
        if not mlb:
            continue
        result.append({
            "classe": _str(_find_column(row, ABC_COLUMN_MAP["classe"])),
            "mlb": mlb,
            "sku": _str(_find_column(row, ABC_COLUMN_MAP["sku"])),
            "titulo": _str(_find_column(row, ABC_COLUMN_MAP["titulo"])),
            "marca": _str(_find_column(row, ABC_COLUMN_MAP["marca"])),
            "status": _str(_find_column(row, ABC_COLUMN_MAP["status"])),
            "tipo": _str(_find_column(row, ABC_COLUMN_MAP["tipo"])),
            "catalogo": _str(_find_column(row, ABC_COLUMN_MAP["catalogo"])),
            "logistica": _str(_find_column(row, ABC_COLUMN_MAP["logistica"])),
            "estoque": _parse_int(_find_column(row, ABC_COLUMN_MAP["estoque"])),
            "preco_atual": _parse_decimal(_find_column(row, ABC_COLUMN_MAP["preco_atual"])),
            "quantidade": _parse_int(_find_column(row, ABC_COLUMN_MAP["quantidade"])),
            "ticket_medio": _parse_decimal(_find_column(row, ABC_COLUMN_MAP["ticket_medio"])),
            "faturamento": _parse_decimal(_find_column(row, ABC_COLUMN_MAP["faturamento"])),
            "margem": _parse_decimal(_find_column(row, ABC_COLUMN_MAP["margem"])),
            "percentual_total": _parse_decimal(_find_column(row, ABC_COLUMN_MAP["percentual_total"])),
            "percentual_acumulado": _parse_decimal(_find_column(row, ABC_COLUMN_MAP["percentual_acumulado"])),
        })
    return result


def parse_metricas(file_obj):
    """Parse planilha de Métricas e retorna lista de dicts normalizados."""
    rows = _read_spreadsheet(file_obj)
    result = []
    for row in rows:
        mlb = _str(_find_column(row, METRICAS_COLUMN_MAP["mlb"]))
        if not mlb:
            continue
        result.append({
            "mlb": mlb,
            "status": _str(_find_column(row, METRICAS_COLUMN_MAP["status"])),
            "geral": _parse_int(_find_column(row, METRICAS_COLUMN_MAP["geral"])),
            "vendas_30d": _parse_int(_find_column(row, METRICAS_COLUMN_MAP["vendas_30d"])),
            "visitas": _parse_int(_find_column(row, METRICAS_COLUMN_MAP["visitas"])),
            "conversao": _parse_decimal(_find_column(row, METRICAS_COLUMN_MAP["conversao"])),
            "avaliacao": _parse_int(_find_column(row, METRICAS_COLUMN_MAP["avaliacao"])),
            "preco": _parse_decimal(_find_column(row, METRICAS_COLUMN_MAP["preco"])),
            "categoria": _str(_find_column(row, METRICAS_COLUMN_MAP["categoria"])),
            "video": _str(_find_column(row, METRICAS_COLUMN_MAP["video"])),
            "foto": _str(_find_column(row, METRICAS_COLUMN_MAP["foto"])),
            "frete": _str(_find_column(row, METRICAS_COLUMN_MAP["frete"])),
            "ads": _str(_find_column(row, METRICAS_COLUMN_MAP["ads"])),
            "promo": _str(_find_column(row, METRICAS_COLUMN_MAP["promo"])),
        })
    return result


def parse_atualizacoes(file_obj):
    """Parse planilha de anúncios para atualizar."""
    rows = _read_spreadsheet(file_obj)
    result = []
    for row in rows:
        mlb = _str(_find_column(row, ATUALIZACOES_COLUMN_MAP["mlb"]))
        if not mlb:
            continue
        foto_val = _str(_find_column(row, ATUALIZACOES_COLUMN_MAP["precisa_foto"]))
        video_val = _str(_find_column(row, ATUALIZACOES_COLUMN_MAP["precisa_video"]))
        result.append({
            "mlb": mlb,
            "titulo": _str(_find_column(row, ATUALIZACOES_COLUMN_MAP["titulo"])),
            "precisa_foto": foto_val.lower() in ("sim", "s", "yes", "y", "1", "true", "x"),
            "precisa_video": video_val.lower() in ("sim", "s", "yes", "y", "1", "true", "x"),
        })
    return result
