import src.helpers.fo as fo
import src.helpers.pdo as pdo
import os
import pandas as pd


class User:
    def __init__(self, username, topics_data):
        self.name = username
        self.path = f'data/users/{self.name}'
        self.f_data = f'{self.path}/_data.yml'
        self.f_stats = f'{self.path}/stats.csv'
        self.f_progress = f'{self.path}/progress.csv'
        self.data = fo.yml2dict(self.f_data)
        self.df_stats = self.load_stats(topics_data)
        self.df_progress = self.load_progress()
        # 1. находить вопрос наименьшей оценкой.
        # 2. если вопрос имеет оценку F, D, C, B, A - показать вопрос:
        #     правильный ответ:   +1 point
        #     неправильный ответ: -1 point
        # 3. если вопрос имеет оценку S1, S2, S3 и с моментна updated_at
        #    прошло 3 дня, 7 дней, 14 дней соответсвенно - показать вопрос:
        #     правильный ответ:   +1 point
        #     неправильный ответ: сбросить на нижний порог A (15 points)
        #    если нет - искать дальше, проверяя другие SN вопросы
        self.estimate_ranges = {'N': (0, 0), 'F': (1, 3), 'D': (4, 6), 'C': (7, 9), 'B': (10, 14),
                                'A': (15, 20), 'S1': (21, 21), 'S2': (22, 22), 'S3': (23, 23)}

    # === stats ===================================
    def load_stats(self, topics_data):
        '''Загружает stats.csv только один раз и дополняет его новыми темами без повторного чтения'''
        df_stats = pdo.load(self.f_stats, allow_empty=True)
        if df_stats.empty:
            df_stats = pd.DataFrame(columns=['id','topic_id','N','F','D','C','B','A','S1','S2','S3','in_progress','total','suspicious'])
        existing_topics = set(df_stats['topic_id']) if not df_stats.empty else set()
        new_rows = []
        for tid, topic_name in topics_data.items():
            topic_path = f'data/topics/{tid}_{topic_name}/questions/_total.txt'
            total = int(fo.txt2str(topic_path))
            if tid not in existing_topics:
                new_rows.append({
                    'id': len(df_stats) + len(new_rows),
                    'topic_id': tid,
                    'N': total, 'F':0,'D':0,'C':0,'B':0,'A':0,'S1':0,'S2':0,'S3':0,
                    'in_progress': 0,
                    'total': total,
                    'suspicious': 0
                })
            else:
                df_stats.loc[df_stats['topic_id'] == tid, 'total'] = total  # Обновляем total
        if new_rows:
            df_stats = pd.concat([df_stats, pd.DataFrame(new_rows)], ignore_index=True)
            pdo.save(df_stats, self.f_stats)  # Сохраняем только при изменениях
        return df_stats

    def get_stats(self, tid):
        """Возвращает статистику пользователя по конкретной теме."""
        stat_record = self.df_stats[self.df_stats['topic_id'] == tid]
        if stat_record.empty:
            return pdo.convert_int64({
                'topic_id': tid, 'N': 0, 'F': 0, 'D': 0, 'C': 0, 'B': 0, 'A': 0, 'S1': 0, 'S2': 0, 'S3': 0,
                'in_progress': 0, 'total': 0, 'suspicious': 0
            })
        return pdo.convert_int64(stat_record.iloc[0].to_dict())

    def upd_stats(self):
        '''Обновляет stats в памяти, читая progress из памяти, а не из файла'''
        # Обнуляем оценки перед перерасчетом
        self.df_stats[['N', 'F', 'D', 'C', 'B', 'A', 'S1', 'S2', 'S3']] = 0
        # Группируем прогресс по topic_id и estimation, считаем количество каждой оценки
        progress_counts = self.df_progress.groupby(['topic_id', 'estimation']).size().unstack(fill_value=0)
        # Заполняем df_stats оценками из progress_counts
        for grade in self.estimate_ranges.keys():
            if grade in progress_counts:
                self.df_stats[grade] = self.df_stats['topic_id'].map(progress_counts[grade]).fillna(0).astype(int)
        # Считаем, сколько вопросов уже начато (всего, кроме N)
        self.df_stats['in_progress'] = self.df_stats[['F', 'D', 'C', 'B', 'A', 'S1', 'S2', 'S3']].sum(axis=1)
        # Вычисляем N (все вопросы - начатые)
        self.df_stats['N'] = (self.df_stats['total'] - self.df_stats['in_progress']).clip(lower=0)
        # Сохранение данных
        pdo.save(self.df_stats, self.f_stats)

    # === stats ===================================
    def load_progress(self):
        '''Загружает progress.csv только один раз.'''
        df_progress = pdo.load(self.f_progress, allow_empty=True)
        if df_progress.empty:
            df_progress = pd.DataFrame(columns=['id', 'topic_id', 'question_kind', 'question_id', 'points', 'estimation', 'updated_at'])
        return df_progress

    def get_progress(self, tid, q_kind, qid):
        """Получает прогресс пользователя для текущего вопроса."""
        where = {'topic_id': tid, 'question_kind': q_kind, 'question_id': qid}
        progress_records = pdo.filter(self.df_progress, where=where, allow_empty=True)
        if progress_records.empty:
            estimation, points = 'F', 0
        else:
            record = progress_records.iloc[0]
            estimation, points = record['estimation'], record['points']
        threshold = self.estimate_ranges[estimation][1]
        return pdo.convert_int64({'estimation': estimation, 'points': points, 'threshold': threshold})

    def upd_progress(self, tid, q_kind, qid, result):
        '''Обновляет прогресс в памяти и записывает файл только при изменениях'''
        existing_row = self.df_progress[
            (self.df_progress['topic_id'] == tid) &
            (self.df_progress['question_kind'] == q_kind) &
            (self.df_progress['question_id'] == qid)
        ]
        if not existing_row.empty:
            index = existing_row.index[0]
            self.df_progress.at[index, 'points'] = max(0, self.df_progress.at[index, 'points'] + (1 if result else -1))
        else:
            new_id = self.df_progress['id'].max() + 1 if not self.df_progress.empty else 0
            self.df_progress = pd.concat([self.df_progress, pd.DataFrame([{
                'id': new_id, 'topic_id': tid, 'question_kind': q_kind, 'question_id': qid,
                'points': 1 if result else 0, 'estimation': 'F' if result else 'N', 'updated_at': pd.Timestamp.utcnow()
            }])], ignore_index=True)
        self.df_progress['estimation'] = self.df_progress['points'].apply(
            lambda p: next((k for k, (low, high) in self.estimate_ranges.items() if low <= p <= high), 'F')
        )
        pdo.save(self.df_progress, self.f_progress)
