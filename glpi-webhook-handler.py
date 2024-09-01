from flask import Flask, request, jsonify
import logging
import json
import base64
import re
from clasificador import clasifica_ticket

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#def require_basic_auth(func):
#    def decorated(*args, **kwargs):
#        auth = request.authorization
#        if not auth or not (auth.username == username and auth.password == password):
#            return jsonify({'message': 'Unauthorized'}), 401
#        return func(*args, **kwargs)
#    return decorated

@app.route('/webhook/', methods=['GET', 'POST'])
def handle_webhook():
    logger.info(f"entrada: {request.data} (tipo: {type(request.data)})")

    # request.data vale algo del estilo de:  b"{'ticket_id': '0000004'}"
    cadena=request.data.decode('utf-8')
    try:
        data = json.loads(cadena)
        ticket_id=data.get('ticket_id')
        logger.info(f"Nuevo ticket: {ticket_id}")
        clasifica_ticket(ticket_id)
        return jsonify({'message': 'Webhook procesado exitosamente'}), 200
    except json.JSONDecodeError:
      return jsonify({'message': 'Error, La cadena no es un JSON válido'}), 500


if __name__ == '__main__':
    app.run(host='192.168.5.178', port=5000)
