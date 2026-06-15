# CLUSTERIZAÇÃO TEMÁTICA (K-Means sobre o espaço latente)

# imports necessários:
#
# numpy  -> manipulação de arrays numéricos
# pandas -> leitura/escrita dos metadados e do CSV de clusters
# pathlib -> paths multiplataforma
# sklearn.cluster.KMeans -> algoritmo de clusterização
# sklearn.metrics.silhouette_score -> métrica de qualidade da clusterização

import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# datapath
# base_dir -> raiz do projeto (recommendation/)
# latent_path -> representações latentes (64d) geradas pelo autoencoder
# meta_path -> metadados (nome, municipio) na MESMA ordem de latent.npy/embeddings.npy
# clusters_path -> saída: cada vereador com seu cluster temático atribuído
BASE_DIR = Path(__file__).resolve().parent.parent
LATENT_PATH = BASE_DIR / "models" / "latent.npy"
META_PATH = BASE_DIR / "models" / "embeddings_meta.csv"
CLUSTERS_PATH = BASE_DIR / "models" / "clusters.csv"

# configurações
# K_MIN / K_MAX -> faixa de k avaliada. n=94 é PEQUENO, então mantemos k modesto:
#   k grande sobre poucos pontos gera clusters minúsculos/instáveis e silhouette ruim.
# RANDOM_STATE -> reprodutibilidade do K-Means
# N_INIT -> nº de reinicializações do K-Means (escolhe a melhor inércia)
# MIN_CLUSTER_SIZE -> rejeita k que produza cluster com menos que isso (evita singletons)
K_MIN = 2
K_MAX = 8
RANDOM_STATE = 42
N_INIT = 10
MIN_CLUSTER_SIZE = 2

# NOTA DE DESIGN (decisão de arquitetura):
# A clusterização roda no espaço LATENTE de 64d (latent.npy), não nos 768d, porque a
# compressão do autoencoder filtra ruído e ajuda o K-Means a achar grupos mais estáveis.
# Já o RANKING por similaridade roda nos 768d (ver recommend.py / backend pgvector).
# O cluster é uma feature EXPLICATIVA e DESACOPLADA: `cluster_id` é nullable no banco e o
# ranking NÃO depende dele. Se a separação for fraca (silhouette baixa, esperável com n=94),
# o sistema continua 100% funcional — o cluster é só um rótulo de leitura, nunca um filtro.


# carregar_latente -> carrega latent.npy + metadados e valida o alinhamento de tamanho
def carregar_latente(latent_path: Path = LATENT_PATH, meta_path: Path = META_PATH) -> tuple[np.ndarray, pd.DataFrame]:
    """Carrega as representações latentes e os metadados (mesma ordem)."""
    if not latent_path.exists():
        raise FileNotFoundError(
            f"Latente não encontrado em: {latent_path}\n"
            "Execute src/embeddings.py e src/train.py antes da clusterização."
        )
    latente = np.load(latent_path)
    meta = pd.read_csv(meta_path)
    if len(latente) != len(meta):
        raise ValueError(
            f"Desalinhamento: latent.npy tem {len(latente)} linhas e "
            f"embeddings_meta.csv tem {len(meta)}. Regenere o pipeline atomicamente "
            "(make recommendation-build) para manter os artefatos em sincronia."
        )
    print(f"[clustering] Latente: {latente.shape}  | Metadados: {len(meta)} vereadores")
    return latente, meta


# avaliar_k -> varre K_MIN..K_MAX e calcula inércia (elbow) e silhouette de cada k
# retorna um DataFrame de diagnóstico (k, inertia, silhouette, menor_cluster) p/ o notebook
def avaliar_k(latente: np.ndarray, k_min: int = K_MIN, k_max: int = K_MAX) -> pd.DataFrame:
    """Avalia cada k candidato por inércia (elbow) e silhouette (qualidade)."""
    linhas = []
    # silhouette exige 2 <= k <= n-1
    k_max = min(k_max, len(latente) - 1)
    for k in range(k_min, k_max + 1):
        modelo = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=N_INIT)
        labels = modelo.fit_predict(latente)
        # defensivo: se o K-Means colapsa em <2 clusters distintos (ex.: latente
        # degenerado/colapsado), o silhouette é indefinido — pula este k em vez de quebrar.
        n_distintos = len(np.unique(labels))
        if n_distintos < 2:
            print(f"  k={k:>2d}  degenerado: apenas {n_distintos} cluster distinto — pulado")
            continue
        sil = silhouette_score(latente, labels)
        menor = np.bincount(labels).min()
        linhas.append(
            {"k": k, "inertia": float(modelo.inertia_), "silhouette": float(sil), "menor_cluster": int(menor)}
        )
        print(f"  k={k:>2d}  inertia={modelo.inertia_:>10.3f}  silhouette={sil:>6.3f}  menor_cluster={menor}")
    return pd.DataFrame(linhas)


