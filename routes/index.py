from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from src.user import User
import src.helpers.fo as fo
from pprint import pprint as pp


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
    user = User(session['user'])
    stats = user.render_stats_pronouns()
    return render_template('index.html', stats=stats)

# @index_bp.route('/choose_mode', methods=['POST'])
# def choose_mode():
#        mode = request.form.get('mode')
#        if mode == '1':
#         return redirect(url_for('pronouns_mode'))
#        return "Mode not supported", 400

# === mode/pronouns ===================================
# @index_bp.route('/mode/pronouns', methods=['GET', 'POST'])
# def pronouns_mode():
#        user = User('df09')
#        pronouns = Pronouns()
#        if 'q_index' not in session:
#         session['q_index'] = 0
#         session['qs'] = pronouns.get_batch(user.df_progress_pronouns, 30).to_dict(orient='records')
#        qs = session['qs']
#        pp(qs)
#        index = session['q_index']
#        if index >= len(qs):
#         session.pop('q_index')
#         session.pop('qs')
#         return redirect(url_for('index.index'))
#        q = qs[index]
#        def insert_input_field(text, word):
#         return re.sub(rf'\b{re.escape(word)}\b', '<input type="text" name="answer" required>', text, flags=re.IGNORECASE)
#        q_text = insert_input_field(q['example_eng'], q['pronoun_clean'])
#        if request.method == 'POST':
#         answer = request.form.get('answer', '').strip()
#         result, _, _ = pronouns.check_answer(answer, q['pronoun_clean'])
#         session['q_index'] += 1
#         return render_template('pronouns.html', q_text=q_text, q=q, result=result, answer=answer)
#        return render_template('pronouns.html', q_text=q_text, q=q)

