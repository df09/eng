import os
import src.helpers.fo as fo
import src.helpers.pdo as pdo
from logger import logger
import pandas as pd
from src.topic import Topic


class Topics():
    def __init__(self):
        self.path = 'data/topics'
        self.data = self.get_data() # TODO: -> self.list
        self.f_suspicious = f'{self.path}/0_all/suspicious.csv'
        # TODO: self.f_totals = f'{self.path}/0_all/totals.csv'
            # TODO: также не забыть убрать total из stats и брать из totals.csv для темплейтов
        # TODO: self.totals =

    def get_data(self):
        data = {}
        # TODO: collect topics
        # data['topics'] = {}
        seen_ids = set()
        for folder in os.listdir(self.path):
            folder_path = os.path.join(self.path, folder)
            if os.path.isdir(folder_path) and "_" in folder:
                tid, tname = folder.split("_", 1)
                if tid.isdigit():
                    tid = int(tid)
                    if tid in seen_ids:
                        logger.warning(f"Warning: Duplicate ID {tid} found for topic '{tname}'")
                    else:
                        seen_ids.add(tid)
                        data[tid] = tname
        # Добавляем специальный топик "0_all"
        all_topic_path = os.path.join(self.path, "0_all")
        if os.path.exists(all_topic_path):
            data[0] = "all"
        # # TODO: collect totals
        # data['totals'] = {}
        # # TODO: collect suspicious
        # data['suspicious'] = {}
        return data

    def upd_totals(self):
        """Обновляет _total.txt для каждого топика, включая 0_all."""
        for tid, name in self.data.items():
            topic = Topic(tid, name, self.data) if tid == 0 else Topic(tid, name)
            topic.upd_total()

    def choose_tid(self, df_user_stats):
        """Выбирает топик для 0_all."""
        df = df_user_stats[df_user_stats['tid'] != 0]
        filtered_stats = df[df[['N', 'F', 'D', 'C', 'B']].sum(axis=1) > 0]
        return filtered_stats.sample(1)['tid'].values[0] if not filtered_stats.empty else df.sample(1)['tid'].values[0]

    def mark_suspicious(self, data):
        """Помечает вопрос подозрительным."""
        tid, qkind, qid, note = data['tid'], data['qkind'], data['qid'], data['note']
        topic = Topic(tid, self.data[tid])
        if not topic.update_question_suspicious(qkind, qid, 1, note):
            return False
        return True

    def validate_questions(self):
        """Проверяет уникальность вопросов по (tid, qkind, qid)."""
        seen_questions = set()
        duplicates = []
        for tid, tname in self.data.items():
            if tid == 0:
                continue
            topic = Topic(tid, tname)
            for qkind, q_list in topic.qs.items():
                for q in q_list:
                    key = (tid, qkind, q['id'])
                    if key in seen_questions:
                        duplicates.append(key)
                    seen_questions.add(key)
        if duplicates:
            raise ValueError(f'Duplicate questions found: {duplicates}')
        return True

    def validate_progress(self):
        """Удаляет прогресс у удаленных вопросов и сбрасывает его у исправленных подозрительных."""
        valid_questions = set()
        reviewed_questions = set()
        for tid, tname in self.data.items():
            if tid == 0:
                continue
            topic = Topic(tid, tname)
            for qkind, q_list in topic.qs.items():
                for q in q_list:
                    valid_questions.add((tid, qkind, q['id']))
                    if q.get('suspicious_status') == 2:
                        reviewed_questions.add((tid, qkind, q['id']))
        user_folders = [f for f in os.listdir('data/users') if os.path.isdir(f'data/users/{f}')]
        for user in user_folders:
            progress_file = f'data/users/{user}/progress.csv'
            df_progress = pdo.load(progress_file, allow_empty=True)
            if df_progress.empty:
                continue
            # Удаляем прогресс для удаленных вопросов
            df_progress = df_progress[df_progress.apply(lambda row: (row['tid'], row['qkind'], row['qid']) in valid_questions, axis=1)]
            # Удаляем прогресс для исправленных подозрительных вопросов
            df_progress = df_progress[~df_progress.apply(lambda row: (row['tid'], row['qkind'], row['qid']) in reviewed_questions, axis=1)]
            pdo.save(df_progress, progress_file)
        # Сбрасываем suspicious_status = 0 у исправленных вопросов
        for tid, tname in self.data.items():
            if tid == 0:
                continue
            topic = Topic(tid, tname)
            topic.reset_suspicious_questions()
