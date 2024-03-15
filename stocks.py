import asyncio
import aiohttp
import json
import numpy as np
import matplotlib.pyplot as plt
import threading


class Stocks(threading.Thread):

    def __init__(self, tickers=['SPY'], limit=50):
        threading.Thread.__init__(self)
        self.tickers = tickers
        self.storage = []
        self.limit = limit

        self.url = 'wss://stream.data.alpaca.markets/v2/iex'

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.stockData())

    async def stockData(self):
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.ws_connect(self.url) as client:
                auth = {"action": "auth", "key": "", "secret": ""}
                await client.send_str(json.dumps(auth))

                msg = {"action":"subscribe","trades":self.tickers}
                await client.send_str(json.dumps(msg))

                while True:
                    resp = await client.receive()
                    resp = json.loads(resp.data)

                    if resp[0]['T'] == 't':
                        price = float(resp[0]['p'])
                        volume = float(resp[0]['s'])

                        self.storage.append([price, volume])

                        if len(self.storage) > self.limit:
                            del self.storage[0]


def Indicators(x):
    p, v = np.array(x).T.tolist()
    period = 10
    prices, ma, bb_d, bb_u = [], [], [], []
    for i in range(period, len(p)):
        window = p[i-period:i]
        prices.append(p[i])
        ma.append(float(np.mean(window)))
        sd = float(np.std(window))
        bb_d.append(p[i] - 2*sd)
        bb_u.append(p[i] + 2*sd)

    k = range(len(prices))
    return k, prices, ma, bb_d, bb_u


stocks = Stocks()
stocks.start()

fig = plt.figure(figsize=(9, 5))
ax = fig.add_subplot(111)

limit = 15

while True:
    if len(stocks.storage) > limit:
        x, price, ma, bb_d, bb_u = Indicators(stocks.storage)
        ax.cla()
        ax.plot(x, price, color='red', label='StockPrice')
        ax.plot(x, ma, color='blue', label='MovingAverage')
        ax.plot(x, bb_d, color='orange', label='BBDown')
        ax.plot(x, bb_u, color='orange', label='BBUp')
        ax.legend()
        plt.pause(0.001)
    else:
        print('Ticks left: ', limit - len(stocks.storage))



plt.show()
stocks.join()
