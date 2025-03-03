import os
import src.helpers.fo as fo
from logger import logger
import pandas as pd
from src.topic import Topic


class Topics():
    def __init__(self):
        self.path = 'data/topics'
        self.data = self.get_data()

    def get_data(self):
        data = {}
        seen_ids = set()
        for folder in os.listdir(self.path):
            folder_path = os.path.join(self.path, folder)
            if os.path.isdir(folder_path) and "_" in folder:
                topic_id, topic_name = folder.split("_", 1)
                if topic_id.isdigit():
                    topic_id = int(topic_id)
                    if topic_id in seen_ids:
                        logger.warning(f"Warning: Duplicate ID {topic_id} found for topic '{topic_name}'")
                    else:
                        seen_ids.add(topic_id)
                        data[topic_id] = topic_name
        # Добавляем специальный топик "0_all"
        all_topic_path = os.path.join(self.path, "0_all")
        if os.path.exists(all_topic_path):
            data[0] = "all"
        return data

    def upd_totals(self):
        """Обновляет _total.txt для каждого топика, включая 0_all."""
        for tid, name in self.data.items():
            if tid == 0:
                topic = Topic(tid, name, self.data)  # 0_all получает все вопросы
            else:
                topic = Topic(tid, name)
            topic.upd_total()

    def choose_topic_id(self, df_user_stats):
        """
        Выбирает топик для 0_all:
        1. Сначала ищет топики с вопросами, которые не имеют оценки A.
        2. Если таких нет, выбирает случайный топик.
        """
        # Исключаем 0_all
        df = df_user_stats[df_user_stats['topic_id'] != 0]
        # Сначала выбираем топики, где есть вопросы НЕ с оценкой A
        filtered_stats = df[df[['N', 'F', 'D', 'C', 'B']].sum(axis=1) > 0]
        if not filtered_stats.empty:
            return filtered_stats.sample(1)['topic_id'].values[0]
        else:
            # Если все вопросы с A, выбираем случайный топик
            return df.sample(1)['topic_id'].values[0]
