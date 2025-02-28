import os
import shutil
import PyPDF2
from datetime import datetime

def inicializar_archivos():
    archivos = ["rutas.txt", "busquedas.txt", "resultados.txt", "README.txt"]
    for archivo in archivos:
        if not os.path.exists(archivo):
            open(archivo, "w").close()
    if not os.path.exists("PDF"):
        os.makedirs("PDF")
    crear_readme()

def crear_readme():
    contenido = """
Hecho por CarlosMR - github.com/xibhuxan    
    
Este programa busca textos en archivos PDF dentro de las rutas especificadas en rutas.txt.

Archivos utilizados:
- rutas.txt: Contiene las carpetas donde buscar, una por línea.
- busquedas.txt: Contiene los textos a buscar, una línea por texto.
- resultados.txt: Guarda los resultados de las búsquedas con el formato 'texto encontrado: ruta o No encontrado'.
- PDF/: Carpeta donde se copian los archivos PDF encontrados.

Modo de uso:
1. Agregue rutas en rutas.txt.
2. Agregue textos a buscar en busquedas.txt o introdúzcalos manualmente en la terminal.
3. Ejecute el programa y revise resultados.txt.
"""
    with open("README.txt", "w", encoding="utf-8") as f:
        f.write(contenido)

def cargar_rutas(archivo_config="rutas.txt"):
    with open(archivo_config, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def cargar_busquedas(archivo_busquedas="busquedas.txt"):
    with open(archivo_busquedas, "r", encoding="utf-8") as f:
        return list(set(line.strip() for line in f if line.strip()))  # Elimina duplicados

def buscar_texto_en_pdfs(rutas, textos):
    resultados = []
    
    for ruta in rutas:
        for root, _, files in os.walk(ruta):
            for file in files:
                if "oficial" in file.lower() and file.lower().endswith(".pdf"):
                    pdf_path = os.path.join(root, file)
                    for texto in textos:
                        if buscar_en_pdf(pdf_path, texto):
                            resultados.append(f"{datetime.now().isoformat()} - {texto}: {pdf_path}")
                            destino = obtener_nombre_unico(file)
                            shutil.copy(pdf_path, destino)
    
    guardar_resultados(resultados)

def buscar_en_pdf(pdf_path, texto):
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            if not reader.pages:
                return False
            for page in reader.pages:
                contenido = page.extract_text()
                if contenido and texto.lower() in contenido.lower():
                    return True
    except Exception as e:
        print(f"Error al leer {pdf_path}: {e}")
    return False

def obtener_nombre_unico(nombre_archivo):
    base, ext = os.path.splitext(nombre_archivo)
    destino = os.path.join("PDF", nombre_archivo)
    contador = 1
    while os.path.exists(destino):
        destino = os.path.join("PDF", f"{base}({contador}){ext}")
        contador += 1
    return destino

def guardar_resultados(resultados, archivo_resultados="resultados.txt"):
    with open(archivo_resultados, "a", encoding="utf-8") as f:  # Modo 'a' para concatenar
        for resultado in resultados:
            f.write(resultado + "\n")

if __name__ == "__main__":
    inicializar_archivos()
    rutas_a_buscar = cargar_rutas()
    busquedas = cargar_busquedas()
    
    if not rutas_a_buscar:
        print("No se encontraron rutas en rutas.txt. Agregue rutas línea por línea.")
    elif busquedas:
        buscar_texto_en_pdfs(rutas_a_buscar, busquedas)
    else:
        while True:
            texto_a_buscar = input("Introduce el texto a buscar (o escribe 'salir' para terminar): ")
            if texto_a_buscar.lower() == "salir":
                break
            buscar_texto_en_pdfs(rutas_a_buscar, [texto_a_buscar])

