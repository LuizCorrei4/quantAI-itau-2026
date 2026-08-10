# Divisão de Tarefas (Sprint Final: 10/08 a 16/08)

Como temos apenas 6 dias até a entrega e o pipeline de dados já está concluído, precisamos paralelizar o trabalho usando *branches* independentes. A divisão a seguir otimiza o tempo para que os 3 membros da equipe trabalhem simultaneamente sem gerar grandes conflitos de código.

## Pessoa 1: O "Core Quant" (Você)
**Branch sugerida:** `feat/backtest-core`
**Foco:** O coração matemático da estratégia.

* **10-11/ago:** Resolver a etapa pendente da Métrica de Periferia (Testar as 7 candidatas/controles na Parte 2.5 e decidir a vencedora). (FEITO -> `scripts/06_avaliar_periferia.py`, a métrica vencedora está cravada no `plano_final_nexus.md`).
* **11-12/ago:** Codificar o Loop do Backtest (MVP). Ler os dados limpos, calcular a Matriz de Correlação (Ledoit-Wolf), transformar em distâncias, gerar a MST (`networkx`), elencar o Top 10 Equal-Weight e calcular o retorno acumulado com os descontos de custos de transação.
* **13/ago:** Fazer o *merge* do seu trabalho com a Pessoa 2 (Filtros). 

## Pessoa 2: O "Analista de Risco & Robustez" (Colega 1)
**Branch sugerida:** `feat/filtros-robustez`
**Foco:** Proteger a estratégia, gerar as métricas de validação e analisar os cenários.

* **10-11/ago:** Desenvolver o script isolado do **Filtro de Regime** (a lógica do threshold de percentil expansivo) e a função que compara o resultado da estratégia contra os **Benchmarks Completos** (IBOV, CDI, Equal-Weight do Universo, Aleatórios).
* **12/ago:** Escrever as funções que extraem as estatísticas de desempenho de uma curva de retorno (Sharpe, Drawdown, Calmar Ratio, Volatilidade).
* **13-14/ago:** Após o merge com o Core, rodar os **Testes de Robustez** (variar o tamanho das janelas e número de ações selecionadas) e levantar dados empíricos para a Análise Crítica (como a carteira se comporta em crashes vs. mercados calmos).

## Pessoa 3: O "Visual Storyteller" (Colega 2)
**Branch sugerida:** `feat/identidade-relatorio`
**Foco:** O produto final. Garantir a estética premium, clareza e que a apresentação tire nota máxima nos critérios de formatação.

* **10-11/ago:** Criar a Identidade do Robô Nexus (logotipo, cores neon sobre fundo escuro). Iniciar a montagem do "esqueleto" do relatório 16:9 em PDF (Template), já preenchendo a tese acadêmica e a metodologia de forma sucinta.
* **12-13/ago:** Desenvolver funções em Python (`matplotlib`/`networkx`) para gerar as imagens bonitas da MST (grafos comparando mercado calmo vs. crise). Pode usar dados mockados enquanto o backtest oficial não sai. Escrever também a seção de "Como a IA foi utilizada" de forma concreta.
* **14-15/ago:** Receber os gráficos de retorno e as métricas da Pessoa 1 e 2, inserir no relatório final. Enxugar todo o texto para o limite de 750 palavras.

## Agenda Conjunta (Todo o time)
**Branch:** `main` ou `release/final`

* **15/ago:** Reunião de alinhamento para validar o relatório montado pela Pessoa 3. Verificar rigorosamente se não sobrou o nome de ninguém (anonimato total) e se o arquivo tem apenas 5 páginas.
* **16/ago:** Buffer para qualquer incêndio de última hora e submissão do PDF para o Itaú Asset.
