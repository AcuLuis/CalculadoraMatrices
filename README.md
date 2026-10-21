# Calculadora de Matrices

Aplicacion de escritorio para el calculo de propiedades de matrices cuadradas (de 2x2 a 6x6).
Desarrollada en Python con interfaz grafica basada en Tkinter y calculos numericos con NumPy.

---

## Descripcion

Este programa permite ingresar los coeficientes de una matriz cuadrada A (y
opcionalmente una segunda matriz B) y calcular:

Propiedades de A:

- Polinomio caracteristico P(lambda) = det(lambda I - A)
- Valores propios (eigenvalues), con su multiplicidad
- Vectores propios (eigenvectors), escalados para leerse facilmente (por ejemplo `[1, 2]`
  en lugar de `[0.4472, 0.8944]`)
- Diagonalizacion A = P·D·P^-1 (o el motivo por el que no es diagonalizable)
- Determinante
- Matriz inversa (cuando existe), con aviso si la matriz esta mal condicionada
- Transpuesta
- Rango
- Traza
- Forma escalonada reducida por Gauss-Jordan, paso a paso (operaciones de fila)
- Propiedades: simetrica, antisimetrica, diagonal, triangular, ortogonal,
  idempotente, invertible, diagonalizable y definida positiva
- Potencia A^k (k entre -10 y 20; con k negativo usa la inversa)

Operaciones con B: A + B, A - B, A·B y B·A (indicando si A y B conmutan).

### Resultados exactos

Con la opcion "Resultados exactos" (activada por defecto) los calculos se hacen
con fracciones, sin redondeo:

- Inversas, determinantes, polinomios y pasos de Gauss-Jordan con fracciones:
  `[[-2, 1], [3/2, -1/2]]`.
- Valores propios racionales exactos y, cuando el resto del polinomio es de
  grado 2, con radicales: `lambda = (5 + √33)/2 ≈ 5.3723`.
- Vectores propios de valores propios racionales con componentes enteras.

Si una fraccion exacta resulta demasiado grande para leerse (denominador mayor
que 10000), ese resultado se muestra en decimales con una nota.

### Comprobaciones y casos especiales

- Cada resultado clave muestra su verificacion: A·v = lambda·v, A·A^-1 = I y
  A·P = P·D (exacta, o con el error numerico maximo).
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
2. Escribir los valores de A en la cuadricula. Se aceptan:
   - coma o punto decimal: `0,5` o `0.5`
   - fracciones: `1/2`, `-3/4`
   - notacion cientifica: `1e3`
3. Pulsar "Calcular todo" (Enter) o el boton de una operacion concreta. Los botones
   individuales agregan su resultado sin borrar los demas.
4. Para operar con dos matrices, escribir B en la pestana "Matriz B" y usar los
   botones de la fila "Con la matriz B".
5. Al editar las matrices, los resultados visibles se recalculan automaticamente. Si
   alguna celda es invalida, los resultados se atenuan y se avisa de que no
   corresponden a los datos actuales. Si un calculo no se pudo hacer por datos
   invalidos, se completa solo en cuanto se corrigen.

Otras funciones:

- **Pegar una matriz** (Ctrl+V en una celda): desde Excel u hojas de calculo, o como
  texto (`1 2; 3 4`, `[[1, 2], [3, 4]]`, salida de NumPy). Si es cuadrada y se pega
  en la primera celda, la dimension se ajusta sola; si no, se pega como bloque a
  partir de la celda seleccionada.
- **Ejemplos**: identidad, matriz aleatoria y ejemplos ilustrativos (singular,
  simetrica, valor propio repetido, no diagonalizable, valores propios complejos,
  con fracciones). Se cargan en la matriz visible (A o B).
- **Celdas vacias = 0**: si esta activado, las celdas vacias cuentan como cero (y se
  indica cuantas). Si no, se marcan como error.
- **Errores en la propia celda**: las celdas invalidas se marcan en rojo y bajo la
  cuadricula se explica el problema de cada una, sin ventanas emergentes.
- **Copiar**: cada resultado tiene su boton "Copiar"; "Copiar resultados" copia las
  matrices y todos los resultados. Las matrices copiadas se pueden volver a pegar.
- **Cerrar resultados**: el boton de cada tarjeta la quita del panel.

### Atajos de teclado

| Atajo          | Accion                                  |
|----------------|-----------------------------------------|
| Enter          | Calcular todas las propiedades de A     |
| Flechas        | Moverse entre celdas                    |
| Ctrl+V         | Pegar una matriz                        |
| Ctrl+2 ... Ctrl+6 | Cambiar la dimension                 |
| Ctrl+Shift+C   | Copiar las matrices y todos los resultados |
| Ctrl+L         | Limpiar campos y resultados             |

---

## Estructura del proyecto

```
CalculadoraMatrices/
├── Matrices.py          # Interfaz grafica (punto de entrada)
├── calculos.py          # Operaciones, interpretacion de entradas y formato
├── exacto.py            # Algebra exacta con fracciones
├── tests/
│   ├── test_calculos.py # Tests de operaciones, entradas y formato
│   └── test_exacto.py   # Tests del algebra exacta
├── README.md            # Documentacion del proyecto
└── IMAGES/              # Recursos graficos de referencia
    ├── numeros.jpg
    ├── matriz-2x2-2.jpg
    └── matriz-3x3.jpg
```

