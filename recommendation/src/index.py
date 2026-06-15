# ÍNDICE FAISS  —  DEMO / OFFLINE APENAS
#
# ⚠️ ESTE ÍNDICE NÃO É USADO EM PRODUÇÃO. ⚠️
# Em produção, a busca por similaridade roda no Postgres via pgvector (índice HNSW de
# cosseno na coluna politicos.embedding) — ver server/app/services/recomendacao.py.
# Para n=94 o pgvector resolve o top-k em microssegundos; um índice FAISS paralelo seria
# uma segunda fonte de verdade redundante a versionar e sincronizar.
#
# Este módulo existe SOMENTE como oráculo de validação no notebook 04: provamos que a
# busca em numpy, em FAISS e no pgvector retornam o MESMO top-k (tabela de paridade).
# O backend (server/) NUNCA importa este arquivo.

import numpy as np
import faiss
from pathlib import Path

from embeddings import MODELS_DIR

EMBEDDINGS_PATH = MODELS_DIR / "embeddings.npy"
FAISS_PATH = MODELS_DIR / "faiss_index.bin"


# construir_index -> índice plano de produto interno sobre embeddings.npy
# como os vetores têm norma L2 = 1, produto interno (IP) == similaridade de cosseno.
# IndexFlatIP é busca EXATA (sem aproximação) — correto e suficiente p/ n=94.
def construir_index(embeddings_path: Path = EMBEDDINGS_PATH) -> faiss.Index:
    emb = np.load(embeddings_path).astype(np.float32)
    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(emb)
    print(f"[faiss] Índice construído: ntotal={index.ntotal}, d={index.d}")
    return index


# salvar_index -> persiste o índice (apenas p/ a demo do notebook)
def salvar_index(index: faiss.Index, caminho: Path = FAISS_PATH) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(caminho))
    print(f"[salvo] Índice FAISS (demo) → {caminho}")


# buscar -> top-k por similaridade de cosseno (IP) para um vetor de query 768d
def buscar(index: faiss.Index, query: np.ndarray, k: int = 5) -> tuple[np.ndarray, np.ndarray]:
    q = np.asarray(query, dtype=np.float32).reshape(1, -1)
    scores, idxs = index.search(q, k)
    return scores[0], idxs[0]


if __name__ == "__main__":
    index = construir_index()
    salvar_index(index)
    # sanity: cada perfil é seu próprio vizinho mais próximo (score ≈ 1.0)
    emb = np.load(EMBEDDINGS_PATH).astype(np.float32)
    scores, idxs = buscar(index, emb[0], k=1)
    print(f"[faiss] Sanity — perfil 0 vs si mesmo: idx={idxs[0]}, score={scores[0]:.4f}")
