"""Gera PDFs sintéticos de teste com PyMuPDF (sem binários versionados).

Uso: python scripts/make_fixtures.py [diretório_de_saída]

Fixtures (A.13.9): uma_coluna, duas_colunas, cabecalho_rodape, somente_imagem, protegido,
corrompido, vazio, nota_rodape_juridica, grande_500 (teste `slow`), texto_juridico,
além de pagina_em_branco (PDF válido sem texto e sem imagem).
"""

from __future__ import annotations

import sys
import textwrap
from collections.abc import Callable
from pathlib import Path

import pymupdf

PAGE_W, PAGE_H = 595, 842
FONT = "helv"
PASSWORD = "segredo"  # noqa: S105 - senha fictícia de fixture

LOREM = (
    "A administração pública direta e indireta de qualquer dos poderes obedecerá aos princípios "
    "de legalidade, impessoalidade, moralidade, publicidade e eficiência, conforme a Constituição."
)


def _lines(
    page: pymupdf.Page,
    x: float,
    y: float,
    paragraphs: list[str],
    width_chars: int,
    *,
    size: float = 11,
    leading: float = 14,
    gap: float = 18,
) -> float:
    """Escreve parágrafos quebrados em linhas (como em um PDF real); devolve o y final."""
    for par in paragraphs:
        for line in textwrap.wrap(par, width_chars):
            page.insert_text((x, y), line, fontsize=size, fontname=FONT)
            y += leading
        y += gap
    return y


def _save(doc: pymupdf.Document, path: Path, **kwargs: object) -> Path:
    doc.save(path, **kwargs)
    doc.close()
    return path


def build_uma_coluna(out: Path) -> Path:
    """1 coluna: parágrafos quebrados em linhas no meio das frases."""
    doc = pymupdf.open()
    for i in range(1, 4):
        page = doc.new_page(width=PAGE_W, height=PAGE_H)
        _lines(
            page,
            72,
            110,
            [f"Parágrafo um da página {i}. {LOREM}", f"Parágrafo dois da página {i}. {LOREM}"],
            78,
        )
    return _save(doc, out / "uma_coluna.pdf")


def build_duas_colunas(out: Path) -> Path:
    """Pág. 1: 2 colunas. Pág. 2: título de largura total + 2 colunas. Pág. 3: coluna + caixa."""
    doc = pymupdf.open()
    esq = [f"ESQUERDA-{k} {LOREM}" for k in (1, 2)]
    dir_ = [f"DIREITA-{k} {LOREM}" for k in (1, 2)]

    p1 = doc.new_page(width=PAGE_W, height=PAGE_H)
    _lines(p1, 72, 110, esq, 34)
    _lines(p1, 320, 110, dir_, 34)

    p2 = doc.new_page(width=PAGE_W, height=PAGE_H)
    p2.insert_text(
        (72, 100), "TITULO-LARGURA-TOTAL DA SECAO DE PRINCIPIOS", fontsize=16, fontname=FONT
    )
    _lines(p2, 72, 140, esq, 34)
    _lines(p2, 320, 140, dir_, 34)

    p3 = doc.new_page(width=PAGE_W, height=PAGE_H)
    _lines(p3, 72, 110, [f"PRINCIPAL-1 {LOREM}", f"PRINCIPAL-2 {LOREM}"], 55)
    _lines(p3, 410, 130, ["CAIXA-LATERAL destaque importante para memorizar o conceito."], 22)
    return _save(doc, out / "duas_colunas.pdf")


def build_cabecalho_rodape(out: Path) -> Path:
    """Cabeçalho/rodapé repetidos com numeração + marca de licenciamento rotacionada e clara."""
    doc = pymupdf.open()
    total = 6
    for i in range(1, total + 1):
        page = doc.new_page(width=PAGE_W, height=PAGE_H)
        page.insert_text(
            (72, 40), "Direito Constitucional - Prof. Fulano de Tal", fontsize=9, fontname=FONT
        )
        _lines(page, 72, 120, [f"CORPO-{i} {LOREM}", f"Segundo bloco {i}. {LOREM}"], 78)
        page.insert_text((72, 810), f"Página {i} de {total}", fontsize=9, fontname=FONT)
        page.insert_text(
            (540, 700),
            "Licenciado para MARIA SOUZA - CPF 111.222.333-96",
            fontsize=10,
            fontname=FONT,
            rotate=90,
            color=(0.8, 0.8, 0.8),
        )
    return _save(doc, out / "cabecalho_rodape.pdf")


def build_somente_imagem(out: Path) -> Path:
    """Página só com imagem de página inteira (sem camada de texto)."""
    doc = pymupdf.open()
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 60, 80))
    pix.set_rect(pix.irect, (200, 200, 200))
    page.insert_image(page.rect, pixmap=pix)
    return _save(doc, out / "somente_imagem.pdf")


def build_protegido(out: Path) -> Path:
    """PDF protegido por senha (AES-256)."""
    doc = pymupdf.open()
    doc.new_page(width=PAGE_W, height=PAGE_H).insert_text((72, 100), "Conteúdo secreto")
    return _save(
        doc,
        out / "protegido.pdf",
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        user_pw=PASSWORD,
        owner_pw=PASSWORD + "-dono",
    )


