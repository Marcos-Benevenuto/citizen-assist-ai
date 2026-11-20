"""Executa as perguntas de teste, calcula indicadores e compara os modelos de resposta.

Executar: python tests/testes.py
Gera: tests/resultados.csv
"""
import csv
import os
import sys
import time

PASTA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PASTA, "..", "src"))
import sistema  # noqa: E402

# (tipo, pergunta, esperado) - esperado = id do registro ou VAZIA/AMBIGUA/SEM_RESPOSTA
CASOS = [
    ("direta", "Como tirar o CPF?", "DOC-001"),
    ("reformulacao", "Quero regularizar meu CPF", "DOC-001"),
    ("direta", "Como emitir segunda via do RG?", "DOC-002"),
    ("direta", "Onde faço meu título de eleitor?", "DOC-003"),
    ("direta", "Como renovar a CNH?", "DOC-004"),
    ("reformulacao", "Perdi a certidão de nascimento, como pedir outra?", "DOC-005"),
    ("direta", "O que é a conta gov.br prata ou ouro?", "SRV-001"),
    ("reformulacao", "Como consultar minha aposentadoria no INSS?", "SRV-002"),
    ("direta", "Como ter o cartão do SUS?", "SRV-003"),
    ("direta", "Como entrar no CadÚnico?", "SRV-004"),
    ("reformulacao", "Onde baixo a carteira de trabalho digital?", "SRV-005"),
    ("reformulacao", "Comprei um produto com defeito, onde reclamo?", "COM-001"),
    ("reformulacao", "Não tenho dinheiro para advogado", "COM-002"),
    ("direta", "Como denunciar violência contra idoso?", "COM-003"),
    ("reformulacao", "Preciso de ajuda, sofri violência doméstica", "COM-004"),
    ("direta", "Como funciona o Conselho Tutelar?", "COM-005"),
    ("fora do tema", "Qual a previsão do tempo amanhã?", "SEM_RESPOSTA"),
    ("fora do tema", "Como fazer a matrícula na escola?", "SEM_RESPOSTA"),
    ("limite: entrada vazia", "", "VAZIA"),
    ("limite: consulta ambígua", "violência", "AMBIGUA"),
    ("limite: sem resposta confiável", "Como declarar imposto de renda?", "SEM_RESPOSTA"),
]

STATUS_ESPERADO = {"VAZIA": "vazia", "AMBIGUA": "ambigua", "SEM_RESPOSTA": "sem_resposta"}


def obtido_como_texto(res):
    if res["status"] == "ok":
        return res["registro"]["id"]
    return {"vazia": "VAZIA", "ambigua": "AMBIGUA", "sem_resposta": "SEM_RESPOSTA"}[res["status"]]


def nota_modelo(texto, reg):
    """4 critérios objetivos de clareza/consistência (0 a 4)."""
    t = texto.lower()
    return sum([
        reg["referencia"] in texto,                 # cita a fonte
        reg["data_verificacao"] in texto,           # informa data de verificação
        "confirme" in t and "oficial" in t,         # aviso de limitação
        reg["titulo"] in texto,                     # identifica o assunto
    ])


def main():
    registros = sistema.carregar_base()
    linhas, tempos, acertos = [], [], 0
    notas = {"A": [], "B": []}

    for n, (tipo, pergunta, esperado) in enumerate(CASOS, start=1):
        inicio = time.perf_counter()
        res = sistema.consultar(pergunta, registros)
        ms = (time.perf_counter() - inicio) * 1000
        obtido = obtido_como_texto(res)
        acerto = obtido == esperado
        acertos += acerto
        tempos.append(ms)
        linhas.append([n, tipo, pergunta, esperado, obtido, "ACERTO" if acerto else "ERRO", f"{ms:.3f}"])
        if res["status"] == "ok":
            for m in ("A", "B"):
                notas[m].append(nota_modelo(sistema.formatar_resposta(res["registro"], m), res["registro"]))

    with open(os.path.join(PASTA, "resultados.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "tipo", "pergunta", "esperado", "obtido", "classificacao", "tempo_ms"])
        w.writerows(linhas)

    print(f"{'N':<3}{'TIPO':<32}{'ESPERADO':<14}{'OBTIDO':<14}{'RESULTADO':<10}{'MS':>8}")
    for l in linhas:
        print(f"{l[0]:<3}{l[1]:<32}{l[3]:<14}{l[4]:<14}{l[5]:<10}{l[6]:>8}")

    total = len(CASOS)
    print(f"\nPerguntas testadas: {total}")
    print(f"Acertos: {acertos}")
    print(f"Taxa de acerto: {acertos / total * 100:.1f}%")
    print(f"Tempo médio de consulta: {sum(tempos) / total:.3f} ms")
    print("\nComparação dos modelos de resposta (nota média de 0 a 4):")
    for m in ("A", "B"):
        print(f"  Modelo {m}: {sum(notas[m]) / len(notas[m]):.2f}")


if __name__ == "__main__":
    main()
