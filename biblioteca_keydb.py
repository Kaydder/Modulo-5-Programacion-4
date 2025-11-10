import redis
import json
import uuid
import os
from dotenv import load_dotenv

# ============================================================
# Aplicación de Biblioteca Personal con KeyDB y redis-py
# Autor: Kayder Murillo
# Descripción: Programa de línea de comandos que administra
# libros almacenados como objetos JSON en KeyDB.
# ============================================================

# ------------------------------------------------------------
# Cargar configuración desde .env
# ------------------------------------------------------------
load_dotenv()

HOST = os.getenv("KEYDB_HOST", "localhost")
PORT = int(os.getenv("KEYDB_PORT", 6379))
PASSWORD = os.getenv("KEYDB_PASSWORD", "")

# ------------------------------------------------------------
# Conexión a KeyDB
# ------------------------------------------------------------
def conectar_keydb():
    try:
        cliente = redis.Redis(
            host=HOST,
            port=PORT,
            password=PASSWORD,
            decode_responses=True
        )
        # Probar conexión
        cliente.ping()
        return cliente
    except redis.AuthenticationError:
        print("Error: Credenciales inválidas para KeyDB.")
        exit(1)
    except redis.ConnectionError:
        print("Error: No se pudo conectar al servidor KeyDB. Verifica que esté en ejecución.")
        exit(1)

# ------------------------------------------------------------
# Funciones CRUD
# ------------------------------------------------------------
def agregar_libro(r):
    titulo = input("Título: ").strip()
    autor = input("Autor: ").strip()
    genero = input("Género: ").strip()
    estado = input("Estado (Leído/No leído): ").strip().capitalize()

    if estado not in ["Leído", "No leído"]:
        print("Estado inválido. Use 'Leído' o 'No leído'.\n")
        return

    id_libro = str(uuid.uuid4())
    clave = f"libro:{id_libro}"

    libro = {
        "id": id_libro,
        "titulo": titulo,
        "autor": autor,
        "genero": genero,
        "estado": estado
    }

    try:
        r.set(clave, json.dumps(libro))
        print("Libro agregado correctamente.\n")
    except redis.RedisError as e:
        print(f"Error al agregar libro: {e}\n")

def ver_libros(r):
    try:
        claves = r.scan_iter(match="libro:*")
        encontrado = False
        print("\nLISTADO DE LIBROS:")
        print("-" * 80)
        for clave in claves:
            libro = json.loads(r.get(clave))
            print(f"ID: {libro['id']} | "
                  f"Título: {libro['titulo']} | "
                  f"Autor: {libro['autor']} | "
                  f"Género: {libro['genero']} | "
                  f"Estado: {libro['estado']}")
            encontrado = True
        print("-" * 80 + "\n")
        if not encontrado:
            print("No hay libros registrados.\n")
    except redis.RedisError as e:
        print(f"Error al consultar libros: {e}\n")

def buscar_libros(r):
    campo = input("Buscar por (titulo/autor/genero): ").strip().lower()
    if campo not in ["titulo", "autor", "genero"]:
        print("Campo inválido.\n")
        return
    termino = input(f"Ingrese el {campo} que desea buscar: ").strip().lower()

    try:
        claves = r.scan_iter(match="libro:*")
        resultados = []
        for clave in claves:
            libro = json.loads(r.get(clave))
            if termino in libro[campo].lower():
                resultados.append(libro)

        if resultados:
            print("\nRESULTADOS DE BÚSQUEDA:")
            print("-" * 80)
            for libro in resultados:
                print(f"ID: {libro['id']} | "
                      f"Título: {libro['titulo']} | "
                      f"Autor: {libro['autor']} | "
                      f"Género: {libro['genero']} | "
                      f"Estado: {libro['estado']}")
            print("-" * 80 + "\n")
        else:
            print("No se encontraron libros que coincidan.\n")
    except redis.RedisError as e:
        print(f"Error al buscar libros: {e}\n")

def actualizar_libro(r):
    ver_libros(r)
    id_libro = input("Ingrese el ID del libro que desea actualizar: ").strip()
    clave = f"libro:{id_libro}"

    if not r.exists(clave):
        print("No se encontró un libro con ese ID.\n")
        return

    libro = json.loads(r.get(clave))

    nuevo_titulo = input(f"Nuevo título [{libro['titulo']}]: ").strip() or libro['titulo']
    nuevo_autor = input(f"Nuevo autor [{libro['autor']}]: ").strip() or libro['autor']
    nuevo_genero = input(f"Nuevo género [{libro['genero']}]: ").strip() or libro['genero']
    nuevo_estado = input(f"Nuevo estado (Leído/No leído) [{libro['estado']}]: ").strip().capitalize() or libro['estado']

    if nuevo_estado not in ["Leído", "No leído"]:
        print("Estado inválido.\n")
        return

    libro_actualizado = {
