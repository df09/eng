from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from src.user import User
from src.topics import Topics
from src.topic import Topic
from logger import logger
import re

index_bp = Blueprint('index', __name__)
topics = Topics()

# === main menu ===================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
@index_bp.route('/')
@login_required
def index():
    user = User(session['user'], topics.data)
    stats = user.df_stats.to_dict(orient="records")
    return render_template('index.html', topics=topics.data, stats=stats)
@index_bp.route('/choose_topic', methods=['GET', 'POST'])
def choose_topic():
    tid = request.args.get('tid')
    if not tid or not tid.isdigit():
        return 'Invalid tid', 400  # Проверка на число
    tid = int(tid)
    if tid in topics.data:
        # Очистка старых вопросов, если пользователь переключает тему
        session.pop('qs', None)
        session.pop('q_index', None)
        # Перенаправление на страницу темы
        return redirect(url_for('index.topic', tid=tid))
    return 'tid not supported', 400

# === topic ===================================
@index_bp.route('/topic/<int:tid>')
def topic(tid):
    if tid not in topics.data:
        return 'Invalid topic', 400
    user = User(session['user'], topics.data)  # Загружаем пользователя
    topic = Topic(tid, topics.data[tid])  # Загружаем тему
    # Если вопросов ещё нет, создаём новую пачку
    if 'qs' not in session or 'q_index' not in session:
        session['q_index'] = 0
        session['qs'] = topic.get_batch(user.df_progress_pronouns, 30).to_dict(orient='records')
    qs = session['qs']
    index = session['q_index']
    # Если вопросы закончились, сбрасываем сессию и возвращаем в главное меню
    if index >= len(qs):
        session.pop('q_index')
        session.pop('qs')
        return redirect(url_for('index.index'))
    # Получаем текущий вопрос
    q = qs[index]
    # Определяем тип вопроса
    q_type = q.get('q_type', 'q_select')  # По умолчанию q_select
    # Перенаправляем на соответствующий шаблон
    if q_type == 'q_select': return redirect(url_for('index.q_select', tid=tid, qid=index))
    if q_type == 'q_single': return redirect(url_for('index.q_single', tid=tid, qid=index))
    if q_type == 'q_multi':  return redirect(url_for('index.q_multi',  tid=tid, qid=index))
    return 'Unknown question type', 400