def build_corrompido(out: Path) -> Path:
    """Arquivo com cabeçalho %PDF mas conteúdo truncado/ininteligível."""
    path = out / "corrompido.pdf"
    path.write_bytes(
        b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n" + b"\x00\xff" * 64
    )
    return path


def build_vazio(out: Path) -> Path:
    """Arquivo de 0 byte."""
    path = out / "vazio.pdf"
    path.write_bytes(b"")
    return path


def build_pagina_em_branco(out: Path) -> Path:
    """PDF válido de 1 página sem texto e sem imagem."""
    doc = pymupdf.open()
    doc.new_page(width=PAGE_W, height=PAGE_H)
    return _save(doc, out / "pagina_em_branco.pdf")


def build_nota_rodape_juridica(out: Path) -> Path:
    """Notas de rodapé jurídicas na margem inferior (NÃO devem ser removidas) + numeração."""
    doc = pymupdf.open()
    notas = [
        "1 Constituição Federal, art. 5º, inciso II: ninguém será obrigado a fazer ou deixar de "
        "fazer alguma coisa senão em virtude de lei.",
        "1 Lei 8.112/90, art. 41: são estáveis após três anos de efetivo exercício os servidores.",
        "1 Súmula Vinculante 13 do STF veda a prática de nepotismo na administração pública.",
        "1 Lei 14.133/21, art. 5º: a aplicação desta Lei observará os princípios da legalidade.",
    ]
    for i, nota in enumerate(notas, start=1):
        page = doc.new_page(width=PAGE_W, height=PAGE_H)
        _lines(page, 72, 120, [f"TEXTO-PRINCIPAL-{i} {LOREM}¹"], 78)
        _lines(page, 72, 775, [nota], 95, size=8, leading=10, gap=0)
        page.insert_text((290, 825), str(i), fontsize=9, fontname=FONT)
    return _save(doc, out / "nota_rodape_juridica.pdf")


def build_texto_juridico(out: Path) -> Path:
    """Texto jurídico com Art., §, incisos e Lei 8.666/93."""
    doc = pymupdf.open()
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    _lines(
        page,
        72,
        110,
        [
            "Art. 5º Todos são iguais perante a lei, sem distinção de qualquer natureza.",
            "§ 1º As normas definidoras dos direitos e garantias fundamentais têm aplicação imediata.",
            "I - homens e mulheres são iguais em direitos e obrigações;",
            "II - ninguém será obrigado a fazer ou deixar de fazer alguma coisa senão em virtude de lei.",
            "A Lei 8.666/93 institui normas para licitações e contratos da Administração Pública.",
            "(CESPE/2019) Julgue o item a seguir sobre o princípio da legalidade.",
            "a) alternativa um; b) alternativa dois.",
        ],
        90,
        gap=8,
    )
    return _save(doc, out / "texto_juridico.pdf")


def build_grande_500(out: Path) -> Path:
    """500 páginas com cabeçalho, rodapé numerado e corpo (teste de desempenho `slow`)."""
    doc = pymupdf.open()
    for i in range(1, 501):
        page = doc.new_page(width=PAGE_W, height=PAGE_H)
        page.insert_text((72, 40), "Curso Exemplo - Prof. Fulano", fontsize=9, fontname=FONT)
        _lines(page, 72, 110, [f"Página interna {i}. {LOREM}"] * 4, 78, gap=10)
        page.insert_text((72, 810), f"Página {i} de 500", fontsize=9, fontname=FONT)
    return _save(doc, out / "grande_500.pdf", garbage=1)


BUILDERS: dict[str, Callable[[Path], Path]] = {
    "uma_coluna": build_uma_coluna,
    "duas_colunas": build_duas_colunas,
    "cabecalho_rodape": build_cabecalho_rodape,
    "somente_imagem": build_somente_imagem,
    "protegido": build_protegido,
    "corrompido": build_corrompido,
    "vazio": build_vazio,
    "pagina_em_branco": build_pagina_em_branco,
    "nota_rodape_juridica": build_nota_rodape_juridica,
    "texto_juridico": build_texto_juridico,
}
SLOW_BUILDERS: dict[str, Callable[[Path], Path]] = {"grande_500": build_grande_500}

DEFAULT_OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "sinteticos"


def build_all(out_dir: Path, *, include_slow: bool = False) -> dict[str, Path]:
    """Gera as fixtures e devolve nome -> caminho (a de 500 páginas só com `include_slow`)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    builders = {**BUILDERS, **(SLOW_BUILDERS if include_slow else {})}
    return {name: builder(out_dir) for name, builder in builders.items()}


def main(argv: list[str]) -> int:
    """Ponto de entrada de linha de comando (gera todas, inclusive a de 500 páginas)."""
    out_dir = Path(argv[1]) if len(argv) > 1 else DEFAULT_OUT
    built = build_all(out_dir, include_slow=True)
    for name, path in built.items():
        print(f"{name}: {path}")
    print(f"{len(built)} fixture(s) em {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
