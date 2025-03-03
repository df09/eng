from random import shuffle
import os
import pandas as pd
import src.helpers.pdo as pdo
import src.helpers.fo as fo
from logger import logger
import re


class Topic:
    def __init__(self, tid, name, topics_data=None):
        self.id = tid
        self.name = name
        self.estimation_order = {'N':0,'F':1,'D':2,'C':3,'B':4,'A':5}
        self.path = f'./data/topics/{tid}_{name}'
        self.f_q_chooses = f'{self.path}/questions/chooses.csv'
        self.f_q_inputs = f'{self.path}/questions/inputs.csv'
        self.d_q_fills = f'{self.path}/questions/fills'
        self.f_total = f'{self.path}/questions/_total.txt'
        # 0.all topic
        if self.id == 0:
            self.qs = self.load_all_questions(topics_data)
            self.f_total = f'data/topics/0_all/_total.txt'
            self.theory = ''
        else:
            self.f_q_chooses = f'{self.path}/questions/chooses.csv'
            self.f_q_inputs = f'{self.path}/questions/inputs.csv'
            self.d_q_fills = f'{self.path}/questions/fills'
            self.f_total = f'{self.path}/questions/_total.txt'
            self.qs = {
                'choose': self.load_choose_questions(),
                'input': self.load_input_questions(),
                'fill': self.load_fill_questions()
            }
            self.theory = fo.txt2str(f'{self.path}/theory.txt')
        self.upd_total()

    # === load.all ===================================
    def load_all_questions(self, topics_data):
        """Загружает вопросы из всех тем."""
        questions = {'choose': [], 'input': [], 'fill': []}
        for topic_id, topic_name in topics_data.items():
            if topic_id == 0:
                continue
            topic = Topic(topic_id, topic_name)
            for kind in questions.keys():
                questions[kind].extend(topic.qs.get(kind, []))
        return questions

    # === load.choose ===================================
    def load_choose_questions(self):
        df = pdo.load(self.f_q_chooses, allow_empty=True)
        df = df.fillna('')  # Заменяем NaN на пустые строки
        df = df.applymap(lambda x: 0 if isinstance(x, float) and pd.isna(x) else x)  # Убираем NaN
        questions = df.to_dict(orient='records')
        for question in questions:
            question['is_suspicious'] = question.get('is_suspicious', 0) or 0
        return questions

    # === load.input ===================================
    def load_input_questions(self):
        df = pdo.load(self.f_q_inputs, allow_empty=True)
        df = df.fillna('')  # Убираем NaN из строк
        df = df.applymap(lambda x: 0 if isinstance(x, float) and pd.isna(x) else x)  # Убираем NaN
        questions = df.to_dict(orient='records')
        for question in questions:
            question['question'], question['correct'], question['hints'] = self.format_q_input(question['question'])
            question['is_suspicious'] = question.get('is_suspicious', 0) or 0
        return questions
    def format_q_input(self, question):
        '''
        Ищет [<answer>:<hints>] или [<answer>] в вопросе, заменяет его на '___',
        и возвращает (отформатированный вопрос, правильный ответ, список подсказок).
        '''
        match = re.search(r'\[([^:\]]+)(?::([^]]+))?\]', question)
        if not match:
            raise ValueError('The question does not contain the correct answer in the [answer] or [answer:hints] format.')
        correct = match.group(1)
        hints = match.group(2).split(',') if match.group(2) else []
        formatted_question = question.replace(match.group(0), '___')
        return formatted_question, correct, hints

    # === load.fill ===================================
    def load_fill_questions(self):
        '''Загружает fill-вопросы из файлов и парсит их с учетом пропусков.'''
        questions = []
        for filename in os.listdir(self.d_q_fills):
            name_without_ext = os.path.splitext(filename)[0] # remove extension
            parts = name_without_ext.split('_')
            if len(parts) == 2:  # <id>_<name>
                qid, qname = parts
                is_suspicious, hash_value = 0, ''
            elif len(parts) >= 3:  # <id>_<name>_<hash>
                qid, qname, hash_value = parts[0], parts[1], '_'.join(parts[2:])
                hash_value = hash_value if pd.notna(hash_value) else ''  # Убираем NaN
                is_suspicious = 1
            else:
                raise ValueError(f"Unexpected filename format: {filename}")
            filepath = os.path.join(self.d_q_fills, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                question = f.read().strip()
                formatted_question, correct = self.format_q_fill(question)
                questions.append({
                    'id': qid,
                    'name': qname,
                    'question': formatted_question,
                    'correct': correct,
                    'is_suspicious': is_suspicious,
                    'hash': hash_value
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
        num_choose = len(self.qs.get('choose', []))
        num_input = len(self.qs.get('input', []))
        num_fill = len(self.qs.get('fill', []))
        total = num_choose + num_input + num_fill
        fo.str2txt(str(total), self.f_total)

    def choose_question(self, df_progress):
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
        # Создаём ключ для идентификации (question_kind + question_id)
        df_progress4topic['key'] = df_progress4topic['question_kind'] + '_' + df_progress4topic['question_id'].astype(str)
        df_questions['key'] = df_questions['kind'] + '_' + df_questions['id'].astype(str)

        # Добавляем недостающие вопросы
        missing_questions = df_questions[~df_questions['key'].isin(df_progress4topic['key'])]
        new_id = df_progress['id'].max(skipna=True) + 1 if not df_progress.empty else 0
        if not missing_questions.empty:
            new_progress = pd.DataFrame({
                'id': range(new_id, new_id + len(missing_questions)),
                'topic_id': self.id,
                'question_kind': missing_questions['kind'].values,
                'question_id': missing_questions['id'].values,
                'points': 0,
                'estimation': 'N',
                'asked_at': pd.NaT
            })
            df_progress_combined = pd.concat([df_progress4topic, new_progress], ignore_index=True)
        else:
            df_progress_combined = df_progress4topic.copy()
        # Преобразуем 'estimation' в числовое значение
        df_progress_combined['estimation_numeric'] = df_progress_combined['estimation'].map(self.estimation_order).fillna(0).astype(int)
        # **ШАГ 1: Выбираем вопросы с N, F, D, C, B**
        priority_questions = df_progress_combined[df_progress_combined['estimation'].isin(['N', 'F', 'D', 'C', 'B'])]
        if priority_questions.empty:
            # **ШАГ 2: Если нет, пробуем A**
            priority_questions = df_progress_combined[df_progress_combined['estimation'] == 'A']
        if priority_questions.empty:
            raise ValueError(f"No suitable questions found in topic {self.id}.")
        # перемешиваем, сортируем по asked_at, nat идут первыми, но в случайном порядке
        priority_questions = priority_questions.sample(frac=1, random_state=None)
        priority_questions = priority_questions.sort_values(by='asked_at', ascending=True, na_position='first')
        # Берём первый (самый старый, но перемешанный среди NaT)
        return priority_questions.iloc[0]

    def get_question(self, tid, q_kind, qid):
        '''
        Получает вопрос указанного типа из self.qs.
        Для q_fill работает с обычным списком, а не с DataFrame.
        '''
        if q_kind not in self.qs:
            raise ValueError(f'Invalid question type "{q_kind}" for topic {tid}.')
        # q_fill
        if q_kind == 'fill':
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
        data = question.iloc[0].fillna('').to_dict()
        if q_kind == 'choose':
            # Перемешиваем опции для 'choose'
            options = [opt.strip() for opt in data['options'].split(';')]
            shuffle(options)
            data['options'] = options
            # Подготавливаем правильные ответы
            correct = [opt.strip() for opt in data['correct'].split(';')]
            data['correct'] = sorted(correct)
        return pdo.convert_int64(data)
