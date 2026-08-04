# PENDENTE: Validação do Universo de Dados

A validação empírica que motivou o pivô para "sobreviventes por liquidez" não foi suficientemente checada. Pelo menos um ticker citado como evidência de falha (SOUZ3) não corresponde a um código real da B3 (o ticker correto da Souza Cruz é CRUZ3), e outro (VVAR3) não é um caso de deslistagem — é uma troca de ticker (Via Varejo virou VIIA3 em 2021, empresa segue ativa). Isso significa que a decisão de pivotar para sobreviventes pode ter sido tomada com evidência incompleta.

**Próximo passo obrigatório antes de tratar o universo de dados como definitivo:**
Construir uma tabela de mapeamento de tickers renomeados/fundidos na B3 (ex: VVAR3->VIIA3) e re-testar a disponibilidade via yfinance usando os tickers corrigidos. Só cair de volta para "sobreviventes" nos casos em que a empresa realmente faliu ou foi deslistada sem sucessora mapeável (ex: Oi, IRB Brasil), não para casos de rebranding/fusão que tenham um ticker sucessor rastreável.
