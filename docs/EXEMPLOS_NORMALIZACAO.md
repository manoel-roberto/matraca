# Exemplos de Normalização Textual (Antes e Depois)

Tabela gerada a partir dos testes golden (`tests/golden/casos_normalizacao.tsv`).
Estes casos garantem a fidelidade jurídica e a pronúncia fluida em português brasileiro para narração via TTS.

| Nº | Entrada (Texto original) | Saída (Texto para narração) | Regra / Observação |
|:---|:---|:---|:---|
| 1 | `Art. 5º, inciso II` | `Artigo quinto, inciso dois` | Artigo ordinal até 9 e inciso cardinal |
| 2 | `Art. 37, caput` | `Artigo trinta e sete, caput` | Artigo cardinal a partir de 10 |
| 3 | `Arts. 5º e 6º` | `Artigos quinto e sexto` | Plural de artigos até 9 |
| 4 | `§ 1º` | `parágrafo primeiro` | Parágrafo ordinal até 9 |
| 5 | `§ 2º` | `parágrafo segundo` | Parágrafo ordinal 2 |
| 6 | `§ 10` | `parágrafo dez` | Parágrafo cardinal a partir de 10 |
| 7 | `§ 1º do art. 7º` | `parágrafo primeiro do Artigo sétimo` | Referência composta |
| 8 | `§ único` | `parágrafo único` | Parágrafo único |
| 9 | `§§ 1º e 2º` | `parágrafos primeiro e segundo` | Plural de parágrafos |
| 10 | `Lei 8.666/93` | `Lei oito mil seiscentos e sessenta e seis, de noventa e três` | Lei com barra e ano curto |
| 11 | `Lei nº 14.133, de 1º de abril de 2021` | `Lei número catorze mil cento e trinta e três, de primeiro de abril de dois mil e vinte e um` | Lei completa com data por extenso |
| 12 | `Decreto-Lei 200/67` | `Decreto-Lei duzentos, de sessenta e sete` | Decreto-Lei com barra |
| 13 | `10%` | `dez por cento` | Porcentagem inteira |
| 14 | `2,5%` | `dois vírgula cinco por cento` | Porcentagem decimal |
| 15 | `R$ 1.250,00` | `mil duzentos e cinquenta reais` | Moeda com milhar |
| 16 | `R$ 0,50` | `cinquenta centavos` | Moeda apenas centavos |
| 17 | `01/02/2020` | `primeiro de fevereiro de dois mil e vinte` | Data completa padrão dd/mm/aaaa |
| 18 | `3/4` | `3/4` | Caso ambíguo mantido (fração) |
| 19 | `2020/2021` | `2020/2021` | Caso ambíguo mantido (período/exercício) |
| 20 | `Martin` | `Martin` | Caso negativo: Art. em palavra |
| 21 | `Particular` | `Particular` | Caso negativo: art em palavra |
| 22 | `Cart.` | `Cart.` | Caso negativo: abreviação de cartório não vira artigo |
| 23 | `Rei João II` | `Rei João segundo` | Caso negativo: numeral romano não é inciso |
| 24 | `Século XX` | `Século vinte` | Caso negativo: século não é inciso |
| 25 | `Capítulo II` | `Capítulo segundo` | Caso negativo: capítulo não é inciso |
| 26 | `II - homens e mulheres` | `inciso dois - homens e mulheres` | Inciso no início de linha |
| 27 | `c/c o art. 10` | `combinado com o Artigo dez` | Abreviação c/c |
| 28 | `p. ex. na lei` | `por exemplo na lei` | Abreviação p. ex. |
| 29 | `nº 123` | `número 123` | Abreviação nº |
| 30 | `n.º 456` | `número 456` | Abreviação n.º |
| 31 | `1.234.567` | `um milhão duzentos e trinta e quatro mil quinhentos e sessenta e sete` | Número com separador de milhar |
| 32 | `1.234,56` | `mil duzentos e trinta e quatro vírgula cinquenta e seis` | Decimal com separador de milhar |
| 33 | `0,75` | `zero vírgula setenta e cinco` | Decimal menor que 1 |
| 34 | `100%` | `cem por cento` | Cem por cento |
| 35 | `0,5%` | `zero vírgula cinco por cento` | Meio por cento |
| 36 | `R$ 1,00` | `um real` | Moeda no singular |
| 37 | `R$ 2,00` | `dois reais` | Moeda no plural |
| 38 | `R$ 1.000.000,00` | `um milhão de reais` | Moeda um milhão |
| 39 | `Art. 1º` | `Artigo primeiro` | Artigo 1 ordinal |
| 40 | `Art. 2º` | `Artigo segundo` | Artigo 2 ordinal |
| 41 | `Art. 3º` | `Artigo terceiro` | Artigo 3 ordinal |
| 42 | `Art. 4º` | `Artigo quarto` | Artigo 4 ordinal |
| 43 | `Art. 6º` | `Artigo sexto` | Artigo 6 ordinal |
| 44 | `Art. 7º` | `Artigo sétimo` | Artigo 7 ordinal |
| 45 | `Art. 8º` | `Artigo oitavo` | Artigo 8 ordinal |
| 46 | `Art. 9º` | `Artigo nono` | Artigo 9 ordinal |
| 47 | `Art. 10` | `Artigo dez` | Artigo 10 cardinal |
| 48 | `Art. 11` | `Artigo onze` | Artigo 11 cardinal |
| 49 | `Art. 99` | `Artigo noventa e nove` | Artigo 99 cardinal |
| 50 | `Art. 100` | `Artigo cem` | Artigo 100 cardinal |
| 51 | `§ 3º` | `parágrafo terceiro` | Parágrafo 3 ordinal |
| 52 | `§ 4º` | `parágrafo quarto` | Parágrafo 4 ordinal |
| 53 | `§ 5º` | `parágrafo quinto` | Parágrafo 5 ordinal |
| 54 | `§ 6º` | `parágrafo sexto` | Parágrafo 6 ordinal |
| 55 | `§ 7º` | `parágrafo sétimo` | Parágrafo 7 ordinal |
| 56 | `§ 8º` | `parágrafo oitavo` | Parágrafo 8 ordinal |
| 57 | `§ 9º` | `parágrafo nono` | Parágrafo 9 ordinal |
| 58 | `§ 11` | `parágrafo onze` | Parágrafo 11 cardinal |
| 59 | `§ 20` | `parágrafo vinte` | Parágrafo 20 cardinal |
| 60 | `inciso I` | `inciso um` | Inciso 1 |
| 61 | `inciso III` | `inciso três` | Inciso 3 |
| 62 | `inciso IV` | `inciso quatro` | Inciso 4 |
| 63 | `inciso V` | `inciso cinco` | Inciso 5 |
| 64 | `inciso VI` | `inciso seis` | Inciso 6 |
| 65 | `inciso VII` | `inciso sete` | Inciso 7 |
| 66 | `inciso VIII` | `inciso oito` | Inciso 8 |
| 67 | `inciso IX` | `inciso nove` | Inciso 9 |
| 68 | `inciso X` | `inciso dez` | Inciso 10 |
| 69 | `inc. I` | `inciso um` | Abreviação inc. |
| 70 | `al. a` | `alínea a` | Abreviação al. |
| 71 | `alínea b` | `alínea b` | Alínea preservada |
| 72 | `Portaria 123/2020` | `Portaria cento e vinte e três, de dois mil e vinte` | Portaria com barra |
| 73 | `Resolução 45/99` | `Resolução quarenta e cinco, de noventa e nove` | Resolução com barra |
| 74 | `05/10/1988` | `cinco de outubro de mil novecentos e oitenta e oito` | Data da CF/88 |
| 75 | `15/11/1889` | `quinze de novembro de mil oitocentos e oitenta e nove` | Data da Proclamação |
| 76 | `31/12/2023` | `trinta e um de dezembro de dois mil e vinte e três` | Último dia do ano |
| 77 | `CF/88` | `Constituição Federal de oitenta e oito` | Sigla CF/88 |
| 78 | `STF` | `S T F` | Sigla STF |
| 79 | `STJ` | `S T J` | Sigla STJ |
| 80 | `OAB` | `O A B` | Sigla OAB |
| 81 | `CLT` | `C L T` | Sigla CLT |
| 82 | `CPC` | `C P C` | Sigla CPC |
| 83 | `pala-\nvra` | `palavra` | Hifenização quebrada em linha |
| 84 | `ex-\npresidente` | `ex-presidente` | Hifenização de prefixo ex mantida |
| 85 | `anti-\ninflamatório` | `anti-inflamatório` | Hifenização de prefixo anti mantida |
| 86 | `Texto com “aspas” e ‘aspas’` | `Texto com "aspas" e 'aspas'` | Normalização de aspas |
| 87 | `Texto com  espaços   duplos` | `Texto com espaços duplos` | Limpeza de múltiplos espaços |

