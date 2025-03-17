import pandas as pd
import os
import sys
from datetime import datetime

def generate_trade_log(df, log_filename='trade_log.csv'):
    """
    df üzerinde gezinerek her işlem için giriş/çıkış zamanlarını, işlem süresini ve realized pnl'i tespit eder
    ve sonuçları bir CSV dosyasına kaydeder.
    
    Parametreler:
    - df: Backtesting stratejinizin ürettiği DataFrame (en az 'open_time', 'position', 'realized_pnl' sütunlarını içermelidir)
    - log_filename: Oluşturulacak log dosyasının adı (varsayılan: 'trade_log.csv')
    
    Returns:
    - log_df: Oluşturulan işlem loglarının yer aldığı DataFrame
    """
    logs = []
    current_trade = None  # Mevcut işlem bilgilerini tutan sözlük

    # DataFrame satırları arasında gezinme
    for i in range(len(df)):
        row = df.iloc[i]
        pos = row['position']
        
        # İşlem açık değilse ve pozisyon açılıyorsa, işlem girişini kaydet
        if current_trade is None and pos is not None:
            current_trade = {
                'entry_time': row['open_time'],
                'entry_realized_pnl': row['realized_pnl'],
                'trade_type': pos  # 'long' veya 'short'
            }
        elif current_trade is not None:
            # İşlem devam ederken pozisyon kapanıyor (None oluyor) veya pozisyon türü değişiyorsa (switch)
            if pd.isna(pos) or pos is None:
                # İşlem kapanmış: çıkış zamanı, realized pnl farkı ve işlem süresi hesaplanır
                exit_time = row['open_time']
                exit_realized_pnl = row['realized_pnl']
                trade_pnl = exit_realized_pnl - current_trade['entry_realized_pnl']
                logs.append({
                    'trade_type': current_trade['trade_type'],
                    'entry_time': current_trade['entry_time'],
                    'exit_time': exit_time,
                    'realized_pnl': trade_pnl
                })
                current_trade = None
            elif pos != current_trade['trade_type']:
                # Pozisyon değiştirilmiş: Önce mevcut işlemi, bir önceki satırı çıkış olarak kabul edip kapatıyoruz
                prev_row = df.iloc[i - 1]
                exit_time = prev_row['open_time']
                exit_realized_pnl = prev_row['realized_pnl']
                trade_pnl = exit_realized_pnl - current_trade['entry_realized_pnl']
                logs.append({
                    'trade_type': current_trade['trade_type'],
                    'entry_time': current_trade['entry_time'],
                    'exit_time': exit_time,
                    'realized_pnl': trade_pnl
                })
                # Aynı satırda yeni işlem açılıyor:
                current_trade = {
                    'entry_time': row['open_time'],
                    'entry_realized_pnl': row['realized_pnl'],
                    'trade_type': pos
                }
    
    # Döngü sonunda hâlâ açık bir işlem varsa, son satırdaki zamanı çıkış olarak kabul ediyoruz
    if current_trade is not None:
        last_row = df.iloc[-1]
        exit_time = last_row['open_time']
        exit_realized_pnl = last_row['realized_pnl']
        trade_pnl = exit_realized_pnl - current_trade['entry_realized_pnl']
        logs.append({
            'trade_type': current_trade['trade_type'],
            'entry_time': current_trade['entry_time'],
            'exit_time': exit_time,
            'realized_pnl': trade_pnl
        })
    
    # Log kayıtlarını DataFrame'e çevir ve CSV dosyasına yaz
    log_df = pd.DataFrame(logs)



#   Get the current time
    current_time = datetime.now()
    current_time = current_time.strftime('%Y%m%d_%H%M%S')

    log_filename = f"{current_time}_{log_filename}"
    if getattr(sys, 'frozen', False):  # PyInstaller ile derlenmişse
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))  # Geliştirme ortamı için
        exe_dir = os.path.dirname(exe_dir)
        exe_dir = os.path.dirname(exe_dir) # app.py'nin bulunduğu dizin
    
    result_dir = os.path.join(exe_dir, "backtesting_results/")
    result_  = os.path.join(result_dir, log_filename)

    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    log_df.to_csv(result_, index=False)
    print(f"Saved to '{result_}'.")
    return log_df

# Örneğin, backtesting stratejinizden elde ettiğiniz df ile:
# df = futures_strategy(....)
# trade_log_df = generate_trade_log(df)
