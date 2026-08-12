"""
Treinamento de Machine Learning (Seleção de Algoritmos)

Este script lê a base de features extraída, separa os dados In-Sample
(2011 a 2018) e treina 3 modelos diferentes (Logistic Regression, 
Random Forest e XGBoost) usando validação cruzada temporal.

O modelo que apresentar a melhor capacidade de generalização e
o maior ROC AUC (capacidade de separar quem sobe de quem cai)
será coroado como o Vencedor e salvo para a "Batalha dos Filtros".
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score, accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
import joblib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.nexus import config

def main():
    print("=== TREINAMENTO DE MACHINE LEARNING ===")
    
    # 1. Carregar Dados
    caminho_features = config.PROCESSADOS / "features_ml.parquet"
    print(f"Lendo base de dados: {caminho_features}")
    df = pd.read_parquet(caminho_features)
    
    # Preencher Nulos pontuais (ex: Farness) 
    # (Para farness, quem não estava no pool ganha um valor alto/ruim = 1.0)
    if 'farness_mst' in df.columns:
        df['farness_mst'] = df['farness_mst'].fillna(1.0)
        
    df = df.dropna()
    
    # Separar o período In-Sample (Até o final de 2018)
    df_train = df[df['data_rebalanceamento'] <= pd.Timestamp('2018-12-31')].copy()
    
    features = [
        'distancia_sma50', 'distancia_sma200', 'volatilidade_21d', 
        'rsi_14d', 'retorno_5d', 'retorno_21d', 'farness_mst'
    ]
    
    features_presentes = [f for f in features if f in df_train.columns]
    
    X = df_train[features_presentes]
    y = df_train['target_direcao']
    
    print(f"\nTreinando em {len(X)} amostras do período In-Sample (2011-2018)...")
    
    # 2. Definição dos Modelos (Todos com configurações conservadoras anti-overfitting)
    modelos = {
        "Regressao_Logistica": LogisticRegression(max_iter=1000, class_weight='balanced'),
        "Random_Forest": RandomForestClassifier(
            n_estimators=100, 
            max_depth=5, 
            min_samples_leaf=10, 
            class_weight='balanced',
            random_state=42
        ),
        "XGBoost": XGBClassifier(
            n_estimators=100, 
            max_depth=3, 
            learning_rate=0.05, 
            scale_pos_weight=1.0, 
            random_state=42,
            use_label_encoder=False,
            eval_metric='logloss'
        )
    }
    
    # Validação Cruzada Temporal (Respeita a linha do tempo, não misturando futuro com passado)
    tscv = TimeSeriesSplit(n_splits=3)
    
    resultados_auc = {nome: [] for nome in modelos.keys()}
    resultados_acc = {nome: [] for nome in modelos.keys()}
    
    # Como a Regressão Logística precisa de dados padronizados (Z-score)
    scaler = StandardScaler()
    
    print("\nExecutando Validação Cruzada (TimeSeriesSplit) para cada modelo...")
    for train_index, test_index in tscv.split(X):
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]
        
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        for nome, modelo in modelos.items():
            # XGBoost e RF se dão bem com dados não escalados, mas LogReg exige scaling.
            # Vamos usar escalado para todos para simplificar a esteira.
            modelo.fit(X_train_scaled, y_train)
            
            # Avaliação
            y_pred = modelo.predict(X_test_scaled)
            y_prob = modelo.predict_proba(X_test_scaled)[:, 1]
            
            auc = roc_auc_score(y_test, y_prob)
            acc = accuracy_score(y_test, y_pred)
            
            resultados_auc[nome].append(auc)
            resultados_acc[nome].append(acc)
            
    # 3. Decisão
    print("\n=== RESULTADOS GLOBAIS ===")
    melhor_modelo_nome = None
    melhor_auc_medio = 0.0
    
    for nome in modelos.keys():
        auc_medio = np.mean(resultados_auc[nome])
        acc_medio = np.mean(resultados_acc[nome])
        print(f" -> {nome}: ROC AUC Médio = {auc_medio:.4f} | Acurácia Média = {acc_medio:.4f}")
        
        if auc_medio > melhor_auc_medio:
            melhor_auc_medio = auc_medio
            melhor_modelo_nome = nome
            
    print(f"\n🏆 O VENCEDOR FOI: {melhor_modelo_nome} (AUC: {melhor_auc_medio:.4f})")
    
    # 4. Treinar o vencedor na base In-Sample Completa
    print("\nRetreinando o vencedor com toda a base In-Sample e extraindo a Importância das Features...")
    modelo_final = modelos[melhor_modelo_nome]
    
    X_full_scaled = scaler.fit_transform(X)
    modelo_final.fit(X_full_scaled, y)
    
    # Feature Importance (Apenas se for baseado em árvore)
    if hasattr(modelo_final, 'feature_importances_'):
        importancias = modelo_final.feature_importances_
        df_importancias = pd.DataFrame({'Feature': features_presentes, 'Importancia': importancias})
        df_importancias = df_importancias.sort_values(by='Importancia', ascending=False)
        print("\n=== FEATURE IMPORTANCE (Lógica da Máquina) ===")
        print(df_importancias.to_string(index=False))
        
    # 5. Salvar o Artefato (MLOps)
    pasta_modelos = Path("modelos")
    pasta_modelos.mkdir(exist_ok=True)
    
    artefato = {
        'modelo': modelo_final,
        'scaler': scaler,
        'features': features_presentes,
        'nome_modelo': melhor_modelo_nome
    }
    
    caminho_modelo = pasta_modelos / "alpha_ml_vencedor.joblib"
    joblib.dump(artefato, caminho_modelo)
    
    print(f"\n[+] Modelo vencedor ({melhor_modelo_nome}) salvo com sucesso em: {caminho_modelo.resolve()}")

if __name__ == '__main__':
    main()
