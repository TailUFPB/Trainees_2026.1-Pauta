## Fluxo de execução

### Embeddings 

Para a geração dos embeddings, foi carregado o modelo `neuralmind/bert-base-portuguese-cased`. Esse modelo gerou os embeddings para o campo "proposta ementa" do dataset `df_nlp_final.csv`. 

#### Pipeline de execução da geração dos embeddings:

1. Carregamento e validação do dataset: foi carregado o dataset `df_nlp_final.csv` e validado as colunas obrigatórias.
2. Geração dos embeddings: foram gerados os embeddings para o campo "proposta ementa" do dataset `df_nlp_final.csv`.
3. Agregação por vereador: foram agregados os embeddings das propostas de cada vereador pela média, agrupando por vereador e município.
4. Salvamento: foram salvos os embeddings e os metadados.

### Autoencoder

Para reduzir a dimensionalidade dos perfis dos vereadores de 768 para 64 dimensões latentes, foi implementada e treinada uma rede neural do tipo Autoencoder. Esse gargalo geométrico filtra ruídos residuais e otimiza o custo computacional (memória e tempo de processamento) para as etapas de recomendação e busca semântica.

#### Pipeline de execução e treinamento do Autoencoder:

1. **Criação do Dataset (`EmbeddingsDataset`)**: Os embeddings agregados (`embeddings.npy`) são encapsulados em uma classe customizada do PyTorch, convertendo os arrays NumPy para tensores do tipo `float32` prontos para o fluxo de deep learning.
2. **Carregamento dos dados (`carregar_embeddings`)**: Configuração do `DataLoader` utilizando um tamanho de lote de 16 (`batch_size=16`) e embaralhamento dos dados (`shuffle=True`) para alimentar o loop de otimização de forma homogênea.
3. **Arquitetura da rede (`Autoencoder`)**: Estrutura simétrica dividida em duas sub-redes principais:
   - **Encoder**: Reduz as 768 dimensões originais para 256 (camada linear + ativação ReLU) e finalmente para as 64 dimensões do espaço latente.
   - **Decoder**: Recebe o gargalo de 64 dimensões, expande para 256 (camada linear + ativação ReLU) e reconstrói as 768 dimensões originais do BERT.
4. **Loop de Treinamento (`treinar`)**: Execução do loop por 200 épocas utilizando o otimizador **Adam** (com taxa de aprendizado `lr=0.001`) e a função de perda de Erro Quadrático Médio (**MSELoss**). O critério avalia a capacidade do Decoder de reconstruir perfeitamente a entrada após a compressão.
5. **Salvamento dos Pesos (`salvar_modelo`)**: Exportação do dicionário de pesos sintonizados (`state_dict`) da rede para o arquivo `autoencoder.pt`.
6. **Extração das Representações Latentes (`salvar_latente`)**: O modelo é colocado em modo de avaliação (`model.eval()`). Os embeddings originais passam exclusivamente pelo **Encoder** congelado para extrair a matriz comprimida final, que é salva em disco como `latent.npy` com a dimensão exata de `(94, 64)`.