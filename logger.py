import logging

# Создаём логгер
log_name = 'main'
logger = logging.getLogger(log_name)
logger.setLevel(logging.DEBUG)

# Проверяем, есть ли уже обработчики (чтобы не дублировались)
if not logger.hasHandlers():
    # Обработчик для записи в файл
    file_handler = logging.FileHandler(log_name+'.log')
    file_handler.setLevel(logging.DEBUG)
    # Формат логов
    formatter = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s: %(message)s")
    file_handler.setFormatter(formatter)
    # Добавляем обработчик в логгер
    logger.addHandler(file_handler)
