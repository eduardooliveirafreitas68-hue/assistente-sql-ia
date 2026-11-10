"""Testes do critério de comparação da avaliação (sem API)."""

import numpy as np

from avaliacao.avaliar import comparar_resultados


def test_exato_ignora_ordem_de_linhas_e_colunas_extras():
    gabarito = [("moto", 8.24), ("carro", 14.59)]
    obtido = [("carro", 120, 14.59), ("moto", 300, 8.24)]
    assert comparar_resultados(gabarito, obtido) == "exato"


def test_inteiros_numpy_e_python_sao_iguais():
    assert comparar_resultados([(12000,)], [(np.int64(12000),)]) == "exato"
    assert comparar_resultados([(5,), (12,)], [(np.float64(12.0),), (np.int64(5),)]) == "exato"


def test_rotulos_diferentes_com_numeros_iguais():
    gabarito = [("outros horários", 9.15), ("pico jantar", 29.93)]
    obtido = [("Outros horários", 5335, 488, 9.15), ("Pico do jantar (18h-21h)", 5964, 1785, 29.93)]
    assert comparar_resultados(gabarito, obtido) == "numeros"


def test_numeros_diferentes_e_errado():
    gabarito = [("Pizza Quatro Queijos", 1352), ("Pizza Calabresa", 1339)]
    obtido = [("Pizza Quatro Queijos", 1436), ("Pizza Calabresa", 1411)]
    assert comparar_resultados(gabarito, obtido) is None


def test_quantidade_de_linhas_diferente_e_errado():
    assert comparar_resultados([(1,), (2,)], [(1,)]) is None


def test_so_texto_diferente_sem_colunas_numericas_e_errado():
    assert comparar_resultados([("São Paulo",)], [("Recife",)]) is None
