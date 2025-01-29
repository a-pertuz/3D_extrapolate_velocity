Se necesita: 
Archivo SEGY de la línea sísmica con coordenadas UTM definidas en cada traza.
Archivo de velocidades interpoladas en 2D (Trace ,TWT, VNMO)

Al principio hay que indicar las coordenadas X,Y,TWT min/max del area que queremos extrapolar.

Se indica también la resolución en X,Y y en TWT.

El programa crea un archivo combinado: (Trace, X, Y, TWT, VNMO)

Ese archivo lo extrapola mediante NearestNDInterpolator a todo el espacio definido por xmin,xmax,ymin,ymax,twt_min,twt_max 

La salida es un archivo de texto (Trace, X, Y, TWT, VNMO)

También se grafica la salida en 3D.


Desarrollado para el Trabajo de Fin de Máster:
Pertuz Domínguez, A. (2024). Recuperación y procesamiento de secciones de sísmica de reflexión 2D antiguas: el ejemplo del yacimiento de gas Viura (La Rioja, España). 
https://docta.ucm.es/entities/publication/5166e5c0-4184-43ce-9cc0-78ee3da0adf8
