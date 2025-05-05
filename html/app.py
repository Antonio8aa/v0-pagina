from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, Image, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import re
from flask import Flask, render_template, redirect, url_for, flash, request, session, send_file
from flask_bcrypt import Bcrypt
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import utils
import qrcode as qr
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from io import BytesIO
from flask_caching import Cache
from functools import wraps
import pyodbc
import secrets

app = Flask(__name__)
clave_secreta = secrets.token_hex(16)
app.secret_key = clave_secreta
bcrypt = Bcrypt(app)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})  # Puedes cambiar 'simple' por otras opciones como 'memcached' o 'redis'

# Configuración de la base de datos
server = 'DESKTOP-Q5OLFD7'
database = 'TiendaPesca'
username = 'sa'
password = 'H9cmhlci'

# Establecer conexión con la base de datos
conn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+password)

def requerir_autenticacion(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'usuario_pesca' not in session:
            flash('Debes iniciar sesión para acceder a esta página', 'error')
            return redirect(url_for('iniciosesion'))
        return func(*args, **kwargs)
    return wrapper


@app.route('/limpiar_cache')
def limpiar_cache():
    cache.clear()
    return 'Caché limpiada'

@app.route('/')
@cache.memoize(timeout=60)  # El resultado se almacenará en caché durante 60 segundos
def index():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Art_Tipo")
    Art_Tipo = cursor.fetchall()
    return render_template('index.html', Art_Tipo=Art_Tipo)
    
@app.route('/indexadmin')
@cache.memoize(timeout=60)  # El resultado se almacenará en caché durante 60 segundos
def indexadmin():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Art_Tipo")
    Art_Tipo = cursor.fetchall()
    return render_template('indexadmin.html', Art_Tipo=Art_Tipo)

@app.route('/indexusuario')
@cache.memoize(timeout=60)  # El resultado se almacenará en caché durante 60 segundos
def indexusuario():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Art_Tipo")
    Art_Tipo = cursor.fetchall()
    return render_template('indexusuario.html', Art_Tipo=Art_Tipo)

@app.route('/articulos')
def articulos():
    with obtener_cursor() as cursor:

        # Realizar la consulta para obtener la información de los articulos
        cursor.execute("SELECT * FROM Art_Tipo")
        Art_Tipo = cursor.fetchall()

    return render_template('productos.html', Art_Tipo=Art_Tipo)


def obtener_articulo_por_id(articulo_id):
    try:
        # Establece la conexión con la base de datos
            with conn.cursor() as cursor:
                # Ejecuta la consulta SQL para obtener el articulo por su ID
                cursor.execute("SELECT * FROM Articulos WHERE Articulo_ID=?", articulo_id)
                articulo = cursor.fetchone()

                # Verifica si se encontró el articulo
                if articulo:
                    # Construye un diccionario con la información del articulo
                    articulo_dict = {
                        'Articulo_ID': articulo[0],
                        'Nombre_Pr': articulo[1],
                        'Descripcion_P': articulo[2],
                        'Stock': articulo[3],
                        'Precio_P': articulo[4],
                        'Tipo_Articulo': articulo[5],
                        'imagen': articulo[6]
                    }

                    return articulo_dict
                else:
                    return None  # Retorna None si no se encuentra el articulo
                
    except Exception as e:
        print(f"Error al obtener el articulo: {e}")
        return None

@app.route('/ver_carrito')
def ver_carrito():
    print(f"Contenido de la sesión: {session}")
    # Verifica si 'carrito' está en la sesión y tiene elementos
    if 'carrito' in session and session['carrito']:
        carrito = session['carrito']
        total_carrito = sum(item['precio'] * item['cantidad'] for item in carrito)
        session['total_carrito'] = total_carrito  # Almacena el total en la sesión
    else:
        carrito = []  # Define una lista vacía si no hay elementos en el carrito
        total_carrito = 0

    return render_template('ver_carrito.html', carrito=carrito, total_carrito=total_carrito)

@app.route('/agregar_al_carrito/<int:articulo_id>', methods=['POST'])
def agregar_al_carrito(articulo_id):
    print(f"Agregando al carrito el articulo con ID {articulo_id}")
    # Obtener el articulo de la base de datos
    articulos = obtener_articulo_por_id(articulo_id)

    if 'carrito' not in session:
        session['carrito'] = []

    cantidad_seleccionada = int(request.form.get('cantidad', 1))

    if cantidad_seleccionada <= 0:
        flash('La cantidad debe ser mayor que cero.', 'error')
    elif cantidad_seleccionada > articulos['Stock']:
        flash('No hay suficiente stock disponible para esa cantidad.', 'error')
    else:
        # Verificar si el articulo ya está en el carrito
        articulo_existente = next((item for item in session['carrito'] if item['articulo_id'] == articulo_id), None)

        if articulo_existente:
            # Actualizar la cantidad del articulo existente
            articulo_existente['cantidad'] += cantidad_seleccionada
        else:
            # Agregar el articulo al carrito en la sesión
            session['carrito'].append({
                'articulo_id': articulos['Articulo_ID'],
                'nombre': articulos['Nombre_Pr'],
                'descripcion': articulos['Descripcion_P'],
                'precio': articulos['Precio_P'],
                'cantidad': cantidad_seleccionada,
            })

        session['articulo_id_en_carrito'] = articulo_id  # Almacena el ID del último articulo en la sesión
        session.modified = True

    # Redirigir a la página del carrito o a donde desees
    return redirect(url_for('ver_carrito'))
 
def obtener_cliente_pesca_id(nombre, apellido):
    with obtener_cursor() as cursor:
        # Realizar la consulta para obtener el ID del cliente_pesca
        cursor.execute("SELECT Cliente_ID FROM Cliente_Pesca WHERE nombre_c = ? AND apellido_c = ?", (nombre, apellido))
        resultado = cursor.fetchone()

        if resultado:
            # Si se encuentra un resultado, retornar el ID del cliente_pesca
            return resultado[0]
        else:
            # Manejar el caso en el que no se encuentre un cliente_pesca con ese nombre y apellido
            # Puedes levantar una excepción, retornar un valor predeterminado, etc.
            return None

from datetime import datetime
from flask import request, session, redirect, url_for, flash, render_template
import sqlite3  # Si usas SQLite, por ejemplo

@app.route('/procesar_pago', methods=['GET', 'POST'])
@requerir_autenticacion
def procesar_pago():
    # Obtener el carrito de la sesión
    carrito = session.get('carrito', [])
    total_carrito = sum(item['precio'] * item['cantidad'] for item in carrito)

    if request.method == 'POST':
        nombre_cliente_pesca = request.form['nombre_cliente_pesca']
        apellido_cliente_pesca = request.form['apellido_cliente_pesca']
        tienda_id = request.form['Tienda_ID']
        numero_tarjeta = request.form['numero_tarjeta']
        fecha_vencimiento = request.form['fecha_vencimiento']
        cvv = request.form['cvv']

        try:
            tienda_id = int(tienda_id)
        except ValueError:
            flash('Sucursal inválida.', 'danger')
            return redirect(url_for('procesar_pago'))

        with obtener_cursor() as cursor:
            cursor.execute("SELECT Nombre_T, Direccion_T FROM TiendaPesca WHERE Tienda_ID = ?", (tienda_id,))
            tienda_info = cursor.fetchone()
            if tienda_info is None:
                flash('La sucursal seleccionada no existe.', 'danger')
                return redirect(url_for('procesar_pago'))

        tienda_nombre, tienda_direccion = tienda_info

        # Verificar si la fecha de vencimiento es válida
        try:
            fecha_vencimiento_dt = datetime.strptime(fecha_vencimiento, '%m/%y')
            if fecha_vencimiento_dt < datetime.now():
                flash('La fecha de vencimiento de la tarjeta no es válida.', 'danger')
                return redirect(url_for('procesar_pago'))
        except ValueError:
            flash('La fecha de vencimiento de la tarjeta es inválida.', 'danger')
            return redirect(url_for('procesar_pago'))

        # Obtener el ID del cliente
        cliente_pesca_id = obtener_cliente_pesca_id(nombre_cliente_pesca, apellido_cliente_pesca)

        session['datos_venta_pesca'] = {
            'nombre_cliente_pesca': nombre_cliente_pesca,
            'apellido_cliente_pesca': apellido_cliente_pesca,
            'cliente_pesca_id': cliente_pesca_id,
            'tienda_id': tienda_id,
            'tienda_nombre': tienda_nombre,
            'tienda_direccion': tienda_direccion,
            'total_carrito': total_carrito,
            'numero_tarjeta_ultimos4': numero_tarjeta[-4:],
            'fecha_vencimiento': fecha_vencimiento,
            'cvv_ultimos2': cvv[-2:],
            'carrito': carrito
        }

        print(f"[LOG] tienda_id recibido del formulario: {tienda_id}")

        return redirect(url_for('confirmar_venta_pesca'))

    # Si es GET, obtener la lista de tiendas
    with obtener_cursor() as cursor:
        cursor.execute("SELECT * FROM TiendaPesca")
        tiendas = cursor.fetchall()

    return render_template('procesar_pago.html', tiendas=tiendas, carrito=carrito, total_carrito=total_carrito)

def actualizar_stock(articulo_id, cantidad):
    try:
        # Establece la conexión con la base de datos
        with conn.cursor() as cursor:
            # Actualiza el stock del articulo restando la cantidad vendida
            cursor.execute("UPDATE Articulos SET Stock = Stock - ? WHERE Articulo_ID = ?", (cantidad, articulo_id))
            conn.commit()

    except Exception as e:
        print(f"Error al actualizar el stock del articulo: {e}")

def generar_pdf(datos_venta_pesca, carrito, qr_filename):
    fecha_venta_pesca = datetime.now()
    pdf_filename = f"ticket_{fecha_venta_pesca.strftime('%Y%m%d%H%M%S')}.pdf"
    pdf_path = f"static/pdf/{pdf_filename}"

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    elements = []

    # Encabezado
    encabezado = [[datos_venta_pesca['tienda_nombre'], '']]
    tabla_encabezado = Table(encabezado, colWidths=[400, 100])
    tabla_encabezado.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#31AFAA')),
                                          ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                          ('ALIGNMENT', (0, 0), (-1, 0), 'CENTER'),
                                          ('FONTSIZE', (0, 0), (-1, 0), 14),
                                          ('BOTTOMPADDING', (0, 0), (-1, 0), 12)]))
    elements.append(tabla_encabezado)

    # Información del cliente_pesca
    info_cliente_pesca = [
    ['Nombre del Cliente_Pesca:', f"{datos_venta_pesca.get('nombre_cliente_pesca', '')} {datos_venta_pesca.get('apellido_cliente_pesca', '')}"],
    ['Información de la Tarjeta:', ''],
    ['Número de Tarjeta:', f"**** **** **** {datos_venta_pesca.get('numero_tarjeta', '0000')[-4:]}"],
    ['Fecha de Vencimiento:', datos_venta_pesca.get('fecha_vencimiento', 'N/A')],
    ['CVV:', f"*{datos_venta_pesca.get('cvv', '*')}"]
]

    # Definir estilos de las tablas
    estilos_tabla = TableStyle([('BOTTOMPADDING', (0, 0), (-1, -1), 5)])

    # Crear la tabla de información del cliente_pesca sin aplicar el estilo directamente
    tabla_info_cliente_pesca = Table(info_cliente_pesca, colWidths=[200, 300])
    tabla_info_cliente_pesca.setStyle(estilos_tabla)

    # Añadir la tabla de información del cliente_pesca a la lista de elementos
    elements.append(tabla_info_cliente_pesca)

    # Detalles de la compra
    detalles_compra = [['TiendaPesca Seleccionada:', datos_venta_pesca['tienda_nombre']],
                       ['Total de la Compra:', f"${datos_venta_pesca['total_carrito']}"],
                       ['Articulos Seleccionados:', '']]
    tabla_detalles = Table(detalles_compra, colWidths=[200, 300])
    tabla_detalles.setStyle(estilos_tabla)
    elements.append(tabla_detalles)

    # Articulos
    articulos = [[Paragraph(item['nombre'], styles['BodyText']),
                  Paragraph(item['descripcion'], styles['BodyText']),
                  Paragraph(f"Cantidad: {item['cantidad']}", styles['BodyText'])] for item in carrito]
    tabla_articulos = Table(articulos, colWidths=[200, 300, 100])
    tabla_articulos.setStyle(estilos_tabla)
    elements.append(tabla_articulos)

    # Código QR
    qr_path = f"static/qr_codes/{qr_filename}"
    qr_img = Image(qr_path, width=150, height=150)
    elements.append(qr_img)
    elements.append(Paragraph("Escanea este QR para recolectar tus articulos", styles['BodyText']))

    doc.build(elements)
    return pdf_path

