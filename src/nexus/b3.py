"""Composição das carteiras teóricas dos índices da B3.

A B3 expõe as carteiras vigentes por um endpoint que recebe os parâmetros
codificados em base64 na própria URL. Só existe a carteira *do dia* — não há
histórico público por esse caminho, o que é justamente a limitação que nos
força a reconstruir o universo por liquidez (ver
`dados/processados/relatorio_qualidade.md`, seção 4).
"""

from __future__ import annotations

import base64
import json

import pandas as pd
import requests

URL = "https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/GetPortfolioDay/{}"
CABECALHO = {"User-Agent": "Mozilla/5.0"}


def carteira_indice(indice: str, timeout: int = 40) -> pd.DataFrame:
    """Retorna a carteira teórica vigente de um índice da B3.

    Colunas: codigo, empresa, tipo, participacao (%), qtd_teorica, indice.
    """
    parametros = {
        "language": "pt-br",
        "pageNumber": 1,
        "pageSize": 500,
        "index": indice,
        "segment": "1",
    }
    codificado = base64.b64encode(json.dumps(parametros).encode()).decode()
    resposta = requests.get(
        URL.format(codificado), headers=CABECALHO, timeout=timeout, verify=False
    )
    resposta.raise_for_status()
    resultados = resposta.json()["results"]

    def _num(texto: str | None) -> float | None:
        if not texto:
            return None
        return float(texto.replace(".", "").replace(",", "."))

    return pd.DataFrame(
        {
            "codigo": [r["cod"] for r in resultados],
            "empresa": [r["asset"] for r in resultados],
            "tipo": [(r.get("type") or "").strip() for r in resultados],
            "participacao": [_num(r.get("part")) for r in resultados],
            "qtd_teorica": [_num(r.get("theoricalQty")) for r in resultados],
            "indice": indice,
        }
    )
