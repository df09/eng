import src.helpers.fo as fo
import src.helpers.pdo as pdo
import os
import pandas as pd
import random


class User:
    def __init__(self, username, topics_data):
        self.name = username
        self.path = f'data/users/{self.name}'
        self.f_data = f'{self.path}/_data.yml'
        self.f_stats = f'{self.path}/stats.csv'
        self.f_progress = f'{self.path}/progress.csv'
        self.data = fo.yml2dict(self.f_data)
        self.df_stats = self.get_df_stats(topics_data)
        self.df_progress = self.get_df_progress()
        self.estimate_ranges = {'N': (0, 0), 'F': (1, 3), 'D': (4, 6), 'C': (7, 9), 'B': (10, 14), 'A': (15, 999)}
        self.upd_df_stats()

    # === stats ===================================
    def get_df_stats(self, topics_data):
        # get df
        df_stats = pdo.load(self.f_stats, allow_empty=True)
        if df_stats.empty:
            df_stats = pd.DataFrame(columns=['id','tid','N','F','D','C','B','A','in_progress','total','suspicious'])
        # upd total add create not-existing stats
        existing_topics = set(df_stats['tid']) if not df_stats.empty else set()
        new_rows = []
        for tid, topic_name in topics_data.items():
            if tid == 0:
                topic_path = f'data/topics/{tid}_{topic_name}/_total.txt'
            else:
                topic_path = f'data/topics/{tid}_{topic_name}/questions/_total.txt'
            total = int(fo.txt2str(topic_path))
            if tid not in existing_topics:
                new_rows.append({
                    'id': len(df_stats) + len(new_rows),
                    'tid': tid,
                    'N': total, 'F':0,'D':0,'C':0,'B':0,'A':0,
                    'in_progress': 0,
                    'total': total,
                    'suspicious': 0
                })
            else:
                df_stats.loc[df_stats['tid'] == tid, 'total'] = total  # Обновляем total
        # merge dfs and save new rows
        if new_rows:
            df_stats = pd.concat([df_stats, pd.DataFrame(new_rows)], ignore_index=True)
            pdo.save(df_stats, self.f_stats)  # Сохраняем только при изменениях
        return df_stats

    def upd_df_stats(self):
        # reset all
        self.df_stats[['N', 'F', 'D', 'C', 'B', 'A']] = 0
        # grades
        progress_counts = self.df_progress.groupby(['tid', 'estimation']).size().unstack(fill_value=0)
        for grade in self.estimate_ranges.keys():
            if grade in progress_counts:
                self.df_stats[grade] = self.df_stats['tid'].map(progress_counts[grade]).fillna(0).astype(int)
        # in_progress
        self.df_stats['in_progress'] = self.df_stats[['F', 'D', 'C', 'B', 'A']].sum(axis=1)
        # N (not asked yet)
        self.df_stats['N'] = (self.df_stats['total'] - self.df_stats['in_progress']).clip(lower=0)
        # -NaN/-float
        self.df_stats = self.df_stats.fillna(0).astype(int)
        # tid: 0 recalc
        sum_values = self.df_stats[self.df_stats['tid'] != 0].drop(columns=['id', 'tid']).sum() # Вычисляем сумму для строк, где tid != 0
        self.df_stats.loc[self.df_stats['tid'] == 0, sum_values.index] = sum_values.values # Записываем сумму в строку, где tid == 0
        # save
        pdo.save(self.df_stats, self.f_stats)

    def get_stat4topic(self, tid):
        stat_record = self.df_stats[self.df_stats['tid'] == tid]
        if stat_record.empty:
            return {'tid':tid,'N':0,'F':0,'D':0,'C':0,'B':0,'A':0,'in_progress':0,'total':0,'suspicious':0}
        return pdo.convert_int64(stat_record.iloc[0].to_dict())

    # === progress ===================================
    def get_df_progress(self):
        df_progress = pdo.load(self.f_progress, allow_empty=True)
        if df_progress.empty:
            df_progress = pd.DataFrame(columns=['id', 'tid', 'qkind', 'qid', 'points', 'estimation', 'asked_at'])
        return df_progress
    def upd_df_progress(self, tid, qkind, qid, result):
        where = {'tid': tid, 'qkind': qkind, 'qid': qid}
        df_progress4question = pdo.filter(self.df_progress, where=where, allow_empty=True)
        if df_progress4question.empty:
            # add new record
            self.df_progress = pd.concat([self.df_progress, pd.DataFrame([{
                'id': self.df_progress['id'].max() + 1 if not self.df_progress.empty else 0,
                'tid': tid,
                'qkind': qkind,
                'qid': qid,
                'points': 1 if result else 0,
                'estimation': 'F' if result else 'N',
                'asked_at': pd.Timestamp.utcnow()
            }])], ignore_index=True)
        else:
            # upd points
            index = df_progress4question.index[0]
            self.df_progress.at[index, 'points'] = max(0, self.df_progress.at[index, 'points'] + (1 if result else -1))
            # upd estimation
            self.df_progress['estimation'] = self.df_progress['points'].apply(
                lambda p: next((k for k, (low, high) in self.estimate_ranges.items() if low <= p <= high), 'F')
            )
            # upd time
            random_offset = random.randint(0, 86400)  # случайное смещение, только уменьшение времени
            self.df_progress.at[index, 'asked_at'] = pd.Timestamp.utcnow() + pd.Timedelta(milliseconds=random_offset)
        pdo.save(self.df_progress, self.f_progress)

    def get_progress4question(self, tid, qkind, qid):
        where = {'tid': tid, 'qkind': qkind, 'qid': qid}
        df_progress4question = pdo.filter(self.df_progress, where=where, allow_empty=True)
        if df_progress4question.empty:
            estimation, points = 'N', 0
        else:
            record = df_progress4question.iloc[0]
            estimation, points = record['estimation'], record['points']
        return pdo.convert_int64({
            'tid': tid,
            'qkind': qkind,
            'qid': qid,
            'estimation': estimation,
            'points': points,
            'threshold': self.estimate_ranges[estimation][1]
        })
