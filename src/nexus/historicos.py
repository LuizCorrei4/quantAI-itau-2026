"""Candidatos históricos: tickers que negociaram na B3 entre 2012 e 2026 e que
não constam mais nas carteiras vigentes dos índices.

Esta lista é uma *hipótese a ser testada*, não uma verdade. Cada código é
submetido ao yfinance pelo script `01_universo.py`; o que não retornar dados é
descartado e registrado. Um palpite errado custa apenas uma requisição.

A coluna `sucessor` registra a empresa que herdou o histórico (fusão, troca de
ticker ou incorporação). Descoberta empírica relevante: o Yahoo Finance
*reescreve* o histórico sob o ticker novo, então casos de rename não são buraco
de dados — só as deslistagens sem sucessora é que são.
"""

from __future__ import annotations

import pandas as pd

# (codigo, nome, motivo_saida, sucessor)
_REGISTROS: list[tuple[str, str, str, str | None]] = [
    # --- Deslistagens efetivas (empresa deixou a bolsa, sem sucessora negociável) ---
    ("CRUZ3", "Souza Cruz", "fechamento de capital (OPA British American Tobacco, 2015)", None),
    ("CIEL3", "Cielo", "fechamento de capital (2024)", None),
    ("ENBR3", "EDP Brasil", "fechamento de capital (OPA EDP, 2023)", None),
    ("ELPL4", "Eletropaulo", "aquisição pela Enel e deslistagem (2018)", None),
    ("ELPL3", "Eletropaulo ON", "aquisição pela Enel e deslistagem (2018)", None),
    ("MPLU3", "Multiplus", "incorporada pela LATAM (2019)", None),
    ("LINX3", "Linx", "aquisição pela StoneCo (2021)", None),
    ("BRPR3", "BR Properties", "venda de ativos e deslistagem (2022)", None),
    ("SQIA3", "Sinqia", "aquisição pela Evertec (2023)", None),
    ("TAMM4", "TAM", "fusão LATAM e deslistagem (2016)", None),
    ("NETC4", "Net Serviços", "fechamento de capital (2015)", None),
    ("CTIP3", "Cetip", "incorporada pela BM&FBovespa (2017)", None),
    ("ALLL3", "ALL Logística", "incorporada pela Rumo (2015)", None),
    ("FIBR3", "Fibria", "incorporada pela Suzano (2019)", None),
    ("SMLE3", "Smiles", "incorporada pela GOL (2021)", None),
    ("BISA3", "Brookfield Incorporações", "fechamento de capital (2015)", None),
    ("ABRE11", "Abril Educação", "virou Somos Educação, adquirida (2018)", None),
    ("SSBR3", "Sonae Sierra Brasil", "fechamento de capital (2018)", None),
    ("PRML3", "Prumo Logística", "fechamento de capital (2018)", None),
    ("MAGG3", "Magnesita", "fusão com RHI (2017)", None),
    ("BKBR3", "Burger King Brasil", "virou Zamp", "ZAMP3"),
    ("MOSI3", "Mosaico", "adquirida pelo Méliuz (2021)", None),
    ("SULA11", "SulAmérica", "incorporada pela Rede D'Or (2022)", "RDOR3"),
    ("GNDI3", "Notre Dame Intermédica", "incorporada pela Hapvida (2022)", "HAPV3"),
    ("BIDI11", "Banco Inter units", "migração para Nasdaq via BDR (2022)", "INBR32"),
    ("BIDI4", "Banco Inter PN", "migração para Nasdaq via BDR (2022)", "INBR32"),
    ("CESP6", "CESP", "virou Auren Energia (2022)", "AURE3"),
    ("CESP3", "CESP ON", "virou Auren Energia (2022)", "AURE3"),
    ("IGTA3", "Iguatemi", "reorganização societária (2021)", "IGTI11"),
    ("QGEP3", "Queiroz Galvão E&P", "virou Enauta", "ENAT3"),
    ("ENAT3", "Enauta", "fusão com 3R e virou Brava (2024)", "BRAV3"),
    ("RRRP3", "3R Petroleum", "fusão com Enauta e virou Brava (2024)", "BRAV3"),
    ("AESB3", "AES Brasil", "aquisição pela Auren (2024)", "AURE3"),
    ("TIET11", "AES Tietê units", "virou AES Brasil (2020)", "AESB3"),
    ("GETI4", "AES Tietê PN", "reorganização (2018)", "AESB3"),
    ("GETI3", "AES Tietê ON", "reorganização (2018)", "AESB3"),
    # --- Recuperações judiciais / colapsos do ciclo 2012-2016 ---
    ("OGXP3", "OGX Petróleo", "recuperação judicial", "OGXP3"),
    ("MMXM3", "MMX Mineração", "recuperação judicial", None),
    ("LLXL3", "LLX Logística", "virou Prumo", "PRML3"),
    ("PDGR3", "PDG Realty", "recuperação judicial", None),
    ("LUPA3", "Lupatech", "recuperação judicial", None),
    ("RSID3", "Rossi Residencial", "reestruturação", None),
    ("TCSA3", "Tecnisa", "permanece listada", None),
    ("VIVR3", "Viver Incorporadora", "recuperação judicial", None),
    ("CTAX3", "Contax", "reestruturação, virou Liq", "LIQO3"),
    ("INEP4", "Inepar", "recuperação judicial", None),
    ("PMAM3", "Paranapanema", "recuperação judicial", None),
    ("ETER3", "Eternit", "recuperação judicial (2018-2020)", None),
    # --- Trocas de ticker / reorganizações (histórico deve estar no sucessor) ---
    ("BTOW3", "B2W Digital", "fusão com Lojas Americanas (2021)", "AMER3"),
    ("LAME3", "Lojas Americanas ON", "reorganização Americanas (2021)", "AMER3"),
    ("LAME4", "Lojas Americanas PN", "reorganização Americanas (2021)", "AMER3"),
    ("VVAR3", "Via Varejo", "virou Via, depois Casas Bahia", "BHIA3"),
    ("VVAR11", "Via Varejo units", "unificação de classes", "BHIA3"),
    ("VIIA3", "Via", "virou Grupo Casas Bahia (2023)", "BHIA3"),
    ("KROT3", "Kroton", "virou Cogna (2019)", "COGN3"),
    ("ESTC3", "Estácio", "virou Yduqs (2020)", "YDUQ3"),
    ("HGTX3", "Cia Hering", "incorporada pelo Grupo Soma (2021)", "AZZA3"),
    ("SOMA3", "Grupo Soma", "fusão com Arezzo (2024)", "AZZA3"),
    ("ARZZ3", "Arezzo", "fusão com Soma, virou Azzas (2024)", "AZZA3"),
    ("BRML3", "BR Malls", "fusão com Aliansce Sonae (2022)", "ALOS3"),
    ("ALSC3", "Aliansce Shopping", "fusão com Sonae (2019)", "ALOS3"),
    ("ALSO3", "Aliansce Sonae", "fusão com BR Malls (2022)", "ALOS3"),
    ("LCAM3", "Unidas (Loc. Américas)", "incorporada pela Localiza (2022)", "RENT3"),
    ("PCAR4", "Pão de Açúcar PN", "unificação de classes (2020)", "PCAR3"),
    ("BVMF3", "BM&FBovespa", "virou B3 (2017)", "B3SA3"),
    ("SUZB5", "Suzano PNA", "unificação de classes (2017)", "SUZB3"),
    ("NATU3", "Natura", "reorganização Natura&Co (2019)", "NTCO3"),
    ("TIMP3", "TIM Participações", "reorganização (2020)", "TIMS3"),
    ("VIVT4", "Telefônica Brasil PN", "unificação de classes (2021)", "VIVT3"),
    ("BRDT3", "Petrobras Distribuidora", "virou Vibra Energia (2021)", "VBBR3"),
    ("CCRO3", "CCR", "virou Motiva (2025)", "MOTV3"),
    ("DTEX3", "Duratex", "virou Dexco (2021)", "DXCO3"),
    ("HRTP3", "HRT Participações", "virou PetroRio/PRIO", "PRIO3"),
    ("MPXE3", "MPX Energia", "virou Eneva (2014)", "ENEV3"),
    ("TRPL4", "ISA CTEEP PN", "virou ISA Energia (2024)", "ISAE4"),
    ("TRPL3", "ISA CTEEP ON", "virou ISA Energia (2024)", "ISAE3"),
    ("CARD3", "CSU CardSystem", "virou CSU Digital", "CSUD3"),
    ("JSLG3", "JSL", "reorganização Simpar (2020)", "SIMH3"),
    # --- Membros históricos do IBOV que perderam liquidez / saíram do índice ---
    ("DASA3", "Dasa", "saiu do índice", None),
    ("CGAS5", "Comgás", "saiu do índice", None),
    ("LIGT3", "Light", "recuperação judicial (2023)", None),
    ("CPFE3", "CPFL Energia", "baixo free float após OPA", None),
    ("EMAE4", "EMAE", "baixa liquidez", None),
    ("CLSC4", "Celesc", "baixa liquidez", None),
    ("COCE5", "Coelce", "baixa liquidez", None),
    ("CMIG3", "Cemig ON", "classe menos líquida", None),
    ("CPLE3", "Copel ON", "classe menos líquida", None),
    ("CPLE5", "Copel PNA", "classe descontinuada", None),
    ("USIM3", "Usiminas ON", "classe menos líquida", None),
    ("GOAU3", "Metalúrgica Gerdau ON", "classe menos líquida", None),
    ("RAPT3", "Randon ON", "classe menos líquida", None),
    ("ALPA3", "Alpargatas ON", "classe menos líquida", None),
    ("POMO3", "Marcopolo ON", "classe menos líquida", None),
    ("OIBR3", "Oi ON", "recuperação judicial", None),
    ("OIBR4", "Oi PN", "recuperação judicial", None),
    ("ELET6", "Eletrobras PNB", "classe menos líquida", None),
    ("MRVE3", "MRV", "permanece listada", None),
    ("GFSA3", "Gafisa", "permanece listada", None),
    ("MILS3", "Mills", "permanece listada", None),
    ("IDNT3", "Ideiasnet", "baixa liquidez", None),
    ("TPIS3", "Triunfo", "baixa liquidez", None),
    ("MEAL3", "IMC / Intl Meal Company", "baixa liquidez", None),
    ("AMAR3", "Marisa Lojas", "reestruturação", None),
    ("SEDU3", "Somos Educação", "adquirida pela Kroton (2018)", None),
    ("TCNO4", "Tecnosolo", "baixa liquidez", None),
    ("CRDE3", "CR2 Empreendimentos", "baixa liquidez", None),
    ("FHER3", "Fertilizantes Heringer", "recuperação judicial", None),
    ("GPCP3", "GPC Participações", "baixa liquidez", None),
    ("SGPS3", "Springs Global", "baixa liquidez", None),
    ("TLPP4", "Telesp", "reorganização Telefônica", "VIVT3"),
    ("TNLP4", "Telemar Norte Leste", "reorganização Oi", "OIBR4"),
    ("TMAR5", "Telemar", "reorganização Oi", "OIBR4"),
    ("CMET4", "Caemi Metalurgia", "incorporada pela Vale", "VALE3"),
]


def candidatos_historicos() -> pd.DataFrame:
    """Tabela de candidatos históricos com motivo de saída e sucessor mapeado."""
    return pd.DataFrame(
        _REGISTROS, columns=["codigo", "empresa", "motivo_saida", "sucessor"]
    ).drop_duplicates(subset="codigo", keep="first")