def generar_qr(datos_venta_pesca):
    fecha_venta_pesca = datetime.now()
    qr_filename = f"qr_code_{fecha_venta_pesca.strftime('%Y%m%d%H%M%S')}.png"
    qr_path = f"static/qr_codes/{qr_filename}"

    # Crear una cadena con los datos relevantes para el código QR
    qr_data = f"ID de Venta_Pesca: {datos_venta_pesca['venta_pesca_id']}\n"
    qr_data += f"Fecha de Compra: {fecha_venta_pesca}\n"
    qr_data += f"Nombre del Comprador: {datos_venta_pesca['nombre_cliente_pesca']} {datos_venta_pesca['apellido_cliente_pesca']}\n"
    qr_data += f"TiendaPesca: {datos_venta_pesca['tienda_nombre']}\n"  # Usar el nombre completo de la tienda
    qr_data += f"Total de la Compra: {datos_venta_pesca['total_carrito']}"

    # Crear el código QR y guardarlo como imagen
    qr_img = qr.make(qr_data)
    qr_img.save(qr_path)

    return qr_filename

@app.route('/confirmar_venta_pesca', methods=['GET', 'POST'])
@requerir_autenticacion
def confirmar_venta_pesca():
    # Obtener los datos guardados en la sesión
    datos_venta_pesca = session.get('datos_venta_pesca', None)
    carrito = session.get('carrito', [])

    # Verificar si hay datos de venta_pesca en la sesión
    if not datos_venta_pesca:
        return redirect(url_for('procesar_pago'))
    
    if request.method == 'POST':
        # Obtener datos del formulario y realizar la confirmación de la venta_pesca
        fecha_venta_pesca = datetime.now()
        cliente_pesca_id = datos_venta_pesca['cliente_pesca_id']
        tienda_id = datos_venta_pesca['tienda_id']
        total_venta_pesca = datos_venta_pesca['total_carrito']

        # Iterar sobre los elementos del carrito
        for articulo_en_carrito in carrito:
            articulo_id = articulo_en_carrito['articulo_id']
            cantidad_articulo = articulo_en_carrito['cantidad']

            # Realizar la inserción en la tabla de Venta_Pescas para cada articulo en el carrito
            with obtener_cursor() as cursor:
                cursor.execute("INSERT INTO Venta_Pesca (Articulo_ID, Cantidad, Fecha_Venta, Cliente_ID, Tienda_ID, Total_Venta) VALUES (?, ?, ?, ?, ?, ?)",
                             articulo_id, cantidad_articulo, fecha_venta_pesca, cliente_pesca_id, tienda_id, total_venta_pesca)
                conn.commit()

            # Actualizar el stock del articulo en la base de datos
            actualizar_stock(articulo_id, cantidad_articulo)

        # Obtener el ID de la venta_pesca recién creada
        with obtener_cursor() as cursor:
            cursor.execute("SELECT MAX(Venta_ID) FROM Venta_Pesca")
            venta_pesca_id = cursor.fetchone()[0]

        # Limpiar el carrito y otros datos de la sesión después de completar la venta_pesca
        session.pop('datos_venta_pesca', None)
        session.pop('articulo_id_en_carrito', None)
        session.pop('carrito', None)

        # Agregar el ID de la venta_pesca a los datos de venta_pesca para el QR
        datos_venta_pesca['venta_pesca_id'] = venta_pesca_id

        # Generar el código QR y obtener la ruta del archivo
        qr_filename = generar_qr(datos_venta_pesca)

        pdf_path = generar_pdf(datos_venta_pesca, carrito, qr_filename)

        # Almacenar el PDF en el directorio 'static/pdfs'
        pdf_name = f"ticket_{fecha_venta_pesca.strftime('%Y%m%d%H%M%S')}.pdf"
        return send_file(pdf_path, as_attachment=True, download_name=pdf_name)

    return render_template('confirmar_venta.html', datos_venta_pesca=datos_venta_pesca, carrito=carrito)

