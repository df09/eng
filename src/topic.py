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
        self.d_q_fill = f'{self.path}/questions/fill'
        self.f_total = f'{self.path}/questions/_total.txt'
        self.qs = {
            'choose': pdo.load(self.f_q_chooses, allow_empty=True).to_dict(orient="records"),
            # 'choose': {},
            'input': pdo.load(self.f_q_inputs, allow_empty=True).to_dict(orient="records"),
            # 'input': {},
            # 'fill': self.load_fill_questions()
            'fill': {},
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
        # Загружаем вопросы нужного типа
        df_questions = pd.DataFrame(self.qs[q_kind])
        if df_questions.empty:
            raise ValueError(f"No questions found in topic {tid} for type '{q_kind}'.")
        # Ищем нужный вопрос
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
    # TODO
    def load_fill_questions(self):
        """Загружает fill-вопросы из директории."""
        fill_questions = []
        if os.path.exists(self.d_q_fill):
            for filename in os.listdir(self.d_q_fill):
                if filename.endswith('.txt'):
                    filepath = os.path.join(self.d_q_fill, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        question_text = f.read().strip()
                        fill_questions.append({'id': filename[:-4], 'question': question_text})
        return fill_questions

    # === total ===================================
    def upd_total(self):
        num_choose = len(self.qs['choose'])
        num_input = len(self.qs['input'])
        num_fill = len(self.qs['fill'])
        total = num_choose + num_input + num_fill
        fo.str2txt(str(total), self.f_total)