## Revisão manual amostral (20 casos verificados conforme critério da Fase 3)

1. `Art. 5º, inciso II` → `Artigo quinto, inciso dois` (OK: ordinal até 9 e cardinal no inciso)
2. `Art. 37, caput` → `Artigo trinta e sete, caput` (OK: cardinal a partir de 10 e caput mantido)
3. `Arts. 5º e 6º` → `Artigos quinto e sexto` (OK: plural coordenado)
4. `§ 1º` → `parágrafo primeiro` (OK: parágrafo ordinal)
5. `§ 10` → `parágrafo dez` (OK: parágrafo cardinal)
6. `§ 1º do art. 7º` → `parágrafo primeiro do Artigo sétimo` (OK: combinação harmônica)
7. `Lei 8.666/93` → `Lei oito mil seiscentos e sessenta e seis, de noventa e três` (OK: lei por extenso com ano)
8. `Lei nº 14.133, de 1º de abril de 2021` → `Lei número catorze mil cento e trinta e três, de primeiro de abril de dois mil e vinte e um` (OK: número e data por extenso)
9. `Decreto-Lei 200/67` → `Decreto-Lei duzentos, de sessenta e sete` (OK: decreto por extenso)
10. `10%` / `2,5%` → `dez por cento` / `dois vírgula cinco por cento` (OK: percentual exato)
11. `R$ 1.250,00` → `mil duzentos e cinquenta reais` (OK: moeda correta)
12. `01/02/2020` → `primeiro de fevereiro de dois mil e vinte` (OK: primeiro dia do mês por extenso)
13. `3/4` → `3/4` (OK: caso ambíguo intocado)
14. `2020/2021` → `2020/2021` (OK: período/ano mantido intocado)
15. `Martin` / `Particular` / `Cart.` → inalterados (OK: sem falso positivo com 'Art.')
16. `Rei João II` → `Rei João segundo` (OK: monarca não vira inciso)
17. `Século XX` → `Século vinte` (OK: século não vira inciso)
18. `1.234.567` → `um milhão duzentos e trinta e quatro mil quinhentos e sessenta e sete` (OK: milhar expandido)
19. `CF/88` → `Constituição Federal de oitenta e oito` (OK: sigla jurídica principal expandida)
20. `pala-\nvra` → `palavra` (OK: hifenização de quebra de linha unificada)
