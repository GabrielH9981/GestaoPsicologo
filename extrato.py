# -*- coding: utf-8 -*-
import re
import unicodedata
import pandas as pd
import numpy as np
from difflib import SequenceMatcher


def normalize(s):
    """Lowercase + remove acentos + colapsa espaços."""
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode()
    return ' '.join(s.lower().split())


def _find_col(cols, candidates):
    norm = [c.strip().lower() for c in cols]
    for cand in candidates:
        for i, c in enumerate(norm):
            if cand in c:
                return cols[i]
    return None


def _to_float(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip().replace('R$', '').replace(' ', '')
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except Exception:
        return np.nan


def _parse_date(s):
    if pd.isna(s):
        return ''
    txt = str(s).strip()
    fmts = ['%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y %H:%M', '%d/%m/%Y %H:%M:%S']
    for f in fmts:
        try:
            from datetime import datetime
            return datetime.strptime(txt, f).strftime('%d/%m/%Y')
        except Exception:
            pass
    try:
        dt = pd.to_datetime(txt, dayfirst=True, errors='coerce')
        if pd.notna(dt):
            return dt.strftime('%d/%m/%Y')
    except Exception:
        pass
    return ''


def _extract_name(desc):
    """Extrai nome do remetente da descrição do extrato."""
    if pd.isna(desc):
        return ''
    text = ' '.join(str(desc).split())
    pat = re.compile(r'transfer[eê]ncia\s+recebida(?:\s+pelo\s+pix)?\s*[-–]\s*(.*?)\s*[-–]', re.IGNORECASE)
    m = pat.search(text)
    if m:
        name = re.sub(r'[•\u2022]+', '', m.group(1)).strip(' -')
        return ' '.join(name.split())
    return ''


def _similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def processar_csv(file_stream, pacientes_db, dependentes_db):
    """
    Processa o CSV do extrato e tenta vincular cada entrada a um paciente.

    Args:
        file_stream: objeto de arquivo do CSV
        pacientes_db: lista de dicts {'id', 'nome'} dos pacientes cadastrados
        dependentes_db: lista de dicts {'nome_extrato_norm', 'paciente_id', 'paciente_nome'} dos dependentes

    Returns:
        lista de dicts com os resultados agrupados por nome do extrato
    """
    try:
        df = pd.read_csv(file_stream, sep=None, engine='python')
    except Exception:
        file_stream.seek(0)
        df = pd.read_csv(file_stream, sep=';', engine='python')

    cols = list(df.columns)
    date_col = _find_col(cols, ['data', 'data hora', 'datahora', 'date'])
    desc_col = _find_col(cols, ['descrição', 'descricao', 'description', 'histórico', 'historico'])
    value_col = _find_col(cols, ['valor', 'valor líquido', 'valorliquido', 'amount', 'crédito', 'credito'])

    if not value_col or not desc_col:
        raise ValueError('CSV inválido: colunas de valor ou descrição não encontradas.')

    df['_valor'] = df[value_col].apply(_to_float)
    df['_data'] = df[date_col].apply(_parse_date) if date_col else ''
    df['_nome'] = df[desc_col].apply(_extract_name)

    # Filtra só entradas positivas com nome extraído (transferências recebidas de pessoas)
    df_use = df[
        (df['_nome'].str.strip() != '') &
        (df['_valor'].notna()) &
        (df['_valor'] > 0)
    ].copy()

    grp = df_use.groupby('_nome', dropna=False).agg(
        total_valor=('_valor', 'sum'),
        sessoes=('_valor', 'count'),
        ultima_data=('_data', lambda s: max([d for d in s.tolist() if d], default=''))
    ).reset_index().rename(columns={'_nome': 'nome_extrato'})

    # Índices para busca rápida
    dep_index = {d['nome_extrato_norm']: d for d in dependentes_db}
    pac_index = [(normalize(p['nome']), p) for p in pacientes_db]

    resultados = []
    for _, row in grp.iterrows():
        nome_ext = row['nome_extrato']
        nome_norm = normalize(nome_ext)
        total = round(float(row['total_valor']), 2)
        sessoes = int(row['sessoes'])
        data = row['ultima_data']

        paciente_id = None
        paciente_nome = None
        match_tipo = None  # 'dependente', 'exato', 'fuzzy', None

        # 1. Busca em dependentes cadastrados
        if nome_norm in dep_index:
            dep = dep_index[nome_norm]
            paciente_id = dep['paciente_id']
            paciente_nome = dep['paciente_nome']
            match_tipo = 'dependente'
        else:
            # 2. Match exato contra pacientes
            for pac_norm, pac in pac_index:
                if pac_norm == nome_norm:
                    paciente_id = pac['id']
                    paciente_nome = pac['nome']
                    match_tipo = 'exato'
                    break

            # 3. Fuzzy match (threshold 0.82)
            if not paciente_id:
                best_score = 0
                best_pac = None
                for pac_norm, pac in pac_index:
                    score = _similarity(nome_norm, pac_norm)
                    if score > best_score:
                        best_score = score
                        best_pac = pac
                if best_score >= 0.82 and best_pac:
                    paciente_id = best_pac['id']
                    paciente_nome = best_pac['nome']
                    match_tipo = 'fuzzy'

        resultados.append({
            'nome_extrato': nome_ext,
            'nome_extrato_norm': nome_norm,
            'total_valor': total,
            'total_fmt': f"{total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'sessoes': sessoes,
            'ultima_data': data,
            'paciente_id': paciente_id,
            'paciente_nome': paciente_nome,
            'match_tipo': match_tipo,
        })

    return resultados
