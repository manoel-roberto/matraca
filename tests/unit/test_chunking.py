"""Testes unitários do segmentador de texto para áudio (RF-12, A.13.5)."""

from __future__ import annotations

import pytest

from matraca.audio.chunking import chunk_text

pytestmark = pytest.mark.unit


def test_chunking_texto_curto() -> None:
    """Texto menor que o limite deve retornar como um único chunk idêntico."""
    texto = "Este é um texto curto de teste para síntese de voz."
    chunks = chunk_text(texto, max_chars=500)
    assert len(chunks) == 1
    assert chunks[0] == texto


def test_chunking_vazio() -> None:
    """Texto vazio ou composto apenas por espaços retorna lista vazia."""
    assert chunk_text("") == []
    assert chunk_text("   \n\n  \t ") == []


def test_chunking_limite_invalido() -> None:
    """Limite inferior a 50 caracteres deve levantar ValueError."""
    with pytest.raises(ValueError, match="max_chars deve ser pelo menos 50"):
        chunk_text("Texto", max_chars=40)


def test_chunking_respeita_paragrafos() -> None:
    """Parágrafos que cabem juntos devem ser agrupados com quebra dupla; quando excedem, separam."""
    p1 = "Primeiro parágrafo do texto com conteúdo informativo."
    p2 = "Segundo parágrafo detalhando o assunto em questão."
    p3 = "Terceiro parágrafo concluindo o raciocínio exposto."

    texto = f"{p1}\n\n{p2}\n\n{p3}"
    chunks = chunk_text(texto, max_chars=120)

    # Cada parágrafo tem ~50 chars, logo 2 cabem em 120 e o 3º vai para novo chunk
    assert len(chunks) == 2
    assert p1 in chunks[0]
    assert p2 in chunks[0]
    assert chunks[1] == p3


def test_chunking_ignora_pontos_de_abreviacoes() -> None:
    """Abreviações como Dr., Sr., etc. não devem causar divisão prematura de frase."""
    texto = "O Dr. Silva e o Sr. Oliveira compareceram, etc. Tudo conforme o combinado."
    # Limite suficiente para o texto caber numa só frase ou chunk
    chunks = chunk_text(texto, max_chars=100)
    assert len(chunks) == 1
    assert "Dr. Silva" in chunks[0]
    assert "Sr. Oliveira" in chunks[0]


def test_chunking_ignora_pontos_em_numeros() -> None:
    """Separadores de milhar como 1.000 ou 10.500 não são tratados como quebra de frase."""
    texto = "Foram arrecadados 1.000 reais na primeira etapa e 10.500 reais na segunda etapa."
    chunks = chunk_text(texto, max_chars=100)
    assert len(chunks) == 1
    assert "1.000" in chunks[0]
    assert "10.500" in chunks[0]


def test_chunking_paragrafo_gigante_sem_pontuacao() -> None:
    """Texto longo contínuo sem pontuação é dividido por palavras sem cortar no meio."""
    palavras = ["palavra" + str(i) for i in range(100)]
    texto = " ".join(palavras)

    chunks = chunk_text(texto, max_chars=200)
    assert len(chunks) > 1

    for c in chunks:
        assert len(c) <= 200
        # Nenhuma palavra deve estar cortada pela metade
        for word in c.split():
            assert word.startswith("palavra")

    # Reconstrução equivale ao original
    reconstruido = " ".join(chunks)
    assert reconstruido == texto


def test_chunking_frase_maior_que_limite_com_virgulas() -> None:
    """Frase muito longa é dividida nas vírgulas preservando sentido."""
    f1 = "Esta é a primeira parte da frase bastante extensa,"
    f2 = " acompanhada por uma segunda oração explicativa também longa,"
    f3 = " e finalmente encerrada com a conclusão do raciocínio."
    texto = f1 + f2 + f3

    chunks = chunk_text(texto, max_chars=80)
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c) <= 80


def test_chunking_palavra_isolada_maior_que_limite() -> None:
    """Palavra única contínua maior que o limite não é descartada nem corrompida."""
    palavra_gigante = "A" * 150
    chunks = chunk_text(palavra_gigante, max_chars=100)
    assert len(chunks) == 1
    assert chunks[0] == palavra_gigante
