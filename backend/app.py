from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# 📄 Archivos
BASE_FILE = 'clientes.xlsx'
DATA_FILE = 'datos.csv'
SMS_FILE = 'sms_enviados.csv'

# ✔️ Crear archivos si no existen
if not os.path.exists(SMS_FILE):
    pd.DataFrame(columns=['Fecha', 'Hora', 'Telefono', 'Mensaje', 'Estado']).to_csv(SMS_FILE, index=False)

if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=[
        'DNI', 'Nombre', 'Entidad', 'Deuda Total', 'Monto Cancelación',
        'Oferta Mostrada Cliente', 'Acción', 'Monto Ofertado', 'Fecha y Hora', 'Estado Pago'
    ]).to_csv(DATA_FILE, index=False)

# ------------------ Funciones ------------------

def cargar_base():
    df = pd.read_excel(BASE_FILE)
    return df.fillna('')

def convertir_a_float(valor):
    try:
        return float(str(valor).replace(',', '').strip())
    except:
        return 0.0

def leer_datos():
    return pd.read_csv(DATA_FILE, dtype=str).fillna('')

def guardar_datos(df):
    df.to_csv(DATA_FILE, index=False)

def registrar_evento(dni, nombre, entidad, deuda_total, monto_cancelacion,
                      oferta_mostrada, accion, monto_ofertado, estado_pago=""):
    fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    fila = pd.DataFrame([{
        'DNI': dni,
        'Nombre': nombre,
        'Entidad': entidad,
        'Deuda Total': deuda_total,
        'Monto Cancelación': monto_cancelacion,
        'Oferta Mostrada Cliente': oferta_mostrada,
        'Acción': accion,
        'Monto Ofertado': monto_ofertado if monto_ofertado is not None else '',
        'Fecha y Hora': fecha_hora,
        'Estado Pago': estado_pago
    }])

    df = leer_datos()
    df = pd.concat([df, fila], ignore_index=True)
    guardar_datos(df)
    print(f'📑 Evento registrado: {fila.to_dict(orient="records")[0]}')

def registrar_sms(telefono, mensaje, estado='Enviado'):
    fecha = datetime.now().strftime('%Y-%m-%d')
    hora = datetime.now().strftime('%H:%M:%S')

    nuevo_sms = pd.DataFrame([{
        'Fecha': fecha,
        'Hora': hora,
        'Telefono': telefono,
        'Mensaje': mensaje,
        'Estado': estado
    }])

    historial = pd.read_csv(SMS_FILE)
    historial = pd.concat([historial, nuevo_sms], ignore_index=True)
    historial.to_csv(SMS_FILE, index=False)
    print(f'📨 SMS registrado: {nuevo_sms.to_dict(orient="records")[0]}')

# ------------------ API ------------------

@app.route('/buscar_cliente', methods=['POST'])
def buscar_cliente():
    datos = request.get_json()
    dni = str(datos.get('dni')).strip()

    df = cargar_base()
    cliente = df[df['codcliente'].astype(str) == dni]

    if cliente.empty:
        return jsonify({'error': 'Cliente no encontrado'}), 404

    cliente = cliente.iloc[0]
    deuda_total = convertir_a_float(cliente['Total Soles'])
    monto_cancelacion = convertir_a_float(cliente['Monto Cancelacion'])
    oferta_mostrada = round(monto_cancelacion * 1.15)

    respuesta = {
        'dni': dni,
        'nombre': cliente['NomCliente'],
        'entidad_financiera': cliente['Asignacion'],
        'deuda': deuda_total,
        'monto_cancelacion': monto_cancelacion,
        'oferta_cancelacion': oferta_mostrada
    }

    registrar_evento(
        dni, cliente['NomCliente'], cliente['Asignacion'],
        deuda_total, monto_cancelacion, oferta_mostrada,
        'Consulta', None
    )

    return jsonify(respuesta)

