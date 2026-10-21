import math

import numpy as np
import pytest

from calculos import (
    CLAVES,
    calcular,
    calcular_determinante,
    calcular_espacios_propios,
    calcular_inversa,
    calcular_polinomio,
    calcular_valores_propios,
    escalar_vector,
    formatear_matriz,
    formatear_numero,
    formatear_polinomio,
    parsear_texto_matriz,
    parsear_valor,
)

EJEMPLO_2X2 = np.array([[1, 2], [3, 4]], dtype=float)
EJEMPLO_3X3 = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=float)


def _es_vector_propio(A, valor, v):
    return np.allclose(A @ v, valor * v, atol=1e-8)


# ── Formato ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("valor, esperado", [
    (0.0, "0"),
    (-0.0, "0"),
    (-1e-17, "-1e-17"),        # no se oculta un valor no nulo...
    (2.5, "2.5"),
    (-3.0, "-3"),
    (1 / 3, "0.3333"),
    (12345.6789, "12345.6789"),  # sin recortar a 6 cifras
    (1234567.0, "1234567"),      # sin notación científica
    (1e-6, "1e-6"),              # ...pero no se muestra como 0
    (1.5e13, "1.5e13"),
])
def test_formatear_real(valor, esperado):
    assert formatear_numero(valor) == esperado


@pytest.mark.parametrize("valor, esperado", [
    (complex(1, 2), "1 + 2i"),
    (complex(1, -2), "1 - 2i"),
    (complex(0, 1), "i"),
    (complex(0, -1), "-i"),
    (complex(3, 1e-20), "3"),
    (complex(0.5, -0.8660254), "0.5 - 0.866i"),
])
def test_formatear_complejo(valor, esperado):
    assert formatear_numero(valor) == esperado


def test_formatear_matriz_alinea_columnas():
    texto = formatear_matriz(np.array([[1, -2.5], [10, 3]]))
    assert texto == "[  1  -2.5 ]\n[ 10     3 ]"


def test_formatear_polinomio():
    assert formatear_polinomio([1, -5, -2]) == "λ² − 5λ − 2"
    assert formatear_polinomio([-1, 0, 1]) == "−λ² + 1"
    assert formatear_polinomio([1, 0.5, 0]) == "λ² + 0.5λ"
    assert formatear_polinomio([0, 0]) == "0"


# ── Interpretación de entradas ───────────────────────────────────────

@pytest.mark.parametrize("texto, esperado", [
    ("3", 3.0),
    (" -2.5 ", -2.5),
    ("0,5", 0.5),
    ("1/2", 0.5),
    ("-3/4", -0.75),
    ("1,5/3", 0.5),
    ("−2", -2.0),
    ("1e3", 1000.0),
    (".5", 0.5),
])
def test_parsear_valor_validos(texto, esperado):
    assert parsear_valor(texto) == pytest.approx(esperado)


