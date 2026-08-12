"""
Baselines e o Teste dos Macacos (Monte Carlo)

Este script cumpre o objetivo de responder 
a uma pergunta crítica que qualquer banca quantitativa fará:
"O seu robô deu lucro porque ele é inteligente, ou apenas porque o mercado subiu?"

Para provar o valor do nosso "Alpha", criamos um benchmark absoluto: simulamos
200 "macacos" que escolhem ações de forma 100% aleatória todos os meses.
Se o Sharpe do nosso robô (ex: +0.10 com L=150) for maior que 95% dos macacos,
provamos matematicamente que temos Alpha real (p-value < 0.05).
"""

import sys
from pathlib import Path

# Garante que os módulos internos do src/nexus possam ser importados 
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import random

from src.nexus import config
from src.nexus.portfolio import (
    calcular_pesos_equal_weight,
    apurar_retorno_periodo,
    calcular_turnover,
    descontar_custos
)

N_SIMULACOES = 200
TAMANHO_CARTEIRA_MACACO = 10 # Macaco escolhe 10 ações aleatórias por mês
IMG_DIR = Path("images")
IMG_DIR.mkdir(parents=True, exist_ok=True)

def calcular_sharpe(serie_retornos: pd.Series, serie_cdi: pd.Series) -> float:
    """Calcula o Sharpe anualizado de uma série de retornos mensais."""
    anos = len(serie_retornos) / 12
    if anos == 0: return 0.0
    
    ret_anual = (1 + serie_retornos).prod() ** (1 / anos) - 1
    vol_anual = serie_retornos.std() * np.sqrt(12)
    cdi_anual = (1 + serie_cdi).prod() ** (1 / anos) - 1
    
    if vol_anual == 0: return 0.0
    return (ret_anual - cdi_anual) / vol_anual

