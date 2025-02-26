import pandas as pd
import os
import time

def load(csvfile, allow_empty=False, retries=5, delay=0.2):
    """Загружает CSV, ожидая разблокировки файла при временной блокировке."""
    try:
        for attempt in range(retries):
            if not os.path.exists(csvfile):
                raise FileNotFoundError(f"ERROR: CSV file not found: {csvfile}")

            try:
                with open(csvfile, 'r') as f:
                    first_line = f.readline().strip()

                # Проверяем, есть ли заголовки (первая строка не должна быть пустой)
                if not first_line:
                    if attempt < retries - 1:
                        time.sleep(delay)
                        continue
                    raise ValueError(f"File {csvfile} has no valid headers")

                # Пробуем загрузить CSV
                df = pd.read_csv(csvfile, sep=',', quotechar='"', index_col=False)

                # Проверяем, содержит ли файл заголовки (колонки)
                if df.shape[1] == 0:
                    if attempt < retries - 1:
                        time.sleep(delay)
                        continue
                    raise ValueError(f"File {csvfile} has no valid columns")

                # Если файл пуст (нет строк), но содержит заголовки — допускаем, если allow_empty=True
                if df.empty and not allow_empty:
                    raise ValueError(f"File {csvfile} is empty but must contain data")

                # Удаляем пробелы в заголовках
                df.columns = df.columns.str.strip()

                # Проверяем на дубликаты 'id', если колонка существует
                if "id" in df.columns:
                    duplicates = df[df["id"].duplicated()]["id"].tolist()
                    if duplicates:
                        raise ValueError(f"Duplicate IDs found: {duplicates} in {csvfile}")

                # Удаляем пробелы по краям во всех строковых значениях
                df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

                return df

            except (pd.errors.EmptyDataError, PermissionError, OSError):
                # Ошибки могут возникать, если файл заблокирован или временно пуст
                if attempt < retries - 1:
                    time.sleep(delay)
                    continue
                raise ValueError(f"File {csvfile} is temporarily locked or unreadable")

    except FileNotFoundError:
        raise FileNotFoundError(f"ERROR: CSV file not found: {csvfile}")

def save(df, csvfile):
    # Проверяем, существует ли уже колонка 'id'
    if 'id' not in df.columns:
        df_to_save = df.reset_index().rename(columns={'index': 'id'})
    else:
        df_to_save = df
    df_to_save.to_csv(csvfile, index=False)
# filter:select/sort
def filter(df, where=None, where_not=None, sorts=None, allow_empty=False, allow_many=False):
    if where:
        mask = pd.Series(True, index=df.index)
        for col, val in where.items():
            mask &= (df[col] == val)
        df = df[mask]
    if where_not:
        mask_not = pd.Series(True, index=df.index)
        for col, val in where_not.items():
            mask_not &= (df[col] != val)
        df = df[mask_not]
    if where or where_not:
        if df.empty and not allow_empty:
            raise Exception(f'ERROR: no matches found. <addnew> is not allowed.')
        if len(df) > 1 and not allow_many:
            raise Exception(f'ERROR: found more than 1 matches. <many> is not allowed.')
    if sorts:
        sort_columns = list(sorts.keys())
        ascending = [True if sorts[col] == 'up' else False for col in sort_columns]
        df = df.sort_values(by=sort_columns, ascending=ascending)
    return df
# +
def addnew(df, values):
    if isinstance(values, dict):
        values = pd.DataFrame([values])
    elif isinstance(values, pd.Series):
        values = pd.DataFrame([values])
    return pd.concat([df, values], ignore_index=True)
def update(df, where, values, allow_addnew=False, allow_many=False):
    """
    :param where: Словарь условий {column_name: value} для поиска строк.
    :param values: Словарь с обновлениями {column_name: new_value}.
    :param allow_addnew: Разрешить добавление строки, если не найдено совпадений.
    :param allow_many: Разрешить обновление, если найдено более одной строки.
    """
    # mask
    mask = pd.Series(True, index=df.index)
    for col, val in where.items():
        mask &= (df[col] == val)
    matches = df[mask]
    # check
    if matches.empty:
        if not allow_addnew:
            raise Exception(f'ERROR: no matches found. <addnew> is not allowed.')
        return addnew(df, {**where, **values})
    if len(matches) > 1:
        if not allow_many:
            raise Exception(f'ERROR: found more than 1 matches. <many> is not allowed.')
    for key, value in values.items():
        # Check if the value type is compatible with the column type and convert if necessary
        if not pd.api.types.is_dtype_equal(df[key].dtype, pd.Series([value]).dtype):
            value = pd.Series([value]).astype(df[key].dtype).iloc[0]
        df.loc[mask, key] = value
    return df
