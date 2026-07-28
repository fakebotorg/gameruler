import json
import socket
import sys
import threading
import pygame

pygame.init()

# Configurações da tela
LARGURA, ALTURA = 800, 600
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("App - Jogo da Velha Online")

# Cores
FUNDO = (255, 255, 255)
PRETO = (30, 30, 30)
LINHA_TABULEIRO = (30, 30, 30)
AZUL_X = (0, 120, 215)
VERMELHO_O = (220, 50, 50)
CINZA_TEXTO = (110, 110, 120)
CINZA_CLARO = (240, 240, 245)

# Fontes
fonte_placar_titulo = pygame.font.SysFont("Segoe UI", 24, bold=True)
fonte_placar_numeros = pygame.font.SysFont("Segoe UI", 28, bold=True)
fonte_vez = pygame.font.SysFont("Segoe UI", 22, bold=True)
fonte_grande = pygame.font.SysFont("Segoe UI", 80, bold=True)
fonte_espera = pygame.font.SysFont("Segoe UI", 26, bold=True)

# Configuração do Servidor
HOST = "127.0.0.1"
PORTA = 5000

# Estados do Jogo
# 'procurando', 'jogando'
estado_tela = "procurando"
status_matchmaking = "Conectando ao servidor e procurando oponente..."

tabuleiro = [""] * 9
turno = "X"
nome_jogador_atual = "Jogador"  # Aqui você passaria o nome vindo do login
placar_x = 0
placar_o = 0
fim_de_jogo = False
mensagem_vencedor = ""

clock = pygame.time.Clock()


def buscar_oponente_thread(usuario):
  global estado_tela, status_matchmaking
  try:
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((HOST, PORTA))

    requisicao = {
        "acao": "entrar_fila",
        "usuario": usuario,
        "jogo": "VELHA",
    }
    cliente.send(json.dumps(requisicao).encode("utf-8"))

    # Fica travado aqui aguardando o servidor achar o oponente
    resposta_bytes = cliente.recv(2048)
    resposta = json.loads(resposta_bytes.decode("utf-8"))
    cliente.close()

    if resposta.get("status") == "partida_encontrada":
      estado_tela = "jogando"
    else:
      status_matchmaking = "Erro ao encontrar partida."
  except Exception as e:
    status_matchmaking = "Servidor offline ou erro de conexão."


def iniciar_busca(usuario):
  t = threading.Thread(target=buscar_oponente_thread, args=(usuario,))
  t.daemon = True
  t.start()


def resetar_velha():
  global tabuleiro, turno, fim_de_jogo, mensagem_vencedor
  tabuleiro = [""] * 9
  turno = "O" if turno == "X" else "X"
  fim_de_jogo = False
  mensagem_vencedor = ""


def verificar_vencedor():
  global fim_de_jogo, mensagem_vencedor, placar_x, placar_o
  vitorias = [
      (0, 1, 2),
      (3, 4, 5),
      (6, 7, 8),
      (0, 3, 6),
      (1, 4, 7),
      (2, 5, 8),
      (0, 4, 8),
      (2, 4, 6),
  ]
  for a, b, c in vitorias:
    if tabuleiro[a] == tabuleiro[b] == tabuleiro[c] and tabuleiro[a] != "":
      fim_de_jogo = True
      if tabuleiro[a] == "X":
        placar_x += 1
        mensagem_vencedor = "Jogador X venceu!"
      else:
        placar_o += 1
        mensagem_vencedor = "Jogador O venceu!"
      return

  if "" not in tabuleiro and not fim_de_jogo:
    fim_de_jogo = True
    mensagem_vencedor = "Empate!"


# Inicia a busca automaticamente ao abrir o arquivo (substitua "UserTeste" pelo nome logado)
iniciar_busca(nome_jogador_atual)

while True:
  tela.fill(FUNDO)
  pos_mouse = pygame.mouse.get_pos()

  for evento in pygame.event.get():
    if evento.type == pygame.QUIT:
      pygame.quit()
      sys.exit()

    if evento.type == pygame.MOUSEBUTTONDOWN and estado_tela == "jogando":
      x, y = pos_mouse
      if not fim_de_jogo:
        if 250 <= x <= 550 and 180 <= y <= 480:
          coluna = (x - 250) // 100
          linha = (y - 180) // 100
          indice = linha * 3 + coluna

          if tabuleiro[indice] == "":
            tabuleiro[indice] = turno
            verificar_vencedor()
            if not fim_de_jogo:
              turno = "O" if turno == "X" else "X"
      else:
        resetar_velha()

  # --- TELA 1: PROCURANDO JOGADOR (Matchmaking) ---
  if estado_tela == "procurando":
    txt_titulo = fonte_placar_titulo.render(
        "PROCURANDO OPONENTE...", True, PRETO
    )
    txt_status = fonte_espera.render(status_matchmaking, True, CINZA_TEXTO)

    tela.blit(txt_titulo, (LARGURA // 2 - txt_titulo.get_width() // 2, 220))
    tela.blit(txt_status, (LARGURA // 2 - txt_status.get_width() // 2, 280))

  # --- TELA 2: JOGO ATIVO ---
  elif estado_tela == "jogando":
    # Placar
    txt_placar_titulo = fonte_placar_titulo.render("PLACAR", True, PRETO)
    tela.blit(txt_placar_titulo, (355, 20))

    tela.blit(fonte_placar_numeros.render(str(placar_x), True, PRETO), (330, 60))
    tela.blit(
        fonte_placar_numeros.render("--", True, CINZA_TEXTO), (385, 58)
    )
    tela.blit(
        fonte_placar_numeros.render(str(placar_o), True, VERMELHO_O), (445, 60)
    )

    # Tabuleiro
    pygame.draw.line(tela, LINHA_TABULEIRO, (350, 180), (350, 480), 4)
    pygame.draw.line(tela, LINHA_TABULEIRO, (450, 180), (450, 480), 4)
    pygame.draw.line(tela, LINHA_TABULEIRO, (250, 280), (550, 280), 4)
    pygame.draw.line(tela, LINHA_TABULEIRO, (250, 380), (550, 380), 4)

    for i in range(9):
      linha = i // 3
      coluna = i % 3
      px = 250 + coluna * 100
      py = 180 + linha * 100

      if tabuleiro[i] == "X":
        tela.blit(fonte_grande.render("X", True, AZUL_X), (px + 28, py + 5))
      elif tabuleiro[i] == "O":
        tela.blit(fonte_grande.render("O", True, VERMELHO_O), (px + 23, py + 5))

    # Rodapé
    if fim_de_jogo:
      txt_vez = fonte_vez.render(
          f"{mensagem_vencedor} (Clique para reiniciar)", True, PRETO
      )
    else:
      txt_vez = fonte_vez.render(
          f"VEZ DE: {turno} ({nome_jogador_atual})", True, PRETO
      )

    tela.blit(txt_vez, ((LARGURA - txt_vez.get_width()) // 2, 520))

  pygame.display.flip()
  clock.tick(60)