# Trabalho 2: Controle de Enlace de Dados

Este projeto implementa os mecanismos fundamentais da camada de enlace de dados ponto a ponto, utilizando Sockets TCP puros em Python. O objetivo é simular a transmissão de quadros lidando com delimitação, controle de fluxo e controle de erro de forma unificada.

##  Status da Implementação

- [x] **Framing (Delimitação de Quadros):** Cabeçalho de tamanho fixo (7 bytes) e *payload* de tamanho variável.
- [x] **Controle de Erro:** Implementação matemática (do zero) dos algoritmos **CRC** (Detecção) e **Hamming** (Detecção e Correção / FEC).
- [x] **Controle de Fluxo:** Implementação do algoritmo **Go-Back-N ARQ** com janela deslizante e temporizadores (*timeouts*).

##  Arquitetura do Projeto

* `protocolo.py`: Coração do projeto. Contém a classe `Frame` e as funções matemáticas puras (divisão polinomial XOR para CRC e cálculo de paridade para Hamming).
* `servidor.py`: Receptor inteligente. Lê o cabeçalho, descobre automaticamente o modo de erro utilizado, valida a integridade, gerencia os números de sequência esperados e emite ACKs.
* `cliente.py`: Emissor com interface de linha de comando (`argparse`). Gerencia a janela de envio (Go-Back-N) e possui ferramentas de injeção de ruído para simular falhas na rede.

##  Estrutura do Quadro (Protocolo Híbrido)

O encapsulamento foi projetado (`!BBBHHB`) para suportar todos os requisitos em um único fluxo de Sockets:
* **Byte 1:** Endereço de Origem (0-255)
* **Byte 2:** Endereço de Destino (0-255)
* **Byte 3:** Modo de Erro (1 para CRC, 2 para Hamming)
* **Bytes 4-5:** Tamanho exato do Payload (0-65535)
* **Bytes 6-7:** Número de Sequência (Go-Back-N)
* **Byte 8:** Tipo do Quadro (0 = Dados, 1 = ACK)
* **Payload:** Mensagem (Tamanho variável)
* **Trailer (Opcional):** 1 byte extra anexado *apenas* quando o Modo CRC é utilizado.

---

##  Como Executar e Apresentar (Guia de Testes)

Não há dependências externas. O projeto utiliza apenas as bibliotecas nativas do Python (`socket`, `struct`, `argparse`).

### 1. Iniciar o Servidor (Receptor)
Em um terminal, inicie o servidor. Ele ficará escutando na porta 5000:
```bash
  python servidor.py
```
### 2. Comandos do Cliente (Emissor)
Abra um segundo terminal. Você pode testar diferentes cenários utilizando as flags disponíveis.

  ▶ Cenário 1: Transmissão Perfeita com CRC
Prova que o framing e o Go-Back-N estão funcionando. O servidor valida a divisão polinomial.
```bash
  python cliente.py --modo crc
```
  ▶ Cenário 2: Rejeição por Ruído (CRC)
Injeta um erro proposital em um byte do Quadro 2. O servidor detecta o erro pelo CRC, descarta o pacote silenciosamente e força o cliente a estourar o timeout e retransmitir a janela.
  ```bash
  python cliente.py --modo crc --ruido
```
  ▶ Cenário 3: Perda de Pacote (Go-Back-N)
Derruba fisicamente o Quadro 2 antes de ir para a rede. O servidor recebe o Quadro 3 fora de ordem, reenvia o ACK do Quadro 1, e o cliente faz o retrocesso (Go-Back-N) para reenviar a partir do Quadro 2.
 ```bash
  python cliente.py --modo crc --perda
```
  ▶ Cenário 4: Transmissão e Correção com Hamming (FEC)
Injeta um bit invertido no Quadro 2. O algoritmo de Hamming no servidor calcula a síndrome, identifica e corrige o bit ao vivo, envia o ACK normalmente e o fluxo do Go-Back-N não é interrompido.
 ```bash
  python cliente.py --modo hamming --ruido
```
