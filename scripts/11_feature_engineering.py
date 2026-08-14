"""
===============================================================================
PROJETO NEXUS - DESAFIO ITAÚ ASSET QUANT AI 2026
Módulo de Engenharia de Features para Machine Learning (Direcionalidade Alpha)
Arquivo: scripts/11_feature_engineering.py
===============================================================================

OBJETIVO DO SCRIPT:
-------------------
Este script prepara a base de treinamento e inferência ('features_ml.parquet')
para os modelos de Machine Learning que atuam na Camada 3 de Convicção Direcional
da arquitetura em Cascata (MST -> Momentum -> Machine Learning).

CORREÇÃO DE ALINHAMENTO TEMPORAL (P4 - Rigor Anti Look-Ahead Bias):
------------------------------------------------------------------
- As features (indicadores técnicos, métricas de momento, volatilidade e grafo)
  são estritamente extraídas no dia T-1 (o último dia de negociação estritamente
  anterior à data de rebalanceamento T).
- O target ('target_direcao') mede a rentabilidade futura da ação durante a vigência
  da carteira, isto é, entre o dia do rebalanceamento T e o próximo rebalanceamento T+1:
      Target = 1 se (Preco[T+1] / Preco[T]) - 1 > 0 senão 0.
- Dessa forma, o algoritmo de Machine Learning aprende a mapear as condições
  conhecidas no fechamento de T-1 para a direção do ativo ao longo de [T, T+1],
  eliminando qualquer possibilidade de data leakage temporal.
===============================================================================
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Inserção do diretório raiz do projeto no path para permitir importações de src.nexus
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.nexus import config


def calcular_rsi(serie_precos: pd.Series, janela: int = 14) -> pd.Series:
    """
    Calcula o Índice de Força Relativa (RSI - Relative Strength Index) clássico de Wilder.
    
    O RSI oscila entre 0 e 100 e mede a velocidade e a magnitude dos movimentos
    direcionais de preços recentes para avaliar condições de sobrecompra ou sobrevenda.
    
    Fórmula:
        RS = Média Exponencial dos Ganhos / Média Exponencial das Perdas
        RSI = 100 - (100 / (1 + RS))
        
    Args:
        serie_precos (pd.Series): Série temporal contínua de preços de fechamento ajustados.
        janela (int): Janela de observação em pregões (padrão de mercado = 14 dias).
        
    Returns:
        pd.Series: Série contínua com os valores de RSI calculados.
    """
    # 1. Variação diária nos preços
    delta = serie_precos.diff()
    
    # 2. Segmentação em variações positivas (ganhos) e negativas (perdas)
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
    
    # 3. Suavização exponencial das séries de ganhos e perdas (método clássico de Wilder)
    media_ganho = ganho.ewm(com=janela - 1, min_periods=janela).mean()
    media_perda = perda.ewm(com=janela - 1, min_periods=janela).mean()
    
    # 4. Cálculo da Razão de Força Relativa (RS)
    rs = media_ganho / media_perda
    
    # 5. Normalização do RSI na escala [0, 100]
    rsi = 100 - (100 / (1 + rs))
    return rsi


def main():
    print("=" * 80)
    print("  PROJETO NEXUS - EXTRAÇÃO E ENGENHARIA DE FEATURES DE MACHINE LEARNING")
    print("  (Alinhamento Temporal Estrito T-1 vs [T, T+1] - Rigor Metodológico)")
    print("=" * 80)
    
    # -------------------------------------------------------------------------
    # 1. Carregamento dos Datasets Históricos Processados
    # -------------------------------------------------------------------------
    print("\n[1/4] Carregando bases de dados estruturadas...")
    caminho_precos = config.PROCESSADOS / "precos_ajustados.parquet"
    caminho_universo = config.PROCESSADOS / "universo_mensal.parquet"
    
    precos = pd.read_parquet(caminho_precos)
    universo = pd.read_parquet(caminho_universo)
    
    print(f" -> Histórico de preços: {precos.shape[0]} pregões x {precos.shape[1]} ativos.")
    print(f" -> Universo mensal elegível: {len(universo)} registros de ações elegíveis.")
    
    # Tentativa de carregamento das métricas de Farness geradas na esteira topológica
    caminho_farness = config.RESULTADOS / "farness_completa.parquet"
    if caminho_farness.exists():
        df_farness = pd.read_parquet(caminho_farness)
        print(f" -> Base de Farness da MST carregada: {len(df_farness)} observações topológicas.")
    else:
        df_farness = None
        print(" -> [AVISO]: 'farness_completa.parquet' não encontrada. Farness será omitida ou imputada.")

    # Obtenção cronológica de todas as datas de rebalanceamento mensal
    datas_rebalanceamento = sorted(universo['data_rebalanceamento'].unique())
    print(f" -> Total de datas de rebalanceamento identificadas: {len(datas_rebalanceamento)} meses.")
    
    # -------------------------------------------------------------------------
    # 2. Pré-Cálculo Vetorizado dos Indicadores Contínuos
    # -------------------------------------------------------------------------
    print("\n[2/4] Pré-calculando indicadores técnicos e estatísticos contínuos...")
    
    # Retornos diários contínuos (usados para volatilidade)
    retornos_diarios = precos.pct_change()
    
    # Médias Móveis Simples (SMA) de médio (50d) e longo (200d) prazo
    sma_50 = precos.rolling(window=50).mean()
    sma_200 = precos.rolling(window=200).mean()
    
    # Volatilidade local anualizada (janela de 21 dias úteis ~ 1 mês de pregão)
    volatilidade_21 = retornos_diarios.rolling(window=21).std() * np.sqrt(252)
    
    # Retornos acumulados de curto prazo (5 dias ~ 1 semana) e médio prazo (21 dias ~ 1 mês)
    retorno_5d = precos.pct_change(periods=5)
    retorno_21d = precos.pct_change(periods=21)
    
    # Índice de Força Relativa (14 períodos) aplicado individualmente para cada ativo
    print(" -> Calculando RSI de 14 períodos para todo o universo...")
    rsi_14 = precos.apply(calcular_rsi, janela=14)
    
    # -------------------------------------------------------------------------
    # 3. Construção do Dataset de Painel Mensal (Alinhamento T-1 e Target [T, T+1])
    # -------------------------------------------------------------------------
    print("\n[3/4] Montando painel mensal com alinhamento temporal estrito...")
    
    dataset_linhas = []
    
    for i, data_atual in enumerate(datas_rebalanceamento):
        # Não é possível computar o target para o último rebalanceamento disponível na base
        if i == len(datas_rebalanceamento) - 1:
            break
            
        data_prox = datas_rebalanceamento[i + 1]
        
        # Identificação das ações elegíveis na data de rebalanceamento atual
        ativos_elegiveis = universo[universo['data_rebalanceamento'] == data_atual]['ticker'].tolist()
        
        # Obtenção do último pregão efetivamente encerrado ANTES da data de rebalanceamento (T-1)
        idx_historico_antes = precos.index[precos.index < data_atual]
        if len(idx_historico_antes) == 0:
            # Caso não haja pregões anteriores suficientes
            continue
        ultimo_dia_antes = idx_historico_antes[-1]
        
        # Iteração sobre os ativos elegíveis
        for ticker in ativos_elegiveis:
            # Validação de integridade: o ativo precisa ter cotação no dia do rebalanceamento T e no próximo T+1
            if ticker not in precos.columns:
                continue
                
            preco_hoje = precos.loc[data_atual, ticker]
            preco_futuro = precos.loc[data_prox, ticker]
            
            # Se houver NaN nos preços de execução, descartamos
            if pd.isna(preco_hoje) or pd.isna(preco_futuro) or preco_hoje <= 0:
                continue
                
            # Cotação em T-1 para cálculo das distâncias e indicadores
            preco_t_menos_1 = precos.loc[ultimo_dia_antes, ticker]
            if pd.isna(preco_t_menos_1) or preco_t_menos_1 <= 0:
                continue
                
            # -----------------------------------------------------------------
            # TARGET: Rentabilidade no período de vigência da carteira [T, T+1]
            # -----------------------------------------------------------------
            retorno_real_mes = (preco_futuro / preco_hoje) - 1.0
            alvo_binario = 1 if retorno_real_mes > 0 else 0
            
            # -----------------------------------------------------------------
            # FEATURES: Todas extraídas estritamente no tempo T-1
            # -----------------------------------------------------------------
            # 1. Distância percentual para a Média Móvel de 50 dias em T-1
            val_sma50 = sma_50.loc[ultimo_dia_antes, ticker]
            dist_sma50 = (preco_t_menos_1 / val_sma50) - 1.0 if not pd.isna(val_sma50) and val_sma50 > 0 else np.nan
            
            # 2. Distância percentual para a Média Móvel de 200 dias em T-1
            val_sma200 = sma_200.loc[ultimo_dia_antes, ticker]
            dist_sma200 = (preco_t_menos_1 / val_sma200) - 1.0 if not pd.isna(val_sma200) and val_sma200 > 0 else np.nan
            
            # 3. Volatilidade local anualizada em T-1
            val_vol = volatilidade_21.loc[ultimo_dia_antes, ticker]
            
            # 4. RSI (14 dias) em T-1
            val_rsi = rsi_14.loc[ultimo_dia_antes, ticker]
            
            # 5. Momentum ultracurto (5 dias) em T-1
            val_ret5 = retorno_5d.loc[ultimo_dia_antes, ticker]
            
            # 6. Momentum curto (21 dias) em T-1
            val_ret21 = retorno_21d.loc[ultimo_dia_antes, ticker]
            
            # 7. Métrica Topológica: Farness na MST calculada até T-1
            val_farness = np.nan
            if df_farness is not None:
                filtro = (df_farness['data_rebalanceamento'] == data_atual) & (df_farness['ticker'] == ticker)
                if filtro.any():
                    val_farness = df_farness.loc[filtro, 'farness'].values[0]
            
            # Registro da linha no painel
            linha = {
                'data_rebalanceamento': data_atual,
                'ticker': ticker,
                
                # Features calculadas em T-1
                'distancia_sma50': dist_sma50,
                'distancia_sma200': dist_sma200,
                'volatilidade_21d': val_vol,
                'rsi_14d': val_rsi,
                'retorno_5d': val_ret5,
                'retorno_21d': val_ret21,
                'farness_mst': val_farness,
                
                # Target futuro apurado em [T, T+1]
                'target_direcao': alvo_binario,
                'retorno_real_prox_mes': retorno_real_mes
            }
            dataset_linhas.append(linha)
            
    df_features = pd.DataFrame(dataset_linhas)
    
    # -------------------------------------------------------------------------
    # 4. Tratamento de Nulos e Gravação do Dataset
    # -------------------------------------------------------------------------
    print("\n[4/4] Tratando valores ausentes e salvando 'features_ml.parquet'...")
    
    # Imputação da farness faltante com a mediana mensal (evita outlier de 1.0)
    if 'farness_mst' in df_features.columns:
        df_features['farness_mst'] = df_features.groupby('data_rebalanceamento')['farness_mst'].transform(
            lambda g: g.fillna(g.median()) if not g.dropna().empty else g
        )
        
    qtd_total_inicial = len(df_features)
    
    # Removemos linhas que contenham nulos nas demais features técnicas (ex: início do histórico sem 200 dias de SMA)
    colunas_obrigatorias = [
        'distancia_sma50', 'distancia_sma200', 'volatilidade_21d', 
        'rsi_14d', 'retorno_5d', 'retorno_21d'
    ]
    df_features = df_features.dropna(subset=colunas_obrigatorias)
    qtd_total_final = len(df_features)
    
    print(f" -> Total de observações geradas: {qtd_total_inicial}")
    print(f" -> Observações válidas após limpeza de warmup: {qtd_total_final} (removidas {qtd_total_inicial - qtd_total_final} linhas)")
    print(f" -> Período coberto: {df_features['data_rebalanceamento'].min().strftime('%Y-%m')} a {df_features['data_rebalanceamento'].max().strftime('%Y-%m')}")
    print(f" -> Distribuição de classes (Target Direção):")
    print(df_features['target_direcao'].value_counts(normalize=True).rename({1: 'Alta (1)', 0: 'Queda (0)'}).to_string())
    
    caminho_saida = config.PROCESSADOS / "features_ml.parquet"
    df_features.to_parquet(caminho_saida, index=False)
    print(f"\n[SUCESSO] Base de Features de Machine Learning salva em:\n  -> {caminho_saida.resolve()}")
    print("=" * 80)


if __name__ == '__main__':
    main()
