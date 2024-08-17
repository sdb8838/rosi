from dotenv import load_dotenv
import os
ST_HEADER = 'Asistente ROSI'
user_id = 'evf6107'
AIMODEL = 'Mistral'  # Opciones: 'OpenAI', 'AzureOpenAI', 'Mistral'


load_dotenv()

COLLECTION_NAME_INTRANET = "rag-chroma-intranet"
COLLECTION_NAME_ROSI = "rag-chroma-ROSI"
COLLECTION_NAME_CATEGORIES = "rag-chroma-CATEGORIES"
PERSIST_DIRECTORY = None
llm = None
embeddings = None
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
EMBEDDING_MODEL_OPENAI = "text-embedding-ada-002"
MISTRAL_API_KEY = os.environ["MISTRAL_API_KEY"]
EMBEDDING_MODEL_MISTRAL = "mistral-embed"
LLM_MODEL_MISTRAL = "open-mistral-nemo-2407"
LLM_MODEL_MISTRAL_LARGEST = "mistral-large-latest"
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME")
AZURE_CHAT_MODEL_NAME = os.getenv("AZURE_CHAT_MODEL_NAME")
AZURE_DEPLOYMENT_NAME_EMBEDDINGS = os.getenv("AZURE_DEPLOYMENT_NAME_EMBEDDINGS")
AZURE_OPENAI_ENDPOINT_EMBEDDINGS = os.getenv("AZURE_OPENAI_ENDPOINT_EMBEDDINGS")
AZURE_OPENAI_API_KEY_EMBEDDINGS = os.getenv("AZURE_OPENAI_API_KEY_EMBEDDINGS")


def refresh():
    print(f"Refrescando... modelo={AIMODEL}")
    global PERSIST_DIRECTORY, llm, embeddings
    import os
    if "OpenAI" in AIMODEL :
        PERSIST_DIRECTORY="./.chroma-OpenAI"
        from langchain_openai import OpenAI, OpenAIEmbeddings, ChatOpenAI
        if AIMODEL == "Openai-35":
            LLM_MODEL = "gpt-3.5-turbo"
        else:
            LLM_MODEL = "gpt-4o-mini"
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model=EMBEDDING_MODEL_OPENAI)
        llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model=LLM_MODEL)
    else:  # AIMODEL == "Mistral or Mistral-large":
        PERSIST_DIRECTORY="./.chroma-Mistral"
        from langchain_mistralai.embeddings import MistralAIEmbeddings
        from langchain_mistralai import ChatMistralAI
        from mistralai import Mistral
        client = Mistral(api_key=MISTRAL_API_KEY)
        if AIMODEL == "Mistral-large":
            model = LLM_MODEL_MISTRAL_LARGEST
        else:
            model = LLM_MODEL_MISTRAL
        embeddings = MistralAIEmbeddings(model=EMBEDDING_MODEL_MISTRAL, mistral_api_key=MISTRAL_API_KEY)
        llm = ChatMistralAI(model=model, mistral_api_key=MISTRAL_API_KEY)
    #else:  # AIMODEL = AzureOpenAI
        #PERSIST_DIRECTORY = "./.chroma-Azure"
        #from langchain_openai.embeddings import AzureOpenAIEmbeddings
        #from langchain_openai.chat_models import AzureChatOpenAI
        #from langchain.schema import HumanMessage
        #import os

        # Crear una instancia de AzureOpenAIEmbeddings
        #embeddings = AzureOpenAIEmbeddings(
        #    model="text-embedding-ada-002",
        #    api_key=AZURE_OPENAI_API_KEY_EMBEDDINGS,
        #    api_version="2022-12-01",  # versión que estés usando
        #    azure_endpoint=AZURE_OPENAI_ENDPOINT_EMBEDDINGS,
        #)

        # Crear una instancia de AzureChatOpenAI
        #llm = AzureChatOpenAI(
        #    deployment_name=AZURE_CHAT_MODEL_NAME,
        #    api_key=AZURE_OPENAI_API_KEY,
        #    azure_endpoint=AZURE_OPENAI_ENDPOINT,
        #    api_version="2024-02-15-preview"  # versión que estés usando
        #)


refresh()