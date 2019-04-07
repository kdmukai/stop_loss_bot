import argparse
import boto3
import configparser
import cryptocompare
import datetime
import json
import time

from decimal import Decimal

from stop_loss_bot.models import CryptoStatus



def get_timestamp():
    ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


parser = argparse.ArgumentParser(description='stop_loss_bot.py -- simple stop-loss monitoring, notification, and execution tool')

# Required positional arguments
# parser.add_argument('order_side', type=str,
#                     help="BUY or SELL")

# Optional switches
parser.add_argument('-c', '--settings',
                    default="settings.conf",
                    dest="settings_config",
                    help="Override default settings config file location")


if __name__ == "__main__":
    args = parser.parse_args()

    # market_currency = args.market_currency

    # Read settings
    arg_config = configparser.ConfigParser()
    arg_config.read(args.settings_config)

    # cryptocompare_key = arg_config.get('API_KEYS', 'CRYPTOCOMPARE_KEY')

    coinbasepro_cryptos = arg_config.get('PORTFOLIO', 'COINBASEPRO_CRYPTOS').split(',')
    binance_cryptos = arg_config.get('PORTFOLIO', 'BINANCE_CRYPTOS').split(',')
    bittrex_cryptos = arg_config.get('PORTFOLIO', 'BITTREX_CRYPTOS').split(',')
    misc_cryptos = arg_config.get('PORTFOLIO', 'MISC_CRYPTOS').split(',')

    sns_topic = arg_config.get('AWS', 'SNS_TOPIC')
    aws_access_key_id = arg_config.get('AWS', 'AWS_ACCESS_KEY_ID')
    aws_secret_access_key = arg_config.get('AWS', 'AWS_SECRET_ACCESS_KEY')

    # Prep boto SNS client for email notifications
    sns = boto3.client(
        "sns",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name="us-east-1"     # N. Virginia
    )

    cryptos = set()
    if coinbasepro_cryptos:
        cryptos.update(coinbasepro_cryptos)
    if binance_cryptos:
        cryptos.update(binance_cryptos)
    if bittrex_cryptos:
        cryptos.update(bittrex_cryptos)
    if misc_cryptos:
        cryptos.update(misc_cryptos)

    print(cryptos)

    def process_candle(data, cs, is_current_candle=True):
        candle_timestamp = candle['time']
        if is_current_candle:
            candle_price = Decimal(candle['open'])
        else:
            candle_price = Decimal(candle['close'])

        # print("%s: $%0.8f" % (crypto, candle_price))

        cs.update_with_candle(candle_price, candle_timestamp)


    for crypto in cryptos:
        data = cryptocompare.get_historical_price_day(crypto, 'USD')
        if not data:
            print("%s: No data" % crypto)
            continue

        try:
            cs = CryptoStatus.get(CryptoStatus.crypto == crypto)

        except CryptoStatus.DoesNotExist:
            cs = CryptoStatus.create(
                crypto=crypto,
                date_tracking_started=data['Data'][-1]['time'],
                high=Decimal('0.0')
            )

            # Seed db with past 30 days
            for candle in data['Data'][-30:-1]:
                process_candle(candle, cs, is_current_candle=False)

        # Update for just-closed daily candle
        candle = data['Data'][-1]
        process_candle(candle, cs)

        print("%5s: %6.2f%% ($%0.6f)" % (crypto, cs.current_percentage * Decimal('100.0'), cs.high))


