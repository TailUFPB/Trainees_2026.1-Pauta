# Sistema de Recomendação de Candidatos

Pipeline de recomendação de vereadores por alinhamento temático, construído sobre
dados legislativos municipais coletados do SAPL de municípios paraibanos.

---

## Como funciona

O sistema representa cada vereador como um vetor semântico gerado a partir das
ementas de suas propostas legislativas. Dado um conjunto de pautas do cidadão (texto
livre), o sistema retorna os candidatos cujo perfil de atuação mais se alinha a essas
prioridades, por similaridade de cosseno.

```
proposta_ementa
      ↓
embeddings (SBERT multilíngue)        ← embeddings.py
      ↓
agregação por vereador (média)
      ↓
projeção no espaço centrado           ← subtrai o centróide do corpus + normaliza L2
      ↓
   ├─→ [RANKING]  similaridade de cosseno em 768d   ← produção: pgvector (backend)
   │                                                   demo:    recommend.py / FAISS
   ├─→ [EVIDÊNCIAS] top-2 propostas por match        ← justificativa exibida no frontend
   └─→ [CLUSTERS] autoencoder 768→64 → K-Means       ← autoencoder.py + clustering.py
```

Duas decisões de arquitetura importantes:

1. **O ranking roda no espaço de 768d** (SBERT projetado no espaço centrado), que é o
   contrato do backend (`EMBEDDING_DIM=768`). Em **produção** a busca acontece no
   Postgres via **pgvector** (índice HNSW de cosseno) — ver `server/`. O `recommend.py`
   e o índice FAISS deste módulo são **apenas para demonstração/validação offline**.
2. **A clusterização roda no espaço latente de 64d** (autoencoder), que filtra ruído e
   estabiliza o K-Means. O `cluster_id` é uma feature **explicativa e desacoplada**: o
   ranking não depende dele (é nullable no banco).

> **Fonte única do espaço vetorial:** tanto os perfis dos vereadores quanto a query do
> cidadão passam pela MESMA transformação (`projetar_no_espaco` em `embeddings.py`:
> subtrai o **mesmo** centróide + re-normaliza L2). Sem isso, a query cairia num espaço
> diferente dos perfis e o ranking viraria ruído — por isso o centróide é **persistido**
> (`centroid.npy`) e reusado no backend.

---

## Estrutura

```
recommendation/
│
├── data/
│   ├── df_nlp_filtrado.csv    # dataset principal (propostas + contexto do vereador)
│   └── df_perfil.csv          # dados de apresentação para UI
│
├── src/
│   ├── embeddings.py ✅       # embeddings + projetar_no_espaco + persiste centroid.npy
│   ├── autoencoder.py ✅      # arquitetura da rede neural
│   ├── train.py ✅            # treinamento do autoencoder
│   ├── clustering.py ✅       # K-Means no latente + escolha de k (silhouette/elbow)
│   ├── recommend.py ✅        # embed_query + recomendar (demo/validação offline)
│   ├── index.py ✅            # índice FAISS (DEMO-ONLY; produção usa pgvector)
│   ├── workflow.md ✅         # fluxo do pipeline, etapa a etapa
│   │
│   └── notebooks/
│       ├── 1_embeddings.ipynb ✅   # exploração e validação dos embeddings
│       ├── 2_autoencoder.ipynb ✅  # treinamento e avaliação do autoencoder
│       ├── 3_clustering.ipynb ✅   # elbow/silhouette e visualização dos clusters
│       └── 4_recomendacao.ipynb ✅ # demonstração + paridade numpy/FAISS/pgvector
│
├── models/
│   ├── embeddings.npy ✅      # matriz de embeddings (94, 768) — projetada e normalizada
│   ├── centroid.npy ✅        # centróide do corpus (768,) — projeta a query no mesmo espaço
│   ├── autoencoder.pt ✅      # pesos do modelo treinado
│   ├── latent.npy ✅          # representações latentes (94, 64)
│   ├── embeddings_meta.csv ✅ # (nome, municipio) na mesma ordem de embeddings.npy
│   ├── proposal_embeddings.npy ✅      # embeddings dos resumos das propostas, projetados (N, 768)
│   ├── proposal_embeddings_meta.csv ✅ # identificação + resumo das propostas
│   ├── clusters.csv ✅        # (nome, municipio, cluster_id)
│   └── faiss_index.bin ✅     # índice FAISS (demo)
│
└── requirements.txt ✅
```