@app.route('/eliminar_del_carrito/<int:articulo_id>', methods=['POST', 'GET'])
def eliminar_del_carrito(articulo_id):
    # Obtén el carrito de la sesión
    carrito = session.get('carrito', [])

    # Filtra los articulos para mantener solo aquellos que no coincidan con el ID del articulo a eliminar
    carrito = [item for item in carrito if item['articulo_id'] != articulo_id]

    # Actualiza el carrito en la sesión
    session['carrito'] = carrito
    session.modified = True
    # Redirige de nuevo a la página del carrito
    return redirect(url_for('ver_carrito'))

# ... (otras importaciones y código)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/about2')
def about2():
    return render_template('about2.html')


@app.route('/glasses')
def glasses():
    with obtener_cursor() as cursor:

        # Realizar la consulta para obtener la información de los articulos
        cursor.execute("SELECT * FROM Art_Tipo")
        Art_Tipo = cursor.fetchall()

    return render_template('glasses.html', Art_Tipo=Art_Tipo)

@app.route('/shop')
def shop():
    return render_template('shop.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/shop2')
def shop2():
    return render_template('shop2.html')

@app.route('/contact2')
def contact2():
    return render_template('contact2.html')

@app.route('/iniciosesion', methods=['GET', 'POST'])
def iniciosesion():
    if request.method == 'POST':
        # Obtener datos del formulario
        usuario_pesca = request.form['username']
        contraseña = request.form['password']

        # Realizar la consulta para verificar si es un cliente_pesca
        with obtener_cursor() as cursor:
            cursor.execute("SELECT * FROM Usuario_Pesca WHERE Usuario = ?", usuario_pesca)
            user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user.Contraseña, contraseña):
            # Limpiar el carrito existente si hay uno
            if 'carrito' in session:
                del session['carrito']

            # Almacenar el nuevo usuario_pesca en la sesión
            session['usuario_pesca'] = usuario_pesca
            return redirect(url_for('indexusuario'))
        else:
            # Realizar la consulta para verificar si es un administrador
            with obtener_cursor() as cursor:
                cursor.execute("SELECT * FROM Vendedores WHERE Nombre_V = ? AND Licencia_V = ?", usuario_pesca, contraseña)
                admin = cursor.fetchone()

            if admin:
                # Si el administrador existe, almacenar en la sesión
                session['usuario_pesca'] = usuario_pesca
                return redirect(url_for('indexadmin'))  # Cambiar a 'indexadmin'

            else:
                flash('Nombre de usuario_pesca o contraseña incorrectos.', 'danger')

    return render_template('iniciosesion.html')

