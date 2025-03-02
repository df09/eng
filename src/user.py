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

        # Загружаем единожды
        self.data = fo.yml2dict(self.f_data)
        self.df_stats = self.load_stats(topics_data)  # Оптимизированный метод
        self.df_progress = self.load_progress()  # Оптимизированный метод
        self.estimate_ranges = {'F': [0, 2], 'D': [3, 5], 'C': [6, 9], 'B': [10, 14], 'A': [15, 999]}

    def load_stats(self, topics_data):
        '''Загружает stats.csv только один раз и дополняет его новыми темами без повторного чтения'''
        df_stats = pdo.load(self.f_stats, allow_empty=True)

        if df_stats.empty:
            df_stats = pd.DataFrame(columns=['id', 'topic_id', 'A', 'B', 'C', 'D', 'F', 'in_progress', 'total'])

        existing_topics = set(df_stats['topic_id']) if not df_stats.empty else set()
        new_rows = []

        for tid, topic_name in topics_data.items():
            topic_path = f'data/topics/{tid}_{topic_name}/questions/_total.txt'
            total = int(fo.txt2str(topic_path))

            if tid not in existing_topics:
                new_rows.append({
                    'id': len(df_stats) + len(new_rows),
                    'topic_id': tid,
                    'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0,
                    'in_progress': 0,
                    'total': total
                })
            else:
                df_stats.loc[df_stats['topic_id'] == tid, 'total'] = total  # Обновляем total

        if new_rows:
            df_stats = pd.concat([df_stats, pd.DataFrame(new_rows)], ignore_index=True)
            pdo.save(df_stats, self.f_stats)  # Сохраняем только при изменениях

        return df_stats

    def load_progress(self):
        '''Загружает progress.csv только один раз.'''
        df_progress = pdo.load(self.f_progress, allow_empty=True)
        if df_progress.empty:
            df_progress = pd.DataFrame(columns=['id', 'topic_id', 'question_kind', 'question_id', 'points', 'estimation'])
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

    def save_progress(self, tid, q_kind, qid, result):
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
                'points': 1 if result else 0, 'estimation': 'F'
            }])], ignore_index=True)

        # Обновляем estimation в памяти
        self.df_progress['estimation'] = self.df_progress['points'].apply(
            lambda p: next((k for k, (low, high) in self.estimate_ranges.items() if low <= p <= high), 'F')
        )

        pdo.save(self.df_progress, self.f_progress)  # Сохраняем только изменённые данные
        self.upd_stats()

    def upd_stats(self):
        '''Обновляет stats в памяти, читая progress из памяти, а не из файла'''
        self.df_stats[['A', 'B', 'C', 'D', 'F']] = 0  # Обнуляем категории

        progress_counts = self.df_progress.groupby(['topic_id', 'estimation']).size().unstack(fill_value=0)

        for grade in self.estimate_ranges.keys():
            if grade in progress_counts:
                self.df_stats[grade] = self.df_stats['topic_id'].map(progress_counts[grade]).fillna(0).astype(int)

        self.df_stats['in_progress'] = self.df_stats[['A', 'B', 'C', 'D', 'F']].sum(axis=1)

        pdo.save(self.df_stats, self.f_stats)  # Сохраняем только при изменениях
