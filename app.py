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

# --- Modelos de la Base de Datos ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    tasks = db.relationship('Task', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(10), default='Baja')
    due_date = db.Column(db.Date, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Rutas de Autenticación ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user:
            flash('El nombre de usuario ya existe.', 'danger')
            return redirect(url_for('register'))
        
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registro exitoso. ¡Ahora puedes iniciar sesión!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Has iniciado sesión correctamente.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Credenciales inválidas. Inténtalo de nuevo.', 'danger')
    return render_template('login.html')

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

    tasks_query = current_user.tasks

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
    if request.is_json:
        data = request.get_json()
        task_content = data.get('task')
        task_priority = data.get('priority', 'Baja')
        due_date_str = data.get('due_date')
    else:
        task_content = request.form.get('task')
        task_priority = request.form.get('priority', 'Baja')
        due_date_str = request.form.get('due_date')

    if not task_content:
        return jsonify({'success': False, 'error': 'El contenido de la tarea no puede estar vacío.'}), 400

    from datetime import datetime
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Fecha de vencimiento inválida.'}), 400

    new_task = Task(content=task_content, priority=task_priority, due_date=due_date, owner=current_user)
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