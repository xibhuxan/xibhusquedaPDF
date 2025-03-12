import os
import shutil
import PyPDF2
from datetime import datetime
from collections import Counter
from multiprocessing import Pool, cpu_count

def inicializar_archivos():
    archivos = ["rutas.txt", "busquedas.txt", "resultados.txt", "duplicados.txt", "README.txt"]
    for archivo in archivos:
        if not os.path.exists(archivo):
            open(archivo, "w").close()
    if not os.path.exists("PDF"):
        os.makedirs("PDF")
    crear_readme()

def crear_readme():
    contenido = """
Hecho por CarlosMR - https://github.com/xibhuxan/xibhusquedaPDF 

Este programa busca textos en archivos PDF dentro de las rutas especificadas en rutas.txt.

Archivos utilizados:
- rutas.txt: Contiene las carpetas donde buscar, una por línea.
- busquedas.txt: Contiene los textos a buscar, una línea por texto.
- resultados.txt: Guarda los resultados de las búsquedas con el formato 'texto encontrado: ruta o No encontrado'.
- duplicados.txt: Guarda los textos duplicados y la cantidad de veces que se repiten.
- PDF/: Carpeta donde se copian los archivos PDF encontrados.

Modo de uso:
1. Agregue las rutas donde se buscarán los PDF en el archivo rutas.txt.
2. Agregue los textos a buscar en busquedas.txt un texto concreto por línea.
3. Ejecute el programa y revise resultados.txt.
4. Los PDF encontrados se copiarán en la carpeta PDF.

El programa detectará automáticamente los textos duplicados y los guardará en duplicados.txt con su cantidad.
De esta manera, con la cantidad de duplicados, los PDF encontrados y los textos no encontrados, debería dar el total de los textos a buscar.
Total = Duplicados + Encontrados + No encontrados
"""
    with open("README.txt", "w", encoding="utf-8") as f:
        f.write(contenido)

def agregar_separador(archivo):
    with open(archivo, "a", encoding="utf-8") as f:
        f.write("\n" + "="*50 + f"\nEjecutado el {datetime.now().isoformat()}\n" + "="*50 + "\n")

def cargar_rutas(archivo_config="rutas.txt"):
    with open(archivo_config, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def cargar_busquedas(archivo_busquedas="busquedas.txt"):
    with open(archivo_busquedas, "r", encoding="utf-8") as f:
        textos = [line.strip() for line in f if line.strip()]
    contar_duplicados(textos)
    return list(set(textos))

def contar_duplicados(textos):
    conteo = Counter(textos)
    duplicados = {texto: cantidad for texto, cantidad in conteo.items() if cantidad > 1}
    agregar_separador("duplicados.txt")
    with open("duplicados.txt", "a", encoding="utf-8") as f:
        for texto, cantidad in duplicados.items():
            f.write(f"{texto}: {cantidad} veces\n")

def buscar_texto_en_pdfs(rutas, textos):
    archivos_pdf = []
    
    for ruta in rutas:
        for root, _, files in os.walk(ruta):
            for file in files:
                if "oficial" in file.lower() and file.lower().endswith(".pdf"):
                    archivos_pdf.append(os.path.join(root, file))
    
    with Pool(cpu_count()) as pool:
        resultados = pool.starmap(procesar_pdf, [(pdf, textos) for pdf in archivos_pdf])

    resultados = [r for sublist in resultados for r in sublist]  # Aplanar lista

    # Extraer solo los textos encontrados
    textos_encontrados = {line.split(" - ")[1].split(":")[0] for line in resultados}

    # Determinar los textos no encontrados
    no_encontrados = set(textos) - textos_encontrados

    for texto in no_encontrados:
        resultados.append(f"{datetime.now().isoformat()} - {texto}: No encontrado")

    agregar_separador("resultados.txt")
    guardar_resultados(resultados)

def procesar_pdf(pdf_path, textos):
    resultados = []
    nombre_archivo = os.path.basename(pdf_path)  # Obtener solo el nombre del archivo
    
    for texto in textos:
        if buscar_en_pdf(pdf_path, texto):
            resultados.append(f"{datetime.now().isoformat()} - {texto}: {pdf_path}")
            
            destino = obtener_nombre_unico(nombre_archivo)  # Pasar solo el nombre, no la ruta completa
            shutil.copy(pdf_path, destino)
    
    return resultados


def buscar_en_pdf(pdf_path, texto):
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            if not reader.pages:
                return False
            for page in reader.pages:
                contenido = page.extract_text()
                if contenido:
                    contenido = " ".join(contenido.split())  # Limpiar espacios
                    if texto.lower() in contenido.lower():
                        return True
    except Exception as e:
        print(f"Error al leer {pdf_path}: {e}")
    return False

def obtener_nombre_unico(nombre_archivo):
    base, ext = os.path.splitext(nombre_archivo)
    destino = os.path.join("PDF", nombre_archivo)  # Asegurar que se guarde en la carpeta "PDF"
    contador = 1
    while os.path.exists(destino):
        destino = os.path.join("PDF", f"{base}({contador}){ext}")
        contador += 1
    return destino

def guardar_resultados(resultados, archivo_resultados="resultados.txt"):
    with open(archivo_resultados, "a", encoding="utf-8") as f:
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

