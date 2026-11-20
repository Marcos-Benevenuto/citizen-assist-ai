"""Citizen Assist AI - assistente de orientação cidadã (protótipo textual).

Executar: python src/sistema.py
Não usa APIs externas nem coleta dados pessoais.
"""
import json
import os
import re
import unicodedata

PASTA = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BASE = os.path.join(PASTA, "..", "data", "base.json")

CAMPOS_OBRIGATORIOS = ["id", "tema", "titulo", "palavras_chave", "orientacao",
                       "referencia", "data_verificacao", "relacionados"]

NOTA_MINIMA = 2  # pontuação mínima para considerar que há correspondência

AVISO = ("Aviso: este assistente NÃO é um canal oficial de órgãos públicos. "
         "Confirme os requisitos atualizados na fonte indicada.")

# Modelos de instrução (prompt) documentados - ver README
PROMPT_A = ("Papel: assistente de orientação cidadã. Responda de forma curta "
            "(orientação + fonte).")
PROMPT_B = ("Papel: assistente de orientação cidadã NÃO oficial. Regras: "
            "1) use somente a base verificada; 2) escreva em linguagem simples; "
            "3) informe tema, fonte e data de verificação; 4) inclua aviso para "
            "confirmar informações atualizadas; 5) se não houver resposta na base, "
            "diga isso e sugira outro tema; 6) nunca peça dados pessoais.")

STOPWORDS = {"como", "onde", "que", "qual", "quais", "o", "a", "os", "as", "um", "uma",
             "de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas", "para",
             "por", "meu", "minha", "com", "e", "ou", "se", "eu", "quero", "preciso",
             "posso", "pode", "ter", "faco", "fazer", "nao", "tenho", "ao", "e", "pra",
             "sobre", "me", "ajuda", "funciona"}


class BaseInvalidaError(Exception):
    """Erro ao carregar ou validar a base de conhecimento."""


# ---------------------------------------------------------------- base de dados
def carregar_base(caminho=CAMINHO_BASE):
    """Lê o JSON e valida: arquivo ausente, vazio, inválido e campos obrigatórios."""
    if not os.path.exists(caminho):
        raise BaseInvalidaError(f"Arquivo da base não encontrado: {caminho}")
    try:
        with open(caminho, encoding="utf-8") as arq:
            conteudo = arq.read().strip()
        if not conteudo:
            raise BaseInvalidaError("O arquivo da base está vazio.")
        registros = json.loads(conteudo)
    except json.JSONDecodeError as erro:
        raise BaseInvalidaError(f"JSON inválido na base: {erro}")

    if not isinstance(registros, list) or not registros:
        raise BaseInvalidaError("A base deve ser uma lista com pelo menos um registro.")

    ids = set()
    for i, reg in enumerate(registros, start=1):
        for campo in CAMPOS_OBRIGATORIOS:
            if campo not in reg or reg[campo] in ("", [], None):
                raise BaseInvalidaError(f"Registro {i}: campo obrigatório ausente ou vazio: '{campo}'")
        if reg["id"] in ids:
            raise BaseInvalidaError(f"Identificador repetido: {reg['id']}")
        ids.add(reg["id"])
    for reg in registros:
        for rel in reg["relacionados"]:
            if rel not in ids:
                raise BaseInvalidaError(f"{reg['id']} aponta para registro inexistente: {rel}")
    return registros


def montar_estruturas(registros):
    """Cria dicionários de apoio: por id, por tema e o grafo de relacionados."""
    por_id = {r["id"]: r for r in registros}
    por_tema = {}
    for r in registros:
        por_tema.setdefault(r["tema"], []).append(r["id"])
    grafo = {r["id"]: list(r["relacionados"]) for r in registros}
    return por_id, por_tema, grafo


# ------------------------------------------------------------------------ busca
def normalizar(texto):
    """Minúsculas, sem acentos e sem pontuação."""
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9\s]", " ", texto)


def tokens(texto):
    """Palavras relevantes (sem stopwords e com plural simples removido)."""
    saida = set()
    for p in normalizar(texto).split():
        if p in STOPWORDS or len(p) < 2:
            continue
        if len(p) > 3 and p.endswith("s"):
            p = p[:-1]
        saida.add(p)
    return saida


def pontuar(pergunta, reg):
    """Pontuação = palavras em comum (+1 cada) + frases-chave inteiras (+2 cada)."""
    texto = " ".join(normalizar(pergunta).split())
    tokens_pergunta = tokens(pergunta)
    tokens_reg = set()
    pontos = 0
    for chave in reg["palavras_chave"]:
        chave_norm = " ".join(normalizar(chave).split())
        tokens_reg |= tokens(chave)
        if f" {chave_norm} " in f" {texto} ":
            pontos += 2
    return pontos + len(tokens_pergunta & tokens_reg)