def main():
    print("=== INICIANDO O TESTE DE MONTE CARLO (MACACOS ALEATÓRIOS) ===")
    
    # 1. Carregamento dos dados
    universo = pd.read_parquet(config.PROCESSADOS / "universo_mensal.parquet")
    precos = pd.read_parquet(config.PROCESSADOS / "precos_ajustados.parquet")
    cdi = pd.read_parquet(config.PROCESSADOS / "cdi_diario.parquet")
    
    datas_rebalanceamento = sorted(universo['data_rebalanceamento'].unique())
    # Faremos o teste dos macacos no mesmo campo de batalha em que calibramos o Momentum:
    # O período In-Sample (2011 a 2018).
    datas_in_sample = [d for d in datas_rebalanceamento if d <= pd.Timestamp('2018-12-31')]
    
    sharpes_macacos = []
    
    print(f"Simulando {N_SIMULACOES} carteiras aleatórias ao longo de {len(datas_in_sample)-1} meses...")
    
    for sim in range(N_SIMULACOES):
        retornos_simulacao = []
        retornos_cdi = []
        pesos_anteriores = None
        
        # Para que cada simulação seja diferente, garantimos a aleatoriedade
        np.random.seed(sim + 42) 
        
        for i, data_atual in enumerate(datas_in_sample):
            if i == len(datas_in_sample) - 1:
                break
                
            data_prox = datas_in_sample[i+1]
            ativos_elegiveis = universo[universo['data_rebalanceamento'] == data_atual]['ticker'].tolist()
            
            # O Macaco faz sua escolha cega: pega N ações quaisquer do universo permitido
            candidatas_macaco = list(np.random.choice(ativos_elegiveis, size=TAMANHO_CARTEIRA_MACACO, replace=False))
            
            # Peso igual para todos os ativos sorteados
            pesos_novos = calcular_pesos_equal_weight(candidatas_macaco)
            turnover = calcular_turnover(pesos_anteriores, pesos_novos)
            
            # Apuração do retorno das ações escolhidas pelo macaco
            ret_bruto = apurar_retorno_periodo(precos, candidatas_macaco, data_atual, data_prox)
            ret_liq = descontar_custos(ret_bruto, turnover, config.CUSTO_POR_OPERACAO)
            
            # Retorno do CDI no mês correspondente
            idx_c_start = cdi.index.get_indexer([data_atual], method='pad')[0]
            idx_c_end = cdi.index.get_indexer([data_prox], method='pad')[0]
            ret_cdi = (cdi['cdi_acumulado'].iloc[idx_c_end] / cdi['cdi_acumulado'].iloc[idx_c_start]) - 1
            
            retornos_simulacao.append(ret_liq)
            retornos_cdi.append(ret_cdi)
            
            pesos_anteriores = pesos_novos
            
        # Calculamos o Sharpe final deste macaco específico
        sharpe_sim = calcular_sharpe(pd.Series(retornos_simulacao), pd.Series(retornos_cdi))
        sharpes_macacos.append(sharpe_sim)
        
        if (sim + 1) % 50 == 0:
            print(f"  -> {sim + 1} macacos concluíram o desafio...")

    # 2. Estatísticas do Teste
    sharpes_macacos = np.array(sharpes_macacos)
    sharpe_medio = sharpes_macacos.mean()
    sharpe_p95 = np.percentile(sharpes_macacos, 95) # Top 5% dos macacos
    sharpe_p05 = np.percentile(sharpes_macacos, 5)  # Piores 5% dos macacos
    
    # Nosso robô alcançou Sharpe 0.10 com L=150 no In-Sample
    SHARPE_NEXUS = 0.10
    
    p_value = np.mean(sharpes_macacos >= SHARPE_NEXUS)
    
    print("\n=== RESULTADOS DO TESTE DE MONTE CARLO ===")
    print(f"Sharpe Médio Aleatório (Ruído do Mercado): {sharpe_medio:.3f}")
    print(f"Top 5% dos Macacos alcançaram Sharpe de: {sharpe_p95:.3f}")
    print(f"Sharpe do nosso Nexus (L=150): {SHARPE_NEXUS:.3f}")
    print(f"Probabilidade de obtermos esse resultado por pura sorte (p-value): {p_value:.1%}")
    
    if p_value < 0.05:
        print("Veredito: SUCESSO ESTATÍSTICO! O Robô tem Alpha real contra o mercado (95% de confiança).")
    else:
        print("Veredito: ALERTA! Nosso resultado ainda está muito misturado com o ruído do mercado. O Alpha é fraco.")

    # 3. Geração do Gráfico Matador de Falácias
    plt.figure(figsize=(10, 6))
    plt.hist(sharpes_macacos, bins=30, color='lightgray', edgecolor='black', alpha=0.7, label='200 Carteiras Aleatórias (Macacos)')
    
    # Marca a média dos macacos
    plt.axvline(x=sharpe_medio, color='black', linestyle='--', linewidth=2, label=f'Média Aleatória: {sharpe_medio:.2f}')
    
    # Marca a zona de 95% de confiança (para a direita disso, é Alpha puro)
    plt.axvline(x=sharpe_p95, color='orange', linestyle=':', linewidth=2, label=f'Intervalo de Confiança 95% (> {sharpe_p95:.2f})')
    
    # Marca o nosso robô Nexus
    plt.axvline(x=SHARPE_NEXUS, color='purple', linestyle='-', linewidth=3, label=f'Robô Nexus L=150 ({SHARPE_NEXUS:.2f})')
    
    plt.title('Teste de Robustez: Robô Nexus vs 200 Carteiras Aleatórias (In-Sample)', fontsize=14, fontweight='bold')
    plt.xlabel('Sharpe Ratio (In-Sample: 2011 - 2018)', fontsize=12)
    plt.ylabel('Frequência (Qtd de Simulações)', fontsize=12)
    plt.legend(loc='upper right')
    plt.grid(True, alpha=0.2)
    
    # Caixa de texto com o p-value para a banca
    textstr = f"Nexus é melhor que {(1-p_value)*100:.1f}% das opções aleatórias."
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    plt.gca().text(0.05, 0.95, textstr, transform=plt.gca().transAxes, fontsize=12,
            verticalalignment='top', bbox=props)
            
    plt.tight_layout()
    img_path = IMG_DIR / "02_baseline_macacos_in_sample.png"
    plt.savefig(img_path, dpi=150)
    plt.close()
    
    print(f"\n[+] Histograma salvo em: {img_path.resolve()}")

if __name__ == '__main__':
    main()
