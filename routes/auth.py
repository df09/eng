from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from routes import bcrypt
import src.helpers.fo as fo
from src.helpers.cmd import cmd
from logger import logger


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        path = f'data/users/{username}'
        if not fo.f_exist(path):
            # prepare fs
            logger.info(cmd('pwd'))
            cmd(f'cp -r ./data/users/_default ./{path}')
            data = fo.yml2dict(f'{path}/_data.yml')
            data['name'] = username
            data['password'] = password
            fo.dict2yml(data, f'{path}/_data.yml')
            # proceed
            session['user'] = username
            flash('Account created!', 'success')
            return redirect(url_for('index.index'))
        flash('Username already exists!', 'danger')
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username != '_default':
            path = f'./data/users/{username}'
            if fo.d_exist(path):
                saved_password = fo.yml2dict(f'{path}/_data.yml')['password']
                if bcrypt.check_password_hash(saved_password, password):
                    session['user'] = username
                    flash('Login successful!', 'success')
                    return redirect(url_for('index.index'))
        flash('Login failed. Check username and password.', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out!', 'info')
    return redirect(url_for('auth.login'))
