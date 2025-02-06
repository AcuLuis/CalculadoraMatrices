# Calculadora de Matrices: Polinomio Característico, Valores Propios y Vectores Propios

Este programa es una calculadora de matrices que permite calcular el **polinomio característico**, los **valores propios** y los **vectores propios** de matrices cuadradas de dimensiones 2x2 y 3x3. Está desarrollado en Python utilizando las bibliotecas `tkinter` para la interfaz gráfica y `numpy` para los cálculos matemáticos.

---

## Características

- **Interfaz gráfica intuitiva**: Permite ingresar los valores de la matriz de manera sencilla.
- **Cálculos precisos**:
  - Polinomio característico.
  - Valores propios.
  - Vectores propios.
- **Soporte para matrices**:
  - Matrices 2x2.
  - Matrices 3x3.
- **Validación de entradas**: Asegura que los datos ingresados sean números válidos.
- **Botón de limpieza**: Permite borrar los campos para ingresar nuevos valores.
- **Botón de volver**: Regresa a la ventana principal para seleccionar otra dimensión de matriz.

---

## Requisitos

Para ejecutar este programa, necesitas tener instalado:

- **Python 3.x**: Puedes descargarlo desde [python.org](https://www.python.org/).
- **Bibliotecas requeridas**:
  - `tkinter`: Normalmente viene incluida con Python.
  - `numpy`: Para cálculos matemáticos.
  - `Pillow`: Para manejar imágenes en la interfaz gráfica.

Puedes instalar las bibliotecas necesarias ejecutando el siguiente comando:
`bash pip install numpy pillow`

## Instrucciones de uso
1. **Ejecuta el programa**:
- **Abre una terminal o línea de comandos.**
- **Navega hasta la carpeta donde se encuentra el archivo del programa**.**
- **Ejecuta el siguiente comando: python Matrices.py**

2. **Selecciona la dimensión de la matriz**:
En la ventana principal, elige entre 2x2 o 3x3 según la dimensión de la matriz que deseas calcular.

3. **Ingresa los valores de la matriz**:
Completa los campos con los valores de la matriz.
Asegúrate de ingresar solo números.

4. **Realiza los cálculos**:
Haz clic en los botones correspondientes para calcular:
- **Polinomio Característico**.
- **Valores Propios**.
- **Vectores Propios**.
5. **Limpia los campos**:
Si deseas ingresar una nueva matriz, haz clic en el botón Limpiar.

6. **Volver al menú principal**:
Para cambiar la dimensión de la matriz, haz clic en el botón Volver.

## Estructura del proyecto
El proyecto está organizado de la siguiente manera:

/proyecto
│
├── main.py                  # Código principal del programa
│
└── IMAGES/                  # Carpeta con imágenes utilizadas en la interfaz
    ├── numeros.jpg          # Imagen de fondo de la ventana principal
    ├── matriz-2x2-2.jpg     # Imagen de ejemplo para matriz 2x2
    └── matriz-3x3.jpg       # Imagen de ejemplo para matriz 3x3

## Ejemplos de uso
Matriz 2x2
- **Ingresa los valores de la matriz**:
x1 = 1, y1 = 2
x2 = 3, y2 = 4

- **Resultados**:

Polinomio característico: λ^2 - 5λ - 2

Valores propios: 5.37, -0.37

Vectores propios: [0.82, 0.58], [-0.82, 0.58]

Matriz 3x3
- **Ingresa los valores de la matriz**:

x1 = 1, y1 = 2, z1 = 3
x2 = 4, y2 = 5, z2 = 6
x3 = 7, y3 = 8, z3 = 9

- **Resultados**:

Polinomio característico: -λ^3 + 15λ^2 + 18λ
Valores propios: 16.12, -1.12, 0
Vectores propios: [0.23, 0.53, 0.82], [-0.82, 0.58, 0.82], [0.23, -0.53, 0.82]

## Licencia
Este proyecto está bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.