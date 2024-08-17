import sys
import globales
import os
from dotenv import load_dotenv

import glpi_api
from langchain_core.tools import tool
from typing import (Any, List)

load_dotenv()

glpi_api_url = os.getenv("GLPI_API_URL")
app_token = os.getenv("GLPI_APP_TOKEN")
user_token = os.getenv("GLPI_USER_TOKEN")

COD_ID = '2'
COD_TITULO = '1'
COD_ESTADO = '12'
COD_FECHA_APERTURA = '15'
COD_SOLICITANTE = '4'
COD_UBICACION = '83'
COD_DESCRIPCION = '21'

try:
    with (glpi_api.connect(glpi_api_url, app_token, user_token) as glpi):
        # print(glpi.get_config())
        pass
except glpi_api.GLPIError as err:
    print(str(err))


glpi = glpi_api.GLPI(url=glpi_api_url,
           apptoken=app_token,
           auth=user_token)

@tool
def get_tickets() ->List[Any]:
    """Devuelve los tickets en ROSI/GLPI del usuario"""

    print(f"user_id:{globales.user_id}")
    busqueda = [
        {'field': COD_SOLICITANTE, 'searchtype': 'equals', 'value': globales.user_id},
        {'link': 'AND', 'field': COD_ESTADO, 'searchtype': 'equals', 'value': 'notclosed'}
    ]

    tickets = glpi.search('Ticket', criteria=busqueda, forcedisplay=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18])

    tickets_valor=[]
    estadoGLPI={1: 'nuevo', 2: 'en curso', 4: 'en espera', 5: 'resuelto', 6: 'cerrado'}
    for i in tickets:
        tickets_valor.append({
            'id': i['2'],
            'Título': i.get('1',''),
            'Estado': estadoGLPI[i.get('12',1)],
            'Fecha apertura': i.get('15',''),
            'Solicitante': glpi.get_item('User', i.get('4',globales.user_id))['name'],
            'Ubicación': i.get('83',''),
            'Descripción': i.get('21',''),
            'Categoría': i.get('7',''),
            'Técnico asignado': i.get('8',''),
            'Fecha comprometida resolución': i.get('18',''),
        }
        )

    return tickets_valor


def get_tickets_sin_tool(fecha_inicial, fecha_final) ->List[Any]:
    busqueda = [
        {'link': 'AND', 'field': 16, 'searchtype': 'morethan', 'value': fecha_inicial},
        {'link': 'AND', 'field': 16, 'searchtype': 'lessthan', 'value': fecha_final},
    ]
    tickets = glpi.search('Ticket', glpilist_limit=1000,
                          criteria=busqueda,
                          fields=['id','name','content','itilcategories_id'],
                          forcedisplay=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,
                                        22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44])

    tickets_valor=[]
    estadoGLPI={1: 'nuevo', 2: 'en curso', 4: 'en espera', 5: 'resuelto', 6: 'cerrado'}
    for i in tickets:
        tickets_valor.append({
            'id':i.get('2',''),
            'titulo': i.get('1',''),
            'ubicacion': i.get('83',''),
            'descripcion': i.get('21',''),
            'categoria': i.get('7',''),
        }
        )

    return tickets_valor

@tool
def get_ticket(ticket_id) ->List[Any]:
    """Devuelve los valores de un ticket en ROSI/GLPI a partir del código/id de ticket.
    El resultado es un diccionarios con los siguientes campos:
    'id': el código de ticket
    'name': el nombre del ticket
    'date': la fecha de apertura
    'closedate': la fecha de cierre
    'solvedate': la fecha de resolución
    'content': el contenido
    'users_id_lastupdater': el código del técnico que lo está resolviendo
    """

    ticket = glpi.get_item('Ticket', ticket_id)
    return ticket


def get_ticket_sin_tool(ticket_id) ->List[Any]:
    ticket = glpi.get_item('Ticket', ticket_id)
    return ticket


@tool
def get_PCs() ->List[Any]:
    """Devuelve los PCs del usuario.
    El resultado es un array de diccionarios con los siguientes campos:
    '1': el identificador del equipo
    '80': el servicio
    '32': el estado
    '45': el sistema operativo
    """

    busqueda = [
        {'field': '70', 'searchtype': 'equals', 'value': globales.user_id}
    ]
    pcs = glpi.search('Computer', criteria=busqueda)
    return pcs

@tool
def user_name(user_id) ->List[Any]:
    """Devuelve el usuario (o técnico) a partir de su código
    user_id: el código de usuario
    Devuelve los siguientes campos:
    'name': identificador del usuario
    'phone': teléfono del usuario
    'mobile': teléfono móvil del usuario
    'realname': apellidos del usuario
    'firstname': nombre del usuario
    """
    user_name = glpi.get_item('User', user_id)
    return user_name


@tool
def add_followup(ticket_id, contenido) -> Any:
    """Añade un seguimiento con el texto 'contenido' en el ticket ticket_id
    """
    followup_data={
        "itemtype": "Ticket",
        "items_id": ticket_id,
        "content": contenido,
        "is_private": False,
        }
    response = glpi.add("TicketFollowup", followup_data)
    return response[0]['id']


def add_followup_sin_tool(ticket_id, contenido) -> Any:
    """Añade un seguimiento con el texto 'contenido' en el ticket ticket_id
    """
    followup_data={
        "itemtype": "Ticket",
        "items_id": ticket_id,
        "content": contenido,
        "is_private": False,
        }
    response = glpi.add("TicketFollowup", followup_data)
    return response[0]['id']