def obtener_cursor():
    return conn.cursor()

@app.route('/lista_articulos')
def lista_articulos():
    with obtener_cursor() as cursor:
        cursor.execute("SELECT * FROM Art_Tipo")
        articulos = cursor.fetchall()

    return render_template('lista_productos.html', articulos=articulos)

@app.route('/actualizar_articulo/<int:articulo_id>', methods=['GET', 'POST'])
def actualizar_articulo(articulo_id):
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        stock = request.form['stock']
        precio = request.form['precio']
        tipo_id = request.form['tipo']

        # Actualizar el articulo en la base de datos
        with obtener_cursor() as cursor:
            cursor.execute("UPDATE Articulos SET Nombre_A=?, Descripcion_A=?, Stock=?, Precio_A=?, Tipo_Articulo=? WHERE Articulo_ID=?", nombre, descripcion, stock, precio, tipo_id, articulo_id)
            conn.commit()

        # Redirigir a la lista de articulos
        return redirect(url_for('lista_articulos'))
    # Obtener la información del articulo para mostrar en el formulario de actualización
    with obtener_cursor() as cursor:
        cursor.execute("SELECT * FROM Articulos WHERE Articulo_ID=?", articulo_id)
        articulo = cursor.fetchone()

    # Obtener la lista de tipos de articulos
    with obtener_cursor() as cursor:
        cursor.execute("SELECT * FROM Tipos_articulos")
        tipos_articulos = cursor.fetchall()

    return render_template('actualizar_producto.html', articulo=articulo, tipos_articulos=tipos_articulos)

