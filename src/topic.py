import os
import random
import pandas as pd
from collections import defaultdict
import src.helpers.fo as fo
import src.helpers.pdo as pdo
from logger import logger


class Topic:
    def __init__(self, tid, name):
        self.id = tid
        self.name = name
        self.estimation_order = {'F':1,'D':2,'C':3,'B':4,'A': 5}
        self.path = f'data/topics/{self.id}_{self.name}'
        self.qs = {
            'choose': pdo.load(f'{self.path}/questions/chooses.csv').to_dict(orient="records"),
            'input': pdo.load(f'{self.path}/questions/inputs.csv').to_dict(orient="records"),
            # TODO
            'fill': self.load_fill_questions()
        }
        # TODO: просто дать ссылку на readme?
        self.theory = fo.txt2str(f'{self.path}/theory.txt')

    # TODO
    def load_fill_questions(self):
        return {}

    # === get question ===================================
    def choose_question(self, df_progress):
        """
        Выбирает вопрос с наименьшим 'estimation', если несколько — выбирает случайный.
        Если вопрос отсутствует в 'df_progress', ему присваивается points=0, estimation='F'.
        Возвращает:
            kind (str)  - question kind ('choose', 'input', 'fill')
            qid  (int)  - id вопроса
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
        # Фильтруем df_progress по topic_id - только вопросы, которые есть в текущем топике
        df_progress_filtered = df_progress[df_progress["topic_id"] == self.id]
        # Если в progress нет записей о вопросе, добавляем его с points=0, estimation='F'
        new_id = df_progress["id"].max() + 1 if not df_progress.empty else 0
        default_progress = pd.DataFrame({
            'id': range(new_id, new_id + len(df_questions)),
            'topic_id': self.id,
            'question_kind': df_questions["kind"],
            'question_id': df_questions['id'],
            'points': 0,
            'estimation': 'F'
        })
        # Объединяем прогресс пользователя с дефолтным списком вопросов (без дубликатов)
        df_progress_combined = pd.concat([df_progress_filtered, default_progress]).drop_duplicates(subset=["question_id"], keep="first")
        # Преобразуем 'estimation' в числовое значение
        estimation_order = {"F": 1, "D": 2, "C": 3, "B": 4, "A": 5}
        df_progress_combined["estimation_numeric"] = df_progress_combined["estimation"].map(estimation_order)
        # Находим вопрос с минимальной 'estimation'
        min_estimation = df_progress_combined["estimation_numeric"].min()
        candidates = df_progress_combined[df_progress_combined["estimation_numeric"] == min_estimation]
        selected = candidates.sample(n=1).iloc[0]
        # Возвращаем только kind, tid, qid
        return selected

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
