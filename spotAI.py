import time
import json
import logging
import threading
import random
import requests
import asyncio
import hmac
import hashlib
import urllib.parse
import queue
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
import pandas as pd
import pandas_ta as ta
import google.generativeai as genai
import os
from dotenv import load_dotenv

print("Script starting...")
print(f"Current working directory: {os.getcwd()}")

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv_success = load_dotenv(dotenv_path=dotenv_path, verbose=True)
print(f"Trying to load .env from: {dotenv_path}")
print(f"load_dotenv() executed. Did it find and load a .env file? -> {load_dotenv_success}")

TELEGRAM_BOT_TOKEN_FROM_ENV = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY_FROM_ENV = os.getenv("GEMINI_API_KEY")
ADMIN_USER_IDS_FROM_ENV = os.getenv("ADMIN_USER_IDS")
BINANCE_API_KEY_FROM_ENV = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET_FROM_ENV = os.getenv("BINANCE_API_SECRET")

print(f"Value of TELEGRAM_BOT_TOKEN from os.getenv: '{TELEGRAM_BOT_TOKEN_FROM_ENV}'")
print(f"Value of GEMINI_API_KEY from os.getenv: '{GEMINI_API_KEY_FROM_ENV}'")
print(f"Value of ADMIN_USER_IDS from os.getenv: '{ADMIN_USER_IDS_FROM_ENV}'")
print(f"Value of BINANCE_API_KEY from os.getenv: '{BINANCE_API_KEY_FROM_ENV}'")
print(f"Value of BINANCE_API_SECRET from os.getenv: '{BINANCE_API_SECRET_FROM_ENV}'")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
ADMIN_USER_IDS_STR = os.getenv("ADMIN_USER_IDS", "123456789")
ADMIN_USER_IDS = []
if ADMIN_USER_IDS_STR and ADMIN_USER_IDS_STR != "123456789":
    try:
        ADMIN_USER_IDS = [int(admin_id.strip()) for admin_id in ADMIN_USER_IDS_STR.split(',') if admin_id.strip()]
    except ValueError:
        logger.error(f"ADMIN_USER_IDS ('{ADMIN_USER_IDS_STR}') contains non-integer values or is not a comma-separated list of numbers. Please check your .env file.")
        ADMIN_USER_IDS = []
elif ADMIN_USER_IDS_STR == "123456789" and ADMIN_USER_IDS_FROM_ENV == "123456789":
     logger.warning("ADMIN_USER_IDS is using the default placeholder value. Ensure it is set correctly if you need specific admin users.")
     ADMIN_USER_IDS = [int(admin_id.strip()) for admin_id in ADMIN_USER_IDS_STR.split(',') if admin_id.strip()]


BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "YOUR_BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "YOUR_BINANCE_API_SECRET")
BINANCE_API_URL = "https://api.binance.com"
BINANCE_TEST_API_URL = "https://testnet.binance.vision"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")

print(f"Final TELEGRAM_BOT_TOKEN variable for script: '{TELEGRAM_BOT_TOKEN}'")
print(f"Final GEMINI_API_KEY variable for script: '{GEMINI_API_KEY}'")
print(f"Final ADMIN_USER_IDS_STR for script: '{ADMIN_USER_IDS_STR}'")
print(f"Final ADMIN_USER_IDS for script: {ADMIN_USER_IDS}")
print(f"Final BINANCE_API_KEY for script: '{BINANCE_API_KEY}'")
print(f"Final BINANCE_API_SECRET for script: '{BINANCE_API_SECRET}'")


if not TELEGRAM_BOT_TOKEN_FROM_ENV:
    logger.critical("CRITICAL: TELEGRAM_BOT_TOKEN was not found by os.getenv after attempting to load .env. Likely .env file not found/readable or key is missing/empty in .env. Exiting.")
    exit()
elif TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
    logger.critical("CRITICAL: TELEGRAM_BOT_TOKEN is still the default placeholder value. This means it was not set correctly in your .env file or the .env file was not loaded. Exiting.")
    exit()


gemini_model = None
if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
        logger.info("Gemini AI Model configured successfully.")
    except Exception as e:
        logger.error(f"Failed to configure Gemini AI: {e}. AI features will be disabled.")
        gemini_model = None
else:
    if not GEMINI_API_KEY_FROM_ENV:
        logger.warning("WARNING: GEMINI_API_KEY was not found by os.getenv after attempting to load .env. AI features will be disabled.")
    elif GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        logger.warning("WARNING: GEMINI_API_KEY is the default placeholder value. This means it was not set in your .env file or the .env file was not loaded. AI features will be disabled.")
    else:
        logger.warning("WARNING: GEMINI_API_KEY not set or is placeholder (reason unclear from direct checks). AI features will be disabled.")
    gemini_model = None

logger.info("Initial configuration and checks complete. Continuing with bot setup...")


# --- END NEW: Gemini AI Configuration ---

# --- MULTI-LANGUAGE SUPPORT ---
translations = {}
user_languages = {}  # Stores chat_id: lang_code
DEFAULT_LANGUAGE = "en"

def _load_translations():
    global translations
    for lang_code in ["en", "id"]:
        try:
            with open(f"lang_{lang_code}.json", "r", encoding="utf-8") as f:
                translations[lang_code] = json.load(f)
            logger.info(f"Successfully loaded lang_{lang_code}.json")
        except FileNotFoundError:
            logger.error(f"Error: lang_{lang_code}.json not found.")
            if lang_code == DEFAULT_LANGUAGE:
                logger.critical(f"Default language file {DEFAULT_LANGUAGE}.json missing. Bot may not function correctly.")
                # Fallback to a minimal set of English strings if default is missing
                translations[DEFAULT_LANGUAGE] = {"welcome_message": "Welcome!", "error_processing_request": "Error processing request."}
        except json.JSONDecodeError:
            logger.error(f"Error: lang_{lang_code}.json is not valid JSON.")
            if lang_code == DEFAULT_LANGUAGE:
                 translations[DEFAULT_LANGUAGE] = {"welcome_message": "Welcome!", "error_processing_request": "Error processing request."}
        except Exception as e:
            logger.error(f"An unexpected error occurred loading lang_{lang_code}.json: {e}")
            if lang_code == DEFAULT_LANGUAGE:
                 translations[DEFAULT_LANGUAGE] = {"welcome_message": "Welcome!", "error_processing_request": "Error processing request."}

_load_translations() # Load at startup

def _get_user_language(chat_id):
    return user_languages.get(chat_id, DEFAULT_LANGUAGE)

def _set_user_language(chat_id, lang_code):
    if lang_code in translations:
        user_languages[chat_id] = lang_code
        return True
    return False

def _t(key, chat_id_or_lang, **kwargs):
    lang_code = ""
    if isinstance(chat_id_or_lang, (int, str)) and str(chat_id_or_lang).isdigit(): # it's a chat_id
        lang_code = _get_user_language(int(chat_id_or_lang))
    elif isinstance(chat_id_or_lang, str) and chat_id_or_lang in translations: # it's a lang_code
        lang_code = chat_id_or_lang
    else:
        lang_code = DEFAULT_LANGUAGE

    if lang_code not in translations or key not in translations[lang_code]:
        # Fallback to English if key not found in user's language or if lang_code is invalid
        if DEFAULT_LANGUAGE in translations and key in translations[DEFAULT_LANGUAGE]:
            translated_string = translations[DEFAULT_LANGUAGE][key]
            logger.warning(f"Translation key '{key}' not found for lang '{lang_code}'. Fell back to '{DEFAULT_LANGUAGE}'.")
        else:
            # Ultimate fallback: return the key itself
            logger.error(f"Translation key '{key}' not found for lang '{lang_code}' AND not in default lang '{DEFAULT_LANGUAGE}'.")
            return key
    else:
        translated_string = translations[lang_code][key]

    try:
        return translated_string.format(**kwargs)
    except KeyError as e_format:
        logger.error(f"Formatting error for key '{key}' in lang '{lang_code}': Missing placeholder {e_format}. String: '{translated_string}'")
        return translated_string # Return unformatted string
    except Exception as e_gen_format:
        logger.error(f"General formatting error for key '{key}' in lang '{lang_code}': {e_gen_format}. String: '{translated_string}'")
        return translated_string

# --- END MULTI-LANGUAGE SUPPORT ---


# Trading modes
TRADING_MODES = {
    "conservative_scalp": {
        "take_profit": 0.5,
        "stop_loss": 0.8,
        "max_trade_time": 180,
        "volume_threshold": 250,
        "price_change_threshold": 0.15,
        "max_trades": 6,
        "description_key": "trading_modes_desc_conservative_scalp" # Placeholder for description key
    },
    "consistent_drip": {
        "take_profit": 1.0,
        "stop_loss": 0.8,
        "max_trade_time": 450,
        "volume_threshold": 150,
        "price_change_threshold": 0.3,
        "max_trades": 4,
        "description_key": "trading_modes_desc_consistent_drip"
    },
    "balanced_growth": {
        "take_profit": 2.0,
        "stop_loss": 1.5,
        "max_trade_time": 900,
        "volume_threshold": 80,
        "price_change_threshold": 0.5,
        "max_trades": 3,
        "description_key": "trading_modes_desc_balanced_growth"
    },
    "momentum_rider": {
        "take_profit": 3.5,
        "stop_loss": 2.0,
        "max_trade_time": 1800,
        "volume_threshold": 50,
        "price_change_threshold": 0.8,
        "max_trades": 2,
        "description_key": "trading_modes_desc_momentum_rider"
    },
    # Add description_key for ai_dynamic_mode if you make it a formal mode
}
# Add a placeholder for AI dynamic mode description if needed, or handle it separately
if DEFAULT_LANGUAGE in translations: # Add English descriptions directly for simplicity if not in JSON
    translations[DEFAULT_LANGUAGE]["trading_modes_desc_conservative_scalp"] = "Very conservative scalping, small profit targets, tight SL, needs high liquidity. R/R ~1:1.5"
    translations[DEFAULT_LANGUAGE]["trading_modes_desc_consistent_drip"] = "Aims for small, consistent profits with a tight SL. R/R ~1:1.25"
    translations[DEFAULT_LANGUAGE]["trading_modes_desc_balanced_growth"] = "Balanced approach, moderate profit targets with controlled risk. R/R ~1:1.33"
    translations[DEFAULT_LANGUAGE]["trading_modes_desc_momentum_rider"] = "Attempts to catch small momentums/trends, larger TP, controlled SL. R/R ~1:1.75"
    translations[DEFAULT_LANGUAGE]["trading_modes_desc_ai_dynamic"] = "Parameters (TP, SL, Time) are dynamically set by AI based on market analysis."


# Bot configuration
CONFIG = {
    "api_key": BINANCE_API_KEY,
    "api_secret": BINANCE_API_SECRET,
    "trading_pair": "BNBUSDT",
    "amount": 0.01,
    "use_percentage": False,
    "trade_percentage": 5.0,
    "take_profit": 1.5,
    "stop_loss": 5.0,
    "trading_enabled": False, # Default to False for safety
    "whale_detection": True,
    "whale_threshold": 100,
    "auto_trade_on_whale": False,
    "trading_strategy": "follow_whale",
    "safety_mode": True,
    "trading_mode": "balanced_growth", # Default mode
    "max_trade_time": 300,
    "auto_select_pairs": True,
    "min_volume": 100,
    "min_price_change": 1.0,
    "max_concurrent_trades": 3,
    "market_update_interval": 30,
    "use_testnet": True, # Default to Testnet for safety
    "use_real_trading": False,
    "mock_mode": True, # If use_real_trading is False, mock_mode is usually True
    "daily_loss_limit": 5.0,
    "daily_profit_target": 2.5,
    "min_bnb_per_trade": 0.011,
    "ai_dynamic_mode": False, # NEW: AI Dynamic mode
    "ai_advice_cache_duration": 300 # NEW: Cache AI advice for 5 minutes (in seconds)
}

# Active trades
ACTIVE_TRADES = []
COMPLETED_TRADES = []

# Daily statistics
DAILY_STATS = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "total_trades": 0,
    "winning_trades": 0,
    "losing_trades": 0,
    "total_profit_pct": 0.0,
    "total_profit_bnb": 0.0,
    "starting_balance": 0.0,
    "current_balance": 0.0
}

# Mock whale transactions
MOCK_WHALE_TRANSACTIONS = []

# Initial mock market data
INITIAL_MARKET_DATA = [
    {"pair": "SOLBNB", "volume": 5882.66, "quote_volume": 1609.2, "price_change": 4.59, "last_price": 0.2735},
    {"pair": "ALTBNB", "volume": 2184.30, "quote_volume": 137.4, "price_change": 11.33, "last_price": 0.0000629},
    {"pair": "SIGNBNB", "volume": 793.73, "quote_volume": 117.1, "price_change": -0.29, "last_price": 0.00014760},
    {"pair": "FETBNB", "volume": 759.47, "quote_volume": 100.4, "price_change": 6.53, "last_price": 0.001322},
    {"pair": "XRPBNB", "volume": 704.39, "quote_volume": 271.7, "price_change": 1.68, "last_price": 0.003858},
    {"pair": "BNBUSDT", "volume": 12500.45, "quote_volume": 3817687.9, "price_change": 2.3, "last_price": 305.42},
]
ADDITIONAL_PAIRS = [
    {"pair": "DOGEBNB", "volume": 0, "quote_volume": 0, "price_change": 0, "last_price": 0.00012},
    {"pair": "ADABNB", "volume": 0, "quote_volume": 0, "price_change": 0, "last_price": 0.00095},
]

# --- NEW: AI Advice Cache ---
ai_advice_cache = {} # { "PAIR": {"timestamp": time.time(), "advice": {...}} }
# --- END NEW: AI Advice Cache ---

class BinanceAPI:
    def __init__(self, config, chat_id_for_translation=None): # chat_id for error messages
        self.config = config
        self.api_key = config["api_key"]
        self.api_secret = config["api_secret"]
        self.base_url = BINANCE_TEST_API_URL if config["use_testnet"] else BINANCE_API_URL
        self.chat_id = chat_id_for_translation if chat_id_for_translation else (ADMIN_USER_IDS[0] if ADMIN_USER_IDS else None)


    def _generate_signature(self, data):
        query_string = urllib.parse.urlencode(data)
        return hmac.new(self.api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    def _get_headers(self):
        return {'X-MBX-APIKEY': self.api_key}

    def get_exchange_info(self):
        try:
            url = f"{self.base_url}/api/v3/exchangeInfo"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting exchange info: {e}")
            return None
        except json.JSONDecodeError:
            logger.error(_t("error_failed_decode_json", self.chat_id, source="exchange info", response_text=response.text if 'response' in locals() else 'No response'))
            return None

    def get_account_info(self):
        try:
            url = f"{self.base_url}/api/v3/account"
            timestamp = int(time.time() * 1000)
            params = {'timestamp': timestamp}
            params['signature'] = self._generate_signature(params)
            headers = self._get_headers()
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logger.error(_t("error_http_getting_account_info", self.chat_id, http_err=http_err, response_text=response.text))
            return None
        except requests.exceptions.RequestException as e:
            logger.error(_t("error_getting_account_info_generic", self.chat_id, e=e))
            return None
        except json.JSONDecodeError:
            logger.error(_t("error_failed_decode_json", self.chat_id, source="account info", response_text=response.text if 'response' in locals() else 'No response'))
            return None

    def get_ticker_price(self, symbol):
        try:
            url = f"{self.base_url}/api/v3/ticker/price"
            params = {'symbol': symbol}
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            return float(response.json()['price'])
        except requests.exceptions.RequestException as e:
            logger.error(_t("error_getting_ticker_price", self.chat_id, symbol=symbol, e=e))
            return None
        except (KeyError, ValueError, json.JSONDecodeError):
            logger.error(_t("error_parse_ticker_price", self.chat_id, symbol=symbol, response_text=response.text if 'response' in locals() else 'No response'))
            return None

    def get_ticker_24hr(self, symbol=None):
        try:
            url = f"{self.base_url}/api/v3/ticker/24hr"
            params = {}
            if symbol:
                params['symbol'] = symbol
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(_t("error_getting_24hr_ticker", self.chat_id, e=e))
            return None
        except json.JSONDecodeError:
            logger.error(_t("error_failed_decode_json", self.chat_id, source="24hr ticker", response_text=response.text if 'response' in locals() else 'No response'))
            return None

    def create_order(self, symbol, side, order_type, quantity=None, price=None, time_in_force=None):
        request_params_for_log = {}
        try:
            url = f"{self.base_url}/api/v3/order"
            timestamp = int(time.time() * 1000)
            params = {'symbol': symbol, 'side': side, 'type': order_type, 'timestamp': timestamp}

            if quantity is not None:
                # This formatting should be improved by fetching stepSize from exchangeInfo
                formatted_quantity = f"{float(quantity):.8f}".rstrip('0').rstrip('.')
                params['quantity'] = formatted_quantity

            if order_type != 'MARKET':
                if price is not None:
                    formatted_price = f"{float(price):.8f}".rstrip('0').rstrip('.')
                    params['price'] = formatted_price
                if time_in_force:
                    params['timeInForce'] = time_in_force
            
            request_params_for_log = params.copy()
            params['signature'] = self._generate_signature(params)

            logger.info(f"Sending order to Binance: URL={url}, Params (pre-signature)={request_params_for_log}")
            response = requests.post(url, params=params, headers=self._get_headers(), timeout=15)
            logger.info(f"Binance order response: Status={response.status_code}, Text={response.text}")

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(_t("error_failed_create_order_binance", self.chat_id,
                                symbol=symbol, status_code=response.status_code,
                                response_text=response.text, sent_params=request_params_for_log))
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"error_message": response.text, "status_code": response.status_code}
        except Exception as e:
            logger.error(_t("error_exception_creating_order", self.chat_id,
                            symbol=symbol, e=e, sent_params=request_params_for_log), exc_info=True)
            return None

    def get_open_orders(self, symbol=None):
        try:
            url = f"{self.base_url}/api/v3/openOrders"
            timestamp = int(time.time() * 1000)
            params = {'timestamp': timestamp}
            if symbol:
                params['symbol'] = symbol
            params['signature'] = self._generate_signature(params)
            response = requests.get(url, params=params, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(_t("error_getting_open_orders", self.chat_id, e=e))
            return None
        except json.JSONDecodeError:
            logger.error(_t("error_failed_decode_json", self.chat_id, source="open orders", response_text=response.text if 'response' in locals() else 'No response'))
            return None

    def cancel_order(self, symbol, order_id):
        try:
            url = f"{self.base_url}/api/v3/order"
            timestamp = int(time.time() * 1000)
            params = {'symbol': symbol, 'orderId': order_id, 'timestamp': timestamp}
            params['signature'] = self._generate_signature(params)
            response = requests.delete(url, params=params, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(_t("error_canceling_order", self.chat_id, order_id=order_id, symbol=symbol, e=e))
            return None
        except json.JSONDecodeError:
            logger.error(_t("error_failed_decode_json", self.chat_id, source="cancel order", response_text=response.text if 'response' in locals() else 'No response'))
            return None

    def get_order(self, symbol, order_id):
        try:
            url = f"{self.base_url}/api/v3/order"
            timestamp = int(time.time() * 1000)
            params = {'symbol': symbol, 'orderId': order_id, 'timestamp': timestamp}
            params['signature'] = self._generate_signature(params)
            response = requests.get(url, params=params, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(_t("error_getting_order", self.chat_id, order_id=order_id, symbol=symbol, e=e))
            return None
        except json.JSONDecodeError:
            logger.error(_t("error_failed_decode_json", self.chat_id, source="get order", response_text=response.text if 'response' in locals() else 'No response'))
            return None

    def get_all_orders(self, symbol, limit=500):
        try:
            url = f"{self.base_url}/api/v3/allOrders"
            timestamp = int(time.time() * 1000)
            params = {'symbol': symbol, 'limit': limit, 'timestamp': timestamp}
            params['signature'] = self._generate_signature(params)
            response = requests.get(url, params=params, headers=self._get_headers(), timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(_t("error_getting_all_orders", self.chat_id, symbol=symbol, e=e))
            return None
        except json.JSONDecodeError:
            logger.error(_t("error_failed_decode_json", self.chat_id, source="all orders", response_text=response.text if 'response' in locals() else 'No response'))
            return None

    def get_bnb_pairs(self):
        try:
            exchange_info = self.get_exchange_info()
            if not exchange_info: return []
            return [sym['symbol'] for sym in exchange_info['symbols'] if 'BNB' in sym['symbol'] and sym['status'] == 'TRADING']
        except Exception as e:
            logger.error(_t("error_getting_bnb_pairs", self.chat_id, e=e))
            return []

    def get_market_data(self):
        try:
            bnb_pairs_filter = self.get_bnb_pairs()
            if not bnb_pairs_filter:
                logger.warning(_t("warning_no_bnb_pairs_from_exchange", self.chat_id))
                return []
            ticker_data = self.get_ticker_24hr()
            if not ticker_data: return []
            market_data = []
            for ticker in ticker_data:
                if ticker['symbol'] in bnb_pairs_filter:
                    try:
                        market_data.append({
                            'pair': ticker['symbol'],
                            'volume': float(ticker['volume']),
                            'quote_volume': float(ticker.get('quoteVolume', 0)),
                            'price_change': float(ticker['priceChangePercent']),
                            'last_price': float(ticker['lastPrice'])
                        })
                    except (ValueError, TypeError, KeyError) as e:
                        logger.warning(_t("warning_could_not_parse_ticker_data", self.chat_id, symbol=ticker.get('symbol', 'N/A'), e=e, ticker_data=ticker))
            market_data.sort(key=lambda x: x.get('quote_volume', x['volume']), reverse=True)
            return market_data
        except Exception as e:
            logger.error(_t("error_getting_market_data", self.chat_id, e=e), exc_info=True)
            return []

    # --- NEW: Get K-lines for AI ---
    def get_klines(self, symbol, interval='15m', limit=100):
        """Get K-line/candlestick data for a symbol."""
        try:
            url = f"{self.base_url}/api/v3/klines"
            params = {'symbol': symbol, 'interval': interval, 'limit': limit}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            # K-line data format:
            # [
            #   [Open time, Open, High, Low, Close, Volume, Close time, Quote asset volume, Number of trades,
            #    Taker buy base asset volume, Taker buy quote asset volume, Ignore]
            # ]
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting klines for {symbol} interval {interval}: {e}")
            return None
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from klines for {symbol}: {response.text if 'response' in locals() else 'No response'}")
            return None
    # --- END NEW ---

class MarketAnalyzer:
    def __init__(self, config, chat_id_for_translation=None):
        self.config = config
        self.market_data = INITIAL_MARKET_DATA.copy() if config["mock_mode"] else []
        self.last_update = 0
        self.update_interval = config["market_update_interval"]
        self.update_thread = None
        self.running = False
        self.lock = threading.Lock()
        self.chat_id = chat_id_for_translation if chat_id_for_translation else (ADMIN_USER_IDS[0] if ADMIN_USER_IDS else None)
        self.binance_api = BinanceAPI(config, self.chat_id) if config["api_key"] and config["api_secret"] else None


    def start_updating(self):
        if not self.running:
            self.running = True
            self.update_thread = threading.Thread(target=self.update_loop)
            self.update_thread.daemon = True
            self.update_thread.start()
            return True
        return False

    def stop_updating(self):
        if self.running:
            self.running = False
            if self.update_thread and self.update_thread.is_alive():
                self.update_thread.join(timeout=5.0)
            return True
        return False

    def update_loop(self):
        while self.running:
            try:
                self.update_market_data()
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(_t("error_market_update_loop", self.chat_id, e=e), exc_info=True)
                time.sleep(self.update_interval * 2)

    def update_market_data(self):
        with self.lock:
            self.last_update = time.time()
            if self.binance_api and not self.config.get("mock_mode", True):
                real_market_data = self.binance_api.get_market_data()
                if real_market_data:
                    self.market_data = real_market_data
                    logger.info(_t("info_updated_market_data_binance", self.chat_id, count=len(real_market_data)))
                    return
            if self.config.get("mock_mode", True):
                logger.info(_t("info_using_mock_market_data", self.chat_id))
                for pair_data in self.market_data:
                    pair_data["volume"] = max(0, pair_data["volume"] * (1 + random.uniform(-0.05, 0.15)))
                    pair_data["price_change"] += random.uniform(-2, 3)
                    pair_data["last_price"] = max(1e-8, pair_data["last_price"] * (1 + random.uniform(-0.01, 0.02)))
                    pair_data["quote_volume"] = pair_data["volume"] * pair_data["last_price"]
                if random.random() < 0.2 and len(ADDITIONAL_PAIRS) > 0 and len(self.market_data) < 20:
                    new_pair = random.choice(ADDITIONAL_PAIRS).copy()
                    new_pair["volume"] = random.uniform(500, 2000)
                    new_pair["price_change"] = random.uniform(-20, 20)
                    new_pair["last_price"] *= (1 + random.uniform(-0.2, 0.2))
                    new_pair["quote_volume"] = new_pair["volume"] * new_pair["last_price"]
                    if not any(p["pair"] == new_pair["pair"] for p in self.market_data):
                        self.market_data.append(new_pair)
                        logger.info(_t("info_added_mock_trending_pair", self.chat_id, pair_name=new_pair['pair']))
                if len(self.market_data) > 10 and random.random() < 0.3:
                    removed_pair = self.market_data.pop(random.randrange(len(self.market_data)))
                    logger.info(_t("info_removed_mock_low_volume_pair", self.chat_id, pair_name=removed_pair['pair']))

    def get_best_trading_pairs(self, min_volume=None, min_price_change=None, limit=5):
        with self.lock:
            min_vol_val = min_volume if min_volume is not None else self.config.get("min_volume", 100)
            min_price_chg_val = min_price_change if min_price_change is not None else self.config.get("min_price_change", 1.0)
            filtered_pairs = [
                p for p in self.market_data
                if (p['pair'].endswith("BNB") and p.get('quote_volume', 0) >= min_vol_val) or
                   (p['pair'].startswith("BNB") and p.get('volume', 0) >= min_vol_val)
                   and abs(p.get("price_change", 0)) >= min_price_chg_val
            ]
            scored_pairs = []
            for pair_data in filtered_pairs:
                vol_score = pair_data.get('quote_volume', pair_data['volume']) / (1000 if pair_data.get('quote_volume') else 100)
                price_change_score = abs(pair_data.get("price_change", 0)) * 2
                scored_pairs.append((pair_data, vol_score + price_change_score))
            scored_pairs.sort(key=lambda x: x[1], reverse=True)
            return [p for p, _ in scored_pairs[:limit]]

    def get_trending_pairs(self, limit=5):
        with self.lock:
            return sorted([p for p in self.market_data if p.get("price_change") is not None],
                          key=lambda x: abs(x["price_change"]), reverse=True)[:limit]

    def get_high_volume_pairs(self, limit=5):
        with self.lock:
            return sorted([p for p in self.market_data if p.get("volume") is not None],
                          key=lambda x: x.get('quote_volume', x['volume']), reverse=True)[:limit]

    def get_pair_data(self, pair_name):
        with self.lock:
            if self.binance_api and not self.config.get("mock_mode", True):
                ticker_info = self.binance_api.get_ticker_24hr(symbol=pair_name)
                if ticker_info and isinstance(ticker_info, dict):
                    try:
                        return {'pair': ticker_info['symbol'], 'volume': float(ticker_info['volume']),
                                'quote_volume': float(ticker_info.get('quoteVolume',0)),
                                'price_change': float(ticker_info['priceChangePercent']),
                                'last_price': float(ticker_info['lastPrice'])}
                    except (ValueError, TypeError, KeyError) as e:
                        logger.warning(_t("warning_could_not_parse_ticker_data", self.chat_id, symbol=pair_name, e=e, ticker_data=ticker_info))
            for p in self.market_data:
                if p["pair"].lower() == pair_name.lower(): return p.copy()
            return None

class WhaleDetector:
    def __init__(self, config, trading_bot=None, chat_id_for_translation=None):
        self.config = config
        self.trading_bot = trading_bot
        self.running = False
        self.detection_thread = None
        self.last_notification_time = 0
        self.chat_id = chat_id_for_translation if chat_id_for_translation else (ADMIN_USER_IDS[0] if ADMIN_USER_IDS else None)
        self.binance_api = BinanceAPI(config, self.chat_id) if config["api_key"] and config["api_secret"] else None

    def start_detection(self):
        if not self.running:
            self.running = True
            self.detection_thread = threading.Thread(target=self.detection_loop)
            self.detection_thread.daemon = True
            self.detection_thread.start()
            return True
        return False

    def stop_detection(self):
        if self.running:
            self.running = False
            if self.detection_thread and self.detection_thread.is_alive():
                self.detection_thread.join(timeout=5.0)
            return True
        return False

    def detection_loop(self):
        while self.running:
            try:
                if self.config.get("mock_mode", True) and self.config["whale_detection"]:
                    if random.random() < 0.1:
                        whale_transaction = self.generate_mock_whale_transaction()
                        if whale_transaction:
                            MOCK_WHALE_TRANSACTIONS.append(whale_transaction)
                            if time.time() - self.last_notification_time > 30 and self.trading_bot:
                                self.last_notification_time = time.time()
                                whale_message = (
                                    f"{_t('whale_alert_notification_title', self.chat_id)}\n\n"
                                    f"{_t('whale_alert_token', self.chat_id, token=whale_transaction['token'])}\n"
                                    f"{_t('whale_alert_amount', self.chat_id, amount=whale_transaction['amount'], asset_name=whale_transaction['token'].replace('USDT','').replace('BNB',''))}\n"
                                    f"{_t('whale_alert_value', self.chat_id, value=whale_transaction['value'])}\n"
                                    f"{_t('whale_alert_type', self.chat_id, type=whale_transaction['type'])}\n"
                                    f"{_t('whale_alert_time', self.chat_id, time=whale_transaction['time'])}\n\n"
                                    f"{_t('whale_alert_potential_impact', self.chat_id, impact=whale_transaction['impact'])}"
                                )
                                keyboard = [
                                    [InlineKeyboardButton(_t('whale_alert_button_follow', self.chat_id), callback_data=f"follow_whale_{whale_transaction['id']}")],
                                    [InlineKeyboardButton(_t('whale_alert_button_ignore', self.chat_id), callback_data=f"ignore_whale_{whale_transaction['id']}")]
                                ]
                                self.trading_bot.send_notification(whale_message, keyboard, self.chat_id)
                                if self.config["auto_trade_on_whale"]:
                                    self.process_whale_for_trading(whale_transaction)
                time.sleep(10)
            except Exception as e:
                logger.error(_t("error_whale_detection_loop", self.chat_id, e=e), exc_info=True)
                time.sleep(20)

    def generate_mock_whale_transaction(self):
        if not (self.trading_bot and self.trading_bot.market_analyzer and self.trading_bot.market_analyzer.market_data):
            logger.warning(_t("warning_cannot_generate_mock_whale_no_bot_analyzer" if not (self.trading_bot and self.trading_bot.market_analyzer) else "warning_cannot_generate_mock_whale_empty_market_data", self.chat_id))
            return None
        pair_data = random.choice(self.trading_bot.market_analyzer.market_data)
        token, price = pair_data["pair"], pair_data.get("last_price", 0)
        if price == 0: price = (300 + random.uniform(-20, 20)) if "BNB" in token else random.uniform(0.001, 10)
        amount = self.config.get("whale_threshold", 100) * random.uniform(1.0, 10.0)
        value = amount * price
        impact = "LOW"
        if value > 1000000: impact = "HIGH - Likely significant price movement"
        elif value > 500000: impact = "MEDIUM - Possible price impact"
        return {'id': int(time.time()), 'token': token, 'type': random.choice(["BUY", "SELL"]),
                'amount': amount, 'price': price, 'value': value,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'impact': impact}

    def process_whale_for_trading(self, whale_transaction):
        if not self.config["trading_enabled"] or "BNB" not in whale_transaction['token']: return
        if not self.trading_bot:
            logger.warning(_t("warning_cannot_process_whale_no_bot", self.chat_id))
            return
        strategy = self.config["trading_strategy"]
        trade_type = "SELL" if (whale_transaction['type'] == "BUY" and strategy == "counter_whale") or \
                                (whale_transaction['type'] == "SELL" and strategy == "follow_whale") else "BUY"
        self.trading_bot.create_trade_from_whale(whale_transaction, trade_type, is_auto_trade=True, chat_id_for_trade=self.chat_id)

class TradingBot:
    def __init__(self, config, telegram_bot=None):
        self.config = config
        self.telegram_bot = telegram_bot # Instance of TelegramBotHandler
        self.running = False
        self.trading_thread = None
        self.whale_detector = None
        # Use a default admin chat_id for internal API/MarketAnalyzer error reporting if telegram_bot not fully up.
        self.default_chat_id_for_internal_errors = ADMIN_USER_IDS[0] if ADMIN_USER_IDS else None
        self.market_analyzer = MarketAnalyzer(config, self.default_chat_id_for_internal_errors)
        self.trade_monitor_thread = None
        self.notification_queue = queue.Queue()
        self.notification_thread = None
        self.binance_api = BinanceAPI(config, self.default_chat_id_for_internal_errors) if config["api_key"] and config["api_secret"] else None
        self.reset_daily_stats()
        self.ai_advice_cache = {} # { "PAIR": {"timestamp": time.time(), "advice": {...}} }

    def reset_daily_stats(self):
        DAILY_STATS.update({"date": datetime.now().strftime("%Y-%m-%d"), "total_trades": 0, "winning_trades": 0,
                            "losing_trades": 0, "total_profit_pct": 0.0, "total_profit_bnb": 0.0,
                            "starting_balance": 0.0, "current_balance": 0.0})
        if self.binance_api and self.config.get("use_real_trading"):
            try:
                account_info = self.binance_api.get_account_info()
                if account_info and 'balances' in account_info:
                    bnb_balance = next((float(a['free']) + float(a['locked']) for a in account_info['balances'] if a['asset'] == 'BNB'), 0.0)
                    DAILY_STATS.update({"starting_balance": bnb_balance, "current_balance": bnb_balance})
            except Exception as e:
                logger.error(_t("error_getting_balance_daily_stats", self.default_chat_id_for_internal_errors, e=e))


    def set_whale_detector(self, detector):
        self.whale_detector = detector

    def send_notification(self, message, keyboard=None, target_chat_id=None): # target_chat_id for specific user context
        if not self.telegram_bot:
            logger.warning(_t("warning_cannot_send_notification_no_bot", self.default_chat_id_for_internal_errors))
            return
        admin_chats_to_notify = []
        if target_chat_id: # Specific user action response
            admin_chats_to_notify.append(target_chat_id)
        elif hasattr(self.telegram_bot, 'admin_chat_ids') and self.telegram_bot.admin_chat_ids: # General bot notification
            admin_chats_to_notify.extend(self.telegram_bot.admin_chat_ids)
        
        if not admin_chats_to_notify:
             logger.warning(_t("warning_cannot_send_notification_no_admin_ids", self.default_chat_id_for_internal_errors))
             return
        try:
            # Queue tuple: (message, keyboard, list_of_chat_ids_to_send_to)
            self.notification_queue.put((message, keyboard, admin_chats_to_notify))
        except Exception as e:
            logger.error(_t("error_queueing_notification", self.default_chat_id_for_internal_errors, e=e))

    def process_notification_queue(self):
        logger.info(_t("info_notification_queue_processor_start", self.default_chat_id_for_internal_errors))
        ptb_event_loop = None
        if self.telegram_bot and hasattr(self.telegram_bot, 'application') and \
           self.telegram_bot.application and hasattr(self.telegram_bot.application, 'bot') and \
           self.telegram_bot.application.bot and hasattr(self.telegram_bot.application.bot, '_loop'): # Note: _loop is internal
            ptb_event_loop = self.telegram_bot.application.bot._loop
        else:
            logger.info(_t("info_ptb_event_loop_not_accessible_notif", self.default_chat_id_for_internal_errors))

        while True:
            try:
                item = self.notification_queue.get(block=True)
                if item is None:
                    logger.info(_t("info_notification_queue_processor_stop_signal", self.default_chat_id_for_internal_errors))
                    self.notification_queue.task_done()
                    break
                message, keyboard, chat_ids_to_notify = item
                logger.debug(f"Processing notification from queue: {message[:30]}... for chat_ids: {chat_ids_to_notify}")

                if not (self.telegram_bot and hasattr(self.telegram_bot, 'application') and
                        self.telegram_bot.application and hasattr(self.telegram_bot.application, 'bot') and
                        self.telegram_bot.application.bot):
                    logger.error(_t("error_notification_telegram_send_init", self.default_chat_id_for_internal_errors))
                    self.notification_queue.task_done()
                    time.sleep(1)
                    continue
                
                if ptb_event_loop is None and hasattr(self.telegram_bot.application.bot, '_loop'):
                    ptb_event_loop = self.telegram_bot.application.bot._loop
                    if ptb_event_loop: logger.info(_t("info_ptb_event_loop_acquired_notification", self.default_chat_id_for_internal_errors))

                for chat_id in chat_ids_to_notify:
                    coro_sent_async = False
                    if ptb_event_loop:
                        try:
                            coro = self.telegram_bot.application.bot.send_message(
                                chat_id=chat_id, text=message,
                                reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
                                parse_mode=ParseMode.HTML # Assuming messages might contain HTML
                            )
                            future = asyncio.run_coroutine_threadsafe(coro, ptb_event_loop)
                            future.result(timeout=20)
                            coro_sent_async = True
                        except asyncio.TimeoutError:
                            logger.error(_t("error_notification_timeout_async", chat_id, chat_id=chat_id))
                        except Exception as e_async:
                            logger.error(_t("error_notification_failed_async", chat_id, chat_id=chat_id, type_name=type(e_async).__name__, e=e_async))
                    
                    if not coro_sent_async:
                        try:
                            logger.info(_t("info_using_fallback_notification", chat_id, chat_id=chat_id))
                            token = self.telegram_bot.token
                            url = f"https://api.telegram.org/bot{token}/sendMessage"
                            payload = {'chat_id': chat_id, 'text': message, 'parse_mode': ParseMode.HTML}
                            if keyboard:
                                payload['reply_markup'] = json.dumps({'inline_keyboard': keyboard})
                            response = requests.post(url, json=payload, timeout=15)
                            if response.status_code == 200:
                                logger.info(_t("info_sent_notification_fallback_success", chat_id, chat_id=chat_id))
                            else:
                                logger.error(_t("error_notification_fallback_failed", chat_id, chat_id=chat_id, status_code=response.status_code, response_text=response.text))
                        except Exception as e_fallback:
                            logger.error(_t("error_notification_fallback_exception", chat_id, chat_id=chat_id, e_fallback=e_fallback))
                self.notification_queue.task_done()
                time.sleep(0.25)
            except Exception as e_outer:
                logger.error(_t("error_notification_queue_outer_loop", self.default_chat_id_for_internal_errors, e=e_outer), exc_info=True)
                if 'item' in locals() and item is not None:
                    try: self.notification_queue.task_done()
                    except ValueError: pass
                time.sleep(5)
        logger.info(_t("info_notification_queue_processor_finished", self.default_chat_id_for_internal_errors))

    def start_trading(self, chat_id_context=None): # chat_id for notifications related to starting
        if not self.running:
            if self.config.get("use_real_trading", False):
                logger.info(_t("info_real_trading_enabled_forcing_mock_off", chat_id_context or self.default_chat_id_for_internal_errors))
                self.config["mock_mode"] = False
                if self.market_analyzer: self.market_analyzer.config["mock_mode"] = False
                if self.whale_detector: self.whale_detector.config["mock_mode"] = False
            self.running = True
            self.apply_trading_mode_settings(chat_id_context or self.default_chat_id_for_internal_errors)
            if self.market_analyzer: self.market_analyzer.start_updating()

            self.trading_thread = threading.Thread(target=self.trading_loop, args=(chat_id_context,))
            self.trading_thread.daemon = True
            self.trading_thread.start()

            self.trade_monitor_thread = threading.Thread(target=self.monitor_trades_loop, args=(chat_id_context,))
            self.trade_monitor_thread.daemon = True
            self.trade_monitor_thread.start()
            
            if self.notification_thread is None or not self.notification_thread.is_alive():
                self.notification_thread = threading.Thread(target=self.process_notification_queue)
                self.notification_thread.daemon = True
                self.notification_thread.start()

            if self.config.get("whale_detection", False) and self.whale_detector:
                self.whale_detector.start_detection()
            self.reset_daily_stats()
            logger.info(_t("info_trading_bot_started", chat_id_context or self.default_chat_id_for_internal_errors,
                            real_trading=self.config.get('use_real_trading'), mock_mode=self.config.get('mock_mode')))
            return True
        logger.info(_t("info_trading_bot_already_running_or_fail", chat_id_context or self.default_chat_id_for_internal_errors))
        return False

    def stop_trading(self, chat_id_context=None):
        if self.running:
            self.running = False
            if self.market_analyzer: self.market_analyzer.stop_updating()
            if self.whale_detector: self.whale_detector.stop_detection()
            if self.trading_thread and self.trading_thread.is_alive(): self.trading_thread.join(timeout=5.0)
            if self.trade_monitor_thread and self.trade_monitor_thread.is_alive(): self.trade_monitor_thread.join(timeout=5.0)
            if self.notification_thread and self.notification_thread.is_alive():
                try:
                    self.notification_queue.put(None)
                    self.notification_thread.join(timeout=5.0)
                except Exception as e:
                    logger.error(_t("error_stopping_notification_thread", chat_id_context or self.default_chat_id_for_internal_errors, e=e))
            logger.info(_t("info_trading_bot_stopped", chat_id_context or self.default_chat_id_for_internal_errors))
            return True
        logger.info(_t("info_trading_bot_already_stopped", chat_id_context or self.default_chat_id_for_internal_errors))
        return False

    def apply_trading_mode_settings(self, chat_id_context=None):
        mode = self.config.get("trading_mode", "balanced_growth")
        if self.config.get("ai_dynamic_mode"): # AI mode overrides manual mode settings for TP/SL/Time
            logger.info(_t("trading_modes_ai_dynamic_mode_enabled", chat_id_context or self.default_chat_id_for_internal_errors))
            # TP/SL/MaxTime will be set per trade by AI
        elif mode in TRADING_MODES:
            mode_settings = TRADING_MODES[mode]
            self.config.update({
                "take_profit": mode_settings["take_profit"], "stop_loss": mode_settings["stop_loss"],
                "max_trade_time": mode_settings["max_trade_time"],
                "min_volume": mode_settings.get("volume_threshold", self.config.get("min_volume")),
                "min_price_change": mode_settings.get("price_change_threshold", self.config.get("min_price_change")),
                "max_concurrent_trades": mode_settings["max_trades"]
            })
            logger.info(_t("info_applied_trading_mode", chat_id_context or self.default_chat_id_for_internal_errors, mode=mode))
        else:
            logger.warning(_t("warning_trading_mode_not_found_using_default", chat_id_context or self.default_chat_id_for_internal_errors, mode=mode))

    def _format_trade_notification(self, trade, selection_detail_text, notification_type_key, chat_id):
        real_trade_status_key = "trade_status_real_no_sim"
        order_id_val = trade.get('order_id')
        if order_id_val:
            if trade.get('real_trade_filled'): real_trade_status_key = "trade_status_real_yes_filled"
            elif trade.get('real_trade_opened'): real_trade_status_key = "trade_status_real_yes_opened"
            else: real_trade_status_key = "trade_status_real_yes_failed_on_binance"
        elif self.config.get("use_real_trading"):
            real_trade_status_key = "trade_status_real_yes_failed_pre_binance"
        
        real_trade_status = _t(real_trade_status_key, chat_id, order_id=order_id_val)

        # For AI trades, include rationale
        ai_rationale = ""
        if trade.get("ai_rationale"):
            ai_rationale = f"\nAI Rationale: {trade['ai_rationale']}"

        return _t(notification_type_key, chat_id,
                  pair=trade['pair'], type=trade['type'], entry_price=trade['entry_price'],
                  amount=trade['amount'], base_asset=trade['base_asset'],
                  bnb_value=trade.get('bnb_value_of_trade', 0),
                  take_profit=trade['take_profit'], stop_loss=trade['stop_loss'],
                  max_time_seconds=trade['max_time_seconds'], entry_time=trade['entry_time'],
                  mode=trade.get('mode', 'N/A').capitalize(),
                  selection_detail_text=selection_detail_text,
                  strategy=trade.get('strategy','N/A'), # For whale trades
                  bnb_value_of_trade=trade.get('bnb_value_of_trade', 0), # For whale trades
                  real_trade_status=real_trade_status) + ai_rationale


    def check_daily_limits(self, chat_id_context=None):
        if DAILY_STATS["starting_balance"] > 0 and self.config.get("use_real_trading"):
            current_profit_pct = (DAILY_STATS["current_balance"] - DAILY_STATS["starting_balance"]) / DAILY_STATS["starting_balance"] * 100
            profit_target = self.config.get("daily_profit_target", 10.0)
            loss_limit = self.config.get("daily_loss_limit", 5.0)
            if current_profit_pct >= profit_target:
                logger.info(_t("info_daily_profit_target_reached", chat_id_context or self.default_chat_id_for_internal_errors, current_profit_pct=current_profit_pct, profit_target=profit_target))
                self.send_notification(_t("daily_stats_notification_profit_target_reached", chat_id_context or self.default_chat_id_for_internal_errors, current_profit_pct=current_profit_pct, profit_target=profit_target), target_chat_id=chat_id_context)
                return False
            if current_profit_pct <= -loss_limit:
                logger.info(_t("info_daily_loss_limit_reached", chat_id_context or self.default_chat_id_for_internal_errors, current_profit_pct=current_profit_pct, loss_limit=loss_limit))
                self.send_notification(_t("daily_stats_notification_loss_limit_reached", chat_id_context or self.default_chat_id_for_internal_errors, current_loss_pct=current_profit_pct, loss_limit=loss_limit), target_chat_id=chat_id_context)
                return False
        return True

    def trading_loop(self, chat_id_context=None): # Pass chat_id for context specific notifications
        while self.running:
            try:
                if not self.config.get("trading_enabled", False):
                    time.sleep(5)
                    continue
                if not self.check_daily_limits(chat_id_context):
                    logger.info(_t("info_daily_limits_reached_pausing", chat_id_context or self.default_chat_id_for_internal_errors))
                    self.config["trading_enabled"] = False
                    time.sleep(3600)
                    continue
                
                active_trades_count = sum(1 for t in ACTIVE_TRADES if not t.get('completed', False))
                if active_trades_count >= self.config.get("max_concurrent_trades", 3):
                    time.sleep(3)
                    continue

                if self.config.get("auto_select_pairs", True) and self.market_analyzer:
                    best_pairs = self.market_analyzer.get_best_trading_pairs(
                        min_volume=self.config.get("min_volume"),
                        min_price_change=self.config.get("min_price_change"), limit=3)
                    if best_pairs:
                        selected_pair_data = random.choice(best_pairs)
                        pair_name = selected_pair_data["pair"]
                        if any(t['pair'] == pair_name and not t.get('completed', False) for t in ACTIVE_TRADES):
                            time.sleep(1)
                            continue
                        trade_type = "BUY" if selected_pair_data.get("price_change", 0) > 0 else "SELL"
                        if random.random() < 0.3:
                            logger.info(_t("info_attempt_auto_create_trade", chat_id_context or self.default_chat_id_for_internal_errors, pair_name=pair_name, trade_type=trade_type))
                            trade = self.create_trade(pair_name, trade_type, selected_pair_data.get("last_price"), chat_id_for_trade=chat_id_context)
                            if trade:
                                selection_details = f"Vol: {selected_pair_data.get('quote_volume', selected_pair_data.get('volume',0)):.2f}, Chg: {selected_pair_data.get('price_change',0):.2f}%"
                                entry_message = self._format_trade_notification(trade, selection_details, "trade_notification_new_auto_selected", chat_id_context or self.default_chat_id_for_internal_errors)
                                self.send_notification(entry_message, target_chat_id=chat_id_context) # Send to specific user if context exists
                time.sleep(random.uniform(4, 7))
            except Exception as e:
                logger.error(_t("error_trading_loop", chat_id_context or self.default_chat_id_for_internal_errors, e=e), exc_info=True)
                time.sleep(10)

    def monitor_trades_loop(self, chat_id_context=None):
        while self.running:
            try:
                current_active_trades = [t for t in ACTIVE_TRADES if not t.get('completed', False)]
                for trade in current_active_trades:
                    current_time = time.time()
                    trade_duration = current_time - trade.get('timestamp', current_time)
                    current_price = None
                    if trade.get('real_trade_filled') and self.binance_api and self.config.get("use_real_trading"):
                        current_price = self.binance_api.get_ticker_price(trade['pair'])
                        if current_price is None:
                            logger.warning(_t("warning_failed_get_real_price_fallback_simulated", chat_id_context or self.default_chat_id_for_internal_errors, pair=trade['pair']))
                            current_price = self.simulate_price_movement(trade)
                    else:
                        current_price = self.simulate_price_movement(trade)
                    if current_price is None: continue

                    tp_hit = (trade['type'] == "BUY" and current_price >= trade['take_profit']) or \
                             (trade['type'] == "SELL" and current_price <= trade['take_profit'])
                    sl_hit = (trade['type'] == "BUY" and current_price <= trade['stop_loss']) or \
                             (trade['type'] == "SELL" and current_price >= trade['stop_loss'])
                    time_limit_reached = trade_duration >= trade.get('max_time_seconds', 300)

                    if tp_hit: self.complete_trade(trade, current_price, "take_profit", chat_id_context)
                    elif sl_hit: self.complete_trade(trade, current_price, "stop_loss", chat_id_context)
                    elif time_limit_reached: self.complete_trade(trade, current_price, "time_limit", chat_id_context)
                time.sleep(1)
            except Exception as e:
                logger.error(_t("error_trade_monitor_loop", chat_id_context or self.default_chat_id_for_internal_errors, e=e), exc_info=True)
                time.sleep(5)

    def simulate_price_movement(self, trade):
        elapsed_time = time.time() - trade.get('timestamp', time.time())
        max_time = trade.get('max_time_seconds', 300)
        if max_time == 0: max_time = 300
        time_factor = min(elapsed_time / max_time, 1.0)
        mode_vol_factor = {"conservative_scalp": 0.7, "consistent_drip": 0.8, "balanced_growth": 1.0, "momentum_rider": 1.2}.get(trade.get('mode', 'balanced_growth'), 1.0)
        max_movement_pct = 1.5 * time_factor * mode_vol_factor
        movement_pct = random.uniform(-max_movement_pct, max_movement_pct)
        current_price = trade.get('entry_price',0) * (1 + movement_pct / 100)
        return max(1e-8, current_price)

    # --- NEW: AI Integration Methods ---
    def _calculate_indicators(self, klines_df):
        """Calculates indicators from klines DataFrame."""
        indicators = {}
        if klines_df.empty or len(klines_df) < 20: # Need enough data for most indicators
            logger.warning(_t("warning_ai_not_enough_data_for_indicators", self.default_chat_id_for_internal_errors, pair=klines_df.name if hasattr(klines_df, 'name') else 'N/A', count=len(klines_df)))
            return indicators

        try:
            # RSI
            rsi = klines_df.ta.rsi(length=14)
            if rsi is not None and not rsi.empty:
                indicators['rsi'] = rsi.iloc[-1]

            # EMA (e.g., 20-period)
            ema = klines_df.ta.ema(length=20)
            if ema is not None and not ema.empty:
                indicators['ema20'] = ema.iloc[-1]
            
            # Bollinger Bands
            bbands = klines_df.ta.bbands(length=20, std=2)
            if bbands is not None and not bbands.empty:
                indicators['bb_lower'] = bbands['BBL_20_2.0'].iloc[-1]
                indicators['bb_middle'] = bbands['BBM_20_2.0'].iloc[-1]
                indicators['bb_upper'] = bbands['BBU_20_2.0'].iloc[-1]
                indicators['bb_width'] = (indicators['bb_upper'] - indicators['bb_lower']) / indicators['bb_middle'] * 100 if indicators['bb_middle'] else 0
        except Exception as e:
            logger.error(f"Error calculating indicators for {klines_df.name if hasattr(klines_df, 'name') else 'DataFrame'}: {e}")
        return indicators

    def get_ai_trade_advice(self, pair_name, chat_id_context=None):
        """Gets trading advice (TP, SL, MaxTime) from Gemini AI."""
        if not gemini_model:
            logger.warning("Gemini model not available, AI advice skipped.")
            return None

        # Check cache
        cache_key = f"ai_advice_{pair_name}"
        cached_item = self.ai_advice_cache.get(cache_key)
        if cached_item and (time.time() - cached_item['timestamp'] < self.config.get("ai_advice_cache_duration", 300)):
            logger.info(_t("info_ai_mode_using_cached", chat_id_context or self.default_chat_id_for_internal_errors, pair=pair_name, seconds_left=int(self.config.get("ai_advice_cache_duration", 300) - (time.time() - cached_item['timestamp']))))
            return cached_item['advice']

        logger.info(_t("info_ai_mode_update_attempt", chat_id_context or self.default_chat_id_for_internal_errors, pair=pair_name))

        # 1. Fetch K-lines
        klines_data = self.binance_api.get_klines(symbol=pair_name, interval='15m', limit=100) # 100 candles * 15m = ~1 day
        if not klines_data or len(klines_data) < 20: # Need enough data for indicators
            logger.warning(_t("warning_ai_no_klines", chat_id_context or self.default_chat_id_for_internal_errors, pair=pair_name, interval='15m'))
            return None

        # Convert to DataFrame
        columns = ['OpenTime', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTime', 
                   'QuoteAssetVolume', 'NumberTrades', 'TakerBuyBaseVol', 'TakerBuyQuoteVol', 'Ignore']
        df = pd.DataFrame(klines_data, columns=columns)
        df[['Open', 'High', 'Low', 'Close', 'Volume', 'QuoteAssetVolume']] = df[['Open', 'High', 'Low', 'Close', 'Volume', 'QuoteAssetVolume']].apply(pd.to_numeric)
        df['OpenTime'] = pd.to_datetime(df['OpenTime'], unit='ms')
        df['CloseTime'] = pd.to_datetime(df['CloseTime'], unit='ms')
        df.set_index('CloseTime', inplace=True) # Set time as index for pandas_ta
        df.name = pair_name # Store pair name for logging in indicator calculation

        # 2. Calculate Indicators
        indicators = self._calculate_indicators(df.copy()) # Pass a copy
        current_price = df['Close'].iloc[-1]

        # 3. Construct Prompt for Gemini
        prompt = f"""You are an expert crypto trading analyst. Your task is to suggest optimal parameters for a short-term (scalp/day trade) on the pair {pair_name}.
Current market conditions for {pair_name}:
- Current Price: {current_price:.6f}
- Recent Candlestick Data (last 5 candles, OHLCV):
"""
        for i in range(1, min(6, len(df))):
            candle = df.iloc[-i]
            prompt += f"  - T-{i}: O={candle['Open']:.4f}, H={candle['High']:.4f}, L={candle['Low']:.4f}, C={candle['Close']:.4f}, V={candle['Volume']:.2f}\n"
        
        prompt += "- Technical Indicators:\n"
        if 'rsi' in indicators: prompt += f"  - RSI(14): {indicators['rsi']:.2f} "
        if 'ema20' in indicators: prompt += f"(Price vs EMA20: {'Above' if current_price > indicators['ema20'] else 'Below' if current_price < indicators['ema20'] else 'At'})\n"
        if 'bb_middle' in indicators:
            prompt += f"  - Bollinger Bands(20,2): Lower={indicators['bb_lower']:.4f}, Middle={indicators['bb_middle']:.4f}, Upper={indicators['bb_upper']:.4f} (Width: {indicators.get('bb_width',0):.2f}%)\n"

        prompt += f"""
Based on this data, suggest:
1. Take Profit (TP) as a percentage from current price (e.g., 0.5 for 0.5%). Range: 0.3% to 5%.
2. Stop Loss (SL) as a percentage from current price (e.g., 0.8 for 0.8%). Range: 0.3% to 5%. SL should generally be tighter or equal to TP.
3. Maximum Trade Time in seconds (e.g., 300 for 5 minutes). Range: 60 to 1800 seconds.
4. A very brief (1-2 sentence) rationale for your suggestion.

Consider the volatility and recent trend. The goal is a quick, profitable trade.

Respond ONLY in JSON format like this:
{{
  "tp_percentage": float (e.g., 1.2),
  "sl_percentage": float (e.g., 0.8),
  "max_trade_time_seconds": int (e.g., 600),
  "rationale": "string"
}}
"""
        logger.info(_t("info_ai_generated_comprehensive_summary", chat_id_context or self.default_chat_id_for_internal_errors, pair=pair_name))
        # logger.debug(f"Gemini Prompt for {pair_name}:\n{prompt}") # Can be very verbose

        # 4. Call Gemini API
        try:
            response = gemini_model.generate_content(prompt)
            # Clean the response: Gemini sometimes wraps JSON in ```json ... ```
            cleaned_response_text = response.text.strip()
            if cleaned_response_text.startswith("```json"):
                cleaned_response_text = cleaned_response_text[7:]
            if cleaned_response_text.endswith("```"):
                cleaned_response_text = cleaned_response_text[:-3]
            
            advice = json.loads(cleaned_response_text)

            # Validate advice structure and types
            if not all(k in advice for k in ["tp_percentage", "sl_percentage", "max_trade_time_seconds", "rationale"]):
                raise ValueError("Missing keys in AI advice")
            if not isinstance(advice["tp_percentage"], (float, int)) or \
               not isinstance(advice["sl_percentage"], (float, int)) or \
               not isinstance(advice["max_trade_time_seconds"], int):
                raise ValueError("Incorrect data types in AI advice")

            # Further validation of ranges (optional, but good practice)
            advice["tp_percentage"] = max(0.1, min(10.0, float(advice["tp_percentage"])))
            advice["sl_percentage"] = max(0.1, min(10.0, float(advice["sl_percentage"])))
            advice["max_trade_time_seconds"] = max(60, min(3600, int(advice["max_trade_time_seconds"])))

            logger.info(_t("info_ai_trade_advice_received", chat_id_context or self.default_chat_id_for_internal_errors,
                            pair=pair_name, tp=advice['tp_percentage'], sl=advice['sl_percentage'], rationale=advice['rationale']))
            
            # Cache the successful advice
            self.ai_advice_cache[cache_key] = {"timestamp": time.time(), "advice": advice}
            return advice
        except json.JSONDecodeError as e_json:
            logger.error(f"AI Error: Failed to decode JSON from Gemini for {pair_name}. Response: '{response.text if 'response' in locals() else 'N/A'}'. Error: {e_json}")
        except ValueError as e_val: # Custom validation errors
             logger.error(f"AI Error: Invalid advice structure or values from Gemini for {pair_name}. Error: {e_val}. Response: '{response.text if 'response' in locals() else 'N/A'}'")
        except Exception as e:
            logger.error(f"AI Error: Exception during Gemini API call or processing for {pair_name}: {e}")
        
        logger.warning(_t("warning_ai_failed_get_valid_advice", chat_id_context or self.default_chat_id_for_internal_errors, pair=pair_name))
        return None
    # --- END NEW: AI Integration Methods ---


    def create_trade(self, pair, trade_type, current_price=None, chat_id_for_trade=None):
        # Determine chat_id for notifications from this trade creation
        effective_chat_id = chat_id_for_trade or self.default_chat_id_for_internal_errors
        
        if "BNB" in pair:
            base_asset, quote_asset = (pair[:-3], pair[-3:]) if pair.endswith("BNB") else (pair[:3], pair[3:])
        else:
            if len(pair) >= 6:
                base_asset, quote_asset = pair[:3], pair[3:]
                if len(pair) > 7 and pair[-4:] in ["USDT", "BUSD", "USDC", "FDUSD"]:
                    base_asset, quote_asset = pair[:-4], pair[-4:]
            else:
                logger.warning(_t("warning_non_standard_pair_defaulting_base_quote", effective_chat_id, pair=pair))
                base_asset, quote_asset = pair[:3], pair[3:] if len(pair) > 3 else (pair, "UNKNOWN")

        if current_price is None and self.market_analyzer:
            pair_data = self.market_analyzer.get_pair_data(pair)
            current_price = pair_data["last_price"] if pair_data and pair_data.get("last_price", 0) > 0 else None
        
        if current_price is None or current_price <= 0:
            logger.error(_t("warning_invalid_current_price_trade_creation", effective_chat_id, current_price=current_price, pair=pair))
            self.send_notification(_t("trade_failed_invalid_price", effective_chat_id, pair=pair, current_price=current_price), target_chat_id=effective_chat_id)
            return None

        min_bnb_value_per_trade = self.config.get('min_bnb_per_trade', 0.011)
        bnb_to_invest_calculated = self.config.get('amount', 0.01)

        if self.config.get('use_percentage', False) and self.binance_api and self.config.get('use_real_trading', False):
            try:
                account_info = self.binance_api.get_account_info()
                if account_info and 'balances' in account_info:
                    bnb_balance_free = next((float(bal['free']) for bal in account_info['balances'] if bal['asset'] == 'BNB'), 0)
                    if bnb_balance_free > 0:
                        perc_amount_bnb = bnb_balance_free * (self.config.get('trade_percentage', 5.0) / 100.0)
                        bnb_to_invest_calculated = max(min_bnb_value_per_trade, perc_amount_bnb)
                        logger.info(_t("info_percentage_trade_calculation", effective_chat_id,
                                        percentage=self.config.get('trade_percentage', 5.0), balance=bnb_balance_free,
                                        perc_amount_bnb=perc_amount_bnb, bnb_to_invest=bnb_to_invest_calculated))
                    else:
                        logger.warning(_t("warning_bnb_balance_zero_percentage_trade", effective_chat_id))
                        bnb_to_invest_calculated = max(min_bnb_value_per_trade, self.config.get('amount', 0.01))
                else:
                    logger.warning(_t("warning_failed_get_account_info_percentage_trade", effective_chat_id))
                    bnb_to_invest_calculated = max(min_bnb_value_per_trade, self.config.get('amount', 0.01))
            except Exception as e:
                logger.error(_t("warning_error_calculating_percentage_trade_amount", effective_chat_id, e=e))
                bnb_to_invest_calculated = max(min_bnb_value_per_trade, self.config.get('amount', 0.01))
        else:
            bnb_to_invest_calculated = max(min_bnb_value_per_trade, self.config.get('amount', 0.01))

        if self.config.get('use_real_trading', False) and self.binance_api:
            account_info_final_check = self.binance_api.get_account_info()
            bnb_available_real = 0
            if account_info_final_check and 'balances' in account_info_final_check:
                bnb_available_real = next((float(bal['free']) for bal in account_info_final_check['balances'] if bal['asset'] == 'BNB'), 0)
            if bnb_to_invest_calculated > bnb_available_real:
                err_msg = _t("trade_failed_insufficient_balance_binance_api", effective_chat_id,
                               pair=pair, needed_bnb=bnb_to_invest_calculated, available_bnb=bnb_available_real)
                logger.error(err_msg)
                self.send_notification(err_msg, target_chat_id=effective_chat_id)
                return None

        trade_quantity = 0
        actual_bnb_value_of_trade = bnb_to_invest_calculated
        if quote_asset == 'BNB':
            trade_quantity = actual_bnb_value_of_trade / current_price
        elif base_asset == 'BNB':
            trade_quantity = actual_bnb_value_of_trade
        else:
            logger.warning(_t("warning_non_direct_bnb_pair_amount_logic", effective_chat_id, pair=pair))
            trade_quantity = self.config.get('amount', 0.01)
            actual_bnb_value_of_trade = 0 # Hard to determine for non-BNB pairs without more price data

        if trade_quantity <= 0:
            logger.error(f"Calculated trade quantity zero or negative ({trade_quantity}) for {pair}. BNB to invest: {bnb_to_invest_calculated}, Price: {current_price}")
            return None

        # --- Dynamic parameters from AI if enabled ---
        ai_rationale = None
        if self.config.get("ai_dynamic_mode", False):
            ai_advice = self.get_ai_trade_advice(pair, chat_id_context=effective_chat_id)
            if ai_advice:
                take_profit_pct = ai_advice["tp_percentage"]
                stop_loss_pct = ai_advice["sl_percentage"]
                max_trade_time_seconds = ai_advice["max_trade_time_seconds"]
                ai_rationale = ai_advice["rationale"]
                logger.info(_t("info_ai_mode_updated_params", effective_chat_id, pair=pair, tp=take_profit_pct, sl=stop_loss_pct))
                # Notify about AI parameter update
                self.send_notification(_t("trading_modes_ai_update_notification", effective_chat_id, 
                                          pair=pair, tp=take_profit_pct, sl=stop_loss_pct, rationale=ai_rationale), 
                                          target_chat_id=effective_chat_id)
            else: # Fallback to mode settings if AI fails
                logger.warning(f"AI advice failed for {pair}, falling back to mode settings.")
                take_profit_pct = self.config.get("take_profit", 1.5)
                stop_loss_pct = self.config.get("stop_loss", 5.0)
                max_trade_time_seconds = self.config.get('max_trade_time',300)
        else: # Standard mode settings
            take_profit_pct = self.config.get("take_profit", 1.5)
            stop_loss_pct = self.config.get("stop_loss", 5.0)
            max_trade_time_seconds = self.config.get('max_trade_time',300)
        # --- End AI parameter logic ---

        entry_price_for_calc = current_price
        tp_price = entry_price_for_calc * (1 + take_profit_pct / 100) if trade_type == "BUY" else entry_price_for_calc * (1 - take_profit_pct / 100)
        sl_price = entry_price_for_calc * (1 - stop_loss_pct / 100) if trade_type == "BUY" else entry_price_for_calc * (1 + stop_loss_pct / 100)

        trade = {
            'id': int(time.time() * 1000), 'timestamp': time.time(), 'pair': pair,
            'base_asset': base_asset, 'quote_asset': quote_asset, 'type': trade_type,
            'entry_price': entry_price_for_calc, 'amount': trade_quantity,
            'bnb_value_of_trade': actual_bnb_value_of_trade,
            'take_profit': tp_price, 'stop_loss': sl_price,
            'max_time_seconds': max_trade_time_seconds,
            'entry_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'completed': False, 'mode': self.config.get('trading_mode','N/A'),
            'order_id': None, 'real_trade_opened': False, 'real_trade_filled': False,
            'strategy': 'Standard Auto-Selected',
            'percentage_based': self.config.get('use_percentage', False),
            'ai_rationale': ai_rationale # Store AI rationale if used
        }

        if self.binance_api and self.config.get("use_real_trading", False):
            logger.info(_t("info_attempt_real_order_binance", effective_chat_id, pair=pair, side=trade_type, quantity=trade_quantity))
            order_response = self.binance_api.create_order(symbol=pair, side=trade_type, order_type="MARKET", quantity=trade_quantity)

            if order_response and order_response.get('orderId'):
                trade['order_id'] = order_response['orderId']
                trade['real_trade_opened'] = True
                logger.info(_t("info_success_real_order_placed", effective_chat_id,
                                order_id=trade['order_id'], pair=pair, side=trade_type, status=order_response.get('status')))
                if order_response.get('status') == 'FILLED':
                    trade['real_trade_filled'] = True
                    avg_executed_price, total_qty_filled = 0, 0
                    if order_response.get('fills') and len(order_response['fills']) > 0:
                        total_value = sum(float(f['price']) * float(f['qty']) for f in order_response['fills'])
                        total_qty_filled = sum(float(f['qty']) for f in order_response['fills'])
                        if total_qty_filled > 0: avg_executed_price = total_value / total_qty_filled
                    elif float(order_response.get('price', 0)) > 0 and float(order_response.get('executedQty', 0)) > 0:
                        avg_executed_price = float(order_response.get('price'))
                        total_qty_filled = float(order_response.get('executedQty'))
                    
                    if avg_executed_price > 0 and total_qty_filled > 0:
                        logger.info(_t("info_update_entry_price_from_fill", effective_chat_id,
                                        old_price=trade['entry_price'], new_price=avg_executed_price, order_id=trade['order_id']))
                        logger.info(_t("info_update_amount_from_fill", effective_chat_id,
                                        old_amount=trade['amount'], new_amount=total_qty_filled))
                        trade['entry_price'] = avg_executed_price
                        trade['amount'] = total_qty_filled
                        trade['take_profit'] = avg_executed_price * (1 + take_profit_pct / 100) if trade_type == "BUY" else avg_executed_price * (1 - take_profit_pct / 100)
                        trade['stop_loss'] = avg_executed_price * (1 - stop_loss_pct / 100) if trade_type == "BUY" else avg_executed_price * (1 + stop_loss_pct / 100)
                elif order_response.get('status') == 'REJECTED':
                    trade['real_trade_opened'] = False
                    self.send_notification(_t("trade_rejected_by_binance", effective_chat_id,
                                              pair=pair, trade_type=trade_type, quantity=trade_quantity,
                                              order_id=trade['order_id'], code=order_response.get('code',''), msg=order_response.get('msg','')),
                                           target_chat_id=effective_chat_id)
                else:
                    logger.warning(_t("warning_real_trade_order_status_not_filled", effective_chat_id,
                                      order_id=trade['order_id'], status=order_response.get('status')))
            else:
                err_code = order_response.get('code', 'N/A') if isinstance(order_response, dict) else 'N/A'
                err_msg_api = order_response.get('msg', str(order_response)) if isinstance(order_response, dict) else str(order_response)
                logger.error(_t("trade_failed_api_error_binance", effective_chat_id,
                                pair=pair, trade_type=trade_type, quantity=trade_quantity,
                                error_code=err_code, error_message=err_msg_api[:100]))
                self.send_notification(_t("trade_failed_api_error_binance", effective_chat_id,
                                          pair=pair, trade_type=trade_type, quantity=trade_quantity,
                                          error_code=err_code, error_message=err_msg_api[:100]),
                                       target_chat_id=effective_chat_id)
        elif self.config.get("use_real_trading", False) and not self.binance_api:
            logger.warning(_t("warning_real_trading_no_binance_api", effective_chat_id))

        ACTIVE_TRADES.append(trade)
        return trade

    def create_trade_from_whale(self, whale_transaction, trade_type, is_auto_trade=False, chat_id_for_trade=None):
        effective_chat_id = chat_id_for_trade or self.default_chat_id_for_internal_errors
        pair, current_price = whale_transaction['token'], whale_transaction['price']
        if current_price <= 0:
            logger.warning(_t("warning_whale_tx_invalid_price", effective_chat_id, pair=pair, current_price=current_price))
            return None
        trade = self.create_trade(pair, trade_type, current_price, chat_id_for_trade=effective_chat_id)
        if not trade: return None
        trade.update({'whale_id': whale_transaction['id'], 'strategy': f"Whale-Based ({self.config.get('trading_strategy','N/A')})"})
        
        notification_key = "trade_notification_new_auto_selected" if is_auto_trade else "trade_notification_new_whale_manual_follow"
        selection_details = f"Whale Alert ID: {whale_transaction['id']}" if is_auto_trade else ""
        entry_message = self._format_trade_notification(trade, selection_details, notification_key, effective_chat_id)
        self.send_notification(entry_message, target_chat_id=effective_chat_id)
        return trade

    def complete_trade(self, trade, exit_price=None, reason="unknown", chat_id_context=None):
        effective_chat_id = chat_id_context or self.default_chat_id_for_internal_errors
        if trade.get('completed', False): return

        estimated_exit_price = exit_price
        if estimated_exit_price is None:
            if reason == "take_profit": estimated_exit_price = trade['take_profit']
            elif reason == "stop_loss": estimated_exit_price = trade['stop_loss']
            else:
                current_market_price = self.binance_api.get_ticker_price(trade['pair']) if trade.get('real_trade_filled') and self.binance_api and self.config.get("use_real_trading") else None
                estimated_exit_price = current_market_price if current_market_price else self.simulate_price_movement(trade)
        
        final_exit_price = estimated_exit_price

        if trade.get('real_trade_filled') and self.binance_api and self.config.get("use_real_trading"):
            try:
                opposite_side = "SELL" if trade['type'] == "BUY" else "BUY"
                closing_quantity = trade['amount']
                logger.info(_t("info_attempt_close_real_trade_binance", effective_chat_id,
                                pair=trade['pair'], side=opposite_side, quantity=closing_quantity, original_order_id=trade['order_id']))
                close_order_response = self.binance_api.create_order(symbol=trade['pair'], side=opposite_side, order_type="MARKET", quantity=closing_quantity)

                if close_order_response and close_order_response.get('orderId'):
                    trade['close_order_id'] = close_order_response['orderId']
                    logger.info(_t("info_success_real_closing_order_placed", effective_chat_id,
                                    order_id=trade['close_order_id'], status=close_order_response.get('status')))
                    if close_order_response.get('status') == 'FILLED':
                        avg_executed_exit_price, total_qty_closed = 0, 0
                        if close_order_response.get('fills') and len(close_order_response['fills']) > 0:
                            total_value = sum(float(f['price']) * float(f['qty']) for f in close_order_response['fills'])
                            total_qty_closed = sum(float(f['qty']) for f in close_order_response['fills'])
                            if total_qty_closed > 0: avg_executed_exit_price = total_value / total_qty_closed
                        elif float(close_order_response.get('price', 0)) > 0 and float(close_order_response.get('executedQty', 0)) > 0:
                             avg_executed_exit_price = float(close_order_response.get('price'))
                             total_qty_closed = float(close_order_response.get('executedQty'))
                        if avg_executed_exit_price > 0 and total_qty_closed > 0:
                            logger.info(_t("info_update_exit_price_from_fill", effective_chat_id, old_price=final_exit_price, new_price=avg_executed_exit_price))
                            final_exit_price = avg_executed_exit_price
                            if abs(total_qty_closed - closing_quantity) > 1e-8:
                                logger.warning(_t("warning_partial_close_quantity_mismatch", effective_chat_id,
                                                  expected_quantity=closing_quantity, closed_quantity=total_qty_closed, order_id=trade['close_order_id']))
                        else:
                             logger.warning(_t("warning_closing_order_filled_no_valid_data_pnl_estimate", effective_chat_id, order_id=trade['close_order_id']))
                    else:
                        logger.error(f"Closing order {trade['close_order_id']} for {trade['pair']} status is {close_order_response.get('status')}. PnL uses est. price.")
                else:
                    err_code_close = close_order_response.get('code', 'N/A') if isinstance(close_order_response, dict) else 'N/A'
                    err_msg_close = close_order_response.get('msg', str(close_order_response)) if isinstance(close_order_response, dict) else str(close_order_response)
                    logger.error(f"FAILED to create closing order: {trade['pair']} {opposite_side}. API Code: {err_code_close}, Msg: {err_msg_close}. PnL uses est. price: {final_exit_price:.6f}")
            except Exception as e_close:
                logger.error(f"EXCEPTION during real trade closing: {e_close}. PnL uses est. price.", exc_info=True)
        
        result_pct = 0
        if trade['entry_price'] > 0:
            result_pct = ((final_exit_price - trade['entry_price']) / trade['entry_price']) * 100 if trade['type'] == "BUY" else \
                         ((trade['entry_price'] - final_exit_price) / trade['entry_price']) * 100
        profit_in_bnb = 0.0
        if trade['quote_asset'] == 'BNB':
             profit_in_bnb = (final_exit_price - trade['entry_price']) * trade['amount'] if trade['type'] == "BUY" else \
                             (trade['entry_price'] - final_exit_price) * trade['amount']
        elif trade['base_asset'] == 'BNB':
            profit_in_bnb = (result_pct / 100.0) * trade['amount']

        trade.update({'completed': True, 'exit_price': final_exit_price,
                      'exit_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                      'result': result_pct, 'close_reason': reason, 'profit_in_bnb': profit_in_bnb})

        DAILY_STATS.update({"total_trades": DAILY_STATS["total_trades"] + 1,
                            "total_profit_pct": DAILY_STATS["total_profit_pct"] + result_pct,
                            "total_profit_bnb": DAILY_STATS["total_profit_bnb"] + profit_in_bnb})
        if result_pct > 0: DAILY_STATS["winning_trades"] += 1
        else: DAILY_STATS["losing_trades"] += 1
        if (trade.get('real_trade_filled') or (trade.get('close_order_id') and trade.get('real_trade_opened'))) and \
           self.config.get("use_real_trading") and DAILY_STATS["current_balance"] is not None:
            DAILY_STATS["current_balance"] += profit_in_bnb

        is_win = result_pct > 0
        result_text_key = "trade_status_win" if is_win else "trade_status_loss"
        emoji = "✅" if is_win else "❌" # These are fine as non-translatable UI elements
        reason_text_key_map = {"take_profit": "trade_close_reason_tp", "stop_loss": "trade_close_reason_sl",
                               "time_limit": "trade_close_reason_time_limit", "unknown": "trade_close_reason_manual_other"}
        reason_text_key = reason_text_key_map.get(reason, "trade_close_reason_manual_other")

        real_trade_status_text_key = "trade_status_real_no_sim"
        entry_order_id_val = trade.get('order_id')
        exit_order_id_val = trade.get('close_order_id')
        if entry_order_id_val:
            if trade.get('real_trade_filled'):
                real_trade_status_text_key = "trade_status_real_entry_filled_exit_placed" if exit_order_id_val else "trade_status_real_entry_filled_exit_sim_failed"
            elif trade.get('real_trade_opened'):
                real_trade_status_text_key = "trade_status_real_entry_opened_not_filled_sim_close"
            else:
                real_trade_status_text_key = "trade_status_real_entry_failed_open_fill_sim"
        elif self.config.get("use_real_trading"):
            real_trade_status_text_key = "trade_status_real_yes_failed_pre_binance"

        complete_message = _t("trade_notification_completed", effective_chat_id,
                              emoji=emoji, result_text=_t(result_text_key, effective_chat_id),
                              pair=trade['pair'], type=trade['type'], entry_price=trade['entry_price'], exit_price=final_exit_price,
                              result_pct=result_pct, profit_in_bnb=profit_in_bnb, amount=trade['amount'], base_asset=trade['base_asset'],
                              reason_text=_t(reason_text_key, effective_chat_id), entry_time=trade['entry_time'], exit_time=trade['exit_time'],
                              duration_seconds=int(time.time() - trade.get('timestamp', time.time())),
                              mode=trade.get('mode', 'N/A').capitalize(), strategy=trade.get('strategy', 'N/A'),
                              real_trade_status_text=_t(real_trade_status_text_key, effective_chat_id, entry_order_id=entry_order_id_val, exit_order_id=exit_order_id_val))
        
        if trade.get("ai_rationale"): # Add AI rationale if it was an AI trade
            complete_message += f"\nAI Rationale: {trade['ai_rationale']}"

        self.send_notification(complete_message, target_chat_id=effective_chat_id)
        if trade in ACTIVE_TRADES: ACTIVE_TRADES.remove(trade)
        COMPLETED_TRADES.append(trade)

    def get_daily_stats_message(self, chat_id):
        win_rate = (DAILY_STATS["winning_trades"] / DAILY_STATS["total_trades"] * 100) if DAILY_STATS["total_trades"] > 0 else 0
        balance_change_bnb = DAILY_STATS.get("current_balance",0) - DAILY_STATS.get("starting_balance",0)
        return (
            f"{_t('daily_stats_title_date', chat_id, date=DAILY_STATS.get('date', 'N/A'))}\n\n"
            f"{_t('daily_stats_total_trades', chat_id)}: {DAILY_STATS.get('total_trades',0)}\n"
            f"{_t('daily_stats_winning_trades', chat_id)}: {DAILY_STATS.get('winning_trades',0)}\n"
            f"{_t('daily_stats_losing_trades', chat_id)}: {DAILY_STATS.get('losing_trades',0)}\n"
            f"{_t('daily_stats_win_rate', chat_id)}: {win_rate:.1f}%\n\n"
            f"{_t('daily_stats_total_pl_sim_pct', chat_id)}: {DAILY_STATS.get('total_profit_pct',0.0):.2f}%\n"
            f"{_t('daily_stats_total_pl_bnb_real_sim', chat_id)}: {DAILY_STATS.get('total_profit_bnb',0.0):.8f} BNB\n\n"
            f"{_t('daily_stats_starting_balance_bnb', chat_id)}: {DAILY_STATS.get('starting_balance',0.0):.8f}\n"
            f"{_t('daily_stats_current_balance_bnb', chat_id)}: {DAILY_STATS.get('current_balance',0.0):.8f}\n"
            f"{_t('daily_stats_balance_change_bnb', chat_id)}: {balance_change_bnb:.8f} BNB\n\n"
            f"{_t('daily_stats_trading_mode', chat_id)}: {self.config.get('trading_mode','N/A').capitalize()}\n"
            f"{_t('daily_stats_real_trading_status', chat_id, status=(_t('status_enabled', chat_id) if self.config.get('use_real_trading', False) else _t('status_disabled', chat_id) + ' (Simulation)'))}"
        )


class TelegramBotHandler:
    def __init__(self, token, admin_ids):
        self.token = token
        self.admin_user_ids = admin_ids
        self.admin_chat_ids = [] # Dynamically populated per session
        self.trading_bot = None
        self.application = Application.builder().token(token).build()
        self.register_handlers()
        # Add initial admin_user_ids to admin_chat_ids if they are direct chat_ids (common for single user bots)
        # Bot needs to receive a message from an admin first to reliably get chat_id if it's a group.
        # For direct user chats, user_id is often chat_id.
        for user_id in self.admin_user_ids:
            if user_id not in self.admin_chat_ids: # Basic check
                 self.admin_chat_ids.append(user_id)

        logger.info(_t("info_telegram_bot_initialized", DEFAULT_LANGUAGE, admin_user_ids=self.admin_user_ids))

    def register_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("language", self.language_command)) # NEW
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("config", self.config_command))
        self.application.add_handler(CommandHandler("set", self.set_config_command))
        self.application.add_handler(CommandHandler("trades", self.trades_command))
        self.application.add_handler(CommandHandler("whales", self.whales_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("setpercentage", self.set_percentage_command))
        self.application.add_handler(CommandHandler("bnbpairs", self.bnb_pairs_command))
        self.application.add_handler(CommandHandler("whaleconfig", self.whale_config_command))
        self.application.add_handler(CommandHandler("volume", self.volume_command))
        self.application.add_handler(CommandHandler("trending", self.trending_command))
        self.application.add_handler(CommandHandler("modes", self.trading_modes_command))
        self.application.add_handler(CommandHandler("starttrade", self.start_trading_command))
        self.application.add_handler(CommandHandler("stoptrade", self.stop_trading_command))
        self.application.add_handler(CommandHandler("enablereal", self.enable_real_trading_command))
        self.application.add_handler(CommandHandler("disablereal", self.disable_real_trading_command))
        self.application.add_handler(CommandHandler("balance", self.balance_command))
        self.application.add_handler(CommandHandler("testapi", self.test_api_command))
        self.application.add_handler(CommandHandler("toggletestnet", self.toggle_testnet_command))
        self.application.add_handler(CommandHandler("setaimode", self.set_ai_mode_command)) # NEW
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_error_handler(self.error_handler)

    async def is_authorized(self, update: Update) -> bool:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id if update.effective_chat else None

        if user_id not in self.admin_user_ids:
            if chat_id:
                await update.effective_chat.send_message(_t("error_auth_failed", chat_id))
            logger.warning(_t("error_unauthorized_access_log", DEFAULT_LANGUAGE, user_id=user_id, chat_id=chat_id or 'N/A'))
            return False
        
        if chat_id and chat_id not in self.admin_chat_ids:
            self.admin_chat_ids.append(chat_id)
            logger.info(_t("info_added_chat_id_admin_list", DEFAULT_LANGUAGE, chat_id=chat_id, admin_chat_ids=", ".join(map(str,self.admin_chat_ids))))
        
        # Ensure user language is set (e.g., on first interaction after bot restart)
        if chat_id and chat_id not in user_languages:
            _set_user_language(chat_id, DEFAULT_LANGUAGE) # Set to default if not found
            # Optionally, prompt for language selection if it's the very first interaction for this user.
            # await self.language_command(update, None, called_internally=True)

        return True

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id

        # Prompt for language if not set
        if chat_id not in user_languages:
             _set_user_language(chat_id, DEFAULT_LANGUAGE) # Default to English first
             # Then show language selection
             await self.language_command(update, context, called_internally=True)
             return # Exit here, language selection will handle next step

        keyboard_data = [
            ("button_start_trading", "select_trading_mode_start"), # Changed CB to avoid conflict
            ("button_top_volume", "volume"), ("button_trending", "trending"),
            ("button_settings", "config"), ("button_status", "status"),
            ("button_set_ai_mode", "toggle_ai_mode") # NEW
        ]
        keyboard = []
        current_row = []
        for i, (btn_text_key, cb_data) in enumerate(keyboard_data):
            current_row.append(InlineKeyboardButton(_t(btn_text_key, chat_id), callback_data=cb_data))
            if (i+1) % 2 == 0 or btn_text_key == "button_set_ai_mode": # Max 2 buttons per row, or AI button alone
                keyboard.append(current_row)
                current_row = []
        if current_row: keyboard.append(current_row)


        await update.effective_message.reply_text(
            _t("welcome_message", chat_id) + "\n" +
            _t("help_prompt_short", chat_id) + "\n" +
            _t("current_admin_chats", chat_id, chat_ids=", ".join(map(str, self.admin_chat_ids))),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, called_internally=False):
        # No auth check if called internally for first time setup, otherwise check
        if not called_internally and not await self.is_authorized(update): return
        chat_id = update.effective_chat.id

        keyboard = [
            [InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en")],
            [InlineKeyboardButton("Indonesia 🇮🇩", callback_data="set_lang_id")]
        ]
        text_to_send = _t("select_language_prompt", chat_id)
        
        if update.callback_query: # If called from a button
            await update.callback_query.edit_message_text(text_to_send, reply_markup=InlineKeyboardMarkup(keyboard))
        else: # If called by command
            await update.effective_message.reply_text(text_to_send, reply_markup=InlineKeyboardMarkup(keyboard))


    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        help_text = _t("help_command_intro", chat_id) + "\n" + \
            _t("help_start", chat_id) + "\n" + \
            _t("help_language", chat_id) + "\n" + \
            _t("help_help", chat_id) + "\n" + \
            _t("help_status", chat_id) + "\n" + \
            _t("help_config", chat_id) + "\n" + \
            _t("help_set", chat_id) + "\n" + \
            _t("help_trades", chat_id) + "\n" + \
            _t("help_whales", chat_id) + "\n" + \
            _t("help_stats", chat_id) + "\n" + \
            _t("help_setpercentage", chat_id) + "\n" + \
            _t("help_bnbpairs", chat_id) + "\n" + \
            _t("help_volume", chat_id) + "\n" + \
            _t("help_trending", chat_id) + "\n" + \
            _t("help_modes", chat_id) + "\n" + \
            _t("help_whaleconfig", chat_id) + "\n" + \
            _t("help_starttrade", chat_id) + "\n" + \
            _t("help_stoptrade", chat_id) + "\n\n" + \
            _t("help_real_trading_api", chat_id) + "\n" + \
            _t("help_enablereal", chat_id) + "\n" + \
            _t("help_disablereal", chat_id) + "\n" + \
            _t("help_balance", chat_id) + "\n" + \
            _t("help_testapi", chat_id) + "\n" + \
            _t("help_toggletestnet", chat_id) + "\n" + \
            _t("help_setaimode", chat_id)
        await update.effective_message.reply_text(help_text)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        if not self.trading_bot:
            await (update.callback_query or update.message).reply_text(_t("error_bot_not_initialized", chat_id))
            return

        active_trades_list = [t for t in ACTIVE_TRADES if not t.get('completed', False)]
        ds = DAILY_STATS
        win_rate_daily = (ds["winning_trades"] / ds["total_trades"] * 100) if ds["total_trades"] > 0 else 0
        balance_change_bnb = ds.get("current_balance",0) - ds.get("starting_balance",0)

        tb_cfg = self.trading_bot.config
        status_text = (
            f"{_t('status_bot_status_title', chat_id)}\n\n"
            f"{_t('status_trading_engine', chat_id)}: {_t('status_running', chat_id) if self.trading_bot.running else _t('status_stopped', chat_id)}\n"
            f"{_t('status_auto_trading', chat_id)}: {_t('status_enabled', chat_id) if tb_cfg.get('trading_enabled') else _t('status_disabled', chat_id)}\n"
            f"{_t('status_current_mode', chat_id)}: {tb_cfg.get('trading_mode','N/A').capitalize()}\n"
            f"{_t('status_ai_dynamic_mode', chat_id)}: {_t('status_on', chat_id) if tb_cfg.get('ai_dynamic_mode') else _t('status_off', chat_id)}\n"
            f"{_t('status_real_trading', chat_id)}: {_t('status_production', chat_id) if tb_cfg.get('use_real_trading') and not tb_cfg.get('use_testnet') else (_t('status_testnet', chat_id) if tb_cfg.get('use_testnet') else _t('status_simulation', chat_id))}\n"
            f"{_t('status_tpsl_from_mode', chat_id)}: {tb_cfg.get('take_profit',0)}% / {tb_cfg.get('stop_loss',0)}%\n"
            f"{_t('status_max_trade_time', chat_id)}: {tb_cfg.get('max_trade_time',0)}s\n\n"
            f"{_t('status_active_trades', chat_id)}: {len(active_trades_list)}/{tb_cfg.get('max_concurrent_trades',0)}\n"
            f"{_t('status_completed_session', chat_id)}: {len(COMPLETED_TRADES)}\n\n"
            f"{_t('status_daily_stats_title', chat_id, date=ds.get('date', 'N/A'))}\n"
            f"{_t('status_daily_trades', chat_id, total_trades=ds.get('total_trades',0), winning_trades=ds.get('winning_trades',0), losing_trades=ds.get('losing_trades',0))}\n"
            f"{_t('status_daily_win_rate', chat_id)}: {win_rate_daily:.1f}%\n"
            f"{_t('status_daily_pl_bnb', chat_id)}: {ds.get('total_profit_bnb',0.0):.8f} BNB\n"
            f"{_t('status_daily_balance_change', chat_id)}: {balance_change_bnb:.8f} BNB\n\n"
            f"{_t('status_whale_detection', chat_id)}: {_t('status_on', chat_id) if tb_cfg.get('whale_detection') else _t('status_off', chat_id)}\n"
            f"{_t('status_auto_select_pairs', chat_id)}: {_t('status_on', chat_id) if tb_cfg.get('auto_select_pairs') else _t('status_off', chat_id)}\n"
            f"{_t('status_percentage_based_trading', chat_id)}: {(_t('status_on', chat_id) + ' ' + _t('status_percentage_value', chat_id, percentage=tb_cfg.get('trade_percentage'))) if tb_cfg.get('use_percentage') else _t('status_off', chat_id)}"
        )
        keyboard = [
            [InlineKeyboardButton(_t("button_start_trading", chat_id), callback_data="select_trading_mode_start"),
             InlineKeyboardButton(_t("button_stop_trading", chat_id), callback_data="stop_trading")],
            [InlineKeyboardButton(_t("button_top_volume", chat_id), callback_data="volume"),
             InlineKeyboardButton(_t("button_trending", chat_id), callback_data="trending")],
            [InlineKeyboardButton(_t("button_settings", chat_id), callback_data="config"),
             InlineKeyboardButton(_t("button_set_ai_mode", chat_id) if not tb_cfg.get("ai_dynamic_mode") else _t("button_set_ai_mode", chat_id) + " (ON)", callback_data="toggle_ai_mode")],
             # Example for dynamic button label (if you want to show ON/OFF for AI mode on this button)
            [InlineKeyboardButton((_t("button_disable_real_trading", chat_id) if tb_cfg.get('use_real_trading') else _t("button_enable_real_trading", chat_id)),
                                 callback_data="toggle_real_trading")]
        ]
        target = update.callback_query.edit_message_text if update.callback_query else update.effective_message.reply_text
        try:
            await target(status_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(_t("error_send_status_message_too_long", chat_id, e=e))
            await target(status_text[:4000], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

    async def config_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        if not self.trading_bot:
            await (update.callback_query or update.message).reply_text(_t("error_bot_not_initialized", chat_id))
            return

        cfg = self.trading_bot.config
        api_key_disp = ('****' + cfg.get('api_key', '')[-4:]) if cfg.get('api_key') and len(cfg.get('api_key', '')) > 4 else _t("config_api_not_set", chat_id)
        api_secret_disp = ('****' + cfg.get('api_secret', '')[-4:]) if cfg.get('api_secret') and len(cfg.get('api_secret', '')) > 4 else _t("config_api_not_set", chat_id)

        config_text = (
            f"{_t('config_title', chat_id)}\n\n"
            f"{_t('config_trading_mode', chat_id)}: {cfg.get('trading_mode','N/A').capitalize()}\n"
            f"{_t('status_ai_dynamic_mode', chat_id)}: {_t('status_on', chat_id) if cfg.get('ai_dynamic_mode') else _t('status_off', chat_id)}\n"
            f"{_t('config_fixed_trade_amount', chat_id)}: {cfg.get('amount',0.01)} {_t('config_fixed_trade_amount_desc', chat_id)}\n"
            f"{_t('config_min_bnb_value_per_trade', chat_id)}: {cfg.get('min_bnb_per_trade', 0.011)} BNB\n"
            f"{_t('config_percentage_based_trading', chat_id)}: {(_t('config_percentage_yes', chat_id, percentage=cfg.get('trade_percentage')) if cfg.get('use_percentage') else _t('config_percentage_no', chat_id))}\n"
            f"{_t('config_tpsl_from_mode', chat_id)}: {cfg.get('take_profit',0)}% / {cfg.get('stop_loss',0)}%\n"
            f"{_t('config_max_trade_time', chat_id)}: {cfg.get('max_trade_time',0)}s\n"
            f"{_t('config_max_concurrent_trades', chat_id)}: {cfg.get('max_concurrent_trades',0)}\n\n"
            f"{_t('config_auto_select_pairs', chat_id)}: {_t('status_on', chat_id) if cfg.get('auto_select_pairs') else _t('status_off', chat_id)}\n"
            f"{_t('config_min_volume_bnb', chat_id)}: {cfg.get('min_volume',0)}\n"
            f"{_t('config_min_price_change', chat_id)}: {cfg.get('min_price_change',0)}%\n\n"
            f"{_t('config_whale_detection', chat_id)}: {_t('status_on', chat_id) if cfg.get('whale_detection') else _t('status_off', chat_id)}\n"
            f"{_t('config_auto_trade_whale', chat_id)}: {_t('status_on', chat_id) if cfg.get('auto_trade_on_whale') else _t('status_off', chat_id)}\n"
            f"{_t('config_whale_strategy', chat_id)}: {cfg.get('trading_strategy','N/A')}\n"
            f"{_t('config_whale_threshold_bnb', chat_id)}: {cfg.get('whale_threshold',0)}\n\n"
            f"{_t('config_daily_profit_target', chat_id)}: {cfg.get('daily_profit_target', 2.5)}%\n"
            f"{_t('config_daily_loss_limit', chat_id)}: {cfg.get('daily_loss_limit', 5.0)}%\n\n"
            f"{_t('config_api_key', chat_id)}: {api_key_disp}\n{_t('config_api_secret', chat_id)}: {api_secret_disp}\n"
            f"{_t('config_api_mode', chat_id)}: {_t('status_testnet', chat_id) if cfg.get('use_testnet') else _t('status_production', chat_id)}\n"
            f"{_t('config_real_trading', chat_id)}: {_t('status_enabled', chat_id) if cfg.get('use_real_trading') else _t('status_disabled', chat_id)} ({_t('status_simulation', chat_id)})\n"
            f"{_t('config_mock_data_mode', chat_id)}: {_t('status_enabled', chat_id) if cfg.get('mock_mode') else _t('status_disabled', chat_id)}"
        )
        keyboard = [
            [InlineKeyboardButton(_t("button_change_mode", chat_id), callback_data="select_trading_mode_set")],
            [InlineKeyboardButton(_t("button_toggle_auto_select", chat_id), callback_data="toggle_auto_select"),
             InlineKeyboardButton(_t("button_toggle_whale_detection", chat_id), callback_data="toggle_whale_detection")],
            [InlineKeyboardButton(_t("button_toggle_percentage_based", chat_id), callback_data="toggle_percentage_based"),
             InlineKeyboardButton(_t("button_set_ai_mode", chat_id) if not cfg.get("ai_dynamic_mode") else _t("button_set_ai_mode", chat_id) + " (ON)", callback_data="toggle_ai_mode")],
            [InlineKeyboardButton((_t("button_disable_real_trading", chat_id) if cfg.get('use_real_trading') else _t("button_enable_real_trading", chat_id)), callback_data="toggle_real_trading")],
            [InlineKeyboardButton(_t("button_back_to_status", chat_id), callback_data="status")]
        ]
        target = update.callback_query.edit_message_text if update.callback_query else update.effective_message.reply_text
        try:
            await target(config_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(_t("error_send_config_message_too_long", chat_id, e=e))
            await target(config_text[:4000], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

    async def set_config_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        if not self.trading_bot:
            await update.effective_message.reply_text(_t("error_bot_not_initialized", chat_id))
            return

        args = context.args
        if len(args) < 2:
            params_list = (
                "amount, trading_mode, take_profit, stop_loss, max_trade_time, min_volume, \n"
                "min_price_change, auto_select_pairs, whale_detection, api_key, api_secret, \n"
                "use_testnet, use_real_trading, trade_percentage, use_percentage, \n"
                "daily_loss_limit, daily_profit_target, min_bnb_per_trade, mock_mode, ai_dynamic_mode"
            )
            await update.effective_message.reply_text(_t("config_param_usage", chat_id, params_list=params_list))
            return

        param = args[0].lower()
        value_str = " ".join(args[1:])

        if param not in self.trading_bot.config:
            await update.effective_message.reply_text(_t("config_unknown_param", chat_id, param=param))
            return

        original_value = self.trading_bot.config[param]
        new_value = None
        try:
            if isinstance(original_value, bool): new_value = value_str.lower() in ['true', 'yes', '1', 'on', 'enable']
            elif isinstance(original_value, int): new_value = int(value_str)
            elif isinstance(original_value, float): new_value = float(value_str)
            elif isinstance(original_value, str):
                if param == 'trading_mode' and value_str not in TRADING_MODES and value_str != "ai_dynamic": # ai_dynamic is not a formal mode in TRADING_MODES
                    await update.effective_message.reply_text(_t("config_invalid_mode", chat_id, modes=", ".join(TRADING_MODES.keys())))
                    return
                new_value = value_str
            else:
                await update.effective_message.reply_text(_t("config_param_unsupported_type", chat_id, param=param))
                return
        except ValueError:
            await update.effective_message.reply_text(_t("config_invalid_value_type", chat_id, param=param, expected_type=type(original_value).__name__, value_str=value_str))
            return

        self.trading_bot.config[param] = new_value
        msg_parts = [_t("config_updated", chat_id, param=param, new_value=new_value)]

        if param in ['api_key', 'api_secret', 'use_testnet']:
            self.trading_bot.binance_api = BinanceAPI(self.trading_bot.config, chat_id)
            if self.trading_bot.market_analyzer: self.trading_bot.market_analyzer.binance_api = self.trading_bot.binance_api
            if self.trading_bot.whale_detector: self.trading_bot.whale_detector.binance_api = self.trading_bot.binance_api
            msg_parts.append(_t("config_api_reinitialized", chat_id))
        
        if param == 'trading_mode':
            self.trading_bot.apply_trading_mode_settings(chat_id)
            msg_parts.append(_t("config_mode_settings_applied", chat_id))
            if new_value in TRADING_MODES:
                 tm_cfg = TRADING_MODES[new_value]
                 msg_parts.append(_t("config_new_mode_settings", chat_id, mode_name=str(new_value).capitalize(),
                                    tp=tm_cfg.get('take_profit','N/A'), sl=tm_cfg.get('stop_loss','N/A'),
                                    max_time=tm_cfg.get('max_trade_time','N/A'), max_trades=tm_cfg.get('max_trades','N/A')))
        
        if param == "use_real_trading" and new_value is True:
            self.trading_bot.config["mock_mode"] = False
            msg_parts.append(_t("config_mock_mode_auto_off", chat_id))
            if self.trading_bot.market_analyzer: self.trading_bot.market_analyzer.config["mock_mode"] = False
        
        if param == "mock_mode" and new_value is True and self.trading_bot.config.get("use_real_trading") is True:
            self.trading_bot.config["mock_mode"] = False
            msg_parts = [_t("config_cannot_enable_mock_real_on", chat_id, param=param)]

        if param == "ai_dynamic_mode":
            self.trading_bot.apply_trading_mode_settings(chat_id) # Re-apply to potentially disable manual TP/SL if AI on
            if new_value:
                msg_parts.append(_t("trading_modes_ai_dynamic_mode_enabled", chat_id))
            else:
                msg_parts.append(_t("trading_modes_ai_dynamic_mode_disabled", chat_id, previous_mode=self.trading_bot.config.get('trading_mode', 'default')))


        await update.effective_message.reply_text("\n".join(msg_parts))

    async def trades_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        if not self.trading_bot:
            await update.effective_message.reply_text(_t("error_bot_not_initialized", chat_id))
            return

        all_trades = ACTIVE_TRADES + COMPLETED_TRADES
        if not all_trades:
            await update.effective_message.reply_text(_t("trade_no_trades_recorded", chat_id))
            return

        recent_trades = sorted(all_trades, key=lambda x: x.get('timestamp',0), reverse=True)[:10]
        trades_text = f"{_t('trade_recent_trades_title', chat_id)}\n\n"
        for trade in recent_trades:
            status_key = "trade_status_active" if not trade.get('completed', False) else "trade_status_completed_reason"
            status_text = _t(status_key, chat_id, reason=trade.get('close_reason','N/A'))
            result_pct_str = f"{trade.get('result', 0):.2f}%" if trade.get('completed', False) else "N/A"
            
            time_info = _t("trade_entry_time_short", chat_id, time=trade.get('entry_time', 'N/A').split(' ')[1])
            if not trade.get('completed', False):
                elapsed = int(time.time() - trade.get('timestamp',0))
                time_info += _t("trade_elapsed_time_short", chat_id, seconds=elapsed)
            else:
                time_info += _t("trade_exit_time_short", chat_id, time=trade.get('exit_time', 'N/A').split(' ')[1])

            real_trade_status_key = "trade_real_status_sim"
            order_id_val = trade.get('order_id')
            if order_id_val:
                 if trade.get('real_trade_filled'): real_trade_status_key = "trade_real_status_id_filled"
                 elif trade.get('real_trade_opened'): real_trade_status_key = "trade_real_status_id_opened"
                 else: real_trade_status_key = "trade_real_status_id_failed"
            elif self.trading_bot.config.get("use_real_trading"):
                real_trade_status_key = "trade_real_status_attempted_failed_presend"
            real_trade_display = _t(real_trade_status_key, chat_id, order_id=order_id_val)

            trades_text += (
                f"Pair: {trade.get('pair','N/A')} ({trade.get('type','N/A')}) | {trade.get('mode','N/A')}\n"
                f"Status: {status_text}, Result: {result_pct_str}\n"
                f"Entry $: {trade.get('entry_price',0):.6f}, Amount: {trade.get('amount',0):.6f} {trade.get('base_asset','?')}\n"
                f"{time_info}\n"
                f"Real: {real_trade_display}\n"
                f"Profit BNB: {trade.get('profit_in_bnb', 0.0):.8f} (if completed)\n\n"
            )
        if len(trades_text) > 4090:
            trades_text = trades_text[:4000] + _t("trade_message_truncated", chat_id)
        await update.effective_message.reply_text(trades_text if trades_text.strip() else _t("trade_no_trades_recorded", chat_id))

    async def whales_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        if not MOCK_WHALE_TRANSACTIONS:
            await update.effective_message.reply_text(_t("whale_no_mock_alerts", chat_id))
            return
        recent_whales = sorted(MOCK_WHALE_TRANSACTIONS, key=lambda x: x['id'], reverse=True)[:5]
        whales_text = f"{_t('whale_recent_mock_alerts_title', chat_id)}\n\n"
        for whale in recent_whales:
            whales_text += (
                f"{_t('whale_alert_token', chat_id, token=whale['token'])} ({whale['type']})\n"
                f"{_t('whale_alert_amount', chat_id, amount=whale['amount'], asset_name=whale['token'])} Value: ${whale['value']:,.2f}\n" # Simplified for brevity
                f"{_t('whale_alert_potential_impact', chat_id, impact=whale['impact'])}\nTime: {whale['time']}\n\n"
            )
        await update.effective_message.reply_text(whales_text if whales_text.strip() else _t("whale_no_mock_alerts", chat_id))

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        if not self.trading_bot:
            await update.effective_message.reply_text(_t("error_bot_not_initialized", chat_id))
            return
        await update.effective_message.reply_text(self.trading_bot.get_daily_stats_message(chat_id))

    async def set_percentage_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        if not self.trading_bot:
            await update.effective_message.reply_text(_t("error_bot_not_initialized", chat_id))
            return
        args = context.args
        cfg = self.trading_bot.config
        if not args:
            status_key = "set_percentage_status_enabled" if cfg.get("use_percentage") else "set_percentage_status_disabled"
            await update.effective_message.reply_text(
                _t("set_percentage_current_status", chat_id,
                   status=_t(status_key, chat_id),
                   percentage=cfg.get("trade_percentage", 5.0),
                   min_bnb_val=cfg.get("min_bnb_per_trade", 0.011))
            )
            return
        if args[0].lower() in ['on', 'enable', 'true', 'yes']:
            cfg["use_percentage"] = True
            if len(args) > 1:
                try:
                    percentage = float(args[1])
                    if not (0.1 <= percentage <= 100):
                        await update.effective_message.reply_text(_t("set_percentage_invalid_range", chat_id))
                        return
                    cfg["trade_percentage"] = percentage
                except ValueError:
                    await update.effective_message.reply_text(_t("set_percentage_invalid_value", chat_id))
                    return
            await update.effective_message.reply_text(
                _t("set_percentage_enabled_success", chat_id,
                   percentage=cfg['trade_percentage'],
                   min_bnb_val=cfg.get('min_bnb_per_trade',0.011))
            )
        elif args[0].lower() in ["off", "disable", "false", "no"]:
            cfg["use_percentage"] = False
            await update.effective_message.reply_text(_t("set_percentage_disabled_success", chat_id))
        else:
            await update.effective_message.reply_text(_t("set_percentage_invalid_option", chat_id))

    async def test_api_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        if not self.trading_bot:
            await update.effective_message.reply_text(_t("error_bot_not_initialized", chat_id))
            return
        cfg = self.trading_bot.config
        if not cfg.get("api_key") or cfg.get("api_key", "").startswith("YOUR_") or \
           not cfg.get("api_secret") or cfg.get("api_secret", "").startswith("YOUR_"):
            await update.effective_message.reply_text(_t("error_api_credentials_not_set", chat_id))
            return

        status_msg = await update.effective_message.reply_text(_t("api_test_testing_connection", chat_id))
        if not self.trading_bot.binance_api or \
           self.trading_bot.binance_api.api_key != cfg["api_key"] or \
           self.trading_bot.binance_api.api_secret != cfg["api_secret"] or \
           self.trading_bot.binance_api.base_url != (BINANCE_TEST_API_URL if cfg["use_testnet"] else BINANCE_API_URL):
             self.trading_bot.binance_api = BinanceAPI(cfg, chat_id)

        if self.trading_bot.binance_api:
            try:
                ping_url = f"{self.trading_bot.binance_api.base_url}/api/v3/ping"
                ping_response = requests.get(ping_url, timeout=10)
                if ping_response.status_code != 200:
                    await status_msg.edit_text(_t("error_api_test_ping_failed", chat_id, status_code=ping_response.status_code, response_text=ping_response.text))
                    return
                server_time_data = requests.get(f"{self.trading_bot.binance_api.base_url}/api/v3/time", timeout=10).json()
                server_time_str = datetime.fromtimestamp(server_time_data['serverTime'] / 1000).strftime("%Y-%m-%d %H:%M:%S UTC")
                
                await status_msg.edit_text(
                    _t("api_test_ping_server_time_ok", chat_id,
                       mode=_t('status_testnet', chat_id) if cfg.get('use_testnet') else _t('status_production', chat_id),
                       base_url=self.trading_bot.binance_api.base_url, server_time=server_time_str)
                )
                account_info = self.trading_bot.binance_api.get_account_info()
                if account_info and 'balances' in account_info:
                    balances = [f"{b['asset']}: {b['free']} + {b['locked']}" for b in account_info['balances'] if float(b['free']) > 0 or float(b['locked']) > 0][:5]
                    balances_str = "\n".join(balances) if balances else _t("api_test_no_assets_with_balance", chat_id)
                    await status_msg.edit_text(
                        _t("api_test_success", chat_id,
                           mode=_t('status_testnet', chat_id) if cfg.get('use_testnet') else _t('status_production', chat_id),
                           can_trade=account_info.get('canTrade', 'Unknown'),
                           account_type=account_info.get('accountType', 'Unknown'),
                           balances_str=balances_str)
                    )
                else:
                    err_detail_key = "error_api_auth_failed_detail_log"
                    bin_msg, bin_code = "", ""
                    if isinstance(account_info, dict) and 'msg' in account_info:
                        err_detail_key = "error_api_auth_failed_detail_binance"
                        bin_msg, bin_code = account_info.get('msg'), account_info.get('code')
                    await status_msg.edit_text(
                        _t("error_api_auth_failed", chat_id,
                           mode=_t('status_testnet', chat_id) if cfg.get('use_testnet') else _t('status_production', chat_id),
                           error_detail=_t(err_detail_key, chat_id, msg=bin_msg, code=bin_code))
                    )
            except requests.exceptions.Timeout: await status_msg.edit_text(_t("error_api_timeout", chat_id))
            except Exception as e_conn: await status_msg.edit_text(_t("error_api_connection_failed_generic", chat_id, e_conn=str(e_conn)))
        else: await status_msg.edit_text(_t("error_api_not_initialized_config", chat_id))

    async def toggle_testnet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        if not self.trading_bot:
            await update.effective_message.reply_text(_t("error_bot_not_initialized", chat_id))
            return
        cfg = self.trading_bot.config
        cfg["use_testnet"] = not cfg.get("use_testnet", False)
        self.trading_bot.binance_api = BinanceAPI(cfg, chat_id)
        if self.trading_bot.market_analyzer: self.trading_bot.market_analyzer.binance_api = self.trading_bot.binance_api
        if self.trading_bot.whale_detector: self.trading_bot.whale_detector.binance_api = self.trading_bot.binance_api
        mode_key = 'status_testnet' if cfg["use_testnet"] else 'status_production'
        await update.effective_message.reply_text(_t("api_test_toggle_testnet_success", chat_id, mode=_t(mode_key, chat_id)))

    async def enable_real_trading_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        if not self.trading_bot:
            await update.effective_message.reply_text(_t("error_bot_not_initialized", chat_id))
            return
        cfg = self.trading_bot.config
        if not cfg.get("api_key") or cfg.get("api_key", "").startswith("YOUR_") or \
           not cfg.get("api_secret") or cfg.get("api_secret", "").startswith("YOUR_"):
            await update.effective_message.reply_text(_t("error_api_credentials_not_set", chat_id))
            return
        if cfg.get("use_testnet", False):
            await update.effective_message.reply_text(_t("error_real_trading_on_testnet", chat_id))
            return

        status_msg = await update.effective_message.reply_text(_t("api_test_enable_real_testing_production", chat_id))
        test_cfg = {**cfg, "use_real_trading": True, "use_testnet": False}
        test_api = BinanceAPI(test_cfg, chat_id)
        account_info = test_api.get_account_info()

        if account_info and account_info.get('canTrade'):
            cfg.update({"use_real_trading": True, "use_testnet": False, "mock_mode": False})
            self.trading_bot.binance_api = BinanceAPI(cfg, chat_id)
            if self.trading_bot.market_analyzer:
                self.trading_bot.market_analyzer.config.update({"mock_mode": False, "use_testnet": False})
                self.trading_bot.market_analyzer.binance_api = self.trading_bot.binance_api
            if self.trading_bot.whale_detector:
                 self.trading_bot.whale_detector.config.update({"mock_mode": False, "use_testnet": False})
                 self.trading_bot.whale_detector.binance_api = self.trading_bot.binance_api

            bnb_bal = next((b['free'] for b in account_info['balances'] if b['asset'] == 'BNB'), "0.0")
            await status_msg.edit_text(_t("api_test_enable_real_success", chat_id, bnb_balance=bnb_bal))
        else:
            err_detail_key = "error_api_auth_failed_detail_log"
            bin_msg, bin_code = "", ""
            if isinstance(account_info, dict) and 'msg' in account_info:
                err_detail_key = "error_api_auth_failed_detail_binance"
                bin_msg, bin_code = account_info.get('msg'), account_info.get('code')
            await status_msg.edit_text(_t("error_real_trading_enable_api_fail", chat_id, error_detail=_t(err_detail_key, chat_id, msg=bin_msg, code=bin_code)))

    async def disable_real_trading_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        if not self.trading_bot:
            await update.effective_message.reply_text(_t("error_bot_not_initialized", chat_id))
            return
        self.trading_bot.config.update({"use_real_trading": False, "mock_mode": True})
        if self.trading_bot.market_analyzer: self.trading_bot.market_analyzer.config["mock_mode"] = True
        await update.effective_message.reply_text(_t("api_test_disable_real_success", chat_id))

    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        if not self.trading_bot:
            await update.effective_message.reply_text(_t("error_bot_not_initialized", chat_id))
            return
        cfg = self.trading_bot.config
        if not cfg.get("api_key") or cfg.get("api_key","").startswith("YOUR_") or \
           not cfg.get("api_secret") or cfg.get("api_secret","").startswith("YOUR_"):
            await update.effective_message.reply_text(_t("error_api_credentials_not_set", chat_id))
            return
        status_msg = await update.effective_message.reply_text(_t("api_test_fetching_balance", chat_id))
        if not self.trading_bot.binance_api or \
           self.trading_bot.binance_api.api_key != cfg["api_key"] or \
           self.trading_bot.binance_api.api_secret != cfg["api_secret"] or \
           self.trading_bot.binance_api.base_url != (BINANCE_TEST_API_URL if cfg["use_testnet"] else BINANCE_API_URL):
             self.trading_bot.binance_api = BinanceAPI(cfg, chat_id)

        if self.trading_bot.binance_api:
            account_info = self.trading_bot.binance_api.get_account_info()
            if account_info and 'balances' in account_info:
                balances = [b for b in account_info['balances'] if float(b['free']) > 0 or float(b['locked']) > 0]
                balances_text = "\n".join([f"{b['asset']}: {b['free']} + {b['locked']}" for b in balances[:15]])
                if not balances: balances_text = _t("api_test_no_assets_with_balance", chat_id)
                elif len(balances) > 15: balances_text += _t("api_test_balance_and_more_assets", chat_id, count=len(balances)-15)
                
                mode_text = _t('status_testnet', chat_id) if cfg.get("use_testnet") else _t('status_production', chat_id)
                await status_msg.edit_text(
                    f"{_t('api_test_balance_title', chat_id, mode_text=mode_text)}\n\n{balances_text}\n\n"
                    f"{_t('api_test_balance_can_trade', chat_id)}: {account_info.get('canTrade', 'Unknown')}\n"
                    f"{_t('api_test_balance_account_type', chat_id)}: {account_info.get('accountType', 'Unknown')}"
                )
            else:
                err_detail_key = "error_api_auth_failed_detail_log"
                bin_msg, bin_code = "", ""
                if isinstance(account_info, dict) and 'msg' in account_info:
                    err_detail_key = "error_api_auth_failed_detail_binance"
                    bin_msg, bin_code = account_info.get('msg'), account_info.get('code')
                await status_msg.edit_text(_t("api_test_failed_get_balance", chat_id, error_detail=_t(err_detail_key, chat_id, msg=bin_msg, code=bin_code)))
        else: await status_msg.edit_text(_t("error_api_not_initialized_config", chat_id))

    async def bnb_pairs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        ma = self.trading_bot.market_analyzer if self.trading_bot else None
        if not ma:
            await (update.callback_query or update.message).reply_text(_t("error_market_analyzer_not_ready", chat_id))
            return
        if not ma.config.get("mock_mode", True) and (not ma.market_data or time.time() - ma.last_update > 60):
            msg_to_edit = await (update.callback_query or update.message).reply_text(_t("bnb_pairs_updating_market_data", chat_id))
            ma.update_market_data()
            edit_target = msg_to_edit.edit_text if update.callback_query else msg_to_edit.edit_text # for message objects, it's the same
            await edit_target(_t("bnb_pairs_market_data_updated_fetching", chat_id))

        pairs = ma.market_data
        bnb_base = [p for p in pairs if p["pair"].startswith("BNB")]
        bnb_quote = [p for p in pairs if p["pair"].endswith("BNB") and not p["pair"].startswith("BNB")]
        text = f"{_t('bnb_pairs_title', chat_id)}\n\n{_t('bnb_pairs_base_pairs_title', chat_id)}\n"
        if bnb_base: text += "\n".join([_t("bnb_pairs_pair_details_vol", chat_id, pair=p['pair'], volume=p.get('volume',0), price_change=p.get('price_change',0)) for p in bnb_base[:10]])
        else: text += _t("bnb_pairs_no_base_found", chat_id)
        text += f"\n\n{_t('bnb_pairs_quote_pairs_title', chat_id)}\n"
        if bnb_quote: text += "\n".join([_t("bnb_pairs_pair_details_qvol", chat_id, pair=p['pair'], quote_volume=p.get('quote_volume',0), price_change=p.get('price_change',0)) for p in bnb_quote[:10]])
        else: text += _t("bnb_pairs_no_quote_found", chat_id)
        if not bnb_base and not bnb_quote: text = _t("bnb_pairs_no_bnb_pairs_found_market_empty", chat_id)
        
        target = update.callback_query.edit_message_text if update.callback_query else update.effective_message.reply_text
        try: await target(text)
        except Exception as e:
            logger.error(_t("error_send_bnb_pairs_message_too_long", chat_id, e=e))
            await target(text[:4000])

    async def volume_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        ma = self.trading_bot.market_analyzer if self.trading_bot else None
        if not ma:
            await (update.callback_query or update.message).reply_text(_t("error_market_analyzer_not_ready", chat_id))
            return
        pairs = ma.get_high_volume_pairs(10)
        text = f"{_t('volume_title', chat_id)}\n\n"
        kb_rows = []
        if pairs:
            for i, p in enumerate(pairs, 1):
                key = "volume_pair_details_qvol" if 'quote_volume' in p and p.get('quote_volume',0)>0 else "volume_pair_details_vol"
                qvol_display = f"{p.get('quote_volume',0):.0f}"
                vol_display = f"{p.get('volume',0):.0f}"
                text += _t(key, chat_id, index=i, pair=p['pair'], qvol_display=qvol_display, vol_display=vol_display, price_change=p.get('price_change',0)) + "\n"
                if i <= 6:
                    if i % 2 == 1: kb_rows.append([])
                    kb_rows[-1].append(InlineKeyboardButton(_t("button_trade_pair", chat_id, pair_name=p['pair']), callback_data=f"trade_{p['pair']}"))
        else: text += _t("volume_no_high_volume_pairs", chat_id)
        kb_rows.append([InlineKeyboardButton(_t("button_back_to_status", chat_id), callback_data="status")])
        target = update.callback_query.edit_message_text if update.callback_query else update.effective_message.reply_text
        await target(text, reply_markup=InlineKeyboardMarkup(kb_rows))

    async def trending_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        ma = self.trading_bot.market_analyzer if self.trading_bot else None
        if not ma:
            await (update.callback_query or update.message).reply_text(_t("error_market_analyzer_not_ready", chat_id))
            return
        pairs = ma.get_trending_pairs(10)
        text = f"{_t('trending_title', chat_id)}\n\n"
        kb_rows = []
        if pairs:
            for i, p in enumerate(pairs, 1):
                emoji = "🟢" if p.get('price_change',0) > 0 else ("🔴" if p.get('price_change',0) < 0 else "⚪")
                vol_display = f"QVol: {p.get('quote_volume',0):.0f}" if 'quote_volume' in p and p.get('quote_volume',0)>0 else f"Vol: {p.get('volume',0):.0f}"
                text += _t("trending_pair_details", chat_id, index=i, pair=p['pair'], emoji=emoji, price_change=p.get('price_change',0), vol_display=vol_display) + "\n"
                if i <= 6:
                    if i % 2 == 1: kb_rows.append([])
                    kb_rows[-1].append(InlineKeyboardButton(_t("button_trade_pair", chat_id, pair_name=p['pair']), callback_data=f"trade_{p['pair']}"))
        else: text += _t("trending_no_trending_pairs", chat_id)
        kb_rows.append([InlineKeyboardButton(_t("button_back_to_status", chat_id), callback_data="status")])
        target = update.callback_query.edit_message_text if update.callback_query else update.effective_message.reply_text
        await target(text, reply_markup=InlineKeyboardMarkup(kb_rows))

    async def trading_modes_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        text = f"{_t('trading_modes_title', chat_id)}\n\n"
        for name, s in TRADING_MODES.items():
            desc_key = s.get("description_key", "trading_modes_desc_default") # Fallback key
            description = _t(desc_key, chat_id) if desc_key in translations.get(_get_user_language(chat_id), {}) else name.replace('_',' ').capitalize()

            text += _t("trading_modes_mode_details", chat_id,
                       name=name.replace('_',' ').capitalize(), description=description,
                       tp=s['take_profit'], sl=s['stop_loss'], time=s['max_trade_time'], trades=s['max_trades'],
                       vol_thresh=s.get('volume_threshold','N/A'), price_change_thresh=s.get('price_change_threshold','N/A'))
        
        # AI Dynamic Mode special mention
        text += f"\n📌 {_t('status_ai_dynamic_mode', chat_id)}: {_t('trading_modes_desc_ai_dynamic', chat_id)}\n"
        
        kb = [[InlineKeyboardButton(_t("button_back_to_config", chat_id), callback_data="config")]]
        target = update.callback_query.edit_message_text if update.callback_query else update.effective_message.reply_text
        try: await target(text, reply_markup=InlineKeyboardMarkup(kb))
        except Exception as e:
            logger.error(_t("error_send_trading_modes_message_too_long", chat_id, e=e))
            await target(text[:4000], reply_markup=InlineKeyboardMarkup(kb))

    async def whale_config_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        if not self.trading_bot:
            await (update.callback_query or update.message).reply_text(_t("error_bot_not_initialized", chat_id))
            return
        cfg = self.trading_bot.config
        det_btn_key = "button_toggle_whale_detection_disable" if cfg.get('whale_detection') else "button_toggle_whale_detection_enable"
        auto_btn_key = "button_toggle_auto_trade_whale_disable" if cfg.get('auto_trade_on_whale') else "button_toggle_auto_trade_whale_enable"
        kb = [
            [InlineKeyboardButton(_t(det_btn_key, chat_id), callback_data="toggle_whale_detection")],
            [InlineKeyboardButton(_t(auto_btn_key, chat_id), callback_data="toggle_auto_trade_whale")],
            [InlineKeyboardButton(_t("button_strategy_follow_whale", chat_id), callback_data="strategy_follow_whale"),
             InlineKeyboardButton(_t("button_strategy_counter_whale", chat_id), callback_data="strategy_counter_whale")],
            [InlineKeyboardButton(_t("button_cycle_whale_threshold", chat_id, threshold=cfg.get('whale_threshold',0)), callback_data="cycle_whale_threshold")],
            [InlineKeyboardButton(_t("button_back_to_config", chat_id), callback_data="config")]
        ]
        text = (
            f"{_t('whale_config_title', chat_id)}\n\n"
            f"{_t('whale_config_detection_status', chat_id, status=(_t('status_on', chat_id) if cfg.get('whale_detection') else _t('status_off', chat_id)))}\n"
            f"{_t('whale_config_auto_trade_status', chat_id, status=(_t('status_on', chat_id) if cfg.get('auto_trade_on_whale') else _t('status_off', chat_id)))}\n"
            f"{_t('whale_config_strategy_status', chat_id, strategy=cfg.get('trading_strategy','N/A'))}\n"
            f"{_t('whale_config_threshold_status_mock', chat_id, threshold=cfg.get('whale_threshold',0))}"
        )
        target = update.callback_query.edit_message_text if update.callback_query else update.effective_message.reply_text
        await target(text, reply_markup=InlineKeyboardMarkup(kb))

    async def start_trading_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        if not self.trading_bot:
            await update.effective_message.reply_text(_t("error_bot_not_initialized", chat_id))
            return
        if self.trading_bot.running:
             await update.effective_message.reply_text(_t("trading_modes_engine_already_running", chat_id, current_mode=self.trading_bot.config.get('trading_mode','N/A')))
             return
        if self.trading_bot.config.get("use_real_trading") and \
           (not self.trading_bot.config.get("api_key") or self.trading_bot.config.get("api_key", "").startswith("YOUR_") or \
            not self.trading_bot.config.get("api_secret") or self.trading_bot.config.get("api_secret", "").startswith("YOUR_")):
            await update.effective_message.reply_text(_t("trading_modes_cannot_start_real_no_api", chat_id))
            return
        await self.show_trading_mode_selection(update, context, for_starting_trade=True)

    async def show_trading_mode_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, for_starting_trade=False):
        chat_id = update.effective_chat.id
        action_verb = "Start with" if for_starting_trade else "Set to" # Not translated, internal logic
        cb_prefix = "start_mode_" if for_starting_trade else "set_mode_"
        current_mode = self.trading_bot.config.get('trading_mode', 'N/A') if self.trading_bot else 'N/A'
        
        text = f"{_t('trading_modes_select_action', chat_id, action_verb=action_verb.upper())}\n"
        text += f"{_t('trading_modes_current_mode_display', chat_id, current_mode=current_mode.capitalize())}\n\n"
        kb = []
        for name, s in TRADING_MODES.items():
            text += _t("trading_modes_select_mode_option", chat_id, name=name.replace('_',' ').capitalize(), tp=s['take_profit'], sl=s['stop_loss']) + "\n"
            kb.append([InlineKeyboardButton(f"{action_verb} {name.replace('_',' ').capitalize()}", callback_data=f"{cb_prefix}{name}")])
        kb.append([InlineKeyboardButton(_t("button_cancel_back_to_status", chat_id), callback_data="status")])
        target = update.callback_query.edit_message_text if update.callback_query else update.effective_message.reply_text
        await target(text, reply_markup=InlineKeyboardMarkup(kb))

    async def stop_trading_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        if not self.trading_bot:
            await update.effective_message.reply_text(_t("error_bot_not_initialized", chat_id))
            return
        if self.trading_bot.stop_trading(chat_id):
            await update.effective_message.reply_text(_t("trading_modes_stopped_success", chat_id))
        else:
            await update.effective_message.reply_text(_t("trading_modes_already_stopped", chat_id))

    async def set_ai_mode_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        if not self.trading_bot:
            await (update.callback_query or update.message).reply_text(_t("error_bot_not_initialized", chat_id))
            return
        
        cfg = self.trading_bot.config
        cfg["ai_dynamic_mode"] = not cfg.get("ai_dynamic_mode", False)
        self.trading_bot.apply_trading_mode_settings(chat_id) # Re-apply mode settings

        if cfg["ai_dynamic_mode"]:
            msg = _t("trading_modes_ai_dynamic_mode_enabled", chat_id)
            # Try to get initial AI parameters for a default pair like BNBUSDT to show an example
            # This can be slow, so consider making it optional or showing a "Fetching initial AI params..." message
            if gemini_model: # Only if AI is configured
                initial_ai_advice = self.trading_bot.get_ai_trade_advice("BNBUSDT", chat_id_context=chat_id)
                if initial_ai_advice:
                    msg += "\n" + _t("trading_modes_ai_current_params", chat_id, pair="BNBUSDT", 
                                     tp=initial_ai_advice['tp_percentage'], sl=initial_ai_advice['sl_percentage'], 
                                     rationale=initial_ai_advice['rationale'])
                else:
                    msg += "\n" + _t("trading_modes_ai_params_not_set", chat_id)
        else:
            msg = _t("trading_modes_ai_dynamic_mode_disabled", chat_id, previous_mode=cfg.get('trading_mode', 'default'))
        
        target = update.callback_query.edit_message_text if update.callback_query else update.effective_message.reply_text
        await target(msg)
        # Optionally, refresh the config or status view
        if update.callback_query: await self.config_command(update, context)


    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id # Get chat_id for translations
        if not self.trading_bot:
             if update.callback_query: await update.callback_query.answer(_t("error_bot_not_initialized", chat_id), show_alert=True)
             return

        query = update.callback_query
        await query.answer()
        data = query.data

        # Language setting
        if data.startswith("set_lang_"):
            lang_code_to_set = data.replace("set_lang_", "")
            if _set_user_language(chat_id, lang_code_to_set):
                await query.edit_message_text(_t("language_changed_to", chat_id, lang=lang_code_to_set.upper()))
                await self.start_command(update, context) # Show main menu in new language
            else:
                await query.edit_message_text(_t("language_change_failed", chat_id))
            return

        if data == "status": await self.status_command(update, context); return
        if data == "config": await self.config_command(update, context); return
        if data == "volume": await self.volume_command(update, context); return
        if data == "trending": await self.trending_command(update, context); return
        if data == "select_trading_mode_start": await self.show_trading_mode_selection(update, context, for_starting_trade=True); return
        if data == "select_trading_mode_set": await self.show_trading_mode_selection(update, context, for_starting_trade=False); return
        if data == "toggle_ai_mode": await self.set_ai_mode_command(update, context); return


        if data.startswith("start_mode_") or data.startswith("set_mode_"):
            is_starting = data.startswith("start_mode_")
            mode_key = data.split("_", 2)[-1]
            cfg = self.trading_bot.config
            if mode_key in TRADING_MODES:
                cfg["trading_mode"] = mode_key
                self.trading_bot.apply_trading_mode_settings(chat_id)
                tm_cfg = TRADING_MODES[mode_key]
                if is_starting:
                    cfg["trading_enabled"] = True
                    if cfg.get("use_real_trading") and \
                       (not cfg.get("api_key") or cfg.get("api_key","").startswith("YOUR_") or \
                        not cfg.get("api_secret") or cfg.get("api_secret","").startswith("YOUR_")):
                        await query.edit_message_text(_t("trading_modes_cannot_start_real_no_api", chat_id))
                        return
                    if self.trading_bot.start_trading(chat_id):
                        await query.edit_message_text(_t("trading_modes_started_success", chat_id, mode_name=mode_key.replace('_',' ').capitalize(),
                                                          tp=tm_cfg['take_profit'], sl=tm_cfg['stop_loss'], max_time=tm_cfg['max_trade_time']))
                    else:
                        await query.edit_message_text(_t("trading_modes_start_failed_or_running", chat_id, current_mode=cfg.get('trading_mode','N/A').replace('_',' ').capitalize()))
                else:
                     await query.edit_message_text(_t("trading_modes_set_success", chat_id, mode_name=mode_key.replace('_',' ').capitalize(),
                                                      tp=tm_cfg['take_profit'], sl=tm_cfg['stop_loss'], max_time=tm_cfg['max_trade_time']))
            else: await query.edit_message_text(_t("trading_modes_error_not_found", chat_id, mode_name=mode_key))
            return

        if data == "stop_trading":
            if self.trading_bot.stop_trading(chat_id): await query.edit_message_text(_t("trading_modes_stopped_success", chat_id))
            else: await query.edit_message_text(_t("trading_modes_already_stopped", chat_id))
            return

        if data.startswith("trade_"):
            pair = data.replace("trade_", "")
            if not self.trading_bot.running or not self.trading_bot.config.get("trading_enabled"):
                await query.answer(_t("trade_engine_not_active_manual", chat_id), show_alert=True)
                return
            if not self.trading_bot.market_analyzer:
                await query.answer(_t("trade_market_analyzer_not_ready_manual", chat_id), show_alert=True)
                return
            pair_data = self.trading_bot.market_analyzer.get_pair_data(pair)
            if pair_data and pair_data.get("last_price",0) > 0:
                trade_type = "BUY" if pair_data.get("price_change",0) > 0 else "SELL"
                if any(t['pair'] == pair and not t.get('completed', False) for t in ACTIVE_TRADES):
                    await query.answer(_t("trade_pair_already_active", chat_id, pair=pair), show_alert=True)
                    return
                trade = self.trading_bot.create_trade(pair, trade_type, pair_data["last_price"], chat_id_for_trade=chat_id)
                if trade:
                    details = f"Manual Selection ({pair})" # Not translated, internal detail
                    msg = self.trading_bot._format_trade_notification(trade, details, "trade_notification_new_auto_selected", chat_id)
                    await context.bot.send_message(chat_id=query.message.chat_id, text=msg, parse_mode=ParseMode.HTML)
                    await query.edit_message_text(_t("trade_initiate_manual_success", chat_id, pair=pair), reply_markup=None)
                else: await query.answer(_t("trade_initiate_manual_fail", chat_id, pair=pair), show_alert=True)
            else: await query.answer(_t("trade_initiate_manual_no_valid_data", chat_id, pair=pair), show_alert=True)
            return

        if data == "toggle_real_trading":
            if self.trading_bot.config.get("use_real_trading"): await self.disable_real_trading_command(update, context)
            else: await self.enable_real_trading_command(update, context)
            # Commands handle their own messages, so no edit_message_text here.
            # We might want to refresh the config view if called from there.
            # await self.config_command(update, context) # This will refresh the config menu
            return
        if data == "toggle_percentage_based": self.trading_bot.config["use_percentage"] = not self.trading_bot.config.get("use_percentage", False); await self.config_command(update, context); return
        if data == "toggle_auto_select": self.trading_bot.config["auto_select_pairs"] = not self.trading_bot.config.get("auto_select_pairs", True); await self.config_command(update, context); return
        if data == "toggle_whale_detection": self.trading_bot.config["whale_detection"] = not self.trading_bot.config.get("whale_detection", True); await self.whale_config_command(update, context); return
        if data == "toggle_auto_trade_whale": self.trading_bot.config["auto_trade_on_whale"] = not self.trading_bot.config.get("auto_trade_on_whale", False); await self.whale_config_command(update, context); return
        if data == "strategy_follow_whale": self.trading_bot.config["trading_strategy"] = "follow_whale"; await self.whale_config_command(update, context); return
        if data == "strategy_counter_whale": self.trading_bot.config["trading_strategy"] = "counter_whale"; await self.whale_config_command(update, context); return
        if data == "cycle_whale_threshold":
            current = self.trading_bot.config.get("whale_threshold",100)
            thresholds = [10, 25, 50, 100, 200, 500]
            try: next_idx = (thresholds.index(current) + 1) % len(thresholds)
            except ValueError: next_idx = thresholds.index(100) if 100 in thresholds else 0
            self.trading_bot.config["whale_threshold"] = thresholds[next_idx]
            await self.whale_config_command(update, context)
            return

        if data.startswith("follow_whale_"):
            if not self.trading_bot.running or not self.trading_bot.config.get("trading_enabled"):
                await query.answer(_t("whale_follow_engine_not_active", chat_id), show_alert=True); return
            whale_id = int(data.split("_")[2])
            whale_tx = next((w for w in MOCK_WHALE_TRANSACTIONS if w['id'] == whale_id), None)
            if not whale_tx: await query.answer(_t("whale_follow_tx_not_found", chat_id, whale_id=whale_id), show_alert=True); return
            if any(t['pair'] == whale_tx['token'] and not t.get('completed', False) for t in ACTIVE_TRADES):
                await query.answer(_t("trade_pair_already_active", chat_id, pair=whale_tx['token']), show_alert=True); return
            trade_obj = self.trading_bot.create_trade_from_whale(whale_tx, whale_tx['type'], is_auto_trade=False, chat_id_for_trade=chat_id)
            if trade_obj: await query.edit_message_text(_t("whale_follow_attempt_success", chat_id, whale_id=whale_id, token=whale_tx['token']), reply_markup=None)
            else: await query.answer(_t("whale_follow_attempt_fail", chat_id, whale_id=whale_id), show_alert=True)
            return
        if data.startswith("ignore_whale_"):
            whale_id = int(data.split("_")[2])
            await query.edit_message_text(_t("whale_ignore_success", chat_id, whale_id=whale_id), reply_markup=None)
            return

        logger.warning(_t("warning_unhandled_callback_query", DEFAULT_LANGUAGE, data=data))
        await query.answer(_t("error_action_not_implemented", chat_id), show_alert=True)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_authorized(update): return
        chat_id = update.effective_chat.id
        await update.effective_message.reply_text(_t("error_command_only_message", chat_id))

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
        # Determine chat_id for error message, even if update is not ideal
        chat_id_for_error = DEFAULT_LANGUAGE # Fallback lang
        if update and isinstance(update, Update) and update.effective_chat:
            chat_id_for_error = update.effective_chat.id
        elif context.chat_data and 'lang' in context.chat_data: # PTB might store lang here
            # This part is hypothetical, adapt if you store lang in chat_data
            pass # chat_id_for_error might be derivable if lang is known
        
        # Try to get a specific chat_id if possible for the error message
        target_chat_id_for_user_message = None
        if update and isinstance(update, Update) and update.effective_chat:
            target_chat_id_for_user_message = update.effective_chat.id

        if target_chat_id_for_user_message:
            try:
                await context.bot.send_message(chat_id=target_chat_id_for_user_message,
                    text=_t("error_processing_request", target_chat_id_for_user_message)
                )
            except Exception as e_send:
                logger.error(_t("error_exception_in_error_handler", DEFAULT_LANGUAGE, e=e_send))


    def run(self):
        logger.info(_t("info_telegram_polling_start", DEFAULT_LANGUAGE))
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        logger.info(_t("info_telegram_polling_stopped", DEFAULT_LANGUAGE))

    def set_trading_bot(self, trading_bot):
        self.trading_bot = trading_bot

def main():
    _load_translations() # Ensure translations are loaded first

    if BINANCE_API_KEY and BINANCE_API_KEY != "YOUR_BINANCE_API_KEY": CONFIG["api_key"] = BINANCE_API_KEY
    if BINANCE_API_SECRET and BINANCE_API_SECRET != "YOUR_BINANCE_API_SECRET": CONFIG["api_secret"] = BINANCE_API_SECRET

    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or not TELEGRAM_BOT_TOKEN:
        print(_t("warning_critical_telegram_token_not_set", DEFAULT_LANGUAGE)) # Use default lang for console
        logger.critical(_t("warning_critical_telegram_token_not_set", DEFAULT_LANGUAGE))
        return
    if not ADMIN_USER_IDS or ADMIN_USER_IDS == [123456789]:
        print(_t("warning_admin_ids_not_set_default", DEFAULT_LANGUAGE))
        logger.warning(_t("warning_admin_ids_not_set_default", DEFAULT_LANGUAGE))

    telegram_handler = TelegramBotHandler(TELEGRAM_BOT_TOKEN, ADMIN_USER_IDS)
    trading_bot = TradingBot(CONFIG, telegram_handler)
    whale_detector = WhaleDetector(CONFIG, trading_bot, ADMIN_USER_IDS[0] if ADMIN_USER_IDS else None) # Pass a default chat_id
    
    trading_bot.set_whale_detector(whale_detector)
    telegram_handler.set_trading_bot(trading_bot)

    print(_t("info_bot_starting_message", DEFAULT_LANGUAGE))
    print(_t("info_admin_ids_configured", DEFAULT_LANGUAGE, admin_ids=ADMIN_USER_IDS))
    print(_t("info_initial_config_glance", DEFAULT_LANGUAGE,
             real_trading=CONFIG.get('use_real_trading'), testnet=CONFIG.get('use_testnet'), mock_mode=CONFIG.get('mock_mode')))
    print(_t("info_default_trade_amounts", DEFAULT_LANGUAGE, amount=CONFIG.get('amount'), min_bnb_per_trade=CONFIG.get('min_bnb_per_trade')))
    print(_t("info_ctrl_c_to_stop", DEFAULT_LANGUAGE))

    try:
        telegram_handler.run()
    except KeyboardInterrupt:
        logger.info(_t("info_shutdown_signal_received", DEFAULT_LANGUAGE))
    except Exception as e:
        logger.critical(_t("error_critical_main_execution", DEFAULT_LANGUAGE, e=e), exc_info=True)
    finally:
        logger.info(_t("info_graceful_stop_attempt", DEFAULT_LANGUAGE))
        if trading_bot and trading_bot.running:
            trading_bot.stop_trading(ADMIN_USER_IDS[0] if ADMIN_USER_IDS else None)
        logger.info(_t("info_bot_shutdown_complete", DEFAULT_LANGUAGE))

if __name__ == "__main__":
    main()