@pytest.mark.parametrize("texto, mensaje", [
    ("", "vacía"),
    ("nan", "no es un número"),
    ("inf", "no es un número"),
    ("1_000", "no es un número"),
    ("abc", "no es un número"),
    ("1 2", "no es un número"),
    ("1/0", "división por cero"),
    ("1/2/3", "no es un número"),
    ("1e400", "demasiado grande"),
])
def test_parsear_valor_invalidos(texto, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        parsear_valor(texto)


@pytest.mark.parametrize("texto", [
    "1\t2\n3\t4",
    "1 2; 3 4",
    "1, 2\n3, 4",
    "[[1, 2], [3, 4]]",
    "array([[1, 2],\n       [3, 4]])",
    "[1 2]\n [3 4]",
])
def test_parsear_texto_matriz(texto):
    assert parsear_texto_matriz(texto) == [["1", "2"], ["3", "4"]]


def test_parsear_texto_matriz_coma_decimal():
    assert parsear_texto_matriz("0,5 1\n2 3,25") == [["0,5", "1"], ["2", "3,25"]]


def test_formatear_matriz_se_puede_volver_a_pegar():
    A = np.array([[1, -2.5], [10, 3]])
    filas = parsear_texto_matriz(formatear_matriz(A))
    assert np.array([[parsear_valor(c) for c in f] for f in filas]).tolist() == A.tolist()


# ── Cálculos ─────────────────────────────────────────────────────────

def test_ejemplos_readme():
    assert formatear_polinomio(calcular_polinomio(EJEMPLO_2X2)) == "λ² − 5λ − 2"
    assert formatear_polinomio(calcular_polinomio(EJEMPLO_3X3)) == "λ³ − 15λ² − 18λ"
    assert calcular_determinante(EJEMPLO_2X2) == -2
    assert [formatear_numero(v) for v in calcular_valores_propios(EJEMPLO_3X3)] == [
        "16.1168", "0", "-1.1168"
    ]


def test_determinante_singular_es_cero_exacto():
    assert calcular_determinante(EJEMPLO_3X3) == 0.0
    # Escalada: el ruido numérico del determinante sería ~1e2
    assert calcular_determinante(EJEMPLO_3X3 * 1e6) == 0.0


def test_inversa_no_depende_de_la_escala():
    inv, cond = calcular_inversa(np.eye(2) * 1e-6)
    assert inv is not None
    assert np.allclose(inv, np.eye(2) * 1e6)
    assert cond == pytest.approx(1.0)


def test_inversa_singular():
    inv, cond = calcular_inversa(EJEMPLO_3X3)
    assert inv is None and math.isinf(cond)


def test_inversa_mal_condicionada_avisa():
    A = np.array([[1, 1], [1, 1 + 1e-9]])
    (resultado,) = calcular(A, ["inversa"])
    assert resultado.tipo == "aviso"
    assert "mal condicionada" in resultado.texto


def test_escalar_vector():
    assert escalar_vector([0.4472136, 0.8944272]).tolist() == [1, 2]
    assert escalar_vector([-0.8944272, 0.4472136]).tolist() == [2, -1]
    assert escalar_vector([0, -0.7071, 0.7071]).tolist() == [0, 1, -1]


def test_vectores_propios_legibles_y_correctos():
    A = np.array([[1, 2], [2, 4]], dtype=float)
    espacios = calcular_espacios_propios(A)
    assert [e.valor for e in espacios] == [5, 0]
    assert espacios[0].vectores[0].tolist() == [1, 2]
    assert espacios[1].vectores[0].tolist() == [2, -1]


def test_matriz_defectiva_no_inventa_vectores():
    for A in ([[1, 1], [0, 1]], [[2, 1], [-1, 0]]):
        A = np.array(A, dtype=float)
        (espacio,) = calcular_espacios_propios(A)
        assert espacio.multiplicidad == 2
        assert espacio.multiplicidad_geometrica == 1
        assert espacio.defectivo
        assert _es_vector_propio(A, espacio.valor, espacio.vectores[0])

    (resultado,) = calcular(np.array([[1, 1], [0, 1.0]]), ["vectores"])
    assert resultado.tipo == "aviso"
    assert "no es diagonalizable" in resultado.texto


@pytest.mark.parametrize("n", [3, 4, 5, 6])
def test_bloque_de_jordan_con_cambio_de_base(n):
    # Los valores propios se separan numéricamente ~ε^(1/n); deben agruparse
    rng = np.random.default_rng(n)
    J = 2 * np.eye(n) + np.diag(np.ones(n - 1), 1)
    P = rng.integers(-3, 4, (n, n)).astype(float)
    while abs(np.linalg.det(P)) < 0.5:
        P = rng.integers(-3, 4, (n, n)).astype(float)
    A = P @ J @ np.linalg.inv(P)
    (espacio,) = calcular_espacios_propios(A)
    assert espacio.valor == pytest.approx(2)
    assert espacio.multiplicidad == n
    assert espacio.multiplicidad_geometrica == 1


def test_valor_repetido_diagonalizable():
    A = np.array([[3, 1, 1], [1, 3, 1], [1, 1, 3]], dtype=float)
    espacios = calcular_espacios_propios(A)
    assert [(e.valor, e.multiplicidad, e.multiplicidad_geometrica) for e in espacios] == [
        (5, 1, 1), (2, 2, 2)
    ]
    for e in espacios:
        for v in e.vectores:
            assert _es_vector_propio(A, e.valor, v)
    # Primera componente no nula positiva
    assert [v.tolist() for v in espacios[1].vectores] == [[1, -1, 0], [1, 0, -1]]


def test_identidad():
    (espacio,) = calcular_espacios_propios(np.eye(3))
    assert espacio.valor == 1
    assert [v.tolist() for v in espacio.vectores] == [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


def test_valores_complejos():
    A = np.array([[0, -1], [1, 0]], dtype=float)
    espacios = calcular_espacios_propios(A)
    assert [formatear_numero(e.valor) for e in espacios] == ["i", "-i"]
    for e in espacios:
        assert _es_vector_propio(A, e.valor, e.vectores[0])


def test_calcular_todo_sin_errores():
    for A in (EJEMPLO_2X2, EJEMPLO_3X3, np.zeros((4, 4)), np.eye(6)):
        resultados = calcular(A)
        assert [r.clave for r in resultados] == CLAVES
        assert all(r.tipo != "error" for r in resultados)


def test_calcular_respeta_orden_canonico():
    resultados = calcular(EJEMPLO_2X2, ["traza", "polinomio"])
    assert [r.clave for r in resultados] == ["polinomio", "traza"]
