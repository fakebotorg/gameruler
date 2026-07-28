import json
import os
import socket
import threading

# O Render define a porta automaticamente pela variável de ambiente "PORT"
HOST = "0.0.0.0"
PORTA = int(os.environ.get("PORT", 5000))

ARQUIVO_BANCO = "contas.json"


def carregar_banco():
  if os.path.exists(ARQUIVO_BANCO):
    try:
      with open(ARQUIVO_BANCO, "r") as f:
        return json.load(f)
    except:
      return {}
  return {}


def salvar_banco(dados):
  with open(ARQUIVO_BANCO, "w") as f:
    json.dump(dados, f)


banco_usuarios = carregar_banco()

filas_espera = {}
lock_fila = threading.Lock()


def tratar_cliente(conexao, endereco):
  global banco_usuarios
  try:
    dados_recebidos = conexao.recv(1024).decode("utf-8")
    if dados_recebidos:
      requisicao = json.loads(dados_recebidos)
      acao = requisicao.get("acao")
      usuario = requisicao.get("usuario")
      senha = requisicao.get("senha")
      jogo = requisicao.get("jogo", "VELHA")

      if acao == "cadastrar":
        if not usuario or not senha:
          resposta = {
              "status": "erro",
              "mensagem": "Preencha usuário e senha!",
          }
        elif usuario in banco_usuarios:
          resposta = {"status": "erro", "mensagem": "Usuário já existe!"}
        else:
          banco_usuarios[usuario] = senha
          salvar_banco(banco_usuarios)
          resposta = {"status": "sucesso", "mensagem": "Conta criada!"}
        conexao.send(json.dumps(resposta).encode("utf-8"))
        conexao.close()

      elif acao == "entrar" or acao == "entrar_fila":
        if (
            usuario in banco_usuarios
            and banco_usuarios[usuario] == senha
        ):
          with lock_fila:
            if jogo not in filas_espera:
              filas_espera[jogo] = []

            filas_espera[jogo].append(conexao)

            if len(filas_espera[jogo]) >= 2:
              p1 = filas_espera[jogo].pop(0)
              p2 = filas_espera[jogo].pop(0)

              aviso = {
                  "status": "partida_encontrada",
                  "mensagem": "Servergame criado!",
              }
              try:
                p1.send(json.dumps(aviso).encode("utf-8"))
                p1.close()
              except:
                pass
              try:
                p2.send(json.dumps(aviso).encode("utf-8"))
                p2.close()
              except:
                pass
        else:
          resposta = {
              "status": "erro",
              "mensagem": "Dados incorretos!",
          }
          conexao.send(json.dumps(resposta).encode("utf-8"))
          conexao.close()
  except Exception as e:
    try:
      conexao.close()
    except:
      pass


def iniciar_servidor():
  servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  servidor.bind((HOST, PORTA))
  servidor.listen(10)
  print(f"Servidor online rodando na porta {PORTA}...")

  while True:
    conexao, endereco = servidor.accept()
    thread = threading.Thread(target=tratar_cliente, args=(conexao, endereco))
    thread.start()


if __name__ == "__main__":
  iniciar_servidor()