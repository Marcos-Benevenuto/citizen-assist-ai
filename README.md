# Citizen Assist AI

Global Solution 2026.2 – FIAP (CitizenTech)

**Equipe:** _[preencher: nome da equipe]_
**Integrantes / RMs:** _[preencher: nome – RM]_

## 1. Problema, público e temas
Cidadãos costumam encontrar informações dispersas ou difíceis sobre documentos, serviços e direitos. O **Citizen Assist AI** é um assistente textual em Python que responde dúvidas simples do cotidiano a partir de uma base de orientações verificadas, sempre citando a fonte e avisando quando não há resposta suficiente.

- **Público:** qualquer cidadão que precise de orientação inicial.
- **Temas (3):** documentação (CPF, RG, título de eleitor, CNH, certidão), serviços (gov.br, INSS, SUS, CadÚnico, Carteira de Trabalho Digital) e orientações comunitárias (Procon, Defensoria, Disque 100, Ligue 180, Conselho Tutelar).

## 2. Base de conhecimento, estruturas e busca
- **Arquivo:** `data/base.json` com **15 registros** (5 por tema).
- **Campos obrigatórios:** `id`, `tema`, `titulo`, `palavras_chave`, `orientacao`, `referencia`, `data_verificacao`, `relacionados`.
- **Validação (`carregar_base`):** trata arquivo ausente, vazio, JSON inválido, campo faltando, id repetido e relacionado inexistente.
- **Para acrescentar ou corrigir orientações:** basta editar o JSON; o código não muda.
- **Estruturas:** lista de registros; dicionário `por_id`; dicionário `por_tema` (tema → lista de ids); e um **grafo simples** `grafo` (id → ids relacionados), usado na navegação entre assuntos. A hierarquia é: tema → assunto, e entre assuntos as arestas do grafo.
- **Estratégia de busca:** a pergunta é normalizada (minúsculas, sem acentos, sem pontuação e sem palavras comuns). A pontuação de cada registro é: **+1 por palavra em comum** com as palavras-chave e **+2 por frase-chave inteira** encontrada na pergunta. Só há resposta se a nota for **≥ 2**.
- **Várias correspondências:** vence a maior nota; as seguintes aparecem como sugestão. Se houver **empate no topo**, a consulta é considerada ambígua e o usuário escolhe entre as opções empatadas.

## 3. Regras de resposta e modelos de instrução (prompts)
Condicionais tratam quatro situações: pergunta vazia, sem correspondência, ambígua e resposta encontrada. Quando não há base suficiente, o sistema **não inventa** e sugere outros temas.

| Modelo | Instrução | Formato |
|---|---|---|
| **A (curto)** | "Papel: assistente de orientação cidadã. Responda de forma curta (orientação + fonte)." | Orientação + fonte |
| **B (completo)** | "Papel: assistente de orientação cidadã NÃO oficial. Use somente a base verificada, linguagem simples, informe tema, fonte e data de verificação, inclua aviso para confirmar informações atualizadas, diga quando não houver resposta e nunca peça dados pessoais." | Tema/assunto + orientação + fonte + data + aviso |

**Comparação:** cada modelo foi avaliado nas respostas encontradas com 4 critérios (cita a fonte, informa a data, traz aviso de que não é canal oficial, identifica o assunto). **Modelo A: 1,06/4. Modelo B: 4,00/4.** O Modelo B foi escolhido por ser mais consistente e transparente; o Modelo A é mais curto, mas não informa data nem aviso.

## 4. Testes e indicadores
Script: `python tests/testes.py` (gera `tests/resultados.csv` com esperado, obtido, acerto/erro e tempo).

- **Perguntas testadas:** 21 (16 sobre os temas, entre diretas e reformuladas; 2 fora dos temas; 3 de limitação: entrada vazia, consulta ambígua e ausência de resposta confiável).
- **Taxa de acerto:** 21/21 = **100%**.
- **Tempo médio de consulta:** **≈ 0,56 ms** (medido com `time.perf_counter`).
- **Facilidade de uso:** ver `docs/teste_usabilidade.md` _[preencher com o resultado do teste real]_.

**Interpretação e limitações da avaliação:** o resultado de 100% deve ser lido com cuidado, porque as perguntas de teste foram escritas pela própria equipe, conhecendo as palavras-chave da base. Com perguntas de outras pessoas, a taxa tende a cair. O tempo de milissegundos vale para uma base pequena (15 registros). O teste de usabilidade tem poucos participantes.

**Melhorias possíveis:** (1) tolerar erros de digitação (comparação por similaridade de texto); (2) aumentar a base e incluir sinônimos regionais; (3) criar uma interface web.

## 5. Como executar
```
python src/sistema.py
python tests/testes.py
```
Requer apenas Python 3 (sem bibliotecas externas).

## 6. Exemplos
| Entrada | Saída |
|---|---|
| "Como tirar o CPF?" | Orientação do DOC-001, fonte da Receita Federal, data e aviso, mais 3 assuntos relacionados |
| "Não tenho dinheiro para advogado" | Defensoria Pública, com fonte |
| "violência" | Consulta ambígua: pergunta se o usuário quer Disque 100 ou Ligue 180 |
| "Qual a previsão do tempo amanhã?" | Aviso de que não há base suficiente, sem inventar, e lista de temas |
| (vazio) / opção "9" | Mensagem de entrada vazia / opção inexistente |

## 7. Cuidados
- **Clareza:** textos em linguagem simples e respostas curtas.
- **Acessibilidade:** interface textual, menu numerado, sem depender de cor ou imagem.
- **Privacidade:** o sistema não pede nem armazena dados pessoais e avisa o usuário para não digitá-los.
- **Informação não oficial:** o assistente não é canal de órgãos públicos e não promete integração com eles; sempre manda confirmar na fonte.

## 8. Vídeo
Link (YouTube, não listado): _[colar o link]_

## 9. Conclusões
O protótipo cumpre o fluxo completo (pergunta → busca → resposta com fonte → navegação) e trata os casos de erro. As principais limitações são o tamanho da base, a busca por palavras exatas e as fontes que precisam ser reconferidas periodicamente.

## Estrutura
```
src/sistema.py       programa principal
data/base.json       base de conhecimento
tests/testes.py      testes e indicadores
tests/resultados.csv resultado dos testes
docs/                uso_ia.md, teste_usabilidade.md, roteiro_video.md
```