@app.route('/eliminar_articulo/<int:articulo_id>')
def eliminar_articulo(articulo_id):
    try:
        # Eliminar registros relacionados en la tabla Detalle_Venta_Pesca_Pesca
        with obtener_cursor() as cursor:
            cursor.execute("DELETE FROM Detalle_Venta_Pesca_Pesca WHERE Venta_Pesca_IDDV IN (SELECT Venta_Pesca_ID FROM Venta_Pesca WHERE Articulo_ID=?)", articulo_id)

        # Eliminar registros relacionados en la tabla Venta_Pesca
        with obtener_cursor() as cursor:
            cursor.execute("DELETE FROM Venta_Pesca WHERE Articulo_ID=?", articulo_id)

        # Eliminar el articulo de la tabla Articulos
        with obtener_cursor() as cursor:
            cursor.execute("DELETE FROM Articulos WHERE Articulo_ID=?", articulo_id)
            conn.commit()

        flash('Articulo eliminado correctamente.', 'success')
    except Exception as e:
        flash('Error al eliminar el articulo: ' + str(e), 'danger')

    # Redirigir a la lista de articulos
    return redirect(url_for('lista_articulos'))


@app.route('/agregar_articulo', methods=['GET', 'POST'])
def agregar_articulo():
    # Obtener la lista de tipos de articulos
    with obtener_cursor() as cursor:
        cursor.execute("SELECT * FROM Tipos_articulos")
        tipos_articulos = cursor.fetchall()

    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        stock = request.form['stock']
        precio = request.form['precio']
        tipo_id = request.form['tipo']  # Obtener el ID del tipo de articulo seleccionado

        # Obtener la imagen del formulario
        imagen = None
        if 'imagen' in request.files:
            imagen = request.files['imagen']
            # Guardar la imagen en el sistema de archivos o en la base de datos según tus necesidades
        precio_sin_comas = precio.replace(',', '')
        precio_formateado = "${:,.2f}".format(float(precio_sin_comas))
        # Insertar el nuevo articulo en la base de datos
        with pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+password) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Articulos (Nombre_A, Descripcion_A, Stock, Precio_A, Tipo_Articulo, imagen) VALUES (?, ?, ?, ?, ?, ?)", nombre, descripcion, stock, precio_sin_comas, tipo_id, imagen.filename if imagen else None)
            conn.commit()

        # Redirigir a la lista de articulos
        return redirect(url_for('lista_articulos',  precio=precio_formateado))

    # Renderizar el formulario para agregar articulos
    return render_template('agregar_producto.html', tipos_articulos=tipos_articulos)


