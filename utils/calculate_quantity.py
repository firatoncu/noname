import math

# Adım büyüklüğüne uygun miktar hesaplama
def calculate_quantity(position_value, close_price, step_size, precision):
    raw_Q = position_value / close_price
    Q = math.floor(raw_Q / step_size) * step_size
    return round(Q, precision)