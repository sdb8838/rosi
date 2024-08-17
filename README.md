1.- Ejecutar buscarURLs.py (genera URLs_Intranet.json)
2.- Ejecutar ingestion.py (genera .chroma con BD SQLite para categorías, Intranet y BDConocimiento ROSI)
3.- streamlit run main.py

Hay que aceptar: https://huggingface.co/mistralai/Mixtral-8x7B-v0.1

Hay que crear .env con:
OPENAI_API_KEY=
LANGCHAIN_API_KEY=""
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=ROSI

MISTRAL_API_KEY=""
HF_TOKEN=""

# Configuración de Azure OpenAI
#AZURE_OPENAI_ENDPOINT=""
#AZURE_OPENAI_API_KEY=""
#AZURE_DEPLOYMENT_NAME=""
#AZURE_CHAT_MODEL_NAME=""
AZURE_DEPLOYMENT_NAME_EMBEDDINGS=""
AZURE_OPENAI_ENDPOINT_EMBEDDINGS=""
AZURE_OPENAI_API_KEY_EMBEDDINGS=""
# con GPT-4:
#AZURE_OPENAI_ENDPOINT=""
AZURE_OPENAI_API_KEY=""
AZURE_DEPLOYMENT_NAME=""
AZURE_CHAT_MODEL_NAME=""

GLPI_API_URL=
GLPI_APP_TOKEN=
GLPI_USER_TOKEN=

Hay que crear un .streamlit/secrets.toml con:
[ldap]
server_path = ""
domain = ""
search_base = "dc=,dc="
attributes = ["sAMAccountName", "distinguishedName", "userPrincipalName", "displayName", "manager", "title"]
use_ssl = true

[session_state_names]
user = "login_user"
remember_me = "login_remember_me"

[auth_cookie]
name = "ROSI-Cookie"
key = ""
expiry_days = 1
auto_renewal = true
delay_sec = 0.1


# Create a new virtual environment
python -m venv .venv

# Activate it
.venv\Scripts\activate  

# Install your project dependencies
pip install -r requirements.txt 