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
@index_bp.route('/choose_topic', methods=['GET'])
def choose_topic():
    tid = request.args.get('tid')
    if not tid or not tid.isdigit():
        return 'Invalid tid', 400  # Проверка на число
    tid = int(tid)
    return redirect(url_for('index.topic', tid=tid))

# === topic ===================================
@index_bp.route('/topic/<int:tid>')
@login_required
def topic(tid):
    if tid not in topics.data:
        return f'Invalid topic - id:{tid}', 400
    user = User(session['user'], topics.data)
    topic = Topic(tid, topics.data[tid])
    question = topic.choose_question(user.df_progress)
    q_kind = question["question_kind"]
    qid = question["question_id"]
    if q_kind == 'select': return redirect(url_for('index.q_select', tid=tid, qid=qid))
    if q_kind == 'single': return redirect(url_for('index.q_single', tid=tid, qid=qid))
    if q_kind == 'multi':  return redirect(url_for('index.q_multi',  tid=tid, qid=qid))
    return 'Unknown question type', 400
# === questions ===================================
@index_bp.route('/topic/<int:tid>/q_select/<int:qid>', methods=['GET', 'POST'])
@login_required
def q_select(tid, qid):
    # TODO: if estimate F   - ???
    # TODO: if estimate D,C - ???
    # TODO: if estimate B,A - ???
    user = User(session['user'], topics.data)
    topic = Topic(tid, topics.data[tid])
    q = topic.get_question(tid, 'select', qid)

    # if request.method == 'POST':
    #     answer = request.form.get('answer', '').strip()
    #     result = topic.check_answer(answer, q)
    #     session['q_index'] += 1
    #     return render_template('q_select.html', q=q, result=result, answer=answer)
    return render_template('q_select.html', q=q)

@index_bp.route('/topic/<int:tid>/q_single/<int:qid>', methods=['GET', 'POST'])
@login_required
def q_single(tid, qid):
    # TODO: if estimate F   - ???
    # TODO: if estimate D,C - ???
    # TODO: if estimate B,A - ???
    user = User(session['user'], topics.data)
    topic = Topic(tid, topics.data[tid])
    q = topic.get_question(tid, 'single', qid)
    # if request.method == 'POST':
    #     answer = request.form.get('answer', '').strip()
    #     result = topic.check_answer(answer, q)
    #     session['q_index'] += 1
    #     return render_template('q_single.html', q=q, result=result, answer=answer)
    return render_template('q_single.html', q=q)

@index_bp.route('/topic/<int:tid>/q_multi/<int:qid>', methods=['GET', 'POST'])
@login_required
def q_multi(tid, qid, q):
    # TODO: if estimate F   - ???
    # TODO: if estimate D,C - ???
    # TODO: if estimate B,A - ???
    user = User(session['user'], topics.data)
    topic = Topic(tid, topics.data[tid])
    q = topic.get_question(tid, 'multi', qid)
    # if request.method == 'POST':
    #     answer = request.form.get('answer', '').strip()
    #     result = topic.check_answer(answer, q)
    #     session['q_index'] += 1
    #     return render_template('q_multi.html', q=q, result=result, answer=answer)
    return render_template('q_multi.html', q=q)
