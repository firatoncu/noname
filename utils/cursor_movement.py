import sys


def move_cursor_up(lines):
    sys.stdout.write(f"\033[{lines}A")

def logger_move_cursor_up(i = 1):
    move_cursor_up(i)
    save_cursor_position()
    restore_cursor_position()

def clean_line(i = 1):
    for line in range(i):
        print("                                                                                                                                                                           ")
    move_cursor_up(i)
    save_cursor_position()
    restore_cursor_position()


def save_cursor_position():
    sys.stdout.write("\033[s")

def restore_cursor_position():
    sys.stdout.write("\033[u")

# Terminalde satırları güncelleyen fonksiyon
def update_terminal(lines):
    print("\033[H\033[J", end="")  # Terminali temizler (ANSI escape code)
    for line in lines:
        print(line)