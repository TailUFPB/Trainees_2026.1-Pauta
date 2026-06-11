## Fluxo de execução

### Embeddings 

Para a geração dos embeddings, foi carregado o modelo `neuralmind/bert-base-portuguese-cased`. Esse modelo gerou os embeddings para o campo "proposta ementa" do dataset `df_nlp_final.csv`. 

#### Pipeline de execução da geração dos embeddings:

1. Carregamento e validação do dataset: foi carregado o dataset `df_nlp_final.csv` e validado as colunas obrigatórias.
2. Geração dos embeddings: foram gerados os embeddings para o campo "proposta ementa" do dataset `df_nlp_final.csv`.
3. Agregação por vereador: foram agregados os embeddings das propostas de cada vereador pela média, agrupando por vereador e município.
4. Salvamento: foram salvos os embeddings e os metadados.

### Autoencoder

Para que fossem gerados os embeddings no autoencoder, que consistem em matrizes com menor dimensão (com intuito de economizar memória e tempo de processamento), primeiro foi necessário gerar os embeddings (etapa anterior do fluxo de execução) e depois agregá-los por vereador (também parte da etapa anterior do fluxo de execução). 

#### Pipeline de execução da geração dos embeddings no autoencoder:


1. Criação do Dataset (`EmbeddingsDataset`): os embeddings salvos em `.npy` são encapsulados em um `Dataset` do PyTorch, convertendo o array NumPy para tensores `float32`. Isso permite iterar sobre os dados em lotes durante o treinamento.
2. Carregamento dos dados (`carregar_embeddings`): o arquivo `embeddings.npy` é carregado do disco e empacotado em um `DataLoader` com `batch_size=16` e `shuffle=True`, pronto para alimentar o loop de treinamento.
3. Arquitetura da rede (`Autoencoder`): a classe herda de `nn.Module` e define duas sub-redes:
   - **Encoder**: comprime a entrada de 768 dimensões para 256 (camada linear + ReLU) e depois para 64 (espaço latente).
   - **Decoder**: reconstrói a partir do espaço latente de 64 para 256 (camada linear + ReLU) e depois para 768 (dimensão original).
4. Forward pass (`forward`): recebe um tensor de entrada, passa pelo encoder para obter a representação latente, e depois pelo decoder para reconstruir a entrada. Retorna a reconstrução completa — durante o treino, a loss compara a entrada original com a reconstrução.
5. Codificação (`encode`): retorna apenas a representação latente (saída do encoder), sem reconstruir. É o método usado após o treinamento para obter os vetores comprimidos de cada vereador.
6. Extração das representações latentes (`extrair_latente`): função utilitária que, dado um modelo treinado e os embeddings originais, executa o encoder em modo de avaliação (sem gradientes) e retorna as representações no espaço latente como array NumPy de dimensão `(n_vereadores, 64)`.

