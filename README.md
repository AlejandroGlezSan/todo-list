# ToDo List App

Aplicación web moderna de lista de tareas con autenticación, animaciones y UI avanzada.

## Características principales
- Registro e inicio de sesión por email
- Añadir, editar, completar y eliminar tareas
- Filtros por estado y prioridad con animación
- Fechas y horas de vencimiento para tareas
- Notificaciones flotantes (popups)
- Fondo animado poligonal (SVG + JS, estilo low-poly)
- Diseño glassmorphism y responsivo

## Requisitos
- Python 3.8+
- pip
- (Opcional) entorno virtual: venv

## Instalación
1. Clona el repositorio:
   ```sh
   git clone https://github.com/AlejandroGlezSan/todo-list.git
   cd todo-list
   ```
2. Instala dependencias:
   ```sh
   pip install -r requirements.txt
   ```
3. (Opcional) Crea y activa un entorno virtual:
   ```sh
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```
4. Inicializa la base de datos:
   ```sh
   python app.py
   # Se creará instance/tasks.db automáticamente al iniciar
   ```

## Ejecución
```sh
python app.py
```
Abre tu navegador en [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Estructura del proyecto
```
├── app.py                # Backend Flask principal
├── requirements.txt      # Dependencias Python
├── instance/
│   └── tasks.db          # Base de datos SQLite
├── static/
│   └── background-poly.js # Fondo animado SVG
├── templates/
│   ├── index.html        # Página principal (UI)
│   ├── login.html        # Login
│   └── register.html     # Registro
└── README.md             # Este archivo
```

## Personalización
- Cambia colores y animaciones en `static/background-poly.js` y en los bloques `<style>` de los HTML.
- Puedes modificar los filtros, prioridades y campos de tarea en `index.html` y `app.py`.

## Despliegue
- Para producción, usa un servidor WSGI como Gunicorn o despliega en servicios como Heroku, Railway, Vercel (con adaptador Python).

## Créditos
- UI y animaciones inspiradas en CodePen y Three.js.
- Desarrollado por AlejandroGlezSan y colaboradores.

---
¡Contribuciones y sugerencias bienvenidas!
