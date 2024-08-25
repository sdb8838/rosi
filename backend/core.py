import sys
import json
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Any, Optional
from rosi import get_tickets, get_ticket, get_PCs, alta_ticket, user_name, add_followup, get_followups
from langchain_core.tools import BaseTool

load_dotenv()

ROSI_retriever_tool = None
Intranet_retriever_tool = None
agent_executor = None


def create_retrievers_and_agent():
    import globales
    global ROSI_retriever_tool, Intranet_retriever_tool, agent_executor

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
                return json.dumps({"Referencia": reference, "Resultado": result})
            else:
                return "No se encontró información relevante en la Intranet."

    class ROSIRetrieverToolWithReference(BaseTool):
        name = "ROSI_docs"
        description = ("Busca información en la base de datos de conocimiento de ROSI.")
        retriever: Optional[Any]

        def __init__(self, retriever):
            super().__init__()
            self.retriever = retriever

        def _run(self, query: str):
            docs = self.retriever.get_relevant_documents(query)
            print(f"Invocando retriever con: {self.retriever.tags[1]}")
            if docs:
                result = docs[0].page_content  # Contenido del documento más relevante
                reference = docs[0].metadata.get('source', 'Referencia no disponible')  # Obtiene la referencia (si existe)
                res = json.dumps({"Referencia": reference, "Resultado": result})
                return res
            else:
                return "No se encontró información relevante en la BD de conocimiento de ROSI."

    globales.refresh()
    print(f"Refrescando retrievers.... {globales.PERSIST_DIRECTORY}")
    ROSI_retriever = Chroma(
        collection_name=globales.COLLECTION_NAME_ROSI,
        persist_directory=globales.PERSIST_DIRECTORY,
        embedding_function=globales.embeddings,
    ).as_retriever(search_kwargs={"k": 1})  # Fetch only 1 documents

    Intranet_retriever = Chroma(
        collection_name=globales.COLLECTION_NAME_INTRANET,
        persist_directory=globales.PERSIST_DIRECTORY,
        embedding_function=globales.embeddings,
    ).as_retriever(search_kwargs={"k": 1})  # Fetch only 1 documents

    Intranet_retriever_tool = IntranetRetrieverToolWithReference(Intranet_retriever)
    ROSI_retriever_tool = ROSIRetrieverToolWithReference(ROSI_retriever)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", """Eres un asistente para tareas de pregunta-respuesta basado en herramientas del Ayuntamiento de Murcia que tienes a tu disposición.
                       Si tienes una referencia a un link con información, inclúye el link exacto en tu respuesta.
                       Responde con un máximo de 150 palabras"""
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{query}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    tools = [get_tickets, get_ticket, get_PCs, alta_ticket, user_name,
             add_followup, get_followups, ROSI_retriever_tool, Intranet_retriever_tool]

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    agent = create_tool_calling_agent(globales.llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True, handle_parsing_errors=True)


def run_llm(query: str):
    if agent_executor is None:
        create_retrievers_and_agent()
    result = agent_executor.invoke({"query": query,
                                    "chat_history": agent_executor.memory.buffer,
                                    })
    return result


if __name__ == "__main__":
    #res=run_llm("Dame información sobre cómo actualizar SICALWIN")
    #print(run_llm("Cuál es la capital de Francia?")['output'])
    #print(run_llm("Y la de Italia?")['output'])
    res=run_llm("Cómo llevar un documento Gexflow a Junta de Gobierno Local?")
    #res=run_llm("cómo exportar un esquema de Oracle 10G?. Busca en la base de datos de conocimiento de ROSI")
    #res = run_llm("Dime información del ticket 66155")
    #res = run_llm("En Intranet hay información sobre Santa Rita?", [])
    #res=run_llm("cómo exportar un esquema de Oracle 10G?", [])
    #run_llm("No me funciona el ratón")
    #run_llm("Da de alta un ticket para que me coloquen un PC nuevo")
    #run_llm("Cuántos tickets abiertos tengo=", chat_history)
    print(res)
