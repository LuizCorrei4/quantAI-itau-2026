"""
Módulo de Grafos (MST) do Robô Nexus.
Responsável por transformar séries de retornos em árvores geradoras mínimas
e calcular as métricas topológicas (Farness e Distância Média).
"""

import numpy as np
import pandas as pd
import networkx as nx
from sklearn.covariance import LedoitWolf

def calcular_matriz_correlacao(retornos: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula a matriz de correlação estabilizada (Shrinkage Ledoit-Wolf).
    
    Remove dias com NaN para fechar o painel, aplica o algoritmo que encolhe 
    ruídos amostrais e devolve a matriz de correlação no intervalo [-1, 1].
    """
    # 1. Garante que todos os dias têm dados para todas as ações
    ret_limpo = retornos.dropna(axis=0, how='any')
    if len(ret_limpo) < 10:
        # Fallback defensivo: se a queda de NaNs destruir a amostra
        ret_limpo = retornos.fillna(0)
        
    # 2. Motor de covariância encolhida
    lw = LedoitWolf()
    cov_matrix = lw.fit(ret_limpo).covariance_
    
    # 3. Transforma covariância em correlação dividindo pela volatilidade
    vols = np.sqrt(np.diag(cov_matrix))
    corr_matrix = cov_matrix / np.outer(vols, vols)
    
    # 4. Trava limites matemáticos contra erros de ponto flutuante
    corr_matrix = np.clip(corr_matrix, -1.0, 1.0)
    
    return pd.DataFrame(corr_matrix, index=retornos.columns, columns=retornos.columns)


def correlacao_para_distancia(corr: pd.DataFrame) -> pd.DataFrame:
    """
    Converte a matriz de correlação de Pearson na métrica geométrica de Mantegna.
    Fórmula: D = sqrt( 2 * (1 - rho) )
    """
    dist_matrix = np.sqrt(2.0 * (1.0 - corr))
    return pd.DataFrame(dist_matrix, index=corr.columns, columns=corr.columns)


def construir_mst(dist_matrix: pd.DataFrame) -> nx.Graph:
    """
    Transforma a matriz de distâncias na Minimum Spanning Tree (MST).
    Retorna a variável contendo o grafo da MST.
    """

    # transformando a matriz de distâncias em um grafo
    grafo = nx.from_pandas_adjacency(dist_matrix)

    # construindo a MST
    mst = nx.minimum_spanning_tree(grafo, weight='weight')

    return mst


def calcular_farness(mst: nx.Graph) -> pd.Series:
    """
    Calcula a Soma das Distâncias (Farness) para cada nó da MST.
    """
    # obtendo todas as distâncias de forma rápida
    caminhos = dict(nx.shortest_path_length(mst, weight='weight'))
    # calculando a soma das distâncias para cada nó
    farness = {}
    for no in mst.nodes():
        farness[no] = sum(caminhos[no].values())
    # retornando o resultado como uma Series do pandas
    return pd.Series(farness)


def calcular_distancia_media_mst(mst: nx.Graph) -> float:
    """
    Calcula a média de todos os pesos (galhos) da MST.
    """
    # pegando a lista de galhos e pesos da MST, retorna tuplas do tipo: (NóA, NóB, {'weight': 0.85})
    galhos = mst.edges(data=True)
    # extraindo apenas os números de 'weight' e jogando numa lista
    pesos = []
    for _, _, dados in galhos:
        pesos.append(dados['weight'])
    # se a lista não estiver vazia, retorna a média dela ()`np.mean`). Se a árvore quebrar e vier sem galhos, retorna 0.0 por segurança.
    if pesos:
        return np.mean(pesos)
    else:
        return 0.0

