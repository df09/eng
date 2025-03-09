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
        g.user_obj = User(session['user'], topics.topiclist) # передавать сюда
    return g.user_obj

# === main menu ===================================
@index_bp.route('/img/favicon.ico')
def favicon():
    return send_from_directory('static', 'img/favicon.ico', mimetype='image/vnd.microsoft.icon')
@index_bp.route('/')
@login_required
def index():
    topics.validate_questions() # validata db_questions
    topics.validate_progress() # validate db_progress
    topics.upd_topicdata() # validate db_stats
    user = get_current_user()
    stats = user.df_stats.to_dict(orient='records')
    return render_template('index.html', page='index', topiclist=topics.topiclist,
                           topicdata=topics.topicdata, stats=stats)

# === topic theory (RAW) ===================================
@index_bp.route('/topic/<int:tid>/theory', methods=['GET'])
@login_required
def topic_theory(tid):
    if tid not in topics.topiclist:
        return "Invalid topic ID", 400
    topic = Topic(tid, topics.topiclist[tid])
    theory_content = topic.theory.strip() if topic.theory else "No theory available."
    return theory_content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

# === topic ===================================
@index_bp.route('/topic/<int:tid>', methods=['GET'])
@login_required
def topic(tid):
    if tid not in topics.topiclist:
        return f'Invalid topic - id:{tid}', 400
    user = get_current_user()
    # Если tid == 0, выбираем реальный топик
    ist0 = 1 if tid == 0 else 0
    chosed_tid = topics.choose_tid(user.df_stats) if tid == 0 else tid
    if chosed_tid not in topics.topiclist:
        return f'Invalid topic - id:{chosed_tid}', 400
    topic = Topic(chosed_tid, topics.topiclist[chosed_tid])
    question = topic.choose_question(user.df_progress)
    # Проверяем, существует ли вопрос
    if not topic.get_question(chosed_tid, question['qkind'], question['qid']):
        return f'Invalid question {chosed_tid}/{question["qkind"]}: {question["qid"]}', 400
    routes = {'choice': 'index.q_choice', 'input': 'index.q_input', 'fill': 'index.q_fill'}
    return redirect(url_for(routes.get(question['qkind'], 'index.unknown_question'),
                            tid=chosed_tid, qid=question['qid'], ist0=ist0))

# === q_helpers ===================================
def init_q_rout(tid, qkind, qid):
    user = get_current_user()
    topic = Topic(tid, topics.topiclist[tid])
    tdata = topics.get_topicdata4topic(tid)
    stat = user.get_stat4topic(tid)
    progress = user.get_progress4question(tid, qkind, qid)
    question = topic.get_question(tid, qkind, qid)
    return user, topic, tdata, stat, progress, question

# === q_choice ===================================
@index_bp.route('/topic/<int:tid>/q_choice/<int:qid>', methods=['GET', 'POST'])
@login_required
def q_choice(tid, qid):
    ist0 = request.args.get('ist0')
    qkind = 'choice'
    user, topic, tdata, stat, progress, question = init_q_rout(tid, qkind, qid)
    if request.method == 'POST':
        answer = sorted(x.strip() for x in request.form.getlist('answer'))
        is_correct = answer == question['correct']
        user.upd_df_progress(tid, qkind, qid, is_correct)
        user.upd_df_stats()
        _, _, tdata, stat, progress, question = init_q_rout(tid, qkind, qid)
        return jsonify({
            'tdata': tdata,
            'stat': stat,
            'progress': progress,
            'question': question,
            'answer': answer,
            'is_correct': is_correct,
        })
    return render_template('q_choice.html', page='q_choice', tdata=tdata,
                           question=question, progress=progress, stat=stat, ist0=ist0)

# === q_input ===================================
@index_bp.route('/topic/<int:tid>/q_input/<int:qid>', methods=['GET', 'POST'])
@login_required
def q_input(tid, qid):
    ist0 = request.args.get('ist0')
    qkind = 'input'
    user, topic, tdata, stat, progress, question = init_q_rout(tid, qkind, qid)
    if request.method == 'POST':
        answer = request.form.get('answer')
        is_correct = answer.strip().lower() == question['correct'].strip().lower()
        user.upd_df_progress(tid, qkind, qid, is_correct)
        user.upd_df_stats()
        _, _, tdata, stat, progress, question = init_q_rout(tid, qkind, qid)
        return jsonify({
            'tdata': tdata,
            'stat': stat,
            'progress': progress,
            'question': question,
            'answer': answer,
            'is_correct': is_correct,
        })
    return render_template('q_input.html', page='q_input', tdata=tdata,
                           question=question, progress=progress, stat=stat, ist0=ist0)

# === q_fill ===================================
@index_bp.route('/topic/<int:tid>/q_fill/<int:qid>', methods=['GET', 'POST'])
@login_required
def q_fill(tid, qid):
    ist0 = request.args.get('ist0')
    qkind = 'fill'
    user, topic, tdata, stat, progress, question = init_q_rout(tid, qkind, qid)
    if request.method == 'POST':
        answer = request.form.get('answer')
        user_answers = [ans.strip().lower() for ans in json.loads(answer)]
        correct_answers = [item[1].strip().lower() for item in question["correct"]]
        is_correct = user_answers == correct_answers
        user.upd_df_progress(tid, qkind, qid, is_correct)
        user.upd_df_stats()
        _, _, tdata, stat, progress, question = init_q_rout(tid, qkind, qid)
        return jsonify({
            'tdata': tdata,
            'stat': stat,
            'progress': progress,
            'question': question,
            'answer': answer,
            'is_correct': is_correct,
        })
    return render_template('q_fill.html', page='q_fill', tdata=tdata,
                           question=question, progress=progress, stat=stat, ist0=ist0)

# === suspicious ===================================
@index_bp.route('/suspicious', methods=['POST'])
@login_required
def mark_suspicious():
    data = request.json
    return jsonify({'success': topics.mark_suspicious(data)})

