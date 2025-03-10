import sys
import os
import pandas as pd

def renumber_ids(input_file):
    output_file = f"output_{os.path.basename(input_file)}"  # Создаём новый файл с префиксом "output_"

    # Читаем файл построчно
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    header = "id;question;extra;suspicious_status;suspicious_note"
    new_lines = []
    data = []
    
    # Обрабатываем строки
    for line in lines:
        line = line.strip()

        # Если это заголовок, заменяем его на новый порядок колонок
        if line == header:
            new_lines.append("id;suspicious_status;suspicious_note;question;extra")
            continue

        # Оставляем комментарии без изменений
        if line.startswith("#"):
            new_lines.append(line)
            continue

        # Разбиваем строку по `;` и проверяем структуру данных
        parts = line.split(";")
        if len(parts) == 5:
            _, question, extra, suspicious_status, suspicious_note = parts
            data.append([suspicious_status, suspicious_note, question, extra])  # ID добавим позже
        else:
            new_lines.append(line)  # Если формат нарушен, оставляем строку как есть

    # Создаём DataFrame с новыми ID
    if data:
        df = pd.DataFrame(data, columns=["suspicious_status", "suspicious_note", "question", "extra"])
        df.insert(0, "id", range(len(df)))  # Добавляем новый ID (000, 001, ...)
    
        # Конвертируем DataFrame обратно в строки
        new_lines.extend(df.to_csv(sep=";", index=False, header=False).split("\n"))

    # Записываем результат в новый файл
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write("\n".join(filter(None, new_lines)) + "\n")

    print(f"Processed file saved as: {output_file}")

# Запуск скрипта с аргументом (именем входного файла)
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python renumber_ids.py <input_file>")
        sys.exit(1)

    renumber_ids(sys.argv[1])