@app.route('/ver_vendedors')
def ver_vendedors():
    with obtener_cursor() as cursor:
        # Obtener la lista de vendedors
        cursor.execute("SELECT * FROM Vendedores")
        vendedors = cursor.fetchall()

        # Obtener la información de la vista VistaVendedoresPorTiendaPesca
        cursor.execute("SELECT * FROM VistaVendedoresPorTienda")
        vendedors_por_tienda = cursor.fetchall()

    return render_template('ver_empleados.html', vendedors=vendedors, vendedors_por_tienda=vendedors_por_tienda)



@app.route('/agregar_vendedor', methods=['GET', 'POST'])
def agregar_vendedor():
    if request.method == 'POST':
        # Obtener datos del formulario
        licencia = request.form['licencia']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        cargo = request.form['cargo']
        tienda_id = request.form['tienda']
        sueldo = request.form['sueldo']

        # Insertar el nuevo vendedor en la base de datos
        with obtener_cursor() as cursor:
            cursor.execute("INSERT INTO Vendedores (Licencia_E, Nombre_E, Apellido_E, Cargo_E, TiendaPesca_IDE, Sueldo_E) VALUES (?, ?, ?, ?, ?, ?)", licencia, nombre, apellido, cargo, tienda_id, sueldo)
            conn.commit()

        # Redirigir a la lista de vendedors
        return redirect(url_for('ver_vendedors'))

    # Obtener la lista de tiendas para el formulario
    with obtener_cursor() as cursor:
        cursor.execute("SELECT * FROM TiendaPesca")
        tiendas = cursor.fetchall()

    # Renderizar el formulario para agregar vendedors
    return render_template('agregar_vendedor.html', tiendas=tiendas)

