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
        self.df_progress = pdo.load(self.f_progress)

    def get_stats(self, topics_data):
        df_stats = pdo.load(self.f_stats)
        df_stats["topic_id"] = df_stats["topic_id"].astype(int, errors="ignore")
        missing_topics = [tid for tid in topics_data if tid not in df_stats["topic_id"].values]
        # Добавить недостающие topic_id со значениями по умолчанию
        new_rows = pd.DataFrame([{
                "id": len(df_stats) + i,
                "topic_id": tid,
                "a": 0,
                "b": 0,
                "c": 0,
                "d": 0,
                "f": 0,
                "in_progress": 0
            } for i, tid in enumerate(missing_topics)])
        # Объединяем старые и новые данные
        df_stats = pd.concat([df_stats, new_rows], ignore_index=True)
        return df_stats
