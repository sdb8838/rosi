import requests
from bs4 import BeautifulSoup
import json
import urllib.parse

def obtener_urls(url, url_base, url_base2=None, urls_visitadas=None, ):
    print(f"Obteniendo {url}")
    if url_base == None:
        url_base = url
    if urls_visitadas is None:
        urls_visitadas = set()

    try:
        respuesta = requests.get(url)
        respuesta.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al acceder a {url}: {e}")
        return []

    soup = BeautifulSoup(respuesta.content, 'html.parser')
    urls = []

    for enlace in soup.find_all('a', href=True):
        href = urllib.parse.urljoin(url, enlace['href'])  # Obtener URL completa
        if (href.startswith(url_base) or (url_base2 is not None and href.startswith(url_base2))) and href not in urls_visitadas: # and href.endswith(('.html', '/')):
            #obtenemos la extensión:
            parsed_url = urllib.parse.urlparse(href)
            path = parsed_url.path
            indice_punto = path.rfind('.')
            if indice_punto != -1:
                extension = path[indice_punto + 1:]
                indice_barra = extension.find('/')
                extension = extension[:indice_barra].lower()
            else:
                extension = ""

            urls_visitadas.add(href)
            # Procesamos directorios html's y PDF's
            if extension in ["htm", "html", "", "pdf"]:
                urls.append(href)
            # Recursividad con diretorios
            if extension == "":
                urls.extend(obtener_urls(href, url_base, url_base2, urls_visitadas))  # Recursividad para paginación
    return urls

url_pagina = "https://intranet.ayto-murcia.es/web/administracion-electronica"
url_base2="https://intranet.ayto-murcia.es/documents/"
urls_encontradas = obtener_urls(url_pagina, url_pagina, url_base2)
with open("URLs_Intranet.json", "w") as archivo:
    json.dump(urls_encontradas, archivo, indent=4)

print("URLs guardadas en URLs_Intranet.json")