# Ruta para manejar la actualización de vendedors
@app.route('/actualizar_vendedor/<int:Vendedores_ID>', methods=['GET', 'POST'])
def actualizar_vendedor(Vendedores_ID):
    if request.method == 'POST':
        # Obtener datos del formulario
        licencia = request.form['licencia']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        cargo = request.form['cargo']
        sueldo = request.form['sueldo']
        tienda_id = request.form['tienda']

        # Actualizar el vendedor en la base de datos
        with obtener_cursor() as cursor:
            cursor.execute("UPDATE Vendedores SET Licencia_E=?, Nombre_E=?, Apellido_E=?, Cargo_E=?, Sueldo_E=?, TiendaPesca_IDE=? WHERE Vendedores_ID=?", licencia, nombre, apellido, cargo, sueldo, tienda_id, Vendedores_ID)
            conn.commit()

        # Redirigir a la lista de vendedors
        return redirect(url_for('ver_vendedors'))

    # Obtener la información del vendedor para mostrar en el formulario de actualización
    with obtener_cursor() as cursor:
        cursor.execute("SELECT * FROM Vendedores WHERE Vendedor_ID=?", Vendedores_ID)
        vendedor = cursor.fetchone()

    # Obtener la lista de tiendas (o cualquier otra lista que necesites)
    with obtener_cursor() as cursor:
        cursor.execute("SELECT * FROM TiendaPesca")
        tiendas = cursor.fetchall()

    return render_template('actualizar_empleado.html', vendedor=vendedor, tiendas=tiendas)

@app.route('/eliminar_vendedor/<int:Vendedores_ID>')
def eliminar_vendedor(Vendedores_ID):
    # Eliminar el vendedor de la base de datos
    with obtener_cursor() as cursor:
        cursor.execute("DELETE FROM Vendedores WHERE Vendedores_ID=?", Vendedores_ID)
        conn.commit()

    # Redirigir a la lista de vendedors
    return redirect(url_for('ver_vendedors'))
from flask import flash, redirect, render_template, request, url_for

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        # Obtener datos del formulario
        Nombre_C = request.form['Nombre_C']
        Apellido_C = request.form['Apellido_C']
        Direccion_C = request.form['Direccion_C']
        Telefono_C = request.form['Telefono_C']
        nombre_usuario_pesca = request.form['nombre_usuario_pesca']
        contrasena = request.form['contrasena']

        # Verificar si el nombre de usuario_pesca ya está en uso
        with obtener_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM Usuario_Pesca WHERE Usuario = ?", (nombre_usuario_pesca,))
            existe_usuario_pesca = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM Cliente_Pesca WHERE Telefono_C = ?", (Telefono_C,))
            existe_telefono = cursor.fetchone()[0]

        if existe_usuario_pesca:
            flash('El nombre de usuario_pesca ya está en uso. Por favor, elige otro.', 'danger')
            return redirect(url_for('registro'))

        if existe_telefono:
            flash('El número de teléfono ya está en uso. Por favor, introduce otro.', 'danger')
            return redirect(url_for('registro'))

        # Hashear la contraseña con Flask-Bcrypt
        hashed_password = bcrypt.generate_password_hash(contrasena).decode('utf-8')

        # Registrar al cliente_pesca con la contraseña hasheada
        with obtener_cursor() as cursor:
            cursor.execute("EXEC RegistrarClientePesca ?, ?, ?, ?, ?, ?", (Nombre_C, Apellido_C, Direccion_C, Telefono_C, nombre_usuario_pesca, hashed_password))
            conn.commit()

        flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('iniciosesion'))

    return render_template('registro.html')

