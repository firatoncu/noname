import math

def stepsize_precision(client, symbols):
# Adım büyüklükleri ve hassasiyetleri al
    exchange_info = client.futures_exchange_info()
    stepSizes = {}
    quantityPrecisions = {}
    pricePrecisions = {}
    for s in exchange_info['symbols']:
        if s['symbol'] in symbols:
            for f in s['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    stepSizes[s['symbol']] = float(f['stepSize'])
                    quantityPrecisions[s['symbol']] = int(abs(math.log10(float(f['stepSize']))))
                elif f['filterType'] == 'PRICE_FILTER':
                    pricePrecisions[s['symbol']] = int(abs(math.log10(float(f['tickSize']))))

    return stepSizes, quantityPrecisions, pricePrecisions