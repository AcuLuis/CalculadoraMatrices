# Calculadora de Matrices

Aplicacion de escritorio para el calculo de propiedades de matrices cuadradas (2x2 y 3x3).
Desarrollada en Python con interfaz grafica basada en Tkinter y calculos numericos con NumPy.

---

## Descripcion

Este programa permite ingresar los coeficientes de una matriz cuadrada y calcular
las siguientes propiedades de algebra lineal:

- Polinomio caracteristico P(lambda)
- Valores propios (eigenvalues)
- Vectores propios (eigenvectors)
- Determinante
- Matriz inversa (cuando existe)
- Transpuesta
- Rango
- Traza

Soporta matrices de dimension 2x2 y 3x3. Incluye la opcion de calcular todas
las propiedades de forma simultanea.

---

## Requisitos

| Componente | Version minima |
|------------|---------------|
| Python     | 3.8+          |
| NumPy      | 1.20+         |

Tkinter viene incluido en la instalacion estandar de Python en Windows.
En distribuciones Linux puede requerir instalacion separada (`python3-tk`).

### Instalacion de dependencias

```bash
pip install numpy
```

---

## Ejecucion

```bash
python Matrices.py
```

La aplicacion abrira una ventana principal donde se selecciona la dimension
de la matriz (2x2 o 3x3). Al seleccionar una dimension, se abre una ventana
secundaria con el formulario de entrada y el panel de resultados.

---

## Uso

1. Seleccionar la dimension de la matriz en la ventana principal.
2. Ingresar los valores numericos en la cuadricula de entrada.
3. Seleccionar el calculo deseado mediante los botones individuales, o
   presionar "Calcular Todo" (tambien con la tecla Enter) para obtener
   todos los resultados.
4. Usar "Limpiar" (Ctrl+L) para reiniciar los campos.
5. Usar "Volver" (Esc) para regresar a la seleccion de dimension.

### Atajos de teclado

| Atajo   | Accion                        |
|---------|-------------------------------|
| Enter   | Calcular todas las propiedades |
| Ctrl+L  | Limpiar campos y resultados   |
| Esc     | Volver al menu principal      |

---

## Estructura del proyecto

```
CalculadoraMatrices/
├── Matrices.py        # Codigo fuente principal (logica y GUI)
├── README.md          # Documentacion del proyecto
└── IMAGES/            # Recursos graficos de referencia
    ├── numeros.jpg
    ├── matriz-2x2-2.jpg
    └── matriz-3x3.jpg
```

---

## Arquitectura del codigo

El programa esta organizado en los siguientes componentes:

### Funciones de calculo

Funciones puras sin dependencia de la interfaz grafica:

- `formatear_polinomio()` — Genera la representacion en texto del polinomio
  caracteristico con superindices Unicode.
- `formatear_numero_complejo()` — Formatea numeros reales y complejos.
- `formatear_matriz()` — Representa una matriz NumPy como texto alineado.
- `calcular_valores_propios()` — Wrapper sobre `numpy.linalg.eigvals`.
- `calcular_vectores_propios()` — Wrapper sobre `numpy.linalg.eig`.
- `calcular_determinante()` — Wrapper sobre `numpy.linalg.det`.
- `calcular_inversa()` — Calcula la inversa o retorna `None` si es singular.
- `calcular_rango()` — Wrapper sobre `numpy.linalg.matrix_rank`.
- `calcular_traza()` — Wrapper sobre `numpy.trace`.

### Clases de interfaz

- `ScrollableFrame` — Frame con scroll vertical para el panel de resultados.
- `VentanaMatriz` — Ventana secundaria con la cuadricula de entrada, botones
  de calculo y panel de resultados para una dimension N x N.
- `CalculadoraApp` — Ventana principal con la seleccion de dimension.

---

## Ejemplo

### Matriz 2x2

Entrada:

```
| 1  2 |
| 3  4 |
```

Resultados:

| Propiedad                | Valor                              |
|--------------------------|-------------------------------------|
| Polinomio caracteristico | lambda^2 - 5*lambda - 2             |
| Valores propios          | lambda_1 = 5.3723, lambda_2 = -0.3723 |
| Determinante             | det(A) = -2                         |
| Rango                    | rango(A) = 2                        |
| Traza                    | tr(A) = 5                           |

### Matriz 3x3

Entrada:

```
| 1  2  3 |
| 4  5  6 |
| 7  8  9 |
```

Resultados:

| Propiedad                | Valor                                          |
|--------------------------|-------------------------------------------------|
| Polinomio caracteristico | lambda^3 - 15*lambda^2 - 18*lambda              |
| Valores propios          | lambda_1 = 16.1168, lambda_2 = -1.1168, lambda_3 = 0 |
| Determinante             | det(A) = 0                                      |
| Rango                    | rango(A) = 2                                    |
| Traza                    | tr(A) = 15                                      |

---

## Licencia

Este proyecto esta bajo la licencia MIT.