def consultar(pergunta, registros):
    """Retorna um dicionário com status: vazia | sem_resposta | ambigua | ok."""
    if not pergunta or not pergunta.strip():
        return {"status": "vazia", "registro": None, "opcoes": []}

    ranking = sorted(((pontuar(pergunta, r), r) for r in registros),
                     key=lambda x: (-x[0], x[1]["id"]))
    ranking = [(p, r) for p, r in ranking if p >= NOTA_MINIMA]

    if not ranking:
        return {"status": "sem_resposta", "registro": None, "opcoes": []}
    # Empate no topo = ambiguidade: o usuário escolhe entre as opções empatadas
    if len(ranking) > 1 and ranking[0][0] == ranking[1][0]:
        topo = [r for p, r in ranking if p == ranking[0][0]]
        return {"status": "ambigua", "registro": None, "opcoes": topo}
    # Melhor correspondência; as demais viram sugestões
    return {"status": "ok", "registro": ranking[0][1],
            "opcoes": [r for _, r in ranking[1:3]]}


# ------------------------------------------------------------ formatar resposta
def formatar_resposta(reg, modelo="B"):
    if modelo == "A":
        return f"Orientação: {reg['orientacao']}\nFonte: {reg['referencia']}"
    return (f"[Citizen Assist AI - assistente não oficial]\n"
            f"Tema: {reg['tema']} | Assunto: {reg['titulo']}\n"
            f"Orientação: {reg['orientacao']}\n"
            f"Fonte consultada: {reg['referencia']} (verificada em {reg['data_verificacao']})\n"
            f"{AVISO}")


# ------------------------------------------------------------------- interface
def ler(texto):
    try:
        return input(texto).strip()
    except EOFError:
        return "0"


def escolher(opcoes, titulo):
    """Mostra uma lista numerada e devolve o item escolhido (ou None)."""
    print(f"\n{titulo}")
    for i, op in enumerate(opcoes, start=1):
        print(f"  {i}. {op[1]}")
    print("  Enter. Voltar")
    while True:
        valor = ler("Escolha uma opção: ")
        if valor == "" or valor == "0":
            return None
        if valor.isdigit() and 1 <= int(valor) <= len(opcoes):
            return opcoes[int(valor) - 1][0]
        print("Opção inexistente. Digite um número da lista ou Enter para voltar.")


def mostrar_e_navegar(reg_id, por_id, grafo, modelo):
    """Mostra um registro e permite seguir para assuntos relacionados."""
    while reg_id:
        reg = por_id[reg_id]
        print("\n" + "-" * 60)
        print(formatar_resposta(reg, modelo))
        print("-" * 60)
        rel = [(r, por_id[r]["titulo"]) for r in grafo[reg_id]]
        reg_id = escolher(rel, "Assuntos relacionados:")


def menu_temas(por_id, por_tema, grafo, modelo):
    temas = [(t, t.capitalize()) for t in sorted(por_tema)]
    tema = escolher(temas, "Temas disponíveis:")
    if tema is None:
        return
    itens = [(i, por_id[i]["titulo"]) for i in por_tema[tema]]
    reg_id = escolher(itens, f"Assuntos de '{tema}':")
    if reg_id:
        mostrar_e_navegar(reg_id, por_id, grafo, modelo)


def fazer_pergunta(registros, por_id, por_tema, grafo, modelo):
    pergunta = ler("\nDigite sua pergunta (sem dados pessoais): ")
    resultado = consultar(pergunta, registros)
    status = resultado["status"]

    if status == "vazia":
        print("Você não digitou nada. Escreva uma pergunta ou volte e use o menu de temas.")
    elif status == "sem_resposta":
        print("Não encontrei orientação suficiente na base para essa pergunta.")
        print("Não vou inventar uma resposta. Tente outras palavras ou escolha um tema:")
        for t in sorted(por_tema):
            print(f"  - {t}")
    elif status == "ambigua":
        escolhido = escolher([(r["id"], r["titulo"]) for r in resultado["opcoes"]],
                             "Sua pergunta ficou ampla. Qual destes assuntos você quer?")
        if escolhido:
            mostrar_e_navegar(escolhido, por_id, grafo, modelo)
    else:
        mostrar_e_navegar(resultado["registro"]["id"], por_id, grafo, modelo)


def main():
    try:
        registros = carregar_base()
    except BaseInvalidaError as erro:
        print(f"Não foi possível iniciar: {erro}")
        return
    por_id, por_tema, grafo = montar_estruturas(registros)
    modelo = "B"

    print("=" * 60)
    print("CITIZEN ASSIST AI - orientação cidadã (protótipo NÃO oficial)")
    print("Não peça nem digite dados pessoais (CPF, RG, endereço...).")
    print("=" * 60)

    while True:
        print(f"\nMENU  (modelo de resposta atual: {modelo})")
        print("  1. Ver temas")
        print("  2. Fazer uma pergunta")
        print("  3. Trocar modelo de resposta (A curto / B completo)")
        print("  0. Sair")
        opcao = ler("Opção: ")
        if opcao == "1":
            menu_temas(por_id, por_tema, grafo, modelo)
        elif opcao == "2":
            fazer_pergunta(registros, por_id, por_tema, grafo, modelo)
        elif opcao == "3":
            modelo = "A" if modelo == "B" else "B"
            print(f"Modelo de resposta agora: {modelo}")
        elif opcao == "0":
            print("Até logo!")
            break
        elif opcao == "":
            print("Opção vazia. Digite 1, 2, 3 ou 0.")
        else:
            print("Opção inexistente. Digite 1, 2, 3 ou 0.")


if __name__ == "__main__":
    main()
