import random
from asyncio import sleep
from typing import Optional

from backpack import Backpack

from better_proxy import Proxy
from tenacity import stop_after_attempt, retry, wait_random, retry_if_not_exception_type

from .utils import logger


def to_fixed(number, decimal_places):
    if str(int(float(number))) == str(number):
        return number
    return str(number)[:str(number).index('.') + decimal_places + 1].strip(".")


class BackpackTrade(Backpack):
    ASSETS_INFO = {
        "SOL": {
            'decimal': 2
        },
        "USDC": {
            'decimal': 2
        },
        "PYTH": {
            'decimal': 1
        },
        "JTO": {
            'decimal': 1
        },
        "HNT": {
            'decimal': 1
        },
        "MOBILE": {
            'decimal': 0
        },
        'BONK': {
            'decimal': 0,
        },
        "WIFI": {
            'decimal': 0
        },
        "USDT": {
            'decimal': 0
        },
        "JUP": {
            'decimal': 2
        }
    }

    def __init__(self, api_key: str, api_secret: str, proxy: Optional[str] = None, *args):
        super().__init__(
            api_key=api_key,
            api_secret=api_secret,
            proxy=proxy and Proxy.from_str(proxy.strip()).as_url
        )

        self.delays, self.needed_volume, self.min_balance_to_left, self.trade_amount = args

        self.current_volume: float = 0

    async def start_trading(self, pairs: list[str]):
        try:
            while True:
                pair = random.choice(pairs)
                if await self.trade_worker(pair):
                    break
        except ValueError as e:
            logger.info(e)
        except Exception as e:
            logger.error(e)

        logger.info(f"Finished! Traded volume ~ {self.current_volume:.2f}$")

    async def trade_worker(self, pair: str):
        await self.buy(pair)
        await self.sell(pair)

        if self.needed_volume and self.current_volume > self.needed_volume:
            return True

    async def buy(self, symbol: str):
        side = 'buy'
        token = symbol.split('_')[1]
        price, amount = await self.get_trade_info(symbol, side, token)

        amount = str(float(amount) / float(price))

        await self.trade(symbol, amount, side, price)

    async def sell(self, symbol: str):
        side = 'sell'
        token = symbol.split('_')[0]
        price, amount = await self.get_trade_info(symbol, side, token)

        return await self.trade(symbol, amount, side, price)

    async def get_trade_info(self, symbol: str, side: str, token: str):
        price = await self.get_market_price(symbol, side, 3)
        response = await self.get_balances()
        balances = await response.json()
        amount = balances[token]['available']
        amount_usd = float(amount) * float(price) if side != 'buy' else float(amount)

        if self.trade_amount[1] > 0:
            if self.trade_amount[0] > float(amount):
                raise ValueError(f"Not enough funds to trade. Trade Amount Stopped. Current balance ~ {amount}$")
            elif self.trade_amount[1] > amount_usd:
                self.trade_amount[1] = amount_usd

            amount_usd = random.uniform(*self.trade_amount)
            amount_trade = amount_usd / float(price)

        self.current_volume += amount_usd

        if self.min_balance_to_left > 0 and self.min_balance_to_left >= float(amount) - amount_usd:
            raise ValueError(f"Not enough funds to trade. Min Balance Stopped. Current balance ~ {amount_usd}$")

        return price, amount_trade

    @retry(stop=stop_after_attempt(3), wait=wait_random(2, 5), reraise=True,
           retry=retry_if_not_exception_type(ValueError))
    async def trade(self, symbol: str, amount: str, side: str, price: str):
        decimal = BackpackTrade.ASSETS_INFO.get(symbol.split('_')[0].upper(), {}).get('decimal', 0)
        fixed_amount = to_fixed(amount, decimal)

        if fixed_amount == "0":
            raise ValueError("Not enough funds to trade!")

        response = await self.execute_order(symbol, side, order_type="limit", quantity=fixed_amount, price=price)
        logger.debug(f"Side: {side} | Price: {price} | Amount: {fixed_amount} | Response: {await response.text()}")
        result = await response.json()

        if result.get("createdAt"):
            logger.info(f"{side.capitalize()} {fixed_amount} {symbol}. "
                        f"Traded volume: {self.current_volume:.2f}$")

            await self.custom_delay()

            return True

        raise ValueError(f"Failed to trade! Check logs for more info. Response: {await response.text()}")

    async def get_market_price(self, symbol: str, side: str, depth: int = 1):
        response = await self.get_order_book_depth(symbol)
        orderbook = await response.json()
        # print(json.dumps(orderbook, indent=4))

        return orderbook['asks'][depth][0] if side == 'buy' else orderbook['bids'][-depth][0]

    async def get_orderbook(self, symbol: str):
        response = await self.get_order_book_depth(symbol)
        orderbook = await response.json()
        # print(json.dumps(orderbook, indent=4))

        return orderbook

    async def custom_delay(self):
        if self.delays[1] > 0:
            sleep_time = random.uniform(*self.delays)
            logger.info(f"Sleep for {sleep_time:.2f} seconds")
            await sleep(sleep_time)