@tool
def get_followups(ticket_id) -> Any:
    """Devuelve todos los seguimientos del ticket ticket_id"""
    ticket_followups = glpi.get_sub_items(
        'Ticket',
        ticket_id,
        'ITILFollowup',
    )
    return [i['content'] for i in ticket_followups if i['is_private']==0]


def get_KnowledgeBaseItem(kb_id) ->Any:
    """Devuelve:
    id: int
    name: str
    answer: str
    is_faq: int
    users_id: int
    view: int
    date_creation: str
    date_mod: str
    begin_date: str
    end_date: str
    _categories: list
    links: list
    """
    kb = glpi.get_item('KnowbaseItem', kb_id)
    return kb


def userID(login) -> Any:
    # Buscar el usuario por su login
    search_options = [
        {
            "field": "1",  # Campo de login (verifica el ID correcto)
            "searchtype": "contains",
            "value": login,
        },
    ]

    response = glpi.search("User", criteria=search_options, forcedisplay=[2])

    if response:
        user_id = response[0]["2"]  # Obtener el ID del primer resultado
        return user_id
    else:
        print("No se encontró el usuario con el login:", login)


@tool
def alta_ticket(nombre, contenido, tipo) -> Any:
    """Da de alta un ticket en ROSI/GLPI
    Los tickets en ROSI se dan de alta para solicitar asistencia técnica tanto para incidentes en puesto de trabajo o aplicaciones como para solicitudes de trabajo
    Recibe como argumento el nombre, el contenido y el tipo.  El tipo es 1 si es una petición o 2 si es una incidencia.
    Devuelve el código de ticket creado.
    Si no se indica nombre especifica como nombre un resumen de un máximo de 15 palabras del contenido.
    """
    ticket_data={
        "name": nombre,
        "content": contenido,
        "entities_id": "1", # SMI
        #"urgency": "3",
        #"impact": "3",
        #"priority": "3",
        "location_id": 4, # Glorieta
        "type": tipo, # 2: Petición
        "itilcategories_id": "0",
        "user": globales.user_id,
        "_actors":{
            "requester": [
                {"itemtype": "User",
                 "items_id":globales.user_id,
                 "user_notification": 1,
                 }
            ],
            "observer": [],
            "assign": []
        }
    }
    _actors: {"requester": [{"itemtype": "User", "items_id": "99", "use_notification": 1,
                             "alternative_email": "eduardo.vicente@ayto-murcia.es"}], "observer": [], "assign": []}

    """        >>> glpi.add('Computer',
                         {'name': 'computer1', 'serial': '123456', 'entities_id': 0},
                         {'name': 'computer2', 'serial': '234567', 'entities_id': 1})
            [{'id': 5, 'message': ''}, {'id': 6, 'message': ''}]"""
    response = glpi.add("Ticket", ticket_data)
    #response = glpi.send_request("Ticket", ticket_data)

    return response[0]['id']

if __name__ == "__main__":
    ticket=get_ticket_sin_tool(66193)
    print(ticket)
    sys.exit()
    globales.user_id=userID("sdb8838") #"evf6107")
    tickets=get_tickets()
    print(tickets)
    sys.exit()

    alta_ticket("prueba", "txt_Prueba2", 2)
    sys.exit()
    print(get_PCs())
    sys.exit()
    kb=get_KnowledgeBaseItem(6)
    print(f"id:{kb['id']}\nname:{kb['name']}, answer: {kb['answer']}\n")

    sys.exit()
    print(tickets_abiertos())
    sys.exit()
    print(user_name(99))
    #get_ticket(66132)
    sys.exit()

    alta_ticket(nombre = "Problema con la impresora", contenido = "Mi impresora no imprime")
    sys.exit()

    pcs=get_PCs()
    print(f"PCs: {pcs}")
    print(f"Entidades: {glpi.get_my_entities()}")
    print(f"Sesión: {glpi.get_full_session()}")
    print(f"Config: {glpi.get_config()}")
    # Item ticket 66166
    print(glpi.get_item('Ticket', 66166))
    # Todos los tickets:
    #print(glpi.get_all_items('Ticket', serchText={'expand_dropdowns=true'}))
    # Servidores:
    print([d["name"] for d in glpi.get_all_items('Computer', searchText={'name': 'server'})])

    # tickets no cerrados de sdb8838
    COD_ID = '2'
    COD_TITULO = '1'
    COD_ESTADO = '12' # 6=CERRADO
    COD_FECHA_APERTURA = '15'
    COD_SOLICITANTE = '4' # 1270: MªDolores Sánchez Ortega
    COD_UBICACION = '83' # Pedanía Espinardo
    COD_DESCRIPCION = '21'
    """
    busqueda = [
        {'field': COD_SOLICITANTE, 'searchtype': 'equals', 'value': '1509'},
        {'link': 'AND', 'field': COD_ESTADO, 'searchtype': 'equals', 'value': 'notclosed'}
    ]
    tickets = glpi.search('Ticket', criteria=busqueda)
    """
    # Procesamiento de resultados (ejemplo)
    for ticket in tickets_abiertos():
        print(f"ID: {ticket[COD_ID]}, Título: {ticket[COD_TITULO]}, Estado: {ticket[COD_ESTADO]}, Solicitante: {ticket[COD_SOLICITANTE]}")
