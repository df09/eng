from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from src.user import User
from src.topics import Topics
from src.topic import Topic
from logger import logger
import re

index_bp = Blueprint('index', __name__)

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
    topics = Topics()
    user = User(session['user'], topics.data)
    stats = user.df_stats.to_dict(orient="records")
    return render_template('index.html', topics=topics.data, stats=stats)

@index_bp.route('/choose_mode', methods=['POST'])
def choose_mode():
    mode = request.form.get('mode')
    if mode == '1':
        return redirect(url_for('index.mode_pronouns'))
    return 'Mode not supported', 400

# === mode_pronouns ===================================
@index_bp.route('/mode/topic', methods=['GET', 'POST'])
def mode_pronouns():
    user = User(session['user'])
    topic = Topic()
    # get new batch
    if 'q_index' not in session:
        session['q_index'] = 0
        session['qs'] = topic.get_batch(user.df_progress_pronouns, 30).to_dict(orient='records')
        logger.info(session['qs'])
    qs = session['qs']
    index = session['q_index']
    if index >= len(qs):
        session.pop('q_index')
        session.pop('qs')
        return redirect(url_for('index.index'))
    q = qs[index]
    def insert_input_field(text, word):
        return re.sub(rf'\b{re.escape(word)}\b', '<input type="text" name="answer" required>', text, flags=re.IGNORECASE)
    q_text = insert_input_field(q['example_eng'], q['pronoun_clean'])
    if request.method == 'POST':
        answer = request.form.get('answer', '').strip()
        result, _, _ = topic.check_answer(answer, q['pronoun_clean'])
        session['q_index'] += 1
        return render_template('topic.html', q_text=q_text, q=q, result=result, answer=answer)
    return render_template('topic.html', q_text=q_text, q=q)
