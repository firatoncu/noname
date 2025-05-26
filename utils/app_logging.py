import logging
import os
import sys


def logger_func():
    # Logging ayarları
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    return logger

def error_logger_func():
    # .exe'nin veya betiğin çalıştığı dizini al
    if getattr(sys, 'frozen', False):  # PyInstaller ile derlenmişse
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))  # Geliştirme ortamı için
        exe_dir = os.path.dirname(exe_dir) # app.py'nin bulunduğu dizin
    
    log_file = os.path.join(exe_dir, 'error.log')

    # Logger nesnesi oluştur
    logger = logging.getLogger('MyErrorLogger')
    
    logger.setLevel(logging.ERROR)  # Yalnızca ERROR ve üstü seviye
    
    # Mevcut handler'ları temizle (konsola yazmayı önlemek için)
    logger.propagate = False
    logger.handlers.clear()
    
    # FileHandler ile log dosyasını ayarla
    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.ERROR)
    
    # Log formatını belirle
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Handler'ı logger'a ekle
    logger.addHandler(handler)
    
    return logger