# escolher_k -> escolhe o melhor k pela MAIOR silhouette, descartando k que gerem
# clusters minúsculos (menor_cluster < MIN_CLUSTER_SIZE). Elbow (inertia) fica como
# diagnóstico secundário no notebook. Se nenhum k passar no filtro, cai no de maior
# silhouette mesmo assim (e avisa).
def escolher_k(diagnostico: pd.DataFrame, min_cluster_size: int = MIN_CLUSTER_SIZE) -> int:
    if diagnostico.empty:
        raise ValueError(
            "Nenhum k produziu clusters distintos — o espaço latente parece DEGENERADO "
            "(autoencoder colapsado?). Verifique latent.npy (linhas únicas / variância) e "
            "regenere com 'make recommendation-build'."
        )
    validos = diagnostico[diagnostico["menor_cluster"] >= min_cluster_size]
    if validos.empty:
        melhor = diagnostico.loc[diagnostico["silhouette"].idxmax()]
        print(f"[clustering] Nenhum k sem cluster pequeno; usando k={int(melhor.k)} (silhouette={melhor.silhouette:.3f})")
        return int(melhor.k)
    melhor = validos.loc[validos["silhouette"].idxmax()]
    print(f"[clustering] k escolhido = {int(melhor.k)}  (silhouette={melhor.silhouette:.3f}, sem clusters pequenos)")
    return int(melhor.k)


# clusterizar -> ajusta o K-Means final com o k escolhido e retorna labels + modelo
def clusterizar(latente: np.ndarray, k: int) -> tuple[np.ndarray, KMeans]:
    """Ajusta o K-Means final e retorna os rótulos de cluster por vereador."""
    modelo = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=N_INIT)
    labels = modelo.fit_predict(latente)
    tamanhos = np.bincount(labels)
    print(f"[clustering] Clusters (k={k}) — tamanhos: {tamanhos.tolist()}")
    return labels, modelo


# salvar_clusters -> junta os rótulos aos metadados e salva clusters.csv
# colunas: nome, municipio, cluster_id  (chave (municipio, nome) usada no seed do backend)
def salvar_clusters(meta: pd.DataFrame, labels: np.ndarray, caminho: Path = CLUSTERS_PATH) -> pd.DataFrame:
    """Salva o CSV final de clusters (nome, municipio, cluster_id)."""
    saida = meta.copy()
    saida["cluster_id"] = labels.astype(int)
    saida = saida[["nome", "municipio", "cluster_id"]]
    caminho.parent.mkdir(parents=True, exist_ok=True)
    saida.to_csv(caminho, index=False)
    print(f"[salvo] Clusters ({len(saida)} vereadores) → {caminho}")
    return saida


# pipeline principal
# ordem de execução:
# 1. carrega o espaço latente + metadados
# 2. avalia k de K_MIN a K_MAX (inércia + silhouette)
# 3. escolhe k pela melhor silhouette (sem clusters minúsculos)
# 4. ajusta o K-Means final e atribui cluster a cada vereador
# 5. salva clusters.csv
if __name__ == "__main__":
    latente, meta = carregar_latente()

    print("[clustering] Avaliando k candidatos...")
    diagnostico = avaliar_k(latente)

    k = escolher_k(diagnostico)

    labels, _modelo = clusterizar(latente, k)

    saida = salvar_clusters(meta, labels)

    print()
    print(f"Clusterização concluída — {k} clusters temáticos sobre {len(saida)} vereadores.")
