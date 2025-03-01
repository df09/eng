from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g, jsonify
from functools import wraps
from src.user import User
from src.topics import Topics
from src.topic import Topic
from src.helpers import pdo
from logger import logger
from random import shuffle
import re

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

# === q_choose ===================================
@index_bp.route('/topic/<int:tid>/q_choose/<int:qid>', methods=['GET', 'POST'])
@login_required
def q_choose(tid, qid):
    user = get_current_user()
    topic = Topic(tid, topics.data[tid])
    q = topic.get_question(tid, 'choose', qid)
    options = [opt.strip() for opt in q['options'].split(';')]
    shuffle(options)
    # progress
    progress = user.get_progress(tid, 'choose', qid)
    # post
    if request.method == 'POST':
        selected_answers = {opt.strip() for opt in request.form.getlist('answer')}
        correct_answers = {opt.strip() for opt in q['correct'].split(';')}
        result = selected_answers == correct_answers
        # progress
        user.save_progress(tid, 'choose', qid, result)
        progress = user.get_progress(tid, 'choose', qid)

        return jsonify({
            'success': True,
            'question': q['question'],
            'selected': list(selected_answers),
            'correct': list(correct_answers),
            'is_correct': result,
            'progress': {
                'estimation': progress['estimation'],
                'points': progress['points'],
                'threshhold': user.estimate_ranges[progress['estimation']][1]
            }
        })
    return render_template('q_choose.html', page='q_choose', tid=tid, tname=topic.name,
                           q=q, shuffled_options=options, progress={
                               'estimation': progress['estimation'],
                               'points': progress['points'],
                               'threshhold': user.estimate_ranges[progress['estimation']][1]
                           })

# === q_input ===================================
@index_bp.route('/topic/<int:tid>/q_input/<int:qid>', methods=['GET', 'POST'])
@login_required
def q_input(tid, qid):
    user = get_current_user()
    topic = Topic(tid, topics.data[tid])
    q = topic.get_question(tid, 'input', qid)
    q['question'], q['correct'] = topic.format_q_input(q['question'])
    # progress
    progress = user.get_progress(tid, 'input', qid)
    # post
    if request.method == 'POST':
        answer = request.form.get('answer', '').strip()
        correct_answer = q['correct'].strip()
        result = answer.lower() == correct_answer.lower()
        # progress
        user.save_progress(tid, 'input', qid, result)
        progress = user.get_progress(tid, 'input', qid)
        return jsonify({
            'success': True,
            'question': q['question'],
            'selected': answer,
            'correct': correct_answer,
            'is_correct': result,
            'next_question_url': url_for('index.topic', tid=tid) if result else '',
            'progress': {
                'estimation': progress['estimation'],
                'points': progress['points'],
                'threshhold': user.estimate_ranges[progress['estimation']][1]
            }
        })
    return render_template('q_input.html', page='q_input', tid=tid, tname=topic.name, q=q, progress={
        'estimation': progress['estimation'],
        'points': progress['points'],
        'threshhold': user.estimate_ranges[progress['estimation']][1]
    })

# === q_fill ===================================
@index_bp.route('/topic/<int:tid>/q_fill/<int:qid>', methods=['GET', 'POST'])
@login_required
def q_fill(tid, qid):
    user = get_current_user()
    topic = Topic(tid, topics.data[tid])
    q = topic.get_question(tid, 'fill', qid)
    # progress
    progress = user.get_progress(tid, 'fill', qid)
    if request.method == 'POST':
        answers = [ans.strip() for ans in request.form.getlist('answers')]
        correct_answers = [ans.strip() for ans in q['answers']]
        result = answers == correct_answers
        # progress
        user.save_progress(tid, 'fill', qid, result)
        progress = user.get_progress(tid, 'fill', qid)
        return jsonify({
            'success': True,
            'question': q['question'],
            'selected': answers,
            'correct': correct_answers,
            'is_correct': result,
            'next_question_url': url_for('index.topic', tid=tid) if result else '',
            'progress': {
                'estimation': progress['estimation'],
                'points': progress['points'],
                'threshhold': user.estimate_ranges[progress['estimation']][1]
            }
        })
    return render_template('q_fill.html', page='q_fill', tid=tid, tname=topic.name, q=q, progress={
        'estimation': progress['estimation'],
        'points': progress['points'],
        'threshhold': user.estimate_ranges[progress['estimation']][1]
    })
