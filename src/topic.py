import os
import pandas as pd
import src.helpers.pdo as pdo
import src.helpers.fo as fo
from logger import logger
import re
import random


class Topic:
    def __init__(self, tid, name, topics_data=None):
        if tid == 0 and not topics_data:
            raise ValueError('Topic with id=0 doesn\'t have topics_data.')
        self.id = tid
        self.name = name
        self.estimation_order = {'N':0,'F':1,'D':2,'C':3,'B':4,'A':5}
        self.path = f'./data/topics/{tid}_{name}'
        self.f_q_chooses = f'{self.path}/questions/chooses.csv'
        self.f_q_inputs = f'{self.path}/questions/inputs.csv'
        self.d_q_fills = f'{self.path}/questions/fills'
        self.f_total = f'{self.path}/_total.txt' if tid == 0 else f'{self.path}/questions/_total.txt'
        # 0.all topic
        self.qs = self.load_all_questions(topics_data) if self.id == 0 else {
            'choose': self.load_choose_questions(),
            'input': self.load_input_questions(),
            'fill': self.load_fill_questions()
        }
        # theory
        self.theory = '' if self.id == 0 else fo.txt2str(f'{self.path}/theory.txt')

    # === load.all ===================================
    def load_all_questions(self, topics_data):
        """Загружает вопросы из всех тем."""
        questions = {'choose': [], 'input': [], 'fill': []}
        for tid, tname in topics_data.items():
            if tid == 0:
                continue
            topic = Topic(tid, tname)
            for kind in questions.keys():
                questions[kind].extend(topic.qs.get(kind, []))
        return questions

    # === load.choose ===================================
    def load_choose_questions(self):
        df = pdo.load(self.f_q_chooses, allow_empty=True)
        df = df.fillna('')  # Заменяем NaN на пустые строки
        df = df.applymap(lambda x: 0 if isinstance(x, float) and pd.isna(x) else x)  # Убираем NaN
        questions = df.to_dict(orient='records')
        for question in questions:
            question['suspicious_status'] = question.get('suspicious_status', 0) or 0
            question['suspicious_note'] = question.get('suspicious_note', '') or ''
            question['kind'] = 'choose'
        return questions

    # === load.input ===================================
    def load_input_questions(self):
        df = pdo.load(self.f_q_inputs, allow_empty=True)
        df = df.fillna('')  # Убираем NaN из строк
        df = df.applymap(lambda x: 0 if isinstance(x, float) and pd.isna(x) else x)  # Убираем NaN
        questions = df.to_dict(orient='records')
        for question in questions:
            question['question'], question['correct'], question['hints'] = self.format_q_input(question['question'])
            question['suspicious_status'] = question.get('suspicious_status', 0) or 0
            question['suspicious_note'] = question.get('suspicious_note', '') or ''
            question['kind'] = 'input'
        return questions
    def format_q_input(self, question):
        '''
        Ищет [<answer>:<hints>] или [<answer>] в вопросе, заменяет его на '___',
        и возвращает (отформатированный вопрос, правильный ответ, список подсказок).
        '''
        match = re.search(r'\[([^:\]]+)(?::([^]]+))?\]', question)
        if not match:
            raise ValueError('The question does not contain the correct answer in the [answer] or [answer:hints] format.')
        correct = match.group(1)
        hints = match.group(2).split(';') if match.group(2) else []
        formatted_question = question.replace(match.group(0), '___')
        return formatted_question, correct, hints

    # === load.fill ===================================
    def load_fill_questions(self):
        '''Загружает fill-вопросы из файлов и парсит их с учетом пропусков.'''
        questions = []
        for filename in os.listdir(self.d_q_fills):
            name_without_ext = os.path.splitext(filename)[0]  # Убираем расширение
            parts = name_without_ext.split('_')
            if len(parts) != 2:
                raise ValueError(f"Unexpected filename format: {filename}")
            qid, qname = parts
            filepath = os.path.join(self.d_q_fills, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            if not lines:
                raise ValueError(f"File {filename} is empty or incorrectly formatted")
            # Извлечение meta-информации
            meta_match = re.match(r'^\[meta/suspicious_status:(\d),suspicious_note:([\'"])(.*?)\2\]$', lines[0].strip())
            if not meta_match:
                raise ValueError(f"Invalid meta format in file {filename}")
            suspicious_status = int(meta_match.group(1))
            suspicious_note = meta_match.group(3).strip()  # Может быть пустым
            # Убираем meta-строку и обрабатываем оставшийся вопрос
            question_lines = lines[1:]  # Убираем первую строку (meta)
            # Убираем пустые строки только в начале и в конце списка строк
            while question_lines and question_lines[0].strip() == "":
                question_lines.pop(0)  # Убираем пустые строки сверху
            while question_lines and question_lines[-1].strip() == "":
                question_lines.pop()  # Убираем пустые строки снизу
            # Объединяем строки обратно, очищая пробелы в конце строк
            question = "\n".join(line.rstrip() for line in question_lines)
            formatted_question, correct, extra = self.format_q_fill(question)
            questions.append({
                'kind': 'fill',
                'id': qid,
                'name': qname,
                'question': formatted_question,
                'correct': correct,
                'extra': extra,
                'suspicious_status': suspicious_status,
                'suspicious_note': suspicious_note,
            })
        return questions

    def format_q_fill(self, question):
        '''
        Обрабатывает два типа конструкций:
          - [число.ответ] → заменяется на пустое поле
          - [eчисло.ответ] → заменяется на символы Брайля
        Также собирает correct и extra-значения.
        '''
        def replace_correct(match):
            num, answer = match.groups()
            placeholder = '_' * len(f'[{num}.{answer}]')
            return f'<span class="blank m0 p0" data-num="{int(num)}">{placeholder}</span>'
        def replace_extra(match):
            num, answer = match.groups()
            braille_string = ''.join(random.sample('⡾⠧⠼⡍⣾⣿⠹⣟⣯⡿', len(answer)))
            return f'<span class="extra m0 p0 w bg-w" data-num="{int(num)}">{braille_string}</span>'
        # correct
        formatted_question = re.sub(r'\[(\d+)\.(.*?)\]', replace_correct, question)
        correct = sorted(re.findall(r'\[(\d+)\.(.*?)\]', question), key=lambda x: int(x[0]))
        # extra
        formatted_question = re.sub(r'\[e(\d+)\.(.*?)\]', replace_extra, formatted_question)
        extra = sorted(re.findall(r'\[e(\d+)\.(.*?)\]', question), key=lambda x: int(x[0]))
        return formatted_question, correct, extra

    # === common ===================================
    def upd_total(self):
        num_choose = len(self.qs.get('choose', []))
        num_input = len(self.qs.get('input', []))
        num_fill = len(self.qs.get('fill', []))
        total = num_choose + num_input + num_fill
        fo.str2txt(str(total), self.f_total)

    def choose_question(self, df_progress):
        # Объединяем все вопросы в один список, добавляя kind
        questions = []
        for kind, q_list in self.qs.items():
            for q in q_list:
                q['kind'] = kind
                questions.append(q)
        if not questions:
            raise ValueError(f'Topic {self.id} doesn\'t contain questions.')
        df_questions = pd.DataFrame(questions)
        # Фильтруем df_progress по tid
        df_progress4topic = df_progress[df_progress['tid'] == self.id]
        # Создаём ключ для идентификации (qkind + qid)
        df_progress4topic['key'] = df_progress4topic['qkind'] + '_' + df_progress4topic['qid'].astype(str)
        df_questions['key'] = df_questions['kind'] + '_' + df_questions['id'].astype(str)
        # Добавляем недостающие вопросы
        missing_questions = df_questions[~df_questions['key'].isin(df_progress4topic['key'])]
        new_id = df_progress['id'].max(skipna=True) + 1 if not df_progress.empty else 0
        if not missing_questions.empty:
            new_progress = pd.DataFrame({
                'id': range(new_id, new_id + len(missing_questions)),
                'tid': self.id,
                'qkind': missing_questions['kind'].values,
                'qid': missing_questions['id'].values,
                'points': 0,
                'estimation': 'N',
                'asked_at': pd.NaT
            })
            df_progress_combined = pd.concat([df_progress4topic, new_progress], ignore_index=True)
        else:
            df_progress_combined = df_progress4topic.copy()
        # Преобразуем 'estimation' в числовое значение
        df_progress_combined['estimation_numeric'] = df_progress_combined['estimation'].map(self.estimation_order).fillna(0).astype(int)
        # **ШАГ 1: Выбираем вопросы с N, F, D, C, B**
        priority_questions = df_progress_combined[df_progress_combined['estimation'].isin(['N', 'F', 'D', 'C', 'B'])]
        if priority_questions.empty:
            # **ШАГ 2: Если нет, пробуем A**
            priority_questions = df_progress_combined[df_progress_combined['estimation'] == 'A']
        if priority_questions.empty:
            raise ValueError(f"No suitable questions found in topic {self.id}.")
        # перемешиваем, сортируем по asked_at, nat идут первыми, но в случайном порядке
        priority_questions = priority_questions.sample(frac=1, random_state=None)
        priority_questions = priority_questions.sort_values(by='asked_at', ascending=True, na_position='first')
        # Берём первый (самый старый, но перемешанный среди NaT)
        return priority_questions.iloc[0]

    def get_question(self, tid, qkind, qid):
        '''
        Получает вопрос указанного типа из self.qs.
        Для q_fill работает с обычным списком, а не с DataFrame.
        '''
        if qkind not in self.qs:
            raise ValueError(f'Invalid question type "{qkind}" for topic {tid}.')
        # q_fill
        if qkind == 'fill':
            question = next((q for q in self.qs['fill'] if q['id'] == str(qid)), None)
            if not question:
                raise ValueError(f'Question ID {qid} not found in topic {tid} (type "{qkind}").')
            return pdo.convert_int64(question)
        # Для остальных типов работаем с DataFrame
        df_questions = pd.DataFrame(self.qs[qkind])
        if df_questions.empty:
            raise ValueError(f'No questions found in topic {tid} for type "{qkind}".')
        question = df_questions[df_questions['id'] == qid]
        if question.empty:
            raise ValueError(f'Question ID {qid} not found in topic {tid} (type "{qkind}").')
        data = question.iloc[0].fillna('').to_dict()
        if qkind == 'choose':
            # Перемешиваем опции для 'choose'
            options = [opt.strip() for opt in data['options'].split(';')]
            random.shuffle(options)
            data['options'] = options
            # Подготавливаем правильные ответы
            correct = [opt.strip() for opt in data['correct'].split(';')]
            data['correct'] = sorted(correct)
        return pdo.convert_int64(data)

    def reset_suspicious_questions(self):
        """Сбрасывает suspicious_status = 0 у исправленных вопросов."""
        for qkind, q_list in self.qs.items():
            for q in q_list:
                if q.get('suspicious_status') == 2:
                    self.update_question_suspicious(qkind, q['id'], 0, "")
    def update_question_suspicious(self, qkind, qid, status, note):
        """Обновляет suspicious_status и suspicious_note в файле с вопросами."""
        file_map = {'choose': self.f_q_chooses, 'input': self.f_q_inputs, 'fill': self.d_q_fills}

        if qkind not in file_map:
            raise ValueError(f"Некорректный тип вопроса: {qkind}")

        if qkind == 'fill':
            # Получаем qname из загруженных вопросов
            question = next((q for q in self.qs['fill'] if q['id'] == str(qid)), None)
            if not question:
                raise KeyError(f"Вопрос с id={qid} не найден в разделе 'fill'")
            
            qname = question['name']
            question_file = f"{self.d_q_fills}/{qid}_{qname}.txt"
            
            if not os.path.exists(question_file):
                raise FileNotFoundError(f"Файл вопроса не найден: {question_file}")
            
            with open(question_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines or not lines[0].startswith("[meta/"):
                raise ValueError(f"Некорректный формат файла вопроса: {question_file}")
            
            lines[0] = f"[meta/suspicious_status:{status},suspicious_note:'{note}']\n"
            
            with open(question_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)

        else:
            df = pdo.load(file_map[qkind], allow_empty=True)
            if df.empty or 'id' not in df.columns:
                raise ValueError(f"Файл данных {file_map[qkind]} пуст или не содержит колонку 'id'")
            
            exists = df['id'] == qid
            if not exists.any():
                raise KeyError(f"Вопрос с id={qid} не найден в файле {file_map[qkind]}")
            
            df.loc[exists, ['suspicious_status', 'suspicious_note']] = [status, note]
            pdo.save(df, file_map[qkind])

        return True
