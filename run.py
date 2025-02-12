from flask import Flask, render_template, request, redirect, url_for, session
from src.user import User
from src.pronouns import Pronouns
from pprint import pprint as pp
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Для хранения данных в сессии

@app.route('/')
def index():
    user = User('df09')  # Заменить на получение текущего пользователя
    stats = user.render_stats_pronouns()
    return render_template('index.html', stats=stats)

@app.route('/choose_mode', methods=['POST'])
def choose_mode():
    mode = request.form.get('mode')
    if mode == '1':
        return redirect(url_for('pronouns_mode'))
    return "Mode not supported", 400

@app.route('/mode/pronouns', methods=['GET', 'POST'])
def pronouns_mode():
    user = User('df09')
    pronouns = Pronouns()

    if 'q_index' not in session:
        session['q_index'] = 0
        session['qs'] = pronouns.get_batch(user.df_progress_pronouns, 30).to_dict(orient='records')

    qs = session['qs']
    pp(qs)
    index = session['q_index']

    if index >= len(qs):
        session.pop('q_index')
        session.pop('qs')
        return redirect(url_for('index'))

    q = qs[index]
    
    def insert_input_field(text, word):
        return re.sub(rf'\b{re.escape(word)}\b', '<input type="text" name="answer" required>', text, flags=re.IGNORECASE)
    
    q_text = insert_input_field(q['example_eng'], q['pronoun_clean'])
    
    if request.method == 'POST':
        answer = request.form.get('answer', '').strip()
        result, _, _ = pronouns.check_answer(answer, q['pronoun_clean'])
        session['q_index'] += 1
        return render_template('pronouns.html', q_text=q_text, q=q, result=result, answer=answer)
    
    return render_template('pronouns.html', q_text=q_text, q=q)

if __name__ == '__main__':
    app.run(debug=True)