---

## Arquitectura del codigo

### `exacto.py` (algebra exacta, sin dependencia de la interfaz)

Matrices como listas de filas de `fractions.Fraction`:

- Operaciones basicas: `sumar()`, `multiplicar()`, `transpuesta()`, `traza()`,
  `potencia()`.
- `escalonar()` — Gauss-Jordan registrando cada operacion de fila. Funciona tambien
  con floats (con tolerancia y pivoteo parcial).
- `determinante()`, `rango()`, `inversa()`, `nucleo()` (base con vectores enteros).
- `polinomio_caracteristico()` — Metodo de Faddeev-LeVerrier.
- `factorizar()` — Separa las raices racionales del polinomio (se buscan cerca de
  las aproximaciones numericas y se verifican de forma exacta).
- `raices_cuadratica()` — Raices de un factor de grado 2 como `u ± v·√m`.

### `calculos.py` (sin dependencia de la interfaz)

Interpretacion de entradas:

- `parsear_fraccion()` / `parsear_valor()` — Convierten el texto de una celda en
  fraccion exacta o en float (coma decimal, fracciones, signo menos Unicode).
  Rechazan `nan`, `inf` y textos no numericos con un mensaje legible.
- `parsear_texto_matriz()` — Interpreta texto pegado como filas de celdas.

Formato:

- `formatear_numero()` — Reales y complejos, sin `-0`, sin recortar cifras y con
  notacion cientifica solo para valores muy pequenos o muy grandes.
- `formatear_fraccion()`, `formatear_radical()`, `formatear_vector()`,
  `formatear_matriz()` / `formatear_matriz_exacta()` (columnas alineadas),
  `formatear_polinomio()` (superindices Unicode).

Calculos numericos:

- `calcular_polinomio()`, `calcular_determinante()`, `calcular_rango()`,
  `calcular_traza()`, `calcular_inversa()` (devuelve tambien el numero de condicion).
- `calcular_espacios_propios()` — Valores propios distintos con su multiplicidad
  algebraica y una base de su espacio propio. Agrupa los valores propios repetidos
  aunque NumPy los separe por error numerico. Con la matriz en fracciones, usa el
  algebra exacta para los valores racionales y los radicales.

Operaciones listas para mostrar:

- `OPERACIONES` — Lista `(clave, etiqueta, funcion)` en orden canonico.
  `CLAVES_TODO` son las que calcula "Calcular todo"; `CLAVES_CON_B` las que usan B.
- `calcular(matriz, claves, matriz_b=..., exponente=..., exacto=...)` — Devuelve
  una lista de `Resultado(clave, titulo, texto, tipo, preformateado)`, donde `tipo`
  es `"ok"`, `"aviso"` o `"error"`. Nunca lanza excepciones.

### `Matrices.py` (interfaz)

- `ScrollableFrame` — Panel con scroll; la rueda del raton funciona sobre cualquier
  elemento interior (Windows, macOS y Linux), y con Shift desplaza en horizontal.
- `Tarjeta` — Muestra un `Resultado` con botones para copiarlo y cerrarlo, siempre
  visibles aunque una matriz ancha requiera scroll horizontal.
- `EditorMatriz` — Cuadricula de una matriz con validacion por celda y navegacion
  con flechas (se usa para A y para B).
- `CalculadoraApp` — Ventana unica con las cuadriculas, las operaciones y los
  resultados.

---

## Tests

```bash
python -m pytest
```

Cubren el formato de numeros, la interpretacion de entradas, el algebra exacta y
todas las operaciones, incluidos los casos limite (matrices singulares, mal
condicionadas, no diagonalizables y con valores propios complejos), y comparan el
modo exacto con NumPy sobre matrices aleatorias.

---

## Ejemplo

### Matriz 2x2

Entrada:

```
| 1  2 |
| 3  4 |
```

Resultados (modo exacto):

| Propiedad                | Valor                                         |
|--------------------------|-----------------------------------------------|
| Polinomio caracteristico | P(lambda) = lambda^2 - 5*lambda - 2           |
| Valores propios          | (5 + √33)/2 ≈ 5.3723, (5 - √33)/2 ≈ -0.3723   |
| Determinante             | det(A) = -2                                   |
| Inversa                  | [[-2, 1], [3/2, -1/2]]                        |
| Rango                    | rango(A) = 2                                  |
| Traza                    | tr(A) = 5                                     |

### Matriz 3x3

Entrada:

```
| 1  2  3 |
| 4  5  6 |
| 7  8  9 |
```

Resultados (modo exacto):

| Propiedad                | Valor                                              |
|--------------------------|----------------------------------------------------|
| Polinomio caracteristico | P(lambda) = lambda^3 - 15*lambda^2 - 18*lambda     |
| Valores propios          | (15 + 3√33)/2 ≈ 16.1168, 0, (15 - 3√33)/2 ≈ -1.1168 |
| Vector propio de lambda = 0 | v = [1, -2, 1]                                  |
| Determinante             | det(A) = 0                                         |
| Inversa                  | No tiene (la matriz es singular)                   |
| Forma escalonada reducida | [[1, 0, -1], [0, 1, 2], [0, 0, 0]]                |
| Rango                    | rango(A) = 2                                       |
| Traza                    | tr(A) = 15                                         |

---

## Licencia

Este proyecto esta bajo la licencia MIT.
