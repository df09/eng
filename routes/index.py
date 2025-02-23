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
    user = User(session['user'], topics.data)
    stats = user.df_stats.to_dict(orient="records")
    return render_template('index.html', page='index', topics=topics.data, stats=stats)
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
    if q_kind == 'choose': return redirect(url_for('index.q_choose', tid=tid, qid=qid))
    if q_kind == 'input': return redirect(url_for('index.q_input', tid=tid, qid=qid))
    if q_kind == 'fill':  return redirect(url_for('index.q_fill', tid=tid, qid=qid))
    return 'Unknown question type', 400

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
        selected_answers = set(request.form.getlist('answer'))
        correct_answers = set(q["correct"].split(";"))
        result = selected_answers == correct_answers
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
