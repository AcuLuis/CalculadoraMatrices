# Calculadora de Matrices

Aplicacion de escritorio para el calculo de propiedades de matrices cuadradas (de 2x2 a 6x6).
Desarrollada en Python con interfaz grafica basada en Tkinter y calculos numericos con NumPy.

---

## Descripcion

Este programa permite ingresar los coeficientes de una matriz cuadrada y calcular
las siguientes propiedades de algebra lineal:

- Polinomio caracteristico P(lambda) = det(lambda I - A)
- Valores propios (eigenvalues), con su multiplicidad
- Vectores propios (eigenvectors), escalados para leerse facilmente (por ejemplo `[1, 2]`
  en lugar de `[0.4472, 0.8944]`)
- Determinante
- Matriz inversa (cuando existe), con aviso si la matriz esta mal condicionada
- Transpuesta
- Rango
- Traza

Detecta los casos especiales en lugar de mostrar resultados enganosos:

- Matrices singulares: se decide por el rango, no comparando el determinante con un
  umbral fijo (asi `1e-6 * I` se reconoce como invertible).
- Matrices no diagonalizables: se muestran solo los vectores propios independientes
  y se indica que la matriz no es diagonalizable.
- Ruido numerico: nunca se muestra `-0`, y los resultados de matrices enteras
  (determinante, polinomio) se muestran como enteros exactos.

---

## Requisitos

| Componente | Version minima |
|------------|---------------|
| Python     | 3.8+          |
| NumPy      | 1.20+         |
| pytest     | (solo para los tests) |

Tkinter viene incluido en la instalacion estandar de Python en Windows.
En distribuciones Linux puede requerir instalacion separada (`python3-tk`).

### Instalacion de dependencias

```bash
pip install numpy
pip install pytest   # opcional, para ejecutar los tests
```

---

## Ejecucion

```bash
python Matrices.py
```

---

## Uso

1. Elegir la dimension (2x2 a 6x6) en la barra superior. Al cambiarla se conservan
   los valores que caben.
2. Escribir los valores en la cuadricula. Se aceptan:
   - coma o punto decimal: `0,5` o `0.5`
   - fracciones: `1/2`, `-3/4`
   - notacion cientifica: `1e3`
3. Pulsar "Calcular todo" (Enter) o el boton de una operacion concreta. Los botones
   individuales agregan su resultado sin borrar los demas.
4. Al editar la matriz, los resultados visibles se recalculan automaticamente. Si
   alguna celda es invalida, los resultados se atenuan y se avisa de que no
   corresponden a los datos actuales.

Otras funciones:

- **Pegar una matriz** (Ctrl+V en una celda): desde Excel u hojas de calculo, o como
  texto (`1 2; 3 4`, `[[1, 2], [3, 4]]`, salida de NumPy). Si es cuadrada y se pega
  en la primera celda, la dimension se ajusta sola; si no, se pega como bloque a
  partir de la celda seleccionada.
- **Ejemplos**: identidad, matriz aleatoria y ejemplos ilustrativos (singular,
  simetrica, valor propio repetido, no diagonalizable, valores propios complejos).
- **Celdas vacias = 0**: si esta activado, las celdas vacias cuentan como cero (y se
  indica cuantas). Si no, se marcan como error.
- **Errores en la propia celda**: las celdas invalidas se marcan en rojo y bajo la
  cuadricula se explica el problema de cada una, sin ventanas emergentes.
- **Copiar**: cada resultado tiene su boton "Copiar"; "Copiar resultados" copia la
  matriz y todos los resultados. Las matrices copiadas se pueden volver a pegar.
- **Cerrar resultados**: el boton de cada tarjeta la quita del panel.

### Atajos de teclado

| Atajo          | Accion                                  |
|----------------|-----------------------------------------|
| Enter          | Calcular todas las propiedades          |
| Flechas        | Moverse entre celdas                    |
| Ctrl+V         | Pegar una matriz                        |
| Ctrl+2 ... Ctrl+6 | Cambiar la dimension                 |
| Ctrl+Shift+C   | Copiar la matriz y todos los resultados |
| Ctrl+L         | Limpiar campos y resultados             |

---

## Estructura del proyecto

