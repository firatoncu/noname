import logging

def logger_func():
    # Logging ayarları
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    return logger

def error_logger_func():
    # Logging ayarları
    logging.basicConfig(
    filename='error.log',           # Logların yazılacağı dosya adı
    level=logging.ERROR,           # Yalnızca ERROR ve üstü seviye logları yaz
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log formatı
)
    error_logger = logging.getLogger(__name__)

    return error_logger