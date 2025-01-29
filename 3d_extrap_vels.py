import segyio
import pandas as pd
import numpy as np
from scipy.interpolate import NearestNDInterpolator
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os
from tqdm import tqdm  # Importar tqdm para la barra de progreso
from matplotlib.ticker import FuncFormatter

print("Ejecutando interpolación y combinación de datos...")

# Solicitar al usuario los parámetros de entrada
archivo_segy = str(input("Introduce el nombre del archivo SEGY (ejemplo.segy): "))
archivo_vels = str(input("Introduce el nombre del archivo de velocidades (ejemplo.dat): "))
resolucion_xy = int(input("Resolución de la malla en X-Y (m): "))
resolucion_twt = int(input("Resolución de la malla en TWT (ms): "))
x_min = int(input("Coordenada X mínima (m): "))
x_max = int(input("Coordenada X máxima (m): "))
y_min = int(input("Coordenada Y mínima (m): "))
y_max = int(input("Coordenada Y máxima (m): "))
twt_min = int(input("TWT inicio (ms): "))
twt_max = int(input("TWT final (ms): "))

# Obtener el nombre base de los archivos SEGY y de velocidades
nombre_base_segy = os.path.splitext(os.path.basename(archivo_segy))[0]
nombre_base_vels = os.path.splitext(os.path.basename(archivo_vels))[0]
archivo_combinado = f'{nombre_base_vels}_combinado.dat'
archivo_interpolado = f'{nombre_base_vels}_interpolado.dat'
archivo_interpolado_limpio = f'{nombre_base_vels}_interpolado_limpio.dat'

########################################
# Abrir el archivo SEGY y extraer coordenadas X e Y
with segyio.open(archivo_segy, "r", ignore_geometry=True) as archivo_segy:
    coordenadas_x = archivo_segy.attributes(segyio.TraceField.SourceX)[:]
    coordenadas_y = archivo_segy.attributes(segyio.TraceField.SourceY)[:]

# Crear DataFrame con las coordenadas del archivo SEGY
datos_segy = pd.DataFrame({
    'Trace': range(1, len(coordenadas_x) + 1),
    'X': coordenadas_x,
    'Y': coordenadas_y
})

print(f'\nArchivo de coordenadas SEGY:')
print(datos_segy.head())  # Mostrar los primeros registros del DataFrame datos_segy

# Leer el archivo de velocidades (.dat) y combinar datos con las coordenadas del SEGY
datos_velocidades = pd.read_csv(archivo_vels, sep=' ', header=0, names=['Trace', 'TWT', 'VNMO'])

print(f'\nArchivo de velocidades:')
print(datos_velocidades.head())  # Mostrar los primeros registros del DataFrame datos_velocidades

# Combinar las coordenadas del SEGY con las velocidades en un único DataFrame
datos_combinados = pd.merge(datos_segy, datos_velocidades, on='Trace')
print(f'\nArchivo combinado:')
print(datos_combinados.head())  # Mostrar los primeros registros del DataFrame datos_combinados

# Guardar el archivo combinado
datos_combinados.to_csv(archivo_combinado, sep='\t', index=False)
print(f'\nDatos combinados guardados en {archivo_combinado}')

########################################

# Eliminar archivo interpolado anterior si existe
if os.path.exists(archivo_interpolado):
    os.remove(archivo_interpolado)
    print(f'\nArchivo {archivo_interpolado} eliminado correctamente.')
else:
    print(f'\nEl archivo {archivo_interpolado} no existe en el directorio actual.\n')

# Datos para la interpolación
x = datos_combinados['X']
y = datos_combinados['Y']
z = datos_combinados['TWT']  # TWT como la tercera dimensión
c = datos_combinados['VNMO']  # Colorear los puntos según VNMO

# Crear malla para la interpolación
malla_x = np.arange(x_min, x_max + resolucion_xy, resolucion_xy)
malla_y = np.arange(y_min, y_max + resolucion_xy, resolucion_xy)
valores_twt = np.arange(twt_min, twt_max + resolucion_twt, resolucion_twt)
malla_x, malla_y, malla_twt = np.meshgrid(malla_x, malla_y, valores_twt)

