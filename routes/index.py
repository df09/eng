from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from src.user import User
from src.topics import Topics
from src.topic import Topic
from logger import logger
from random import shuffle
from flask import jsonify
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
    # init/validate topics
    for tid, tname in topics.data.items():
        topic = Topic(tid, tname)
    # proceed
    user = User(session['user'], topics.data)
    stats = user.df_stats.to_dict(orient="records")
    return render_template('index.html', page='index', topics=topics.data, stats=stats)
# === topic ===================================
@index_bp.route('/topic/<int:tid>', methods=['GET'])
@login_required
def topic(tid):  # tid уже передаётся из URL
    if tid not in topics.data:
        return f'Invalid topic - id:{tid}', 400
    user = User(session['user'], topics.data)
    topic = Topic(tid, topics.data[tid])
    question = topic.choose_question(user.df_progress)
    q_kind = question["question_kind"]
    qid = question["question_id"]
    routes = {
        'choose': 'index.q_choose',
        'input': 'index.q_input',
        'fill': 'index.q_fill'
    }
    return redirect(url_for(routes.get(q_kind, 'index.unknown_question'), tid=tid, qid=qid))

# === q_choose ===================================
@index_bp.route('/topic/<int:tid>/q_choose/<int:qid>', methods=['GET', 'POST'])
@login_required
def q_choose(tid, qid):
    user = User(session['user'], topics.data)
    topic = Topic(tid, topics.data[tid])
    q = topic.get_question(tid, 'choose', qid)
    options = [opt.strip() for opt in q["options"].split(";")]
    shuffle(options)
    if request.method == 'POST':
        selected_answers = {opt.strip() for opt in request.form.getlist('answer')}
        correct_answers = {opt.strip() for opt in q["correct"].split(";")}
        result = selected_answers == correct_answers  # Порядок теперь не имеет значения
        user.save_progress(tid, 'choose', qid, result)
        response_data = {
            "success": True,
            "question": q["question"],
            "selected": list(selected_answers),
            "correct": list(correct_answers),
            "is_correct": result,
            "next_question_url": url_for('index.topic', tid=tid) if result else ""
        }
        return jsonify(response_data)
    return render_template('q_choose.html', page='q_choose', tid=tid, tname=topic.name, q=q, shuffled_options=options)

# === q_input ===================================
@index_bp.route('/topic/<int:tid>/q_input/<int:qid>', methods=['GET', 'POST'])
@login_required
def q_input(tid, qid):
    user = User(session['user'], topics.data)
    topic = Topic(tid, topics.data[tid])
    q = topic.get_question(tid, 'input', qid)
    q['question'], q['correct'] = topic.format_q_input(q['question'])
    if request.method == 'POST':
        answer = request.form.get('answer', '').strip()
        correct_answer = q["correct"].strip()
        result = answer.lower() == correct_answer.lower()
        user.save_progress(tid, 'input', qid, result)
        response_data = {
            "success": True,
            "question": q["question"],
            "selected": answer,
            "correct": correct_answer,
            "is_correct": result,
            "next_question_url": url_for('index.topic', tid=tid) if result else ""
        }
        return jsonify(response_data)
    return render_template('q_input.html', page='q_input', tid=tid, tname=topic.name, q=q)

# === q_fill ===================================
@index_bp.route('/topic/<int:tid>/q_fill/<int:qid>', methods=['GET', 'POST'])
@login_required
def q_fill(tid, qid, q):
    user = User(session['user'], topics.data)
    topic = Topic(tid, topics.data[tid])
    q = topic.get_question(tid, 'fill', qid)
    # if request.method == 'POST':
    #     answer = request.form.get('answer', '').strip()
    #     result = topic.check_answer(answer, q)
    #     session['q_index'] += 1
    #     return render_template('q_fill.html', page='q_fill',tid=tid,tname=topic.name, q=q, result=result, answer=answer)
    return render_template('q_fill.html', page='q_fill',tid=tid,tname=topic.name, q=q)
