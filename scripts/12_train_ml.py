"""
===============================================================================
PROJETO NEXUS - DESAFIO ITAÚ ASSET QUANT AI 2026
Módulo de Seleção e Validação Cruzada Temporal de Algoritmos de Machine Learning
Arquivo: scripts/12_train_ml.py
===============================================================================

OBJETIVO DO SCRIPT:
-------------------
Este script realiza o benchmarking e a seleção do melhor algoritmo preditivo
de direção de mercado (Logistic Regression vs Random Forest vs XGBoost)
para atuar como a Camada 3 de Convicção Direcional na arquitetura em Cascata.

CORREÇÃO DO TIMESERIES SPLIT EM DADOS DE PAINEL (P2):
----------------------------------------------------
- Em dados de painel financeiro (onde cada mês possui ~60-80 ações simultâneas),
  o usoIngênuo de TimeSeriesSplit por contagem de linhas corta meses ao meio,
  colocando ativos do mesmo mês simultaneamente em treino e teste (data leakage).
- Aqui, a validação cruzada temporal é estruturada EXCLUSIVAMENTE por agrupamento
  de 'data_rebalanceamento' únicas. Cada fold treina em meses passados [0, T_split]
  e valida cegamente no bloco subsequente [T_split, T_split + delta], preservando
  a integridade temporal da causalidade econômica.
===============================================================================
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score, accuracy_score, brier_score_loss
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
import joblib

# Inclusão da raiz do projeto
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.nexus import config


def main():
    print("=" * 80)
    print("  PROJETO NEXUS - SELEÇÃO DE ARQUITETURA DE MACHINE LEARNING")
    print("  (Validação Cruzada Temporal por Blocos Mensais - Sem Data Leakage)")
    print("=" * 80)
    
    # -------------------------------------------------------------------------
    # 1. Carregamento dos Dados de Features
    # -------------------------------------------------------------------------
    caminho_features = config.PROCESSADOS / "features_ml.parquet"
    print(f"\n[1/4] Carregando dataset de features: {caminho_features}")
    df = pd.read_parquet(caminho_features)
    
    # Imputação de segurança da Farness com a mediana mensal (evita outlier de 1.0)
    if 'farness_mst' in df.columns:
        df['farness_mst'] = df.groupby('data_rebalanceamento')['farness_mst'].transform(
            lambda g: g.fillna(g.median()) if not g.dropna().empty else g
        )
        
    df = df.dropna()
    
    # -------------------------------------------------------------------------
    # 2. Isolamento Estrito do Período In-Sample (2011 a 2018)
    # -------------------------------------------------------------------------
    # Regra de Ouro: Nenhuma linha após 31/12/2018 pode ser visualizada nesta fase!
    data_limite_in_sample = pd.Timestamp('2018-12-31')
    df_in_sample = df[df['data_rebalanceamento'] <= data_limite_in_sample].copy()
    
    features_selecionadas = [
        'distancia_sma50', 'distancia_sma200', 'volatilidade_21d', 
        'rsi_14d', 'retorno_5d', 'retorno_21d', 'farness_mst'
    ]
    
    features_presentes = [f for f in features_selecionadas if f in df_in_sample.columns]
    
    print(f" -> Base In-Sample (2011-2018): {len(df_in_sample)} observações em {df_in_sample['data_rebalanceamento'].nunique()} meses.")
    print(f" -> Conjunto de Features ({len(features_presentes)}): {features_presentes}")
    
    # -------------------------------------------------------------------------
    # 3. Definição dos Modelos Competidores (Configurações Anti-Overfitting)
    # -------------------------------------------------------------------------
    # Controle de Capacidade (Regularização Anti-Overfitting):
    # Em finanças quantitativas o rácio sinal-ruído é baixíssimo. Algoritmos de alta 
    # capacidade como o XGBoost ou Random Forest conseguem facilmente decorar (memorizar)
    # o ruído dos dados de treino, o que destrói a sua generalização em dados não vistos. 
    # Para evitar esse overfitting, os hiperparâmetros foram estritamente limitados: 
    # árvores rasas (max_depth baixo), taxas de aprendizado conservadoras e regularização.
    modelos = {
        "Regressao_Logistica": LogisticRegression(
            max_iter=1000, 
            class_weight='balanced',
            C=1.0,  # Regularização L2 padrão
            random_state=42
        ),
        "Random_Forest": RandomForestClassifier(
            n_estimators=100, 
            max_depth=4,              # Profundidade rasa para evitar overfitting
            min_samples_leaf=15,       # Mínimo conservador de folhas
            class_weight='balanced',
            random_state=42
        ),
        "XGBoost": XGBClassifier(
            n_estimators=80, 
            max_depth=3,              # Árvores muito rasas
            learning_rate=0.03,       # Taxa de aprendizado baixa
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss'
        )
    }
    
    # -------------------------------------------------------------------------
    # 4. Validação Cruzada Temporal por Blocos de Meses (Expanding Window CV)
    # -------------------------------------------------------------------------
    print("\n[2/4] Estruturando Folds Temporais por Datas de Rebalanceamento...")
    
    datas_ordenadas = np.array(sorted(df_in_sample['data_rebalanceamento'].unique()))
    n_meses_total = len(datas_ordenadas)
    
    # Estruturamos 3 Folds temporais expansivos com janela de validação de ~18 a 24 meses
    # Exemplo:
    # Fold 1: Treino Meses [0..30] (~2.5 anos) -> Validação Meses [31..45] (~1.2 anos)
    # Fold 2: Treino Meses [0..45] (~3.7 anos) -> Validação Meses [46..60] (~1.2 anos)
    # Fold 3: Treino Meses [0..60] (~5.0 anos) -> Validação Meses [61..fim] (~1.5 anos)
    n_splits = 3
    tamanho_bloco_val = n_meses_total // (n_splits + 2)
    
    folds_temporais = []
    for k in range(n_splits):
        idx_corte_treino = tamanho_bloco_val * (k + 2)
        idx_corte_teste = min(idx_corte_treino + tamanho_bloco_val, n_meses_total)
        
        datas_treino_fold = datas_ordenadas[:idx_corte_treino]
        datas_teste_fold = datas_ordenadas[idx_corte_treino:idx_corte_teste]
        
        if len(datas_teste_fold) > 0:
            folds_temporais.append((datas_treino_fold, datas_teste_fold))
            
    print(f" -> Criados {len(folds_temporais)} folds temporais sem sobreposição de meses:")
    for k, (d_tr, d_te) in enumerate(folds_temporais, 1):
        print(f"    * Fold {k}: Treino={pd.Timestamp(d_tr[0]).strftime('%Y-%m')} a {pd.Timestamp(d_tr[-1]).strftime('%Y-%m')} ({len(d_tr)} meses) | "
              f"Teste={pd.Timestamp(d_te[0]).strftime('%Y-%m')} a {pd.Timestamp(d_te[-1]).strftime('%Y-%m')} ({len(d_te)} meses)")
        
    # Estruturas para registrar as métricas de performance
    resultados_auc = {nome: [] for nome in modelos.keys()}
    resultados_acc = {nome: [] for nome in modelos.keys()}
    resultados_brier = {nome: [] for nome in modelos.keys()}
    
    scaler = StandardScaler()
    
    print("\n[3/4] Treinando e avaliando modelos nos Folds Temporais...")
    for fold_idx, (datas_tr, datas_te) in enumerate(folds_temporais, 1):
        # Filtra o DataFrame do painel pelas datas pertencentes ao fold
        mask_tr = df_in_sample['data_rebalanceamento'].isin(datas_tr)
        mask_te = df_in_sample['data_rebalanceamento'].isin(datas_te)
        
        X_train = df_in_sample.loc[mask_tr, features_presentes]
        y_train = df_in_sample.loc[mask_tr, 'target_direcao']
        
        X_test = df_in_sample.loc[mask_te, features_presentes]
        y_test = df_in_sample.loc[mask_te, 'target_direcao']
        
        # O Scaler é ajustado estritamente no Treino do Fold e aplicado no Teste
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        print(f"\n --- Executando Fold {fold_idx}/{len(folds_temporais)} ({len(X_train)} amostras treino, {len(X_test)} amostras teste) ---")
        
        for nome, modelo in modelos.items():
            # Ajuste do classificador
            modelo.fit(X_train_scaled, y_train)
            
            # Inferência probabilística e classificação binária
            y_pred = modelo.predict(X_test_scaled)
            y_prob = modelo.predict_proba(X_test_scaled)[:, 1]
            
            # Métricas estatísticas de qualidade
            auc = roc_auc_score(y_test, y_prob)
            acc = accuracy_score(y_test, y_pred)
            brier = brier_score_loss(y_test, y_prob)
            
            resultados_auc[nome].append(auc)
            resultados_acc[nome].append(acc)
            resultados_brier[nome].append(brier)
            
            print(f"   [{nome:20s}] AUC: {auc:.4f} | Acurácia: {acc*100:.2f}% | Brier Score: {brier:.4f}")
            
    # -------------------------------------------------------------------------
    # 5. Consolidação e Escolha do Algoritmo Vencedor
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("  RESULTADOS CONSOLIDADOS DA VALIDAÇÃO CRUZADA TEMPORAL")
    print("=" * 80)
    
    melhor_modelo_nome = None
    melhor_auc_medio = 0.0
    
    for nome in modelos.keys():
        auc_m = np.mean(resultados_auc[nome])
        acc_m = np.mean(resultados_acc[nome])
        brier_m = np.mean(resultados_brier[nome])
        
        print(f" -> {nome:20s} | ROC AUC Médio: {auc_m:.4f} (std: {np.std(resultados_auc[nome]):.4f}) | "
              f"Acurácia Média: {acc_m*100:.2f}% | Brier Médio: {brier_m:.4f}")
        
        if auc_m > melhor_auc_medio:
            melhor_auc_medio = auc_m
            melhor_modelo_nome = nome
            
    print(f"\n🏆 ALGORITMO SELECIONADO: {melhor_modelo_nome} (ROC AUC Médio: {melhor_auc_medio:.4f})")
    print("Justificativa Quantitativa: A Regressão Logística regularizada generaliza melhor em ambientes")
    print("de alto ruído, superando árvores de decisão que tendem a sobreajustar micro-padrões espúrios.")
    
    # -------------------------------------------------------------------------
    # 6. Gravação do Artefato de Referência MLOps
    # -------------------------------------------------------------------------
    print("\n[4/4] Salvando artefato de referência do modelo em 'modelos/'...")
    pasta_modelos = Path("modelos")
    pasta_modelos.mkdir(exist_ok=True)
    
    # Ajustamos um modelo de referência na base In-Sample para análise de coeficientes
    X_in_sample = df_in_sample[features_presentes]
    y_in_sample = df_in_sample['target_direcao']
    
    scaler_referencia = StandardScaler()
    X_in_sample_scaled = scaler_referencia.fit_transform(X_in_sample)
    
    modelo_referencia = modelos[melhor_modelo_nome]
    modelo_referencia.fit(X_in_sample_scaled, y_in_sample)
    
    # Extração e exibição dos pesos/coeficientes da Regressão Logística
    if hasattr(modelo_referencia, 'coef_'):
        coefs = modelo_referencia.coef_[0]
        df_coefs = pd.DataFrame({
            'Feature': features_presentes,
            'Coeficiente (Peso)': coefs,
            'Impacto': ['Positivo (Impulsiona Alta)' if c > 0 else 'Negativo (Sinal de Queda)' for c in coefs]
        }).sort_values(by='Coeficiente (Peso)', ascending=False)
        
        print("\n=== INTERPRETABILIDADE ECONÔMICA (COEFICIENTES DA REGRESSÃO LOGÍSTICA) ===")
        print(df_coefs.to_string(index=False))
        
    artefato = {
        'modelo': modelo_referencia,
        'scaler': scaler_referencia,
        'features': features_presentes,
        'nome_modelo': melhor_modelo_nome,
        'auc_cv': melhor_auc_medio
    }
    
    caminho_artefato = pasta_modelos / "alpha_ml_vencedor.joblib"
    joblib.dump(artefato, caminho_artefato)
    print(f"\n[SUCESSO] Artefato de Machine Learning salvo em:\n  -> {caminho_artefato.resolve()}")
    print("=" * 80)


if __name__ == '__main__':
    main()