---

## Instalação

```bash
# da raiz do monorepo:
make recommendation-install        # cria recommendation/.venv (uv, py3.12) + deps

# ou manualmente:
cd recommendation
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

---

## Ordem de execução (build atômico)

Os artefatos devem ser gerados **juntos** para não dessincronizar (embeddings ↔ autoencoder
↔ clusters). Um único alvo encadeia tudo:

```bash
make recommendation-build
# equivale a, dentro de recommendation/:
#   .venv/bin/python src/embeddings.py   # 1. embeddings.npy + centroid.npy
#   .venv/bin/python src/train.py        # 2. autoencoder.pt + latent.npy
#   .venv/bin/python src/clustering.py   # 3. clusters.csv
# e copia centróide + embeddings/metadados das propostas → server/app/assets/
```

---

## Integração com o backend (produção)

O ranking de produção **não** usa este módulo em runtime — usa o backend FastAPI + pgvector,
que já tem a busca de cosseno pronta. Este módulo apenas **alimenta** o banco:

```bash
make server-seed            # 1. cria/atualiza o PERFIL dos políticos (df_perfil.csv)
make recommendation-build   # 2. gera embeddings/centroide/clusters (+ exporta centroid.npy)
make server-seed-vetores    # 3. popula politicos.embedding (768d) e cluster_id
```

- `server/app/cli/seed_vetores.py` casa os artefatos com os políticos por `(municipio, nome)`
  e **aborta sem persistir** se algum vereador não casar (garante 94/94 ou falha alto).
- `server/app/services/recomendacao.gerar_embedding` projeta a query do cidadão no mesmo
  espaço 768d (SBERT + `centroid.npy` + L2) — espelho de `projetar_no_espaco`.
- Para explicar cada match, o backend compara a query projetada com os embeddings (já
  projetados) dos **resumos** das propostas do político, por cosseno semântico. Retorna até
  duas evidências acima de um piso de relevância (se nenhuma passar, não inventa evidência),
  com tipo, número, ano e resumo. A justificativa cita os temas reais dessas propostas
  (whitelist de assuntos municipais), nunca um texto genérico.

---

## Uso (demonstração offline)

```python
# dentro de recommendation/src (a venv precisa estar ativa)
from recommend import recomendar

print(recomendar("pavimentação e saúde pública", k=5))
```

Em produção, `POST /recomendacoes` grava apenas o vetor de interesses, calcula o top-k
por cosseno no pgvector e usa o texto transitoriamente para selecionar evidências mais
precisas. `GET /recomendacoes` reapresenta o ranking salvo sem persistir o texto.

---

## Dependências principais

| Biblioteca               | Uso                                                      |
| ------------------------ | -------------------------------------------------------- |
| `sentence-transformers`  | embeddings de similaridade (SBERT multilíngue, 768d)     |
| `torch`                  | treinamento do autoencoder                               |
| `scikit-learn`           | clusterização K-Means + silhouette                       |
| `faiss-cpu`              | busca vetorial **na demo offline** (produção = pgvector) |
| `pandas` / `numpy`       | manipulação de dados                                     |
| `matplotlib` / `seaborn` | visualizações nos notebooks                              |

---

## Dados

Os dados de entrada (`df_nlp_filtrado.csv` e `df_perfil.csv`) são gerados pelo
pipeline de pré-processamento e NLP — consulte o notebook de pré-processamento
para detalhes sobre a coleta, limpeza e transformação dos dados.

---

> Pipeline completo: embeddings → autoencoder → clusterização → recomendação,
> integrado ao backend (pgvector) que serve o frontend `/recomendacoes`.
