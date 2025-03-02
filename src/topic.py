import os
import re
from logger import logger
import src.helpers.fo as fo
import pandas as pd
import src.helpers.pdo as pdo
from pprint import pprint
from random import shuffle


class Topic:
    def __init__(self, tid, name):
        self.id = tid
        self.name = name
        self.estimation_order = {'F':1,'D':2,'C':3,'B':4,'A': 5}
        self.path = f'data/topics/{self.id}_{self.name}'
        self.f_q_chooses = f'{self.path}/questions/chooses.csv'
        self.f_q_inputs = f'{self.path}/questions/inputs.csv'
        self.d_q_fills = f'{self.path}/questions/fills'
        self.f_total = f'{self.path}/questions/_total.txt'
        self.qs = {
            'choose': self.load_choose_questions(),
            'input': self.load_input_questions(),
            'fill': self.load_fill_questions()
        }
        self.upd_total()
        # TODO: просто дать ссылку на readme?
        self.theory = fo.txt2str(f'{self.path}/theory.txt')

    # === load.choose ===================================
    def load_choose_questions(self):
        return pdo.load(self.f_q_chooses, allow_empty=True).to_dict(orient='records')

    # === load.input ===================================
    def load_input_questions(self):
        questions = pdo.load(self.f_q_inputs, allow_empty=True).to_dict(orient='records')
        for question in questions:
            question['question'], question['correct'], question['hints'] = self.format_q_input(question['question'])
        return questions
    def format_q_input(self, question):
        '''
        Ищет [<answer>:<hints>] или [<answer>] в вопросе, заменяет его на '___',
        и возвращает (отформатированный вопрос, правильный ответ, подсказки).
        '''
        match = re.search(r'\[([^:\]]+)(?::([^]]+))?\]', question)
        if not match:
            raise ValueError('The question does not contain the correct answer in the [answer] or [answer:hints] format.')
        correct = match.group(1)
        hints = match.group(2) if match.group(2) else None
        formatted_question = question.replace(match.group(0), '___')
        return formatted_question, correct, hints

    # === load.fill ===================================
    def load_fill_questions(self):
        '''Загружает fill-вопросы из файлов и парсит их с учетом пропусков.'''
        questions = []
        for filename in os.listdir(self.d_q_fills):
            qid, qname = filename.split('_')
            filepath = os.path.join(self.d_q_fills, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                question = f.read().strip()
                formatted_question, correct = self.format_q_fill(question)
                questions.append({
                    'id': qid,
                    'name': qname,
                    'question': formatted_question,
                    'correct': correct
                })
        return questions
    def format_q_fill(self, question):
        '''
        Заменяет все [число.ответ] на placeholder в виде <span class='blank' data-num='число'>____</span>,
        где количество символов соответствует длине исходной строки [число.ответ].
        Собирает правильные ответы в порядке возрастания номеров.
        '''
        def replace_match(match):
            num, answer = match.groups()
            placeholder = '_' * len(f'[{num}.{answer}]')
            return f'<span class="blank m0 p0" data-num="{int(num)}">{placeholder}</span>'
        formatted_question = re.sub(r'\[(\d+)\.(.*?)\]', replace_match, question)
        correct = sorted(re.findall(r'\[(\d+)\.(.*?)\]', question), key=lambda x: int(x[0]))
        return formatted_question, correct

    # === common ===================================
    def upd_total(self):
        num_choose = len(self.qs['choose'])
        num_input = len(self.qs['input'])
        num_fill = len(self.qs['fill'])
        total = num_choose + num_input + num_fill
        fo.str2txt(str(total), self.f_total)

    def choose_question(self, df_progress):
        '''
        Выбирает вопрос с наименьшим 'estimation', если несколько — выбирает случайный.
        Если вопрос отсутствует в 'df_progress', ему присваивается points=0, estimation='F'.
        '''
        # Объединяем все вопросы в один список, добавляя kind
        questions = []
        for kind, q_list in self.qs.items():
            for q in q_list:
                q['kind'] = kind
                questions.append(q)
        if not questions:
            raise ValueError(f'Topic {self.id} doesn\'t contain questions.')
        df_questions = pd.DataFrame(questions)

        # Фильтруем df_progress по topic_id
        df_progress4topic = df_progress[df_progress['topic_id'] == self.id]
        # Создаем ключ для идентификации (question_kind + question_id)
        df_progress4topic['key'] = df_progress4topic['question_kind'] + '_' + df_progress4topic['question_id'].astype(str)
        df_questions['key'] = df_questions['kind'] + '_' + df_questions['id'].astype(str)
        # Определяем, какие вопросы отсутствуют в прогрессе
        missing_questions = df_questions[~df_questions['key'].isin(df_progress4topic['key'])]
        # Добавляем недостающие вопросы
        new_id = df_progress['id'].max() + 1 if not df_progress.empty else 0
        if not missing_questions.empty:
            new_progress = pd.DataFrame({
                'id': range(new_id, new_id + len(missing_questions)),
                'topic_id': self.id,
                'question_kind': missing_questions['kind'].values,
                'question_id': missing_questions['id'].values,
                'points': 0,
                'estimation': 'F'
            })
            df_progress_combined = pd.concat([df_progress4topic, new_progress], ignore_index=True)
        else:
            df_progress_combined = df_progress4topic.copy()
        # Преобразуем 'estimation' в числовое значение
        df_progress_combined['estimation_numeric'] = df_progress_combined['estimation'].map(self.estimation_order)
        # Находим вопрос с минимальным 'estimation'
        min_estimation = df_progress_combined['estimation_numeric'].min()
        candidates = df_progress_combined[df_progress_combined['estimation_numeric'] == min_estimation]
        # Выбираем случайный вопрос из кандидатов
        return candidates.sample(frac=1).sample(n=1).iloc[0]

    def get_question(self, tid, q_kind, qid):
        '''
        Получает вопрос указанного типа из self.qs.
        Для q_fill работает с обычным списком, а не с DataFrame.
        '''
        if q_kind not in self.qs:
            raise ValueError(f'Invalid question type "{q_kind}" for topic {tid}.')
        # q_fill
        if q_kind == 'fill':
            # fill-вопросы хранятся в списке
            question = next((q for q in self.qs['fill'] if q['id'] == str(qid)), None)
            if not question:
                raise ValueError(f'Question ID {qid} not found in topic {tid} (type "{q_kind}").')
            return pdo.convert_int64(question)
        # Для остальных типов работаем с DataFrame
        df_questions = pd.DataFrame(self.qs[q_kind])
        if df_questions.empty:
            raise ValueError(f'No questions found in topic {tid} for type "{q_kind}".')
        question = df_questions[df_questions['id'] == qid]
        if question.empty:
            raise ValueError(f'Question ID {qid} not found in topic {tid} (type "{q_kind}").')
        data = question.iloc[0].to_dict()
        if q_kind == 'choose':
            # shufle options for 'choose'
            options = [opt.strip() for opt in data['options'].split(';')]
            shuffle(options)
            data['options'] = options
            # prepare correct
            correct = [opt.strip() for opt in data['correct'].split(';')]
            data['correct'] = sorted(correct)
        return pdo.convert_int64(data)
