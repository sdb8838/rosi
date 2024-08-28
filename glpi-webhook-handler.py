from flask import Flask, request, jsonify
import logging
import json

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # Intentar obtener datos JSON
    data = request.json

    # Si no hay datos JSON, intentar procesar el cuerpo como texto
    if data is None:
        try:
            data = json.loads(request.data.decode('utf-8'))
        except json.JSONDecodeError:
            # Si falla, buscar el contenido JSON en el cuerpo del texto
            body = request.data.decode('utf-8')
            start = body.find('{')
            end = body.rfind('}') + 1
            if start != -1 and end != -1:
                try:
                    data = json.loads(body[start:end])
                except json.JSONDecodeError:
                    return jsonify({"error": "No se pudo procesar los datos recibidos"}), 400
            else:
                return jsonify({"error": "No se encontraron datos JSON válidos"}), 400

    # Extraer información relevante del ticket
    ticket_id = data.get('ticket_id')
    title = data.get('title')
    description = data.get('description')
    
    # Registrar la información del ticket
    logger.info(f"Nuevo ticket creado - ID: {ticket_id}, Título: {title}")
    
    # Aquí puedes agregar tu lógica personalizada para procesar el ticket
    # Por ejemplo, podrías:
    # - Enviar una notificación a un sistema externo
    # - Actualizar una base de datos
    # - Iniciar un flujo de trabajo automatizado
    
    # Por ahora, solo registraremos algunos detalles adicionales
    if description:
        logger.info(f"Descripción del ticket: {description[:100]}...")  # Primeros 100 caracteres
    
    return jsonify({"message": "Webhook procesado exitosamente"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
