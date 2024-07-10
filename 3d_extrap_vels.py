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

# Archivos de entrada
archivo_segy = str(input("Introduce el nombre del archivo segy (ejemplo.segy): "))
archivo_vels = str(input("Introduce el nombre del archivo de velocidades (ejemplo.dat): "))
step_xy = int(input("Resolución de la malla en X-Y (m): "))
step_twt = int(input("Resolución de la malla en TWT (ms): "))
x_min = int(input("Coordenada X min (m): "))
x_max = int(input("Coordenada X max (m): "))
y_min = int(input("Coordenada Y min (m): "))
y_max = int(input("Coordenada Y max (m): "))
twt_min = int(input("TWT inicio (ms): "))
twt_max = int(input("TWT final (ms): "))


# Obtener el nombre base del archivo SEGY
archivo_segy_base = os.path.splitext(os.path.basename(archivo_segy))[0]
archivo_vels_base = os.path.splitext(os.path.basename(archivo_vels))[0]
combined_file_path = f'{archivo_vels_base}_combinado.dat'
file_interpolated = f'{archivo_vels_base}_interpolado.dat'
file_clean = f'{archivo_vels_base}_interpolated_clean.dat'


########################################
# Abrir el archivo SEGY y extraer coordenadas X e Y
with segyio.open(archivo_segy, "r", ignore_geometry=True) as segyfile:
    x_coords = segyfile.attributes(segyio.TraceField.SourceX)[:]
    y_coords = segyfile.attributes(segyio.TraceField.SourceY)[:]

# Crear DataFrame con las coordenadas del SEGY
segy_data = pd.DataFrame({
    'Trace': range(1, len(x_coords) + 1),
    'X': x_coords,
    'Y': y_coords
})

print(f'\nArchivo de coordenadas SEGY:')
print(segy_data.head())  # Mostrar los primeros registros del DataFrame segy_data

# Leer el archivo .dat y combinar datos con las coordenadas del SEGY
vels_data = pd.read_csv(archivo_vels, sep=' ', header=0, names=['Trace', 'TWT', 'VNMO'])

print(f'\nArchivo de velocidades:')
print(vels_data.head())  # Mostrar los primeros registros del DataFrame vels_data

combined_data = pd.merge(segy_data, vels_data, on='Trace')
print(f'\nArchivo combinado:')
print(combined_data.head())  # Mostrar los primeros registros del DataFrame combined_data

# Guardar archivo combinado
combined_data.to_csv(combined_file_path, sep='\t', index=False)
print(f'\nDatos combinados guardados en {combined_file_path}')


########################################

if os.path.exists(file_interpolated):
    os.remove(file_interpolated)
    print(f'\nArchivo {file_interpolated} eliminado correctamente.')
else:
    print(f'\nEl archivo {file_interpolated} no existe en el directorio actual.\n')

# Definir límites y separación de la malla en todos los ejes




# Datos para el gráfico
x = combined_data['X']
y = combined_data['Y']
z = combined_data['TWT']  # TWT como la tercera dimensión
c = combined_data['VNMO']  # Colorear los puntos según VNMO

# Crear malla para la interpolación
xs = np.arange(x_min, x_max + step_xy, step_xy)
ys = np.arange(y_min, y_max + step_xy, step_xy)
twt_values = np.arange(twt_min, twt_max + step_twt, step_twt)
x_mesh, y_mesh, twt_mesh = np.meshgrid(xs, ys, twt_values)

# Interpolación usando método de vecinos más cercanos en 3D con tqdm para barra de progreso
interpolator = NearestNDInterpolator((x, y, z), c)
vnmo_interp = np.zeros_like(x_mesh.flatten())  # Array para almacenar los valores interpolados
total_iterations = len(x_mesh.flatten())

with tqdm(total=total_iterations, desc='Interpolando') as pbar:
    for i, (x_val, y_val, twt_val) in enumerate(zip(x_mesh.flatten(), y_mesh.flatten(), twt_mesh.flatten())):
        vnmo_interp[i] = interpolator([x_val, y_val, twt_val])[0]  # Acceder al valor escalar interpolado
        pbar.update(1)  # Actualizar la barra de progreso

vnmo_interp = vnmo_interp.reshape(x_mesh.shape)  # Reshape al tamaño de la malla

# Preparar datos para guardar en archivo
data_to_save = np.column_stack((x_mesh.flatten(), y_mesh.flatten(), twt_mesh.flatten(), vnmo_interp.flatten()))

with open(file_interpolated, 'ab') as f:
    np.savetxt(f, data_to_save, fmt='%d', delimiter='\t')

print(f'\nArchivos interpolados guardados en {file_interpolated}')
# Leer el archivo interpolado para mostrar su contenido
interpolated_data = pd.read_csv(file_interpolated, sep='\t', header=None, names=['X', 'Y', 'TWT', 'VNMO'])
print(f'\nPrimeros registros del archivo interpolado:')
print(interpolated_data.head())



########################################
# Graficar los resultados 3D
data = np.loadtxt(file_interpolated, skiprows=1)
X, Y, TWT, VNMO = data[:, 0], data[:, 1], data[:, 2], data[:, 3]

fig = plt.figure(figsize=(12.8,8))

ax = fig.add_subplot(111, projection='3d')
scatter_interp = ax.scatter(X, Y, TWT, c=VNMO, cmap='rainbow', marker='o', alpha=1, s=50)
# Añadir barra de color fuera del gráfico principal
cbar = fig.colorbar(scatter_interp, ax=ax, orientation='vertical',  shrink=0.7, aspect=15, pad=0.1)  # Ajustar 'labelpad' según necesites
cbar.set_label('VNMO (m/s)', labelpad=10, fontsize=12)

# Ajustar los ticks de la barra de color
cbar.ax.invert_yaxis()  # Invierte la dirección de los ticks

# Ajustar límites y escala de los ejes
ax.set_xlim(x_min-5000, x_max+5000)
ax.set_ylim(y_min-5000, y_max+5000)
ax.set_zlim(twt_min, twt_max)
ax.set_zscale('linear')

# Ajustar ticks en los ejes X e Y cada 5000 unidades
ax.set_xticks(np.arange(x_min, x_max + 1, 5000))
ax.set_yticks(np.arange(y_min, y_max + 1, 5000))

# Ajustar aspecto igualado para los tres ejes (X, Y, Z)
ax.set_box_aspect([1, 0.8, 0.3])

# Formatear los ticks del eje Y como enteros y no usar notación científica
formatter = FuncFormatter(lambda x, pos: f'{int(x):d}')
ax.yaxis.set_major_formatter(formatter)

ax.set_xlabel('X - UTM (m)', labelpad=20, fontsize=12)
ax.set_ylabel('Y - UTM (m)', labelpad=20, fontsize=12)
ax.set_zlabel('TWT (ms)', rotation=90 , labelpad=10, fontsize=12)
ax.invert_zaxis()

plt.show()
