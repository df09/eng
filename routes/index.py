from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g, jsonify
from functools import wraps
from src.user import User
from src.topics import Topics
from src.topic import Topic
from src.helpers import pdo
from logger import logger
import json

index_bp = Blueprint('index', __name__)
topics = Topics()

# === helpers ===================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_obj' not in g:
        g.user_obj = User(session['user'], topics.data)
    return g.user_obj

# === main menu ===================================
@index_bp.route('/img/favicon.ico')
def favicon():
    return send_from_directory('static', 'img/favicon.ico', mimetype='image/vnd.microsoft.icon')
@index_bp.route('/')
@login_required
def index():
    user = get_current_user()
    stats = user.df_stats.to_dict(orient='records')
    return render_template('index.html', page='index', topics=topics.data, stats=stats)

# === topic ===================================
@index_bp.route('/topic/<int:tid>', methods=['GET'])
@login_required
def topic(tid):
    if tid not in topics.data:
        return f'Invalid topic - id:{tid}', 400
    user = get_current_user()
    topic = Topic(tid, topics.data[tid])
    question = topic.choose_question(user.df_progress)
    q_kind = question['question_kind']
    qid = question['question_id']
    routes = {'choose': 'index.q_choose', 'input': 'index.q_input', 'fill': 'index.q_fill'}
    return redirect(url_for(routes.get(q_kind, 'index.unknown_question'), tid=tid, qid=qid))

# === q_helpers ===================================
def init_q_rout(tid, q_kind, qid):
    user = get_current_user()
    topic = Topic(tid, topics.data[tid])
    progress = user.get_progress(tid, q_kind, qid)
    question = topic.get_question(tid, q_kind, qid)
    return user, topic, question, progress

# === q_choose ===================================
@index_bp.route('/topic/<int:tid>/q_choose/<int:qid>', methods=['GET', 'POST'])
@login_required
def q_choose(tid, qid):
    q_kind = 'choose'
    user, topic, question, progress = init_q_rout(tid, q_kind, qid)
    if request.method == 'POST':
        answer = sorted(x.strip() for x in request.form.getlist('answer'))
        is_correct = answer == question['correct']
        user.save_progress(tid, q_kind, qid, is_correct)
        progress = user.get_progress(tid, q_kind, qid)
        return jsonify({
            'progress': progress,
            'question': question,
            'answer': answer,
            'is_correct': is_correct,
        })
    return render_template('q_choose.html', page='q_choose', tid=tid, tname=topic.name,
                           question=question, progress=progress)

# === q_input ===================================
@index_bp.route('/topic/<int:tid>/q_input/<int:qid>', methods=['GET', 'POST'])
@login_required
def q_input(tid, qid):
    q_kind = 'input'
    user, topic, question, progress = init_q_rout(tid, q_kind, qid)
    if request.method == 'POST':
        answer = request.form.get('answer')
        is_correct = answer.strip().lower() == question['correct'].strip().lower()
        user.save_progress(tid, q_kind, qid, is_correct)
        progress = user.get_progress(tid, q_kind, qid)
        return jsonify({
            'progress': progress,
            'question': question,
            'answer': answer,
            'is_correct': is_correct,
        })
    return render_template('q_input.html', page='q_input', tid=tid, tname=topic.name,
                           question=question, progress=progress)

# === q_fill ===================================
@index_bp.route('/topic/<int:tid>/q_fill/<int:qid>', methods=['GET', 'POST'])
@login_required
def q_fill(tid, qid):
    q_kind = 'fill'
    user, topic, question, progress = init_q_rout(tid, q_kind, qid)
    if request.method == 'POST':
        answer = request.form.get('answer')
        user_answers = [ans.strip().lower() for ans in json.loads(answer)]
        correct_answers = [item[1].strip().lower() for item in question["correct"]]
        is_correct = user_answers == correct_answers
        user.save_progress(tid, q_kind, qid, is_correct)
        progress = user.get_progress(tid, q_kind, qid)
        return jsonify({
            'progress': progress,
            'question': question,
            'answer': answer,
            'is_correct': is_correct,
        })
    return render_template('q_fill.html', page='q_fill', tid=tid, tname=topic.name,
                           question=question, progress=progress)
