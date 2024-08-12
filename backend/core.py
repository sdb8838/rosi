import sys
import os
import logging
from dotenv import load_dotenv
from langchain.agents import create_react_agent, AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from typing import Any, Dict, List, Optional
from langchain_mistralai import ChatMistralAI
from rosi import get_tickets, get_ticket, get_PCs, alta_ticket, user_name, add_followup, get_followups
from langchain_core.tools import tool, BaseTool, Tool
from mistralai.client import MistralClient
from langchain_mistralai.embeddings import MistralAIEmbeddings
# Logging Configuration
logging.basicConfig(level=logging.INFO)

load_dotenv()

MISTRAL_API_KEY=os.environ["MISTRAL_API_KEY"]
PERSIST_DIRECTORY="./.chroma"
COLLECTION_NAME_INTRANET="rag-chroma-intranet"
COLLECTION_NAME_ROSI="rag-chroma-ROSI"
EMBEDDING_MODEL="mistral-embed"

mistral_client = MistralClient(api_key=MISTRAL_API_KEY)
mistral_embeddings = MistralAIEmbeddings(model=EMBEDDING_MODEL, mistral_api_key=MISTRAL_API_KEY)

class IntranetRetrieverToolWithReference(BaseTool):
    name = "Intranet_docs"
    description = "Busca información en la Intranet del Ayuntamiento de Murcia.  Ahí tienes documentación sobre Gexflow, administración electrónica, contabilidad, ..."
    retriever: Optional[Any]

    def __init__(self, retriever):
        super().__init__()
        self.retriever = retriever

    def _run(self, query: str):
        docs = self.retriever.get_relevant_documents(query)
        if docs:
            result = docs[0].page_content  # Contenido del documento más relevante
            reference = docs[0].metadata.get('source', 'Referencia no disponible')  # Obtiene la referencia (si existe)
            return f"{result}\n\nReferencia: {reference}"
        else:
            return "No se encontró información relevante en la Intranet."


class ROSIRetrieverToolWithReference(BaseTool):
    name = "ROSI_docs"
    description = ("Busca información en la base de datos de conocimiento de ROSI."
                   "En la contestación indica una referencia al documento utilizado")
    retriever: Optional[Any]

    def __init__(self, retriever):
        super().__init__()
        self.retriever = retriever

    def _run(self, query: str):
        docs = self.retriever.get_relevant_documents(query)
        #docs = self.retriever.invoke(query)
        if docs:
            result = docs[0].page_content  # Contenido del documento más relevante
            reference = docs[0].metadata.get('source', 'Referencia no disponible')  # Obtiene la referencia (si existe)
            return f"{result}\n\nReferencia: {reference}"
        else:
            return "No se encontró información relevante en la BD de conocimiento de ROSI."


ROSI_retriever = Chroma(
    collection_name=COLLECTION_NAME_ROSI,
    persist_directory=PERSIST_DIRECTORY,
    #embedding_function=OpenAIEmbeddings(),
    embedding_function=mistral_embeddings,
).as_retriever(search_kwargs={"k": 1})  # Fetch only 1 documents

Intranet_retriever = Chroma(
    collection_name=COLLECTION_NAME_INTRANET,
    persist_directory=PERSIST_DIRECTORY,
    #embedding_function=OpenAIEmbeddings(),
    embedding_function=mistral_embeddings,
).as_retriever(search_kwargs={"k": 1})  # Fetch only 1 documents

Intranet_retriever_tool = IntranetRetrieverToolWithReference(Intranet_retriever)
ROSI_retriever_tool = ROSIRetrieverToolWithReference(ROSI_retriever)

"""
ROSI_retriever_tool = create_retriever_tool(
    ROSI_retriever,
    "ROSI_Knowledge_db",
    "Busca información en la base de datos de conocimiento de ROSI"
)
Intranet_retriever_tool = create_retriever_tool(
    Intranet_retriever,
    "Intranet_docs",
    "Busca información en la Intranet del Ayuntamiento de Murcia.  Ahí tienes documentación sobre Gexflow, administración electrónica, contabilidad, ..."
)
"""


#llm = AzureOpenAIWrapper(
#    deployment_name="sdb-OpenAI",
#    openai_api_version="2023-05-15",
#    verbose=True,
#    temperature=0,
#)

#llm = ChatOpenAI(model="gpt-4o-mini", verbose=True, temperature=0)
#llm = ChatMistralAI(model="open-mistral-7b", mistral_api_key=MISTRAL_API_KEY)
#llm = ChatMistralAI(model="mistral-large-latest", mistral_api_key=MISTRAL_API_KEY)
llm = ChatMistralAI(model="open-mistral-nemo-2407", mistral_api_key=MISTRAL_API_KEY)

template = """ 
            Eres un asistente para tareas de pregunta-respuesta.
            Si el usuario hace comentarios en relación con un ticket de ROSI/GLPI, crea un seguimiento con dichos comentarios
            Pregunta:
            {input}
            Historial:
            {chat_history}
            """
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant"),
        MessagesPlaceholder(variable_name="chat_history"), #("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)
tools = [get_tickets, get_ticket, get_PCs, alta_ticket, user_name,
         add_followup, get_followups, ROSI_retriever_tool, Intranet_retriever_tool] #, ChatHistoryTool]
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True) #, chat_history=chat_history)

def run_llm(query: str):  #, chat_history: List[Dict[str, Any]] = []):
    #embeddings = OpenAIEmbeddings()
    result = agent_executor.invoke({"input": query,
                                    "chat_history": agent_executor.memory.buffer,
                                    })
    return result


if __name__ == "__main__":
    print(run_llm("Título: prueba"
                  "Descripción: Dame información sobre cómo actualizar SICALWIN"))
    sys.exit()
    #print(run_llm("Cuál es la capital de Francia?")['output'])
    #print(run_llm("Y la de Italia?")['output'])
    #sys.exit()
    #res=run_llm("cómo exportar un esquema de Oracle 10G?")
    res=run_llm("Cómo llevar un documento Gexflow a Junta de Gobierno Local?")
    print(res['output'])

    sys.exit()
    chat_history=[]
    res = run_llm("Dime información del ticket 66155")
    response = (f"{res['output']}")
    chat_history.append(response)
    res = run_llm("A quíen está asignado?", chat_history)

    sys.exit()

    res = run_llm("Cómo llevar un documento Gexflow a Junta de Gobierno Local?", [])

    #res = run_llm("En Intranet hay i nformación sobre Santa Rita?", [])
    #res=run_llm("cómo exportar un esquema de Oracle 10G?", [])
    print(res)
    #run_llm("No me funciona el ratón")
    #run_llm("Da de alta un ticket para que me coloquen un PC nuevo")
    #run_llm("Cuántos tickets abiertos tengo=", chat_history)
