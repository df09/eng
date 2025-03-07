import os
import src.helpers.fo as fo
import src.helpers.pdo as pdo
from logger import logger
import pandas as pd
from src.topic import Topic


class Topics():
    def __init__(self):
        self.path = 'data/topics'
        self.f_topicdata = f'{self.path}/0_all/topicdata.csv'
        self.topiclist = self.get_topiclist()
        self.df_topicdata = self.get_df_topicdata()
        self.topicdata = self.get_topicdata()

    # mix
    def choose_tid(self, df_user_stats):
        """Выбирает топик для 0_all."""
        df = df_user_stats[df_user_stats['tid'] != 0]
        filtered_stats = df[df[['N', 'F', 'D', 'C', 'B']].sum(axis=1) > 0]
        return filtered_stats.sample(1)['tid'].values[0] if not filtered_stats.empty else df.sample(1)['tid'].values[0]
    def mark_suspicious(self, data):
        """Помечает вопрос подозрительным."""
        tid, qkind, qid, note = data['tid'], data['qkind'], data['qid'], data['note']
        topic = Topic(tid, self.topiclist[tid])
        if not topic.update_question_suspicious(qkind, qid, 1, note):
            return False
        return True

    # topiclist
    def get_topiclist(self):
        topiclist = {}
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
                        topiclist[tid] = tname
        # Добавляем специальный топик "0_all"
        all_topic_path = os.path.join(self.path, "0_all")
        if os.path.exists(all_topic_path):
            topiclist[0] = "all"
        return topiclist

    # topicdata
    def get_df_topicdata(self):
        return pdo.load(self.f_topicdata, allow_empty=True)
    def get_topicdata(self):
        return self.df_topicdata.to_dict(orient='records')
    def get_topicdata4topic(self, tid):
        return self.df_topicdata[self.df_topicdata['tid'] == tid].to_dict(orient='records')[0]
    def upd_topicdata(self):
        """Обновляет topicdata.csv для каждого топика, включая 0_all."""
        df_topicdata = pdo.load(self.f_topicdata, allow_empty=True)
        all_topicdata = []
        # Собираем данные по каждому топику
        for tid, name in self.topiclist.items():
            if tid == 0:
                continue
            topic = Topic(tid, name)
            num_choose = len(topic.qs.get('choose', []))
            num_input = len(topic.qs.get('input', []))
            num_fill = len(topic.qs.get('fill', []))
            total = num_choose + num_input + num_fill
            num_suspicious = sum(
                q.get('suspicious_status', 0) > 0 for kind in topic.qs for q in topic.qs[kind]
            )
            all_topicdata.append({'id': tid, 'tid': tid, 'tname': name, 'total': total, 'suspicious': num_suspicious})
        df_new_topicdata = pd.DataFrame(all_topicdata)
        # aggregate data for '0_all'
        if not df_new_topicdata.empty:
            total_sum = df_new_topicdata[['total', 'suspicious']].sum()
            row_all = {'id': 0, 'tid': 0, 'tname': 'all', 'total': total_sum['total'], 'suspicious': total_sum['suspicious']}
            df_new_topicdata = pd.concat([pd.DataFrame([row_all]), df_new_topicdata], ignore_index=True)
        # Сохраняем и обновляем атрибуты
        pdo.save(df_new_topicdata, self.f_topicdata)
        self.df_topicdata = df_new_topicdata
        self.topicdata = self.get_topicdata()

    # validation
    def validate_questions(self):
        """Проверяет уникальность вопросов по (tid, qkind, qid)."""
        seen_questions = set()
        duplicates = []
        for tid, tname in self.topiclist.items():
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
        for tid, tname in self.topiclist.items():
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
            if df_progress.empty:
                continue
            pdo.save(df_progress, progress_file)
        # Сбрасываем suspicious_status = 0 у исправленных вопросов
        for tid, tname in self.topiclist.items():
            if tid == 0:
                continue
            topic = Topic(tid, tname)
            topic.reset_suspicious_questions()
