import flet as ft
from datetime import datetime, timedelta
import os
import json 
import gspread
from dotenv import load_dotenv

# --- CONEXIÓN A GOOGLE SHEETS EN LA NUBE (Vía Variables de Entorno) ---
load_dotenv() 

try:
    credenciales_texto = os.environ.get('CREDENCIALES_GOOGLE')
    if not credenciales_texto:
        raise ValueError("No se encontró la variable de entorno CREDENCIALES_GOOGLE")
    credenciales_dict = json.loads(credenciales_texto)
    gc = gspread.service_account_from_dict(credenciales_dict)
    libro = gc.open('Clientes Kratos') 
    hoja_datos = libro.sheet1 
except Exception as e:
    print(f"Error de conexión con Google Sheets: {e}")
    hoja_datos = None

def main(page: ft.Page):

    # --- NUEVO LOOK KRATOS (NEGRO Y ROJO) ---
    page.title = "Gym Kratos"
    page.bgcolor = ft.Colors.BLACK # Fondo negro puro
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER 
    
    # Le decimos a la app que su color de énfasis sea el rojo
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.RED)
    # ----------------------------------------

    # ---------------------------------------------------
    # PANTALLA 4: RENOVAR MEMBRESÍA
    # ---------------------------------------------------
    def mostrar_renovar(e=None):
        page.controls.clear()
        
        titulo = ft.Text("🔄 RENOVAR MEMBRESÍA", size=24, weight=ft.FontWeight.BOLD)
        texto_mensaje = ft.Text(value="", size=16)
        
        dropdown_clientes = ft.Dropdown(label="Selecciona un cliente", width=300)
        
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

        btn_guardar_renovacion = ft.ElevatedButton("Renovar 30 días", width=300, height=50, on_click=renovar_cliente)
        btn_volver = ft.OutlinedButton("⬅️ Volver al Menú", width=300, height=50, on_click=mostrar_menu)

        page.add(
            titulo, dropdown_clientes, btn_guardar_renovacion, texto_mensaje, 
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
    # PANTALLA 2: REGISTRAR CLIENTE
    # ---------------------------------------------------
    def mostrar_registro(e=None):
        page.controls.clear() 
        
        titulo = ft.Text("📝 NUEVO INGRESO", size=24, weight=ft.FontWeight.BOLD)
        
        input_nombre = ft.TextField(label="Nombre del cliente")
        input_telefono = ft.TextField(label="Teléfono (ej: +56912345678)")
        dropdown_plan = ft.Dropdown(
            label="Tipo de inscripción",
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

        btn_guardar = ft.ElevatedButton("Guardar Cliente", width=300, height=50, on_click=guardar_cliente)
        btn_volver = ft.OutlinedButton("⬅️ Volver al Menú", width=300, height=50, on_click=mostrar_menu)

        page.add(
            titulo, input_nombre, input_telefono, dropdown_plan, 
            btn_guardar, texto_mensaje, 
            ft.Divider(height=20, color="transparent"), btn_volver
        )
        page.update()

# ---------------------------------------------------
    # PANTALLA 1: MENÚ PRINCIPAL
    # ---------------------------------------------------
    def mostrar_menu(e=None):
        page.controls.clear() 
        
        titulo = ft.Text("💪 GYM KRATOS 💪", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_600)
        subtitulo = ft.Text("Menú Principal", size=16, color="grey")

        # Botones con el estilo del gimnasio (Rojo y texto blanco)
        btn_registro = ft.ElevatedButton("Registrar Nuevo Cliente", width=300, height=60, bgcolor=ft.Colors.RED_900, color=ft.Colors.WHITE, on_click=mostrar_registro)
        btn_lista = ft.ElevatedButton("Ver Clientes", width=300, height=60, bgcolor=ft.Colors.RED_900, color=ft.Colors.WHITE, on_click=mostrar_lista)
        btn_renovar = ft.ElevatedButton("Renovar Membresía", width=300, height=60, bgcolor=ft.Colors.RED_900, color=ft.Colors.WHITE, on_click=mostrar_renovar)
        
        btn_eliminar = ft.ElevatedButton("Eliminar Cliente", width=300, height=60, color=ft.Colors.RED_400)
        btn_avisos = ft.ElevatedButton("Avisos de WhatsApp", width=300, height=60, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)

        page.add(
            titulo, subtitulo, ft.Divider(height=20, color="transparent"),
            btn_registro, btn_lista, btn_renovar, btn_eliminar, btn_avisos
        )
        page.update()

    # Arrancamos con el menú
    mostrar_menu()

# Abrimos en el navegador web
ft.app(target=main, view=ft.AppView.WEB_BROWSER)