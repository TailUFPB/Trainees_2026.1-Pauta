# TREINAMENTO DO AUTOENCODER

# imports necessários:

# numpy -> manipulação de arrays numéricos
# torch -> biblioteca de deep learning
# nn -> módulo de redes neurais (usado para definir a função de perda)
# autoencoder -> módulo local com a arquitetura, configurações, dataset e funções utilitárias

import numpy as np
import torch
import torch.nn as nn

from autoencoder import (
    Autoencoder,
    carregar_embeddings,
    extrair_latente,
    device,
    EMBEDDINGS_PATH,
    MODEL_PATH,
    EPOCHS,
    LEARNING_RATE,
)

from pathlib import Path

# datapath
# base_dir -> raiz do projeto (recommendation/)
# latent_path -> caminho onde as representações latentes serão salvas após o treino
BASE_DIR = Path(__file__).resolve().parent.parent
LATENT_PATH = BASE_DIR / "models" / "latent.npy"

# treinar -> executa o loop de treinamento do autoencoder
# o autoencoder é treinado para reconstruir os embeddings originais
# a loss (MSE) mede o erro entre a entrada e a reconstrução
# quanto menor a loss, melhor o autoencoder aprendeu a comprimir e reconstruir os dados
def treinar(model: Autoencoder, dataloader, epochs: int = EPOCHS, lr: float = LEARNING_RATE) -> list[float]:
    """Treina o autoencoder e retorna o histórico de perdas por época."""

    # critério de perda -> MSE (Mean Squared Error)
    # mede a diferença média quadrática entre a entrada original e a saída reconstruída
    criterio = nn.MSELoss()

    # otimizador -> Adam
    # atualiza os pesos da rede com base nos gradientes calculados pela loss
    # lr (learning rate) controla o tamanho dos passos de atualização
    otimizador = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)

    # histórico de perdas -> armazena a loss média de cada época
    # útil para visualizar a curva de aprendizado e verificar convergência
    historico = []

    # coloca o modelo em modo de treino
    # isso ativa camadas como Dropout e BatchNorm (se existirem)
    model.train()

    print(f"[treino] Iniciando treinamento por {epochs} épocas...")
    print(f"[treino] Learning rate: {lr}")
    print(f"[treino] Dispositivo: {device}")
    print()

    # loop de treinamento
    for epoca in range(1, epochs + 1):

        # loss_total -> acumula a loss de todos os batches da época
        # num_batches -> conta quantos batches foram processados
        loss_total = 0.0
        num_batches = 0

        # itera sobre cada batch do DataLoader
        for batch in dataloader:

            # move o batch para o dispositivo (GPU ou CPU)
            batch = batch.to(device)

            # forward pass -> passa o batch pelo autoencoder
            # o modelo recebe os embeddings originais e tenta reconstruí-los
            reconstrucao = model(batch)

            # calcula a loss -> compara a entrada (batch) com a saída (reconstrucao)
            loss = criterio(reconstrucao, batch)

            # backward pass -> calcula os gradientes da loss em relação aos pesos
            # zero_grad -> limpa os gradientes acumulados do passo anterior
            # backward -> calcula os novos gradientes
            # step -> atualiza os pesos com base nos gradientes
            otimizador.zero_grad()
            loss.backward()
            otimizador.step()

            # acumula a loss do batch
            loss_total += loss.item()
            num_batches += 1

        # calcula a loss média da época
        loss_media = loss_total / num_batches
        historico.append(loss_media)

        # exibe o progresso a cada 10 épocas e na última
        if epoca % 10 == 0 or epoca == 1 or epoca == epochs:
            print(f"  Época {epoca:>4d}/{epochs}  |  Loss: {loss_media:.6f}")

    print()
    print("[treino] Treinamento concluído!")
    print(f"[treino] Loss inicial: {historico[0]:.6f}")
    print(f"[treino] Loss final: {historico[-1]:.6f}")

    return historico


# salvar_modelo -> salva os pesos do modelo treinado em disco
# salva apenas os pesos (state_dict), não a arquitetura inteira
# isso permite carregar os pesos em qualquer instância da classe Autoencoder
def salvar_modelo(model: Autoencoder, caminho: Path = MODEL_PATH) -> None:
    """Salva os pesos do modelo treinado."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), caminho)
    print(f"[salvo] Modelo -> {caminho}")


# salvar_latente -> extrai e salva as representações latentes dos embeddings
# usa o encoder do modelo treinado para comprimir os embeddings de 768 para 64 dimensões
# o resultado é salvo como um arquivo .npy para uso nas etapas seguintes (clustering e FAISS)
def salvar_latente(model: Autoencoder, caminho_embeddings: Path = EMBEDDINGS_PATH, caminho_latente: Path = LATENT_PATH) -> np.ndarray:
    """Extrai as representações latentes e salva em disco."""
    embeddings = np.load(caminho_embeddings)
    latente = extrair_latente(model, embeddings)
    np.save(caminho_latente, latente)
    print(f"[salvo] Representações latentes ({latente.shape}) -> {caminho_latente}")
    return latente


# pipeline principal
# ordem de execução:
# 1. carrega os embeddings do disco e cria o DataLoader
# 2. instancia o autoencoder e move para o dispositivo
# 3. executa o loop de treinamento
# 4. salva os pesos do modelo treinado
# 5. extrai e salva as representações latentes
if __name__ == "__main__":

    # carrega os embeddings
    dataloader = carregar_embeddings()

    # instancia o modelo
    model = Autoencoder().to(device)
    print(f"[treino] Parâmetros treináveis: {sum(p.numel() for p in model.parameters()):,}")
    print()

    # treina o autoencoder
    historico = treinar(model, dataloader)

    # salva o modelo treinado
    salvar_modelo(model)

    # extrai e salva as representações latentes
    latente = salvar_latente(model)

    print()
    print("Treinamento concluído com êxito!")
