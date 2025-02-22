import src.helpers.fo as fo
import src.helpers.pdo as pdo
from src.helpers.cmd import cmd
import os
from logger import logger
import pandas as pd


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
        return data
