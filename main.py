import flet as ft
from datetime import datetime, timedelta
import os
import json 
import sys
import types
import urllib.parse
from dotenv import load_dotenv

# --- 1. CARGAR VARIABLES DE ENTORNO (Ruta absoluta para Android) ---
directorio_actual = os.path.dirname(os.path.abspath(__file__))
ruta_env = os.path.join(directorio_actual, '.env')
load_dotenv(ruta_env) 

# --- 2. PARCHE PARA ANDROID (MOCKS ESTRUCTURALES) ---
class DummyServerClass:
    # Una clase vacía perfecta para que Google herede de ella sin errores
    pass

class DummyModule(types.ModuleType):
    def __init__(self, name):
        super().__init__(name)
        self.__path__ = []

    def __getattr__(self, name):
        # Cuando Google pida una herramienta (como WSGIServer), le damos nuestra clase
        return DummyServerClass

# Creamos los módulos falsos como si fueran carpetas reales
wsgiref_mod = DummyModule('wsgiref')
simple_server_mod = DummyModule('wsgiref.simple_server')
util_mod = DummyModule('wsgiref.util')
http_server_mod = DummyModule('http.server')

# Conectamos las carpetas para que la ruta wsgiref.simple_server exista de verdad
wsgiref_mod.simple_server = simple_server_mod
wsgiref_mod.util = util_mod

# Registramos todo en el sistema matriz de Python
sys.modules['wsgiref'] = wsgiref_mod
sys.modules['wsgiref.simple_server'] = simple_server_mod
sys.modules['wsgiref.util'] = util_mod
sys.modules['http.server'] = http_server_mod

import gspread

# --- 3. CONEXIÓN A GOOGLE SHEETS EN LA NUBE ---
try:
    credenciales_texto = os.environ.get('GOOGLE_CREDENTIALS')
    if not credenciales_texto:
        raise ValueError("No se encontró la variable de entorno GOOGLE_CREDENTIALS")
    credenciales_dict = json.loads(credenciales_texto)
    gc = gspread.service_account_from_dict(credenciales_dict)
    libro = gc.open('Clientes Kratos') 
    hoja_datos = libro.sheet1 
except Exception as e:
    print(f"Error de conexión con Google Sheets: {e}")
    hoja_datos = None