```
CalculadoraMatrices/
├── Matrices.py          # Interfaz grafica (punto de entrada)
├── calculos.py          # Logica: calculos, interpretacion de entradas y formato
├── tests/
│   └── test_calculos.py # Tests de la logica
├── README.md            # Documentacion del proyecto
└── IMAGES/              # Recursos graficos de referencia
    ├── numeros.jpg
    ├── matriz-2x2-2.jpg
    └── matriz-3x3.jpg
```

---

## Arquitectura del codigo

### `calculos.py` (sin dependencia de la interfaz)

Interpretacion de entradas:

- `parsear_valor()` — Convierte el texto de una celda en numero (coma decimal,
  fracciones, signo menos Unicode). Rechaza `nan`, `inf` y textos no numericos con un
  mensaje legible.
- `parsear_texto_matriz()` — Interpreta texto pegado como filas de celdas.

Formato:

- `formatear_numero()` — Reales y complejos, sin `-0`, sin recortar cifras y con
  notacion cientifica solo para valores muy pequenos o muy grandes.
- `formatear_vector()`, `formatear_matriz()` (columnas alineadas),
  `formatear_polinomio()` (superindices Unicode).

Calculos:

- `calcular_polinomio()`, `calcular_determinante()`, `calcular_rango()`,
  `calcular_traza()`.
- `calcular_inversa()` — Devuelve `(inversa, numero de condicion)`; la inversa es
  `None` si la matriz es singular.
- `calcular_espacios_propios()` — Valores propios distintos con su multiplicidad
  algebraica y una base de su espacio propio (calculada por forma escalonada, como a
  mano). Agrupa los valores propios repetidos aunque NumPy los separe por error
  numerico.

Operaciones listas para mostrar:

- `OPERACIONES` — Lista `(clave, etiqueta, funcion)` en orden canonico.
- `calcular(matriz, claves)` — Devuelve una lista de `Resultado(clave, titulo,
  texto, tipo)`, donde `tipo` es `"ok"`, `"aviso"` o `"error"`. Nunca lanza
  excepciones.

### `Matrices.py` (interfaz)

- `ScrollableFrame` — Panel con scroll; la rueda del raton funciona sobre cualquier
  elemento interior (Windows, macOS y Linux), y con Shift desplaza en horizontal.
- `Tarjeta` — Muestra un `Resultado` con botones para copiarlo y cerrarlo.
- `CalculadoraApp` — Ventana unica con la cuadricula de entrada, las operaciones y
  los resultados.

---

## Tests

```bash
python -m pytest
```

Cubren el formato de numeros, la interpretacion de entradas y los calculos,
incluidos los casos limite (matrices singulares, mal condicionadas, no
diagonalizables y con valores propios complejos).

---

## Ejemplo

### Matriz 2x2

Entrada:

```
| 1  2 |
| 3  4 |
```

Resultados:

| Propiedad                | Valor                                     |
|--------------------------|-------------------------------------------|
| Polinomio caracteristico | P(lambda) = lambda^2 - 5*lambda - 2       |
| Valores propios          | lambda_1 = 5.3723, lambda_2 = -0.3723     |
| Determinante             | det(A) = -2                               |
| Inversa                  | [[-2, 1], [1.5, -0.5]]                    |
| Rango                    | rango(A) = 2                              |
| Traza                    | tr(A) = 5                                 |

### Matriz 3x3

Entrada:

```
| 1  2  3 |
| 4  5  6 |
| 7  8  9 |
```

Resultados:

| Propiedad                | Valor                                              |
|--------------------------|----------------------------------------------------|
| Polinomio caracteristico | P(lambda) = lambda^3 - 15*lambda^2 - 18*lambda     |
| Valores propios          | lambda_1 = 16.1168, lambda_2 = 0, lambda_3 = -1.1168 |
| Vector propio de lambda = 0 | v = [1, -2, 1]                                  |
| Determinante             | det(A) = 0                                         |
| Inversa                  | No tiene (la matriz es singular)                   |
| Rango                    | rango(A) = 2                                       |
| Traza                    | tr(A) = 15                                         |

---

## Licencia

Este proyecto esta bajo la licencia MIT.
