import os
import logging

from langchain.schema import Document
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rosi import glpi, get_KnowledgeBaseItem, get_ticket_sin_tool, get_tickets_sin_tool
import fitz
import json
import urllib.parse

import requests
import globales

load_dotenv()


def pdf_to_text(pdf_data):
    with fitz.open(stream=pdf_data, filetype="pdf") as pdf_document:
        text = ""
        for page in pdf_document:
            text += page.get_text()
    return text


def create_chroma_vectorstore(documents, embedding_function, persist_directory, collection_name):
    vectorstore = None  # Initialize vectorstore to None
    try:
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embedding_function,
            persist_directory=persist_directory,
            collection_name=collection_name,
        )
    except KeyError as ke:
        logging.error(f"KeyError occurred: {ke}")
        logging.error("Check MistralAI response and library compatibility.")

        if hasattr(embedding_function, "_endpoint_url"):
            response = embedding_function.client.post(
                embedding_function._endpoint_url, json={"input": documents}
            )
            logging.error(f"MistralAI API Response: {response.json()}")
        else:
            logging.error("Missing _endpoint_url attribute in MistralAIEmbeddings.")
    finally:
        # Check and return the vectorstore (whether it was created or not)
        return vectorstore


def cargaBDConocimientoROSI():
    import globales
    plantilla_url = "https://rosi-pre.ayto-murcia.es/front/knowbaseitem.form.php?id="
    docs_list = []
    for i in range(1, 120):
        try:
            kb = get_KnowledgeBaseItem(i)
            doc = f"id:{kb['id']}\nname:{kb['name']}\nanswer: {kb['answer']}\n"
            docs_list.append(Document(page_content=doc, metadata={'source': plantilla_url + str(i)}))
        except:
            print(f"Knowbaseitem {i} no encontrado")
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=2000, chunk_overlap=100
    )
    doc_splits = text_splitter.split_documents(docs_list)
    vectorstore = create_chroma_vectorstore(
        doc_splits, globales.embeddings, globales.PERSIST_DIRECTORY, globales.COLLECTION_NAME_ROSI
    )


def cargaIntranet():
    import globales
    with open("URLs_Intranet.json", "r") as archivo:
        urls_encontradas = json.load(archivo)
    docs = []
    for url in urls_encontradas:
        print(url)
        if "pdf" in url.lower():  # Es un PDF
            # url = "https://intranet.ayto-murcia.es/documents/44134/113357/Documentaci%C3%B3n+Formaci%C3%B3n+Gexflow+-+Tramitaci%C3%B3n+expedientes_v4.pdf/482cd744-daac-c5de-7fd8-566b8f513c30"
            response = requests.get(url)

            if response.status_code == 200:
                pdf_data = response.content  # Obtener los datos binarios directamente de la respuesta
                text = pdf_to_text(pdf_data)
                # print(text)
                docs.append(Document(
                    metadata={
                        'source': url,
                        'title': url,
                        'language': 'es-ES'
                    },
                    page_content=text
                ))
            else:
                print(f"Error al descargar el PDF: {response.status_code}")
        else:
            doc = WebBaseLoader(url).load()[0]
            docs.append(doc)

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=2000, chunk_overlap=100
    )
    doc_splits = text_splitter.split_documents(docs)
    vectorstore = create_chroma_vectorstore(
        doc_splits, globales.embeddings, globales.PERSIST_DIRECTORY, globales.COLLECTION_NAME_INTRANET
    )
    return
    plantilla_url = "https://intranet.ayto-murcia.es/"
    urls_intranet=[
        "web/administracion-electronica",
        "documents/44134/113357/Documentaci%C3%B3n+Formaci%C3%B3n+Gexflow+-+Tramitaci%C3%B3n+expedientes_v4.pdf/482cd744-daac-c5de-7fd8-566b8f513c30",
    ]
    urls = [plantilla_url + str(id_url) for id_url in urls_intranet]
    docs=[]
    for url in urls:
        # obtenemos la extensión:
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path
        indice_punto = path.rfind('.')
        if indice_punto != -1:
            extension = path[indice_punto + 1:]
            indice_barra = extension.find('/')
            extension = extension[:indice_barra].lower()
        else:
            extension = ""

        if extension == "pdf": # Es un PDF
            response = requests.get(url)

            if response.status_code == 200:
                pdf_data = response.content  # Obtener los datos binarios directamente de la respuesta
                text = pdf_to_text(pdf_data)
                #print(text)
                docs.append(Document(
                    metadata={
                        'source': url,
                        'title': url,
                        'language': 'es-ES'
                    },
                    page_content=text
                ))
            else:
                print(f"Error al descargar el PDF: {response.status_code}")
        else:
            loader = WebBaseLoader(url, continue_on_failure=False)
            doc=loader.load()[0]
            docs.append(doc)
    #docs_list = [item for sublist in docs for item in sublist]

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=600, chunk_overlap=50
    )
    doc_splits = text_splitter.split_documents(docs_list)

    vectorstore = create_chroma_vectorstore(
        doc_splits, mistral_embeddings, globales.PERSIST_DIRECTORY, globales.COLLECTION_NAME_INTRANET
    )


def cargaTicketCategorias(fecha_inicial, fecha_final):
    import globales
    datos_entrenamiento = get_tickets_sin_tool(fecha_inicial, fecha_final)
    print(f"Obtenidos {len(datos_entrenamiento)} documentos")
    docs=[]
    categoria_id={}
    for i in datos_entrenamiento:
        titulo=i['titulo']
        descripcion=i['descripcion']
        ubicacion=i['ubicacion']
        categoria=i['categoria']
        if categoria is not None:
            if categoria_id.get(categoria) is None:
                ticket=get_ticket_sin_tool(i['id'])
                categoria_id[categoria]=ticket['itilcategories_id']
            texto=(f"Título:{titulo}"
                   f"Descripción:{descripcion}"
                   f"Ubicación:{ubicacion}")
            print(f"Texto:{texto}"
                  f"Categoría:{categoria}"
                  f"Categoria id: {categoria_id[categoria]}")
            docs.append(Document(page_content=texto, metadata={"categoria": categoria_id[categoria]}))

    # Crear el vectorstore de Chroma
    vectorstore = create_chroma_vectorstore(
        docs, globales.embeddings, globales.PERSIST_DIRECTORY, globales.COLLECTION_NAME_CATEGORIES
    )


if __name__ == "__main__":
    from backend.core import create_retrievers_and_agent
    #for globales.AIMODEL in ['OpenAI', 'Mistral']:
    #    create_retrievers_and_agent()
    print(f"INGESTION DE: {globales.AIMODEL}")
    cargaTicketCategorias("2023-04-03 00:00:00", "2024-08-03 00:00:00")
    #    cargaIntranet()
    cargaBDConocimientoROSI()
