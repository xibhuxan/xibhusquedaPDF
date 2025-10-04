
# XibhusquedaPDF - Buscador de PDFs por medio de texto interno

Este programa busca PDF que contengan un texto concreto dentro de rutas específicas.

## Requisitos
- Python 3.10 o superior
- Instalar dependencias con:

  ```
  pip install -r requirements.txt
  ```

## Uso
1. Especifica las carpetas añadiendo desde la interfaz.
2. Escribe los textos a buscar, uno por línea, en un archivo txt y súbelo a la interfaz, o añade de uno en uno.
3. Ejecuta:

   ```
   python Xibhusqueda.py
   ```

Los PDFs encontrados se copiarán a la carpeta `PDF/`, y los resultados se guardarán en `rutas_encontradas.txt`.

## Compilación para Windows
Si quieres generar un `.exe`, usa:

  ```
  pip install pyinstaller
  pyinstaller --onefile --noconsole --icon=logo.ico Xibhusqueda.py
  ```
Para un ejecutable de linux:

  ```
  pip install pyinstaller
  pyinstaller --onefile --noconsole Xibhusqueda.py
  ```

## Changelog

### v2.0.0
- Interfaz gráfica.
- Eliminado multihilo.

### v1.2.0
- Ejecución multihilo para mayor rapidez.
- Arreglado el no mostrar los no encontrados.
- Muestra la cantidad de duplicados de los textos a buscar.

### v1.1.0
- Ahora busca todas las coincidencias sin detenerse en la primera.
- Se agregó timestamp a cada resultado en `resultados.txt`.
- Manejo de nombres duplicados en la carpeta PDF.

### v1.0.0
- Versión inicial con búsqueda en PDFs y exportación de resultados.

