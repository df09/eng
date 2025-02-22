import re
import sys
import os
import random
import pandas as pd
from collections import defaultdict
import src.helpers.fo as fo
import src.helpers.pdo as pdo
import src.helpers.colors as c
from src.helpers.cmd import cmd

class Pronouns:
    def __init__(self):
        # fs
        self.path = 'data/pronouns'
        self.f_data = f'{self.path}/_data.yml'
        self.f_questions = f'{self.path}/questions.csv'
        self.f_suspicious = f'{self.path}/suspicious.txt'
        # prepare data
        self.data = fo.yml2dict(self.f_data)
        self.validate_data(self.data)
        self.df_questions = self.data2questions(self.data)
        self.validate_questions(self.df_questions)
        pdo.save(self.df_questions, self.f_questions)
        # run logic
        self.estimate_ranges = {'F': [0,2], 'D': [3,5], 'C': [6,9], 'B': [10,14], 'A': 15}

    # validate data
    def validate_data(self, data):
        pronoun_duplicates = self.get_duplicated_pronouns(data)
        if pronoun_duplicates:
            print("Duplicated pronouns found:")
            for pronoun, classes in pronoun_duplicates.items():
                print(f"{pronoun}: {'; '.join(classes)}")
            exit()
        translation_duplicates = self.get_duplicated_translations(data)
        if translation_duplicates:
            print("Duplicated translations found:")
            for translation, classes in translation_duplicates.items():
                print(f"{translation}: {'; '.join(classes)}")
            exit()
        return True
    def get_duplicated_pronouns(self, data):
        pronoun_occurrences = defaultdict(list)
        for pronoun_class, pronoun_details in data.items():
            for pronoun in pronoun_details.keys():
                pronoun_occurrences[pronoun].append(pronoun_class)
        return {key: value for key, value in pronoun_occurrences.items() if len(value) > 1}
    def get_duplicated_translations(self, data):
        translation_occurrences = defaultdict(list)
        for pronoun_class, pronoun_details in data.items():
            for pronoun, details in pronoun_details.items():
                translation = details.get("translation", "")
                if translation:
                    translations = [t.strip() for t in translation.split(',')]
                    for trans in translations:
                        translation_occurrences[trans].append(f"{pronoun_class} - {pronoun}")
        return {key: value for key, value in translation_occurrences.items() if len(value) > 1}
    def validate_questions(self, df_questions):
        for index,q in df_questions.iterrows():
            i = q['id']
            pronoun_clean, _ = self.split_by_brakets(q['pronoun'])
            example_eng = q['example_eng']
            matches = re.findall(rf'\b{re.escape(pronoun_clean)}\b', example_eng, flags=re.IGNORECASE)
            if len(matches) == 0:
                print(f'pronoun не найден. id {i}, pronoun {pronoun}')
                exit()
            elif len(matches) > 1:
                print(f'pronoun найдено несколько раз. id {i}, pronoun {pronoun}')
                exit()

    # prepare df_batch
    def data2questions(self, data):
        rows = []  # Список для строк таблицы
        id_counter = 0  # Уникальный идентификатор
        for category, pronouns in data.items():
            category_eng, category_ru = self.split_by_brakets(category)
            for pronoun, details in pronouns.items():
                ipa = details.get('ipa', '')
                translation = details.get('translation', '')
                number = details.get('number', '')
                person = details.get('person', '')
                examples = details.get('examples', [])
                pronoun_clean, pronoun_details = self.split_by_brakets(pronoun)
                translation_clean, translation_details = self.split_by_brakets(translation)
                for example in examples:
                    rows.append({
                        'id': id_counter,
                        'category_eng': category_eng,
                        'category_ru': category_ru,
                        'pronoun': pronoun,
                        'pronoun_clean': pronoun_clean,
                        'pronoun_details': pronoun_details,
                        'ipa': ipa,
                        'translation': translation,
                        'translation_clean': translation_clean,
                        'translation_details': translation_details,
                        'number': number,
                        'person': person,
                        'example_eng': example.get('eng', ''),
                        'example_ru': example.get('ru', ''),
                        'is_suspicious': 0
                    })
                    id_counter += 1
        df_questions = pd.DataFrame(rows)
        return df_questions

    # run
    def run(self, user, batch_size=30):
        # prepare input data
        df_progress = user.df_progress_pronouns
        df_batch = self.get_batch(df_progress, batch_size)
        user.data['stats']['pronouns']['total'] = len(self.df_questions)
        user.data['stats']['pronouns']['progress'] = len(df_progress)
        # render stats
        os.system('clear')
        user.render_stats_pronouns()
        # курсор в I-beam
        sys.stdout.write("\033[5 q")
        sys.stdout.flush()
        # df_batch
        previous_i = None
        for index,q in df_batch.iterrows():
            # data
            i = q['id']
            category_eng = q['category_eng']
            category_ru = q['category_ru']
            pronoun = q['pronoun']
            pronoun_clean = q['pronoun_clean']
            pronoun_details = q['pronoun_details']
            ipa = q['ipa']
            translation = q['translation']
            translation_clean = q['translation_clean']
            translation_details = q['translation_details']
            number = q['number']
            person = q['person']
            example_eng = q['example_eng']
            example_ru = q['example_ru']
            estimate = q['estimate']
            points = int(q['points'])
            # render
            pfx = f'{index+1}/{batch_size}(#{i})'.ljust(13)
            q_pfx,q_val,q_sfx = self.split_example_eng(example_eng, pronoun_clean, i)
            pronoun_details = f' ({pronoun_details})' if pronoun_details else ''
            self.render_ask(pfx, q_pfx,translation,q_sfx, pronoun_details)
            answer = input()
            result, is_suspicious, is_prev_suspicious = self.check_answer(answer, pronoun_clean)
            # upd progress, stats
            df_progress, user.data['stats']['pronouns'] = self.apply_result(result, df_progress, user.data['stats']['pronouns'], i, points)
            pdo.save(df_progress, user.f_progress_pronouns)
            fo.dict2yml(user.data, user.f_data)
            # render result
            self.render_result(result, pfx, q_pfx,q_val,q_sfx, ipa, pronoun_details, example_ru, is_suspicious, is_prev_suspicious, i, previous_i)
            previous_i = i
        # canceling
        user.df_progress_pronouns = df_progress
        # user.data = user.data
        c.p('  [y]Press enter to continue..', end='')
        input()
        sys.stdout.write("\033]12;white\007")
        sys.stdout.flush()

    # batch
    def get_batch(self, progress, batch_size):
        # Объединение вопросов с прогрессом
        df = self.df_questions.merge(progress, left_on='id', right_on='question_id', how='left')
        df.drop(columns=['question_id'], inplace=True) # Удаляем лишний столбец question_id
        # df['points'] = df['points'].fillna(0).astype(int)
        # df['points'] = df['points'].fillna(0).infer_objects().astype(int) # Заполняем отсутствующие баллы нулями
        df['points'] = pd.to_numeric(df['points'], errors='coerce').fillna(0).astype(int)
        df['estimate'] = df['points'].apply(self.estimate_points) # Определяем рейтинг (оценку) по диапазонам
        # Сортируем сначала по estimate, затем по id
        order = {'F': 0, 'D': 1, 'C': 2, 'B': 3, 'A': 4}
        df = df.sort_values(by=['estimate', 'id'], key=lambda x: x.map(order))
        # Применяем перемешивание внутри групп
        def shuffle_within_group(group):
            return group.sample(frac=1).reset_index(drop=True)
        df = (
            df.groupby(['points', 'category_eng'], group_keys=False, sort=False)
            .apply(shuffle_within_group)
            .reset_index(drop=True)
        )
        return df.head(batch_size)
    # prepare question
    def split_example_eng(self, example_eng, pronoun_clean, i):
        match = re.search(rf'\b{re.escape(pronoun_clean)}\b', example_eng, flags=re.IGNORECASE)
        start, end = match.span()  # Индексы начала и конца совпадения
        before = example_eng[:start].strip()  # Часть до pronoun_clean
        middle = example_eng[start:end].strip()  # Совпавшая часть (по середине)
        after = example_eng[end:].strip()  # Часть после pronoun_clean
        if self.is_contains_letters(before): before = f'{before} '
        if self.is_contains_letters(after): after = f' {after}'
        return before, middle, after
    def is_contains_letters(self, s):
        return bool(any(char.isalpha() for char in s.strip()))
    # answer
    def check_answer(self, answer, pronoun_clean):
        is_suspicious = True if answer == '?' else False
        is_prev_suspicious = True if answer == '??' else False
        result = True if answer.lower() == pronoun_clean.lower() else False
        return result, is_suspicious, is_prev_suspicious
    # result
    def apply_result(self, result, df_progress, stats_pronouns, i, points):
        # upd points, estimate
        points += 1 if result else -3
        points = max(points, 0)
        estimate = self.estimate_points(points)
        # upd progress, stats
        df_progress = pdo.update(df_progress, {'question_id':i}, {'estimate':estimate, 'points':points}, allow_addnew=True)
        stats_pronouns['total'] = len(self.df_questions)
        stats_pronouns['progress'] = len(df_progress)
        for estimate in ['A', 'B', 'C', 'D', 'F']:
            stats_pronouns[estimate] = int(df_progress['estimate'].value_counts().get(estimate, 0))
        return df_progress, stats_pronouns

    # extra logic
    def split_by_brakets(self, text):
        match = re.match(r'^(.*?)\s*\((.*?)\)$', text.strip())
        if match:
            outside, inside = match.groups()
            return outside.strip(), inside.strip()
        return text.strip(), ''
    def estimate_points(self, points):
        for grade, range_ in self.estimate_ranges.items():
            if range_[0] <= points <= range_[-1]:
                return grade
        return 'F' # Если не попадает в диапазоны

    # render
    def render_ask(self, pfx, q_pfx,translation,q_sfx, pronoun_details):
        c.p(f'  [b]{pfx} Q: [c]{q_pfx}[x]{translation}[c]{q_sfx}[x]{pronoun_details}')
        c.p(' '*(len(pfx)+3)+f'[y]A: ', end='')
    def render_result(self, result, pfx, q_pfx,q_val,q_sfx, ipa, pronoun_details, example_ru, is_suspicious, is_prev_suspicious, i, previous_i):
        def clear_lines(lines=2):
            for _ in range(lines):
                sys.stdout.write("\033[F\033[K")
            sys.stdout.flush()
        def mark_suspicious(text):
            text = str(text).replace('"', '')
            cmd(f'echo "{text}" >> {self.f_suspicious}')
        def print_result():
            c.p(f'  [x]{pfx} [{color}]R: [c]{q_pfx}[{color}]{q_val}[c]{q_sfx} [b]{ipa}[x]{pronoun_details} - {example_ru}')
        def print_suspicious_message(message):
            c.p(' ' * (len(pfx) + 1) + message)
        # main block
        color = 'g' if result else 'r'
        if not is_suspicious and not is_prev_suspicious:
            clear_lines(2)
            print_result()
            return
        if is_suspicious:
            mark_suspicious(f'{i}: {q_pfx+q_val+q_sfx}')
            clear_lines(1)
            print_result()
            print_suspicious_message(f'  [y]S: question ({i}) was marked as suspicious.')
        if is_prev_suspicious:
            mark_suspicious(previous_i)
            clear_lines(2)
            print_result()
            print_suspicious_message(f'  [y]S: previous question ({previous_i}) was marked as suspicious.')
