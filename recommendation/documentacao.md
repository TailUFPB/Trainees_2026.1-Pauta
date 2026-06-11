# Sistema de Recomendação de Candidatos

Pipeline de recomendação de vereadores por alinhamento temático, construído sobre
dados legislativos municipais coletados do SAPL de municípios paraibanos.

---

## Como funciona

O sistema representa cada vereador como um vetor semântico gerado a partir das
ementas de suas propostas legislativas. Um autoencoder comprime esses vetores em
um espaço latente de menor dimensão, sobre o qual são aplicados algoritmos de
clusterização e busca por similaridade. Dado um conjunto de preferências do cidadão,
o sistema retorna os candidatos cujo perfil de atuação mais se alinha a essas prioridades.

```
proposta_ementa
      ↓
embeddings (BERT português)
      ↓
agregação por vereador
      ↓
autoencoder (compressão)
      ↓
K-Means (clusterização temática)
      ↓
FAISS (busca por similaridade)
      ↓
ranking de candidatos recomendados
```

---

## Estrutura

```
recommendation/
│
├── data/
│   ├── df_nlp_final.csv       # dataset principal (propostas + contexto do vereador)
│   └── df_perfil.csv          # dados de apresentação para UI
│
├── src/
│   ├── embeddings.py          # geração e salvamento dos embeddings
│   ├── autoencoder.py         # arquitetura da rede neural
│   ├── train.py               # treinamento do autoencoder
│   ├── clustering.py          # clusterização e elbow method
│   ├── index.py               # construção do índice FAISS
│   ├── documentation.md       # documentação do pipeline
│   └── recommend.py           # função principal de recomendação
│
├── models/
│   ├── autoencoder.pt         # pesos do modelo treinado
│   ├── embeddings.npy         # matriz de embeddings
│   ├── faiss_index.bin        # índice de busca vetorial
│   └── clusters.csv           # vereadores com cluster atribuído
│
├── notebooks/
│   ├── 01_embeddings.ipynb    # exploração e validação dos embeddings
│   ├── 02_autoencoder.ipynb   # treinamento e avaliação do autoencoder
│   ├── 03_clustering.ipynb    # elbow method e visualização dos clusters
│   └── 04_recomendacao.ipynb  # demonstração do sistema
│
├── .env
└── requirements.txt
```

---

## Instalação

```bash
pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz com:

```
GROQ_API_KEY=sua_chave_aqui
```

---

## Ordem de execução

```bash
python src/embeddings.py    # 1. gera embeddings.npy
python src/train.py         # 2. treina e salva autoencoder.pt
python src/clustering.py    # 3. gera clusters.csv
python src/index.py         # 4. gera faiss_index.bin
```

Após executar os quatro passos, o sistema de recomendação está pronto para uso via `src/recommend.py`.

---

## Uso

```python
from src.recommend import recomendar

resultados = recomendar("pavimentação e saúde pública", k=5)
print(resultados)
```

---

## Dependências principais

| Biblioteca | Uso |
|---|---|
| `sentence-transformers` | geração de embeddings em português |
| `torch` | treinamento do autoencoder |
| `faiss-cpu` | busca vetorial por similaridade |
| `scikit-learn` | clusterização K-Means |
| `pandas` / `numpy` | manipulação de dados |

---

## Dados

Os dados de entrada (`df_nlp_final.csv` e `df_perfil.csv`) são gerados pelo
pipeline de pré-processamento e NLP — consulte o notebook de pré-processamento
para detalhes sobre a coleta, limpeza e transformação dos dados.

---

> **Em desenvolvimento** — documentação atualizada conforme o pipeline avança.