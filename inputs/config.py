from dotenv import  load_dotenv
import os 
load_dotenv()

THREADS = 1  # Enter amount of threads
CUSTOM_DELAY = (1, 2)  # delay before every TRADE in seconds

NEEDED_TRADE_VOLUME = 0  # volume to trade, if 0 it will never stop
MIN_BALANCE_TO_LEFT = 11  # min amount to left on the balance, if 0, it is traded until the balance is equal to 0.

TRADE_AMOUNT = (1, 2)  # minimum and maximum amount to trade in USD, if 0 it will trade on FULL balance
ALLOWED_ASSETS = ["SOL_USDC", "PYTH_USDC", "JTO_USDC", "BONK_USDC", "JUP_USDC"]


BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')













###################################### left empty
ACCOUNTS_FILE_PATH = "inputs/accounts.txt"
PROXIES_FILE_PATH = "inputs/proxies.txt"
