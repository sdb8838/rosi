from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_mistralai.embeddings import MistralAIEmbeddings
from dotenv import load_dotenv
import rosi
from rosi import glpi
import sys
from langchain_core.tools import BaseTool
from typing import Any,Optional
import os


from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from typing import Any, Dict, List, Optional
from langchain_mistralai import ChatMistralAI
from langchain_core.tools import tool, BaseTool, Tool

from langchain_mistralai.embeddings import MistralAIEmbeddings
from mistralai.client import MistralClient


load_dotenv()


PERSIST_DIRECTORY="./.chroma"
COLLECTION_NAME_ROSI="rag-chroma-ROSI"
COLLECTION_NAME_CATEGORIES="rag-chroma-categories"
api_key=os.getenv("MISTRAL_API_KEY")

embeddings = MistralAIEmbeddings()
db = Chroma(persist_directory=PERSIST_DIRECTORY, collection_name=COLLECTION_NAME_CATEGORIES, embedding_function=embeddings)
dbROSI = Chroma(persist_directory=PERSIST_DIRECTORY, collection_name=COLLECTION_NAME_ROSI, embedding_function=embeddings)
client = MistralClient(api_key=api_key)
llm = ChatMistralAI(model="open-mistral-nemo-2407", mistral_api_key=os.getenv("MISTRAL_API_KEY"))


retriever = Chroma(
    collection_name=COLLECTION_NAME_ROSI,
    persist_directory=PERSIST_DIRECTORY,
    embedding_function=embeddings,
).as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={
        "score_threshold": 0.7,
        "k": 1, # coger sólo un documento
    }
)

def run_llm_similarity(query: str, doc: Document):
    template = """ 
    Eres un experto en la base de datos de conocimiento de GLPI/ROSI.  Apóyate en el contexto para responder.
    Responde con un máximo de 30 palabras.
    Pregunta: {input}
    Contexto:
    {context}
    """
    prompt = PromptTemplate(template=template, input_variables=["input", "context"])
    prompt = prompt.format(input=query, context=doc.page_content)

    result = llm.invoke(input=prompt)
    return result.content



def clasifica_ticket(ticket_id):
    """
    Clasifica un ticket de ROSI en función de su similitud con tickets existentes en una base de datos.
    Args:
        ticket_id: El ID del ticket que se desea clasificar.

        Actualiza el ticket con la categoría predicha.
    """
    ticket=rosi.get_ticket_sin_tool(ticket_id)
    texto=(f"Título: {ticket['name']}"
           f"Descripción: {ticket['content']}"
           f"Categoría: {ticket['itilcategories_id']}")
    if ticket['itilcategories_id'] == 0: # Si no hay categoría la estimo...
        resultados=db.similarity_search_with_score(texto, k=1)
        if resultados:
            documento, puntuacion_similitud = resultados[0]
            if puntuacion_similitud >= 0.5:
                categoria_predicha=documento.metadata["categoria"]
                glpi.update('Ticket',
                            {'id': ticket_id,
                             'itilcategories_id': categoria_predicha})
                print(f"Similitud del {puntuacion_similitud}... se actualiza")
            else:
                print(f"No hay mucha similitud ({puntuacion_similitud}) por lo que no se actualiza")

    # Ahora le añadimos un seguimiento con un comentario del LLM:
    resultados = dbROSI.similarity_search_with_score(texto, k=1)
    if resultados:
        documento, puntuacion_similitud = resultados[0]
        if puntuacion_similitud >= 0.1:
            respuesta_bot = run_llm_similarity(f"Título:{ticket['name']}"
                                    f"Descripción:{ticket['content']}",
                                               documento)
            # Añade un seguimiento con la respuesta del BOT
            rosi.add_followup_sin_tool(ticket_id,
            'IA: ' + respuesta_bot + f"\n+información: {documento.metadata['source']}")
        else:
            print(f"No hay mucha similitud con BD ROSI ({puntuacion_similitud}) por lo que no se añade seguimiento")


#cambia categoría al ticket 66192:
clasifica_ticket(66192)

sys.exit()
# Texto nuevo a clasificar
nuevo_texto = "Revisar buzones sin actividad"

# Realizar la búsqueda en Chroma
resultados = db.similarity_search(nuevo_texto, k=1)  # k=1 para obtener un resultado

# Obtener la categoría predicha
categoria_predicha = resultados[0].metadata["categoria"]
print(f"Categoría predicha para '{nuevo_texto}': {categoria_predicha}")