@app.route('/guardar_oferta', methods=['POST'])
def guardar_oferta():
    datos = request.get_json()
    dni = str(datos.get('dni')).strip()
    oferta_cliente = float(datos.get('oferta'))
    acepto = datos.get('acepto')

    df = cargar_base()
    cliente = df[df['codcliente'].astype(str) == dni].iloc[0]

    deuda_total = convertir_a_float(cliente['Total Soles'])
    monto_cancelacion = convertir_a_float(cliente['Monto Cancelacion'])
    oferta_mostrada = round(monto_cancelacion * 1.15)

    accion = 'Aceptó' if acepto else 'Oferta Enviada'
    estado_pago = 'Pendiente' if acepto else ''

    registrar_evento(
        dni, cliente['NomCliente'], cliente['Asignacion'],
        deuda_total, monto_cancelacion, oferta_mostrada,
        accion, oferta_cliente, estado_pago
    )

    return jsonify({'status': 'guardado'})

@app.route('/obtener_datos', methods=['GET'])
def obtener_datos():
    df = leer_datos()
    datos = df.to_dict(orient='records')
    return jsonify(datos)

@app.route('/accion_oferta', methods=['POST'])
def accion_oferta():
    datos = request.get_json()
    dni = str(datos.get('dni')).strip()
    fecha_hora = datos.get('fecha_hora')
    nueva_accion = datos.get('accion')

    df = leer_datos()
    filtro = (df['DNI'].astype(str) == dni) & (df['Fecha y Hora'] == fecha_hora)

    if filtro.any():
        df.loc[filtro, 'Acción'] = nueva_accion
        if nueva_accion == 'Aceptó':
            df.loc[filtro, 'Estado Pago'] = 'Pendiente'
        else:
            df.loc[filtro, 'Estado Pago'] = ''
        guardar_datos(df)
        return jsonify({'status': 'actualizado'})
    else:
        return jsonify({'error': 'Registro no encontrado'}), 404

@app.route('/cambiar_estado_pago', methods=['POST'])
def cambiar_estado_pago():
    datos = request.get_json()
    dni = str(datos.get('dni')).strip()
    fecha_hora = datos.get('fecha_hora')
    estado_pago = datos.get('estado_pago')

    df = leer_datos()
    filtro = (df['DNI'].astype(str) == dni) & (df['Fecha y Hora'] == fecha_hora)

    if filtro.any():
        df.loc[filtro, 'Estado Pago'] = estado_pago
        guardar_datos(df)
        return jsonify({'status': 'actualizado'})
    else:
        return jsonify({'error': 'Registro no encontrado'}), 404

@app.route('/exportar_datos', methods=['POST'])
def exportar_datos():
    datos = request.get_json()
    registros = datos.get('registros', [])

    if not registros:
        return jsonify({'error': 'No hay registros para exportar'}), 400

    df = pd.DataFrame(registros)
    archivo = f"exportacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    ruta = os.path.join('exportaciones', archivo)
    os.makedirs('exportaciones', exist_ok=True)
    df.to_excel(ruta, index=False)

    return jsonify({'archivo': archivo})

@app.route('/descargar/<path:filename>')
def descargar(filename):
    return send_from_directory('exportaciones', filename, as_attachment=True)

# ------------------ SMS ------------------

@app.route('/enviar_sms', methods=['POST'])
def enviar_sms():
    data = request.json
    telefono = data.get('telefono')
    mensaje = data.get('mensaje')

    if not telefono or not mensaje:
        return jsonify({'error': 'Faltan datos'}), 400

    estado = 'Enviado'

    registrar_sms(telefono, mensaje, estado)

    return jsonify({'status': 'ok', 'mensaje': 'SMS registrado', 'estado_envio': estado})

@app.route('/historial_sms', methods=['GET'])
def historial_sms():
    historial = pd.read_csv(SMS_FILE)
    return historial.to_json(orient='records', force_ascii=False)

@app.route('/descargar_historial_sms', methods=['GET'])
def descargar_historial_sms():
    historial = pd.read_csv(SMS_FILE)
    file_path = 'historial_sms_exportado.csv'
    historial.to_csv(file_path, index=False)
    return send_file(file_path, as_attachment=True)

# ------------------ Frontend ------------------

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory('../frontend', 'admin.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('../frontend', filename)

# ------------------ Run ------------------

if __name__ == '__main__':
    from flask_cors import CORS
    CORS(app)
    app.run(host='0.0.0.0', port=10000)