# --- 4. APLICACIÓN PRINCIPAL FLET ---
def main(page: ft.Page):
    # --- NUEVO LOOK KRATOS (NEGRO Y GRIS PURO) ---
    page.title = "Gym Kratos"
    page.bgcolor = ft.Colors.BLACK # Fondo negro puro
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER 

    # ---------------------------------------------------
    # PANTALLA 2: REGISTRAR CLIENTE
    # ---------------------------------------------------
    def mostrar_registro(e=None):
        page.controls.clear() 
        
        titulo = ft.Text("📝 NUEVO INGRESO", size=24, weight=ft.FontWeight.BOLD)
        
        # --- CAMPOS DE TEXTO BLANCOS Y LETRA NEGRA ABSOLUTA ---
        input_nombre = ft.TextField(
            label="Nombre del cliente", 
            bgcolor=ft.Colors.WHITE, 
            color=ft.Colors.BLACK,
            label_style=ft.TextStyle(color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD),
            width=300
        )
        
        input_telefono = ft.TextField(
            label="Teléfono (ej: +56912345678)", 
            bgcolor=ft.Colors.WHITE, 
            color=ft.Colors.BLACK,
            label_style=ft.TextStyle(color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD),
            width=300
        )
        
        dropdown_plan = ft.Dropdown(
            label="Tipo de inscripción",
            filled=True,
            fill_color=ft.Colors.WHITE,
            color=ft.Colors.BLACK,
            label_style=ft.TextStyle(color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD),
            width=300,
            options=[
                ft.dropdown.Option("Personalizado"),
                ft.dropdown.Option("No personalizado"),
            ],
        )
        
        texto_mensaje = ft.Text(value="", size=16)

        def guardar_cliente(e):
            if hoja_datos is None:
                texto_mensaje.value = "❌ No hay conexión a Google Sheets."
                texto_mensaje.color = "red"
                page.update()
                return

            nombre = input_nombre.value
            telefono = input_telefono.value
            tipo_plan = dropdown_plan.value
            
            if not nombre or not telefono or not tipo_plan:
                texto_mensaje.value = "❌ Llena todos los campos."
                texto_mensaje.color = "red"
                page.update()
                return

            if not telefono.startswith("+569") or len(telefono) != 12 or not telefono[4:].isdigit():
                texto_mensaje.value = "❌ Número no válido (Ej: +56912345678)"
                texto_mensaje.color = "red"
                page.update()
                return

            fecha_termino = datetime.now() + timedelta(days=30)
            fecha_texto = fecha_termino.strftime("%Y-%m-%d")
            
            hoja_datos.append_row([nombre, telefono, tipo_plan, fecha_texto, "Nuevo"])
            
            texto_mensaje.value = f"✅ ¡{nombre} guardado en la nube!"
            texto_mensaje.color = "green"
            input_nombre.value = ""
            input_telefono.value = ""
            dropdown_plan.value = None
            page.update()

        estilo_btn = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=4), 
            bgcolor=ft.Colors.RED_900,
            color=ft.Colors.WHITE,
        )
        btn_guardar = ft.ElevatedButton("GUARDAR CLIENTE", width=300, height=50, style=estilo_btn, on_click=guardar_cliente)
        
        btn_volver = ft.OutlinedButton("⬅️ Volver al Menú", width=300, height=50, on_click=mostrar_menu)

        page.add(
            titulo, input_nombre, input_telefono, dropdown_plan, 
            btn_guardar, texto_mensaje, 
            ft.Divider(height=20, color="transparent"), btn_volver
        )
        page.update()

    # ---------------------------------------------------
    # PANTALLA 3: VER CLIENTES
    # ---------------------------------------------------
    def mostrar_lista(e=None):
        page.controls.clear()
        
        titulo = ft.Text("👥 LISTA DE CLIENTES", size=24, weight=ft.FontWeight.BOLD)
        btn_volver = ft.OutlinedButton("⬅️ Volver al Menú", width=300, height=50, on_click=mostrar_menu)
        
        lista_visual = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=10)

        if hoja_datos is None:
            lista_visual.controls.append(ft.Text("❌ No hay conexión a Google Sheets."))
        else:
            clientes = hoja_datos.get_all_values()
            if not clientes:
                lista_visual.controls.append(ft.Text("No hay clientes registrados aún."))
            else:
                for cliente in clientes:
                    if len(cliente) < 4: continue
                    nombre = cliente[0]
                    telefono = cliente[1]
                    plan = cliente[2]
                    vence = cliente[3]
                    
                    fecha_vencimiento = datetime.strptime(vence, "%Y-%m-%d")
                    if datetime.now() > fecha_vencimiento:
                        estado = "Vencido"
                        color_estado = "red"
                        icono = "❌"
                    else:
                        estado = "Al día"
                        color_estado = "green"
                        icono = "✅"
                    
                    tarjeta = ft.Card(
                        content=ft.Container(
                            padding=15,
                            content=ft.Column([
                                ft.Text(f"👤 {nombre}", weight=ft.FontWeight.BOLD, size=16),
                                ft.Text(f"📱 {telefono} | 🏋️ {plan}"),
                                ft.Text(f"📅 Vence: {vence} | {icono} {estado}", color=color_estado, weight=ft.FontWeight.BOLD),
                            ])
                        )
                    )
                    lista_visual.controls.append(tarjeta)

        page.add(titulo, lista_visual, btn_volver)
        page.update()

    # ---------------------------------------------------
    # PANTALLA 4: RENOVAR MEMBRESÍA
    # ---------------------------------------------------
    def mostrar_renovar(e=None):
        page.controls.clear()
        
        titulo = ft.Text("🔄 RENOVAR MEMBRESÍA", size=24, weight=ft.FontWeight.BOLD)
        texto_mensaje = ft.Text(value="", size=16)
        
        dropdown_clientes = ft.Dropdown(
            label="Selecciona un cliente", 
            filled=True,
            fill_color=ft.Colors.WHITE,
            color=ft.Colors.BLACK,
            label_style=ft.TextStyle(color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD),
            width=300
        )
        
        if hoja_datos is not None:
            clientes = hoja_datos.get_all_values()
            for i, cliente in enumerate(clientes):
                if len(cliente) > 0:
                    nombre = cliente[0]
                    dropdown_clientes.options.append(ft.dropdown.Option(key=str(i + 1), text=nombre))
        else:
            texto_mensaje.value = "❌ No hay conexión a la nube."
            texto_mensaje.color = "red"

        def renovar_cliente(e):
            if not dropdown_clientes.value:
                texto_mensaje.value = "❌ Selecciona un cliente primero."
                texto_mensaje.color = "red"
                page.update()
                return
            
            fila_excel = int(dropdown_clientes.value)
            nueva_fecha = datetime.now() + timedelta(days=30)
            nueva_fecha_texto = nueva_fecha.strftime("%Y-%m-%d")
            
            hoja_datos.update_cell(fila_excel, 4, nueva_fecha_texto)
            
            texto_mensaje.value = f"✅ ¡Membresía renovada hasta {nueva_fecha_texto}!"
            texto_mensaje.color = "green"
            dropdown_clientes.value = None
            page.update()

        estilo_btn_renovar = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=4), 
            bgcolor=ft.Colors.RED_900,
            color=ft.Colors.WHITE,
        )
        btn_guardar_renovacion = ft.ElevatedButton("RENOVAR 30 DÍAS", width=300, height=50, style=estilo_btn_renovar, on_click=renovar_cliente)
        
        btn_volver = ft.OutlinedButton("⬅️ Volver al Menú", width=300, height=50, on_click=mostrar_menu)

        page.add(
            titulo, dropdown_clientes, btn_guardar_renovacion, texto_mensaje, 
            ft.Divider(height=20, color="transparent"), btn_volver
        )
        page.update()

    # ---------------------------------------------------
    # PANTALLA 5: ELIMINAR CLIENTE
    # ---------------------------------------------------
    def mostrar_eliminar(e=None):
        page.controls.clear()
        
        titulo = ft.Text("🗑️ ELIMINAR CLIENTE", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_500)
        texto_mensaje = ft.Text(value="", size=16)
        
        dropdown_clientes = ft.Dropdown(
            label="Selecciona el cliente a eliminar", 
            width=300,
            filled=True,
            fill_color=ft.Colors.WHITE,
            color=ft.Colors.BLACK,
            label_style=ft.TextStyle(color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD)
        )
        
        def cargar_clientes():
            dropdown_clientes.options.clear()
            if hoja_datos is not None:
                clientes = hoja_datos.get_all_values()
                for i, cliente in enumerate(clientes):
                    if len(cliente) > 0:
                        nombre = cliente[0]
                        dropdown_clientes.options.append(ft.dropdown.Option(key=str(i + 1), text=nombre))
            else:
                texto_mensaje.value = "❌ No hay conexión a la nube."
                texto_mensaje.color = "red"

        cargar_clientes() 

        def borrar_cliente(e):
            if not dropdown_clientes.value:
                texto_mensaje.value = "❌ Selecciona un cliente primero."
                texto_mensaje.color = "red"
                page.update()
                return
            
            fila_excel = int(dropdown_clientes.value)
            hoja_datos.delete_rows(fila_excel)
            
            texto_mensaje.value = f"✅ ¡Cliente eliminado para siempre!"
            texto_mensaje.color = "green"
            dropdown_clientes.value = None
            
            cargar_clientes() 
            page.update()

        estilo_btn_borrar = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=4), 
            bgcolor=ft.Colors.GREY_900,
            color=ft.Colors.RED_500,
        )
        btn_borrar = ft.ElevatedButton("ELIMINAR DEFINITIVAMENTE", width=300, height=50, style=estilo_btn_borrar, on_click=borrar_cliente)
        
        btn_volver = ft.OutlinedButton("⬅️ Volver al Menú", width=300, height=50, on_click=mostrar_menu)

        page.add(
            titulo, dropdown_clientes, btn_borrar, texto_mensaje, 
            ft.Divider(height=20, color="transparent"), btn_volver
        )
        page.update()

    # ---------------------------------------------------
    # PANTALLA 6: AVISOS DE WHATSAPP
    # ---------------------------------------------------
    def mostrar_avisos(e=None):
        page.controls.clear()
        
        titulo = ft.Text("💬 AVISOS MOROSOS", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_500)
        btn_volver = ft.OutlinedButton("⬅️ Volver al Menú", width=300, height=50, on_click=mostrar_menu)
        
        lista_morosos = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=10)

        if hoja_datos is None:
            lista_morosos.controls.append(ft.Text("❌ No hay conexión a Google Sheets.", color=ft.Colors.RED_500))
        else:
            clientes = hoja_datos.get_all_values()
            hay_morosos = False
            
            for cliente in clientes:
                if len(cliente) < 4: continue
                nombre = cliente[0]
                telefono = cliente[1]
                vence = cliente[3]
                
                fecha_vencimiento = datetime.strptime(vence, "%Y-%m-%d")
                
                # Solo mostramos a los que ya vencieron
                if datetime.now() > fecha_vencimiento:
                    hay_morosos = True
                    
                    # Le quitamos el '+' al teléfono por si acaso (wa.me prefiere solo números)
                    tel_limpio = telefono.replace("+", "")
                    
                    # Armamos el mensaje automático
                    mensaje = f"¡Hola {nombre}!  Te escribimos de Gym Kratos. Tu membresía venció el {vence}. ¡Te esperamos para renovar y seguir entrenando con todo! "
                    
                    # Convertimos el texto para que pueda viajar por la URL
                    mensaje_url = urllib.parse.quote(mensaje)
                    link_wsp = f"https://wa.me/{tel_limpio}?text={mensaje_url}"
                    
                    tarjeta = ft.Card(
                        content=ft.Container(
                            padding=15,
                            content=ft.Column([
                                ft.Text(f"👤 {nombre} | Venció: {vence}", weight=ft.FontWeight.BOLD, color=ft.Colors.RED_400),
                                ft.ElevatedButton(
                                    "Enviar Cobro por WhatsApp",
                                    bgcolor=ft.Colors.GREEN_700,
                                    color=ft.Colors.WHITE,
                                    url=link_wsp  # ¡Flet hace la magia directa con esta propiedad!
                                )
                            ])
                        )
                    )
                    lista_morosos.controls.append(tarjeta)
                    
            if not hay_morosos:
                lista_morosos.controls.append(ft.Text("¡Qué buena! Hoy podra tomar desayuno!!. 🎉", color=ft.Colors.GREEN_400, size=16))

        page.add(titulo, lista_morosos, btn_volver)
        page.update()

    # ---------------------------------------------------
    # PANTALLA 1: MENÚ PRINCIPAL
    # ---------------------------------------------------
    def mostrar_menu(e=None):
        page.controls.clear() 
        
        titulo = ft.Text("💪 GYM KRATOS 💪", size=35, weight=ft.FontWeight.W_900, color=ft.Colors.RED_600)
        subtitulo = ft.Text("MENÚ PRINCIPAL", size=14, color="grey")

        estilo_base = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=4), 
            bgcolor=ft.Colors.RED_900,
            color=ft.Colors.WHITE,
        )
        
        estilo_eliminar = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=4), 
            bgcolor=ft.Colors.GREY_900, 
            color=ft.Colors.RED_500
        )
        
        estilo_wsp = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=4), 
            bgcolor=ft.Colors.GREEN_800, 
            color=ft.Colors.WHITE
        )

        btn_registro = ft.ElevatedButton("REGISTRAR NUEVO CLIENTE", width=300, height=60, style=estilo_base, on_click=mostrar_registro)
        btn_lista = ft.ElevatedButton("VER CLIENTES", width=300, height=60, style=estilo_base, on_click=mostrar_lista)
        btn_renovar = ft.ElevatedButton("RENOVAR MEMBRESÍA", width=300, height=60, style=estilo_base, on_click=mostrar_renovar)
        btn_eliminar = ft.ElevatedButton("ELIMINAR CLIENTE", width=300, height=60, style=estilo_eliminar, on_click=mostrar_eliminar)
        btn_avisos = ft.ElevatedButton("AVISOS DE WHATSAPP", width=300, height=60, style=estilo_wsp, on_click=mostrar_avisos)

        page.add(
            titulo, subtitulo, ft.Divider(height=10, color="transparent"),
            btn_registro, btn_lista, btn_renovar, btn_eliminar, btn_avisos
        )
        page.update()

    # Arrancamos con el menú
    mostrar_menu()

# Abrimos de forma nativa para el celular (sin WEB_BROWSER)
ft.app(target=main)