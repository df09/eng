import os
import re
from logger import logger
import src.helpers.fo as fo
import pandas as pd
import src.helpers.pdo as pdo
from pprint import pprint


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
            'choose': pdo.load(self.f_q_chooses, allow_empty=True).to_dict(orient="records"),
            'input': pdo.load(self.f_q_inputs, allow_empty=True).to_dict(orient="records"),
            'fill': self.load_fill_questions()
        }
        self.upd_total()
        # TODO: просто дать ссылку на readme?
        self.theory = fo.txt2str(f'{self.path}/theory.txt')

    # === q.common ===================================
    def choose_question(self, df_progress):
        """
        Выбирает вопрос с наименьшим 'estimation', если несколько — выбирает случайный.
        Если вопрос отсутствует в 'df_progress', ему присваивается points=0, estimation='F'.
        """
        # Объединяем все вопросы в один список, добавляя kind
        questions = []
        for kind, q_list in self.qs.items():
            for q in q_list:
                q["kind"] = kind
                questions.append(q)
        if not questions:
            raise ValueError(f"Topic {self.id} doesn't contain questions.")
        df_questions = pd.DataFrame(questions)
        # Фильтруем df_progress по topic_id
        df_progress_filtered = df_progress[df_progress["topic_id"] == self.id]
        # Создаем ключ для идентификации (question_kind + question_id)
        df_progress_filtered["key"] = df_progress_filtered["question_kind"] + "_" + df_progress_filtered["question_id"].astype(str)
        df_questions["key"] = df_questions["kind"] + "_" + df_questions["id"].astype(str)
        # Определяем, какие вопросы отсутствуют в прогрессе
        missing_questions = df_questions[~df_questions["key"].isin(df_progress_filtered["key"])]
        # Добавляем недостающие вопросы
        new_id = df_progress["id"].max() + 1 if not df_progress.empty else 0
        if not missing_questions.empty:
            new_progress = pd.DataFrame({
                'id': range(new_id, new_id + len(missing_questions)),
                'topic_id': self.id,
                'question_kind': missing_questions["kind"].values,
                'question_id': missing_questions["id"].values,
                'points': 0,
                'estimation': 'F'
            })
            df_progress_combined = pd.concat([df_progress_filtered, new_progress], ignore_index=True)
        else:
            df_progress_combined = df_progress_filtered.copy()
        # Преобразуем 'estimation' в числовое значение
        df_progress_combined["estimation_numeric"] = df_progress_combined["estimation"].map(self.estimation_order)
        # Находим вопрос с минимальным 'estimation'
        min_estimation = df_progress_combined["estimation_numeric"].min()
        candidates = df_progress_combined[df_progress_combined["estimation_numeric"] == min_estimation]
        # Выбираем случайный вопрос из кандидатов
        return candidates.sample(frac=1).sample(n=1).iloc[0]

    def get_question(self, tid, q_kind, qid):
        """
        Получает вопрос указанного типа из self.qs.
        Для q_fill работает с обычным списком, а не с DataFrame.
        """
        if q_kind not in self.qs:
            raise ValueError(f"Invalid question type '{q_kind}' for topic {tid}.")
        if q_kind == 'fill':
            # fill-вопросы хранятся в списке
            question = next((q for q in self.qs['fill'] if q['id'] == str(qid)), None)
            if not question:
                raise ValueError(f"Question ID {qid} not found in topic {tid} (type '{q_kind}').")
            return question
        # Для остальных типов работаем с DataFrame
        df_questions = pd.DataFrame(self.qs[q_kind])
        if df_questions.empty:
            raise ValueError(f"No questions found in topic {tid} for type '{q_kind}'.")
        question = df_questions[df_questions['id'] == qid]
        if question.empty:
            raise ValueError(f"Question ID {qid} not found in topic {tid} (type '{q_kind}').")
        return question.iloc[0].to_dict()

    # === q.input ===================================
    def format_q_input(self, question):
        """
        Заменяет _(ответ) на '___' и возвращает вопрос + правильный ответ отдельно.
        """
        match = re.search(r'_\((.*?)\)', question)
        if not match:
            raise ValueError("Вопрос не содержит правильного ответа в формате _(ответ).")
        correct_answer = match.group(1)  # Извлекаем текст внутри _(...)
        formatted_question = question.replace(match.group(0), '___')  # Заменяем _(...) на ___
        return formatted_question, correct_answer

    # === q.fill ===================================
    def load_fill_questions(self):
        """Загружает fill-вопросы из файлов и парсит их с учетом пропусков."""
        fill_questions = []
        for filename in os.listdir(self.d_q_fills):
            qid, qname = filename.split('_')
            filepath = os.path.join(self.d_q_fills, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                question = f.read().strip()
                formatted_question, answers = self.format_q_fill(question)
                fill_questions.append({
                    'id': qid,
                    'name': qname,
                    'question': formatted_question,
                    'answers': answers
                })
        return fill_questions

    def format_q_fill(self, question):
        """
        Заменяет все [число.ответ] на placeholder в виде <span class="blank" data-num="число">____</span>,
        где количество символов соответствует длине исходной строки [число.ответ].
        Собирает правильные ответы в порядке возрастания номеров.
        """
        # Находим все [num.answer]
        matches = re.findall(r'\[(\d+)\.(.*?)\]', question)
        # Сортируем по возрастанию номера
        ordered = sorted(matches, key=lambda x: int(x[0]))
        answers = [f"[{num}.{ans}]" for num, ans in ordered]
        
        def replace_match(match):
            num, answer = match.groups()
            placeholder = '_' * len(f"[{num}.{answer}]")
            return f'<span class="blank m0 p0" data-num="{int(num)}">{placeholder}</span>'
        
        formatted_question = re.sub(r'\[(\d+)\.(.*?)\]', replace_match, question)
        return formatted_question, answers

    # === total ===================================
    def upd_total(self):
        num_choose = len(self.qs['choose'])
        num_input = len(self.qs['input'])
        num_fill = len(self.qs['fill'])
        total = num_choose + num_input + num_fill
        fo.str2txt(str(total), self.f_total)