# Realizar la interpolación usando el método de vecinos más cercanos en 3D
interpolador = NearestNDInterpolator((x, y, z), c)
vnmo_interpolado = np.zeros_like(malla_x.flatten())  # Array para almacenar los valores interpolados
total_iteraciones = len(malla_x.flatten())

# Barra de progreso con tqdm
with tqdm(total=total_iteraciones, desc='Interpolando') as pbar:
    for i, (x_val, y_val, twt_val) in enumerate(zip(malla_x.flatten(), malla_y.flatten(), malla_twt.flatten())):
        vnmo_interpolado[i] = interpolador([x_val, y_val, twt_val])[0]  # Acceder al valor escalar interpolado
        pbar.update(1)  # Actualizar la barra de progreso

vnmo_interpolado = vnmo_interpolado.reshape(malla_x.shape)  # Redimensionar al tamaño de la malla

# Preparar los datos para guardar en el archivo de salida
datos_a_guardar = np.column_stack((malla_x.flatten(), malla_y.flatten(), malla_twt.flatten(), vnmo_interpolado.flatten()))

with open(archivo_interpolado, 'ab') as f:
    np.savetxt(f, datos_a_guardar, fmt='%d', delimiter='\t')

print(f'\nArchivos interpolados guardados en {archivo_interpolado}')

# Leer el archivo interpolado para mostrar su contenido
datos_interpolados = pd.read_csv(archivo_interpolado, sep='\t', header=None, names=['X', 'Y', 'TWT', 'VNMO'])
print(f'\nPrimeros registros del archivo interpolado:')
print(datos_interpolados.head())

########################################
# Graficar los resultados en 3D
datos = np.loadtxt(archivo_interpolado, skiprows=1)
X, Y, TWT, VNMO = datos[:, 0], datos[:, 1], datos[:, 2], datos[:, 3]

# Crear la figura para la visualización 3D
fig = plt.figure(figsize=(12.8, 8))

# Crear el gráfico 3D
ax = fig.add_subplot(111, projection='3d')
grafico_interpolado = ax.scatter(X, Y, TWT, c=VNMO, cmap='rainbow', marker='o', alpha=1, s=50)

# Añadir barra de color fuera del gráfico principal
barra_color = fig.colorbar(grafico_interpolado, ax=ax, orientation='vertical', shrink=0.7, aspect=15, pad=0.1)
barra_color.set_label('VNMO (m/s)', labelpad=10, fontsize=12)

# Invertir la dirección de los ticks de la barra de color
barra_color.ax.invert_yaxis()

# Ajustar los límites y la escala de los ejes
ax.set_xlim(x_min - 5000, x_max + 5000)
ax.set_ylim(y_min - 5000, y_max + 5000)
ax.set_zlim(twt_min, twt_max)
ax.set_zscale('linear')

# Ajustar los ticks en los ejes X e Y
ax.set_xticks(np.arange(x_min, x_max + 1, 5000))
ax.set_yticks(np.arange(y_min, y_max + 1, 5000))

# Ajustar el aspecto igualado de los tres ejes (X, Y, Z)
ax.set_box_aspect([1, 0.8, 0.3])

# Formatear los ticks del eje Y como enteros
formateador = FuncFormatter(lambda x, pos: f'{int(x):d}')
ax.yaxis.set_major_formatter(formateador)

# Etiquetas de los ejes
ax.set_xlabel('X - UTM (m)', labelpad=20, fontsize=12)
ax.set_ylabel('Y - UTM (m)', labelpad=20, fontsize=12)
ax.set_zlabel('TWT (ms)', rotation=90, labelpad=10, fontsize=12)

# Invertir el eje Z para que TWT más alto esté arriba
ax.invert_zaxis()

# Mostrar el gráfico
plt.show()
