import globals
import rosi
from backend.core import run_llm
from backend.core import agent_executor
import streamlit as st
from streamlit_ldap_authenticator import Authenticate
# Declare the authentication object
auth = Authenticate(
    st.secrets['ldap'],
    st.secrets['session_state_names'],
    st.secrets['auth_cookie']
)

# Login Process
user = auth.login()

if user is not None:
    auth.createLogoutForm({'message': f"Welcome {user['displayName']}"})

    # Your page application can be written below
    globals.user_id = rosi.userID(user['sAMAccountName'])
    st.header(globals.ST_HEADER)
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    # React to user input
    if prompt := st.chat_input("Escribe tu pregunta"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        if prompt:
            with st.spinner("Generation response.."):
                generated_response = run_llm(query=prompt)
                response = (
                    f"{generated_response['output']}"
                )
                st.session_state["chat_history"].extend([prompt, response])
                print("Respuesta generada")

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
    # Botón para borrar la conversación
    if st.button("Borrar conversación"):
        st.session_state.messages = []
        st.session_state.chat_history = []
        agent_executor.memory.clear()
        # Opcional: Recargar la página para reflejar el cambio
        st.rerun()
