import math

async def stepsize_precision(client, symbols):
    # Fetch exchange info asynchronously
    exchange_info = await client.futures_exchange_info()
    
    # Initialize dictionaries to store step sizes and precisions
    stepSizes = {}
    quantityPrecisions = {}
    pricePrecisions = {}
    
    # Process the exchange info for each symbol
    for s in exchange_info['symbols']:
        if s['symbol'] in symbols:
            for f in s['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    stepSizes[s['symbol']] = float(f['stepSize'])
                    quantityPrecisions[s['symbol']] = int(abs(math.log10(float(f['stepSize']))))
                elif f['filterType'] == 'PRICE_FILTER':
                    pricePrecisions[s['symbol']] = int(abs(math.log10(float(f['tickSize']))))

    return stepSizes, quantityPrecisions, pricePrecisions