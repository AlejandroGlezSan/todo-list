
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Inicializa la aplicación y la configura
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mi_llave_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- Ruta para confirmar email ---
@app.route('/confirm/<token>')
def confirm_email(token):
    user = User.query.filter_by(email_token=token).first()
    if not user:
        flash('Enlace de confirmación inválido o expirado.', 'danger')
        return redirect(url_for('login'))
    if user.email_confirmed:
        flash('El email ya estaba confirmado. Puedes iniciar sesión.', 'info')
        return redirect(url_for('login'))
    if user.confirm_email(token):
        db.session.commit()
        flash('¡Email confirmado correctamente! Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    else:
        flash('Enlace de confirmación inválido.', 'danger')
        return redirect(url_for('login'))

# --- Manejador para peticiones AJAX no autenticadas ---
@login_manager.unauthorized_handler
def unauthorized_callback():
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'error': 'No autenticado', 'login_required': True}), 401
    return redirect(url_for('login'))

# --- Modelos de la Base de Datos ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email_confirmed = db.Column(db.Boolean, default=False)
    email_token = db.Column(db.String(120), nullable=True)
    tasks = db.relationship('Task', backref='owner', lazy='dynamic')

    def generate_email_token(self):
        import secrets
        self.email_token = secrets.token_urlsafe(32)
        return self.email_token

    def confirm_email(self, token):
        if self.email_token and self.email_token == token:
            self.email_confirmed = True
            self.email_token = None
            return True
        return False

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(10), default='Baja')
    due_date = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Rutas de Autenticación ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    from markupsafe import escape
    if request.method == 'POST':
        email = escape(request.form.get('email', '').strip())
        password = request.form.get('password', '').strip()
        # Validación básica de email
        if not email or '@' not in email or '.' not in email.split('@')[-1]:
            flash('Email inválido. Debe contener "@" y un dominio.', 'danger')
            return redirect(url_for('register'))
        if not password:
            flash('Contraseña requerida.', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('El email ya está registrado.', 'danger')
            return redirect(url_for('register'))
        # Solo crear usuario si todo es válido
        new_user = User(email=email)
        new_user.set_password(password)
        token = new_user.generate_email_token()
        db.session.add(new_user)
        db.session.commit()
        # Simular envío de email: imprimir enlace de confirmación en consola
        confirm_url = url_for('confirm_email', token=token, _external=True)
        print(f"[SIMULADO] Enlace de confirmación para {email}: {confirm_url}")
        flash('Registro exitoso. Revisa tu email para confirmar tu cuenta.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('username') or request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if not user.email_confirmed:
                flash('Debes confirmar tu email antes de iniciar sesión. Revisa tu correo. ', 'danger')
                return render_template('login.html', resend_email=email)
            login_user(user)
            flash('Has iniciado sesión correctamente.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Credenciales inválidas. Inténtalo de nuevo.', 'danger')
    return render_template('login.html')

# --- Ruta para reenviar email de confirmación ---
@app.route('/resend-confirmation', methods=['POST'])
def resend_confirmation():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    if user and not user.email_confirmed:
        token = user.generate_email_token()
        db.session.commit()
        confirm_url = url_for('confirm_email', token=token, _external=True)
        print(f"[SIMULADO] Reenvío de confirmación para {email}: {confirm_url}")
        flash('Se ha reenviado el email de confirmación. Revisa tu correo.', 'success')
    else:
        flash('No se pudo reenviar el email. ¿Ya está confirmado o el email no existe?', 'danger')
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Rutas de la Aplicación de Tareas (Protegidas) ---
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/get-tasks')
@login_required
def get_tasks():
    search_query = request.args.get('search')
    filter_by = request.args.get('filter')
    priority_filter = request.args.get('priority')

    tasks_query = current_user.tasks if hasattr(current_user, 'tasks') else []

    if filter_by and filter_by != 'all':
        tasks_query = tasks_query.filter_by(done=(filter_by == 'completed'))
    
    # Maneja el filtro de prioridad, ignorando el valor 'all'
    if priority_filter and priority_filter != 'all':
        tasks_query = tasks_query.filter_by(priority=priority_filter)
    
    if search_query:
        tasks_query = tasks_query.filter(Task.content.like(f'%{search_query}%'))
    
    tasks = tasks_query.all()
    
    tasks_list = [{
        'id': task.id,
        'content': task.content,
        'done': task.done,
        'priority': task.priority,
        'due_date': task.due_date.isoformat() if task.due_date else None
    } for task in tasks]
    return jsonify(tasks_list)

@app.route('/add', methods=['POST'])
@login_required
def add_task():
    from markupsafe import escape
    if request.is_json:
        data = request.get_json()
        task_content = escape(data.get('task', '').strip())
        task_priority = escape(data.get('priority', 'Baja').strip())
        due_date_str = data.get('due_date')
    else:
        task_content = escape(request.form.get('task', '').strip())
        task_priority = escape(request.form.get('priority', 'Baja').strip())
        due_date_str = request.form.get('due_date')

    if not task_content:
        return jsonify({'success': False, 'error': 'El contenido de la tarea no puede estar vacío.'}), 400

    from datetime import datetime
    due_date = None
    if due_date_str:
        try:
            # Soporta tanto fecha como fecha+hora en formato ISO
            due_date = datetime.fromisoformat(due_date_str)
        except ValueError:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({'success': False, 'error': 'Fecha de vencimiento inválida.'}), 400

    new_task = Task(content=task_content, priority=task_priority, due_date=due_date, user_id=current_user.id)
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'success': True, 'id': new_task.id, 'content': new_task.content, 'done': new_task.done, 'priority': new_task.priority, 'due_date': new_task.due_date.isoformat() if new_task.due_date else None})

@app.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task_to_delete = Task.query.get_or_404(task_id)
    if task_to_delete.owner != current_user:
        return jsonify({'success': False, 'error': 'No tienes permiso para eliminar esta tarea.'}), 403
    db.session.delete(task_to_delete)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/complete/<int:task_id>')
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.owner != current_user:
        return jsonify({'error': 'No tienes permiso para modificar esta tarea.'}), 403
    task.done = not task.done
    db.session.commit()
    return jsonify({'done': task.done})

@app.route('/edit/<int:task_id>', methods=['POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.owner != current_user:
        return jsonify({'error': 'No tienes permiso para editar esta tarea.'}), 403
    
    new_content = request.json.get('content')
    if new_content:
        task.content = new_content
        db.session.commit()
        return jsonify({'success': True, 'content': task.content})
    
    return jsonify({'success': False, 'error': 'Contenido no válido'}), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)