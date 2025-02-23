import src.helpers.fo as fo
import src.helpers.pdo as pdo
from src.helpers.cmd import cmd
import os
from logger import logger
import pandas as pd


class User():
    def __init__(self, username, topics_data):
        self.name = username
        self.path = f'data/users/{self.name}'
        self.f_data = f'{self.path}/_data.yml'
        self.f_stats = f'{self.path}/stats.csv'
        self.f_progress = f'{self.path}/progress.csv'
        self.data = fo.yml2dict(self.f_data)
        self.df_stats = self.get_stats(topics_data)
        self.df_progress = pdo.load(self.f_progress, allow_empty=True)
        self.estimate_ranges = {'F':[0, 2],'D':[3, 5],'C':[6, 9],'B':[10, 14],'A':[15, 999]}

    def get_stats(self, topics_data):
        df_stats = pdo.load(self.f_stats, allow_empty=True)
        df_stats["topic_id"] = df_stats["topic_id"].astype(int, errors="ignore")
        missing_topics = [tid for tid in topics_data if tid not in df_stats["topic_id"].values]
        # Добавить недостающие topic_id со значениями по умолчанию
        new_rows = pd.DataFrame([{ "id": len(df_stats) + i, "topic_id": tid,
                "a": 0, "b": 0, "c": 0, "d": 0, "f": 0, "in_progress": 0
            } for i, tid in enumerate(missing_topics)])
        # Объединяем старые и новые данные
        df_stats = pd.concat([df_stats, new_rows], ignore_index=True)
        return df_stats

    def save_progress(self, tid, q_kind, qid, result):
        """
        Обновляет прогресс пользователя после ответа на вопрос.
        Параметры:
            tid (int)     - ID темы
            q_kind (str)  - Тип вопроса ('choose', 'input', 'fill')
            qid (int)     - ID вопроса
            result (bool) - Верно ли отвечен вопрос
        Возвращает:
            bool: True, если прогресс успешно сохранён.
        """
        # Проверяем, существует ли запись об этом вопросе
        existing_row = self.df_progress[
            (self.df_progress["topic_id"] == tid) &
            (self.df_progress["question_kind"] == q_kind) &
            (self.df_progress["question_id"] == qid)
        ]
        if not existing_row.empty:
            # Если запись существует, обновляем её
            index = existing_row.index[0]
            if result:
                self.df_progress.at[index, "points"] += 1  # Увеличиваем на 1
            elif self.df_progress.at[index, "points"] > 0:
                self.df_progress.at[index, "points"] -= 1  # Уменьшаем, но не даём уйти в отрицательные значения
        else:
            # Если записи нет, создаем новую
            new_id = self.df_progress["id"].max() + 1 if not self.df_progress.empty else 1
            new_row = {
                "id": new_id,
                "topic_id": tid,
                "question_kind": q_kind,
                "question_id": qid,
                "points": 1 if result else 0,  # Начальное значение не может быть отрицательным
                "estimation": "F"
            }
            self.df_progress = pd.concat([self.df_progress, pd.DataFrame([new_row])], ignore_index=True)
        # Пересчитываем estimation на основе points
        for key, (low, high) in self.estimate_ranges.items():
            self.df_progress.loc[
                (self.df_progress["topic_id"] == tid) &
                (self.df_progress["question_kind"] == q_kind) &
                (self.df_progress["question_id"] == qid) &
                (self.df_progress["points"].between(low, high)),
                "estimation"
            ] = key
        # Сохраняем обновлённый CSV
        pdo.save(self.df_progress, self.f_progress)
        return True
