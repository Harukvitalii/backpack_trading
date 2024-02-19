import ccxt.pro as ccxt
import asyncio, os 
from dotenv import load_dotenv
load_dotenv()


class CEX: # CEXClient
    cex_pairs = {}
    
    def __init__(self, tickets: list[str] = []):
        self.exchange = ccxt.okx({
            'apiKey': os.getenv('CEX_API'),
            'secret': os.getenv('CEX_SECRET'),
            'password': os.getenv('PASSWORD'),  # Для деяких бірж потрібен
        })
        self.tickets = [tiket.replace('_', '/') for tiket in tickets]


    async def watch_one_orderbook(self, exchange_spot, symbol):
        # a call cost of 1 in the queue of subscriptions
        # means one subscription per exchange.rateLimit milliseconds
        your_delay = 0.1
        await exchange_spot.throttle(your_delay)
        while True:
            try:
                orderbook = await exchange_spot.watch_order_book(symbol)
                self.save_pair_info(exchange_spot.id, symbol, float(orderbook['asks'][0][0]), float(orderbook['bids'][0][0]))
            except Exception as e:
                print(type(e).__name__, str(e))


    async def watch_some_orderbooks(self, exchange_spot, symbol_list):
        loops = [self.watch_one_orderbook(exchange_spot, symbol) for symbol in symbol_list]
        # let them run, don't for all tasks cause they execute asynchronously
        # don't print here
        await asyncio.gather(*loops)

    def save_pair_info(self, name, symbol, price_ask: float, price_bid: float): 
        symbol0, symbol1 = symbol.split('/')
        # TO DO ADD LIQUIDITY TO BE MORE THEN AMOUNT 
        if name not in self.cex_pairs: 
            self.cex_pairs[name] = {}
        
        if symbol0 in self.cex_pairs[name] and symbol1 in self.cex_pairs[name][symbol0]:
            self.cex_pairs[name][symbol0][symbol1] = price_bid
        else:
            if symbol0 not in self.cex_pairs[name]:
                self.cex_pairs[name][symbol0] = {}
            self.cex_pairs[name][symbol0][symbol1] = {}
            self.cex_pairs[name][symbol0][symbol1] = price_bid
            
        if symbol1 in self.cex_pairs[name] and symbol0 in self.cex_pairs[name][symbol1]:
            self.cex_pairs[name][symbol1][symbol0] = 1/price_ask
        else:
            if symbol1 not in self.cex_pairs[name]:
                self.cex_pairs[name][symbol1] = {}
            self.cex_pairs[name][symbol1][symbol0] = {}
            self.cex_pairs[name][symbol1][symbol0] = 1/price_ask
        
    
    async def spot_short_with_margin(self, symbol, amount, price):
        code = 'BTC'
        amount = 1
        currency = self.exchange.currency(code)
        try:
            response = await self.exchange.sapi_post_margin_loan({
                'asset': currency['id'],
                'amount': self.exchange.currency_to_precision(code, amount)
            })
            print(response)
        except ccxt.InsufficientFunds as e:
            print('sapi_post_margin_loan() failed – not enough funds')
            print(e)
        except Exception as e:
            print('sapi_post_margin_loan() failed')
            print(e)

    async def main(self,):
        exchange_spot = self.exchange
        await exchange_spot.load_markets()
        await self.watch_some_orderbooks(exchange_spot, self.tickets)


# asyncio.run(CEX().main())