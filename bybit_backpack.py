from core import CEX
from core.backpack_trade import BackpackTrade
from inputs.config import (ACCOUNTS_FILE_PATH, PROXIES_FILE_PATH, THREADS, CUSTOM_DELAY,
                           ALLOWED_ASSETS, NEEDED_TRADE_VOLUME, MIN_BALANCE_TO_LEFT, TRADE_AMOUNT,
                           BOT_TOKEN, CHAT_ID)

import time, os, asyncio, requests
from dotenv import load_dotenv
load_dotenv()



class FuturesArbitrage:
    
    def __init__(self): 
        self.cex = CEX([symbol.replace('USDC', 'USDT') for symbol in ALLOWED_ASSETS])
        self.backpack_pairs = {}


    async def fetch_orderbook_and_save(self, backpack, symbol):
        orderbook = await backpack.get_orderbook(symbol)
        self.save_pair_info('backpack', symbol, float(orderbook['asks'][0][0]), float(orderbook['bids'][-1][0]))
    
    async def fetch_all_orderbooks(self, backpack, symbols):
        await asyncio.gather(*(self.fetch_orderbook_and_save(backpack, symbol) for symbol in symbols))

    async def backpack_parse_prices(self,):
        backpack = BackpackTrade(os.getenv('BACKBACK_API_KEY'), os.getenv('BACKBACK_API_SECRET'), 
                                 None, CUSTOM_DELAY, NEEDED_TRADE_VOLUME, MIN_BALANCE_TO_LEFT,
                                 TRADE_AMOUNT)
        while True:
            time1 = time.time()
            await self.fetch_all_orderbooks(backpack, ALLOWED_ASSETS)
            time2 = time.time()
            # print('Time to parse prices:', time2-time1)
        
    
    def save_pair_info(self, name, symbol, price_ask: float, price_bid: float): 
        symbol0, symbol1 = symbol.split('_')
        # TO DO ADD LIQUIDITY TO BE MORE THEN AMOUNT 
        if name not in self.backpack_pairs: 
            self.backpack_pairs[name] = {}
        
        if symbol0 in self.backpack_pairs[name] and symbol1 in self.backpack_pairs[name][symbol0]:
            self.backpack_pairs[name][symbol0][symbol1] = price_bid
        else:
            if symbol0 not in self.backpack_pairs[name]:
                self.backpack_pairs[name][symbol0] = {}
            self.backpack_pairs[name][symbol0][symbol1] = {}
            self.backpack_pairs[name][symbol0][symbol1] = price_bid
            
        if symbol1 in self.backpack_pairs[name] and symbol0 in self.backpack_pairs[name][symbol1]:
            self.backpack_pairs[name][symbol1][symbol0] = 1/price_ask
        else:
            if symbol1 not in self.backpack_pairs[name]:
                self.backpack_pairs[name][symbol1] = {}
            self.backpack_pairs[name][symbol1][symbol0] = {}
            self.backpack_pairs[name][symbol1][symbol0] = 1/price_ask
        
    
    async def find_arbitrage(self,):
        await asyncio.sleep(2)
        exchange_rate = 1.00  # Заміни на актуальний курс обміну

        while True:
            try:
                backpack_prices = self.backpack_pairs['backpack']
                cex_prices = self.cex.cex_pairs[self.cex.exchange.id]
            except KeyError:
                await asyncio.sleep(1)
                continue
            await asyncio.sleep(0.1)
            
            for symbol in ALLOWED_ASSETS:
                symbol0, symbol1 = symbol.split('_')
                
                # Перевірка наявності пари в обох джерелах
                if symbol0 in cex_prices and symbol0 in backpack_prices:
                    # Переведення ціни backpack в USDT (якщо потрібно)
                    # Порівняння цін
                    if symbol1 == 'USDC':
                        # profit = self.calculate_proift_percentage(1/cex_prices['USDT'][symbol0], backpack_prices[symbol0][symbol1])
                        # if profit > 0.001:
                        #     print(time.time() + f'Arbitrage found for {symbol} with profit of {profit}, buy: {1/cex_prices['USDT'][symbol0]}, sell: {backpack_prices[symbol0][symbol1]}')
                        # else:
                        #     # print(f'No arbitrage found for {symbol}')
                        #     pass
                            
                        
                        profit = self.calculate_proift_percentage(1/backpack_prices[symbol1][symbol0], cex_prices[symbol0]['USDT'])
                        profit_percent = profit*100
                        if profit_percent > 0.01:
                        
                            text = f'Arbitrage found for {symbol} with profit of {profit_percent:.4f}, buy: {1/backpack_prices[symbol1][symbol0]}, sell: {cex_prices[symbol0]['USDT']}'

                            url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}'
                            response = requests.get(url)
                            if response.status_code == 200:
                                print('Повідомлення успішно відправлено!')
                            else:
                                print('Виникла помилка при відправці повідомлення:', response.status_code)
                            print(f'Arbitrage found for {symbol} with profit of {profit_percent:.4f}, buy: {1/backpack_prices[symbol1][symbol0]}, sell: {cex_prices[symbol0]['USDT']}')
                        else:
                            # print(f'No arbitrage found for {symbol}')
                            pass
                            
                    else:
                        # print(f'No arbitrage found for {symbol}')
                        pass

            
    @staticmethod
    def calculate_proift_percentage(buy_price, sell_price):
        return sell_price/buy_price - 1

    async def main(self,):
        await asyncio.gather(*[self.backpack_parse_prices(), self.cex.main(), self.find_arbitrage()])

asyncio.run(FuturesArbitrage().main())