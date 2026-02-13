"""
Blueprint de Autenticação (Login/Logout)
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager
from app.models.user import User

bp = Blueprint('auth', __name__, url_prefix='/auth')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('inqueritos.index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('inqueritos.index'))
        
        flash("Usuário ou senha inválidos.", "danger")
    
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    logout_user()
    flash("Sessão encerrada.", "info")
    return redirect(url_for('auth.login'))
