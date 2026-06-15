## Fluxo de execução

### Embeddings

Para a geração dos embeddings, foi carregado o modelo `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` — um SBERT (768d) treinado para similaridade semântica, em que o cosseno reflete o significado (ao contrário de um BERT base, que sofre de anisotropia e exigiria gambiarras como subtração de centróide e casamento léxico). Esse modelo gerou os embeddings para o campo "proposta ementa" do dataset.

#### Pipeline de execução da geração dos embeddings:

1. Carregamento e validação do dataset: foi carregado o dataset `df_nlp_final.csv` e validado as colunas obrigatórias.
2. Geração dos embeddings: foram gerados os embeddings para o campo "proposta ementa" do dataset `df_nlp_final.csv`.
3. Agregação por vereador: foram agregados os embeddings das propostas de cada vereador pela média, agrupando por vereador e município.
4. Preservação das evidências: além dos perfis, são embeddados os **resumos** das
   propostas individuais (linguagem natural, o mesmo texto exibido ao cidadão) e
   projetados no mesmo espaço centrado. O backend compara a query projetada com esses
   vetores por cosseno semântico para escolher as propostas que justificam cada match.
5. Salvamento: são persistidos os perfis agregados e também
   `proposal_embeddings.npy` + `proposal_embeddings_meta.csv`, usados para justificar
   cada recomendação com propostas reais.

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

### Clustering

A clusterização temática roda sobre o espaço **latente de 64d** (`latent.npy`), não sobre os 768d. A compressão do autoencoder filtra ruído residual e estabiliza o K-Means com poucos pontos (n=94). O `cluster_id` resultante é uma feature **explicativa e desacoplada** — o ranking de recomendação não depende dele.

#### Pipeline de execução do Clustering (`clustering.py`):

1. **Carregamento (`carregar_latente`)**: Lê `latent.npy` e `embeddings_meta.csv` validando que estão alinhados (mesma quantidade e ordem de vereadores).
2. **Avaliação de k (`avaliar_k`)**: Varre `k` de 2 a 8 (faixa modesta, pois n=94 é pequeno) ajustando um `KMeans(random_state=42, n_init=10)` para cada k e calculando a **inércia** (curva do cotovelo/elbow) e o **silhouette_score** (qualidade da separação).
3. **Escolha de k (`escolher_k`)**: Seleciona o k de **maior silhouette**, descartando valores que gerem clusters minúsculos (singletons). O elbow fica como diagnóstico secundário.
4. **Atribuição final (`clusterizar`)**: Ajusta o K-Means com o k escolhido e atribui um cluster a cada vereador.
5. **Salvamento (`salvar_clusters`)**: Junta os rótulos aos metadados e salva `clusters.csv` com as colunas `nome, municipio, cluster_id` — a chave `(municipio, nome)` é a usada para popular o backend.

### Recomendação

O ranking representa a query do cidadão no **mesmo espaço de 768d** dos perfis e ordena os vereadores por similaridade de cosseno. Em produção isso roda no Postgres via pgvector (índice HNSW); `recommend.py` é a demonstração/validação offline equivalente.

#### Pipeline de execução da Recomendação (`recommend.py`):

1. **Embedding da query (`embed_query`)**: O texto livre do cidadão é codificado pelo SBERT (normalizado L2) e então passa por `projetar_no_espaco` — subtrai o **mesmo** `centroid.npy` do corpus e re-normaliza L2. É a MESMA transformação dos perfis (sem a etapa de média sobre N propostas, pois a query é um texto único), garantindo que query e perfis vivam no mesmo espaço.
2. **Ranking (`recomendar`)**: Como query e perfis têm norma unitária, o produto escalar contra `embeddings.npy` já é o cosseno. Retorna o top-k `(nome, municipio, cluster_id, score)`.
3. **Validação de paridade (`index.py`, notebook 4)**: A busca em numpy, em FAISS (`IndexFlatIP`) e no pgvector retornam o MESMO top-k — prova de que o índice FAISS é redundante em produção (pgvector basta) e que os três caminhos são consistentes.
4. **Explicação por evidências**: para cada vereador do ranking, o backend seleciona até
   duas das suas propostas por **similaridade semântica** (cosseno) entre a query projetada
   e os resumos projetados das propostas. Só entram propostas acima de um **piso de
   relevância** — se nenhuma passar, o vereador aparece sem evidência (não se inventa
   justificativa). A segunda só aparece quando fica próxima da melhor. A **justificativa**
   cita os temas reais das propostas selecionadas (whitelist de assuntos municipais),
   nunca um texto genérico. A interface mostra tipo, número, ano e resumo, sem LLM e sem links.