# Añade la ruta para mostrar las venta_pescas
@app.route('/Venta_Pescas', methods=['GET', 'POST'])
def Venta_Pescas():
    if request.method == 'POST':
        # Obtén los parámetros de búsqueda desde el formulario
        cantidad = request.form.get('cantidad')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        cliente_pesca = request.form.get('cliente_pesca')
        tienda = request.form.get('tienda')

        # Construye la consulta SQL dinámicamente según los parámetros de búsqueda
        query = "SELECT * FROM VistaVenta_PescasPesca WHERE 1=1"

        if cantidad:
            query += f" AND Cantidad = {cantidad}"

        if fecha_inicio:
            query += f" AND Fecha_Ven >= '{fecha_inicio}'"

        if fecha_fin:
            query += f" AND Fecha_Ven <= '{fecha_fin}'"

        if cliente_pesca:
            query += f" AND NombreCliente_Pesca LIKE '%{cliente_pesca}%'"

        if tienda:
            query += f" AND InfoTiendaPesca LIKE '%{tienda}%'"

        with obtener_cursor() as cursor:
            cursor.execute(query)
            venta_pescas = cursor.fetchall()
    else:
        # Si no se envían parámetros de búsqueda, muestra todas las venta_pescas
        with obtener_cursor() as cursor:
            cursor.execute("SELECT * FROM VistaVenta_PescasPesca")
            venta_pescas = cursor.fetchall()

    # Renderiza la plantilla Venta_Pescas.html con la información de las venta_pescas
    return render_template('Ventas.html', venta_pescas=venta_pescas)


# Agrega la función para obtener datos de venta_pescas por día
@app.route('/Reportes')
def Reportes():
    # Obtener articulos más vendidos
    with obtener_cursor() as cursor:
        cursor.execute("SELECT * FROM VistaArticulosMasVendidosMenos ORDER BY TotalVendido DESC")
        articulos_mas_vendidos = cursor.fetchall()

    # Obtener articulos menos vendidos
    with obtener_cursor() as cursor:
        cursor.execute("SELECT * FROM VistaArticulosMasVendidosMenos ORDER BY TotalVendido ASC")
        articulos_menos_vendidos = cursor.fetchall()

    # Obtener datos de venta_pescas por día
    with obtener_cursor() as cursor:
        cursor.execute("SELECT * FROM VistaVenta_PescasPescaPorDia")
        Vista_Venta_Pescas_PorDia = cursor.fetchall()

    # Pasa los datos de venta_pescas por día al gráfico Plotly
    fig = make_subplots(rows=1, cols=1, subplot_titles=["Venta_Pescas por Día"])
    fig.add_trace(
    go.Bar(
        x=[venta_pesca[0] for venta_pesca in Vista_Venta_Pescas_PorDia],
        y=[venta_pesca[1] for venta_pesca in Vista_Venta_Pescas_PorDia],
        name="Total Articulos Vendidos",
        hovertemplate='<b>Fecha:</b> %{x}<br><b>Total Articulos Vendidos:</b> %{y}<br>' + 
                      '<b>Total Venta_Pesca:</b> %{text}<extra></extra>',
        text=[f"${venta_pesca[2]:,.2f}" for venta_pesca in Vista_Venta_Pescas_PorDia],
    ),
    row=1, col=1,
)
    # Configura el diseño del gráfico
    fig.update_layout(
        title="Venta_Pescas por Día",
        xaxis_title="Fecha",
        yaxis_title="Total de Articulos Vendidos",
    )

    # Convierte el gráfico a HTML y pasa a la plantilla HTML
    graph_html = fig.to_html(full_html=False)

    # Obtener cliente_pescas que más han comprado
    with obtener_cursor() as cursor:
        cursor.execute("SELECT * FROM VistaCliente_PescasMasCompradores ORDER BY Total_Compras DESC")
        cliente_pescas_mas_compradores = cursor.fetchall()

    return render_template('Reportes.html', 
                           articulos_mas_vendidos=articulos_mas_vendidos, 
                           articulos_menos_vendidos=articulos_menos_vendidos, 
                           Vista_Venta_Pescas_PorDia=Vista_Venta_Pescas_PorDia, 
                           graph_html=graph_html,
                           cliente_pescas_mas_compradores=cliente_pescas_mas_compradores)


@app.route('/cerrar_sesion')
def cerrar_sesion():
    # Eliminar la información del usuario_pesca y los datos de venta_pesca de la sesión
    session.pop('usuario_pesca', None)
    session.pop('datos_venta_pesca', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
