import argparse
import boto3
import configparser
import cryptocompare
import json

from decimal import Decimal

from stop_loss_bot import StopLossBot
from stop_loss_bot.models import CryptoStatus


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

    # Read settings
    arg_config = configparser.ConfigParser()
    arg_config.read(args.settings_config)

    warning_threshold = Decimal(arg_config.get('CORE', 'WARNING_THRESHOLD'))

    # cryptocompare_key = arg_config.get('API_KEYS', 'CRYPTOCOMPARE_KEY')

    coinbasepro_cryptos = arg_config.get('PORTFOLIO', 'COINBASEPRO_CRYPTOS').split(',')
    binance_cryptos = arg_config.get('PORTFOLIO', 'BINANCE_CRYPTOS').split(',')
    bittrex_cryptos = arg_config.get('PORTFOLIO', 'BITTREX_CRYPTOS').split(',')
    misc_cryptos = arg_config.get('PORTFOLIO', 'MISC_CRYPTOS').split(',')

    sns_topic__full_report = arg_config.get('AWS', 'SNS_TOPIC__FULL_REPORT')
    sns_topic__warnings = arg_config.get('AWS', 'SNS_TOPIC__WARNINGS')
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

    for crypto in sorted(cryptos):
        data = cryptocompare.get_historical_price_day(crypto, 'USD')
        if not data:
            print("%s: No data" % crypto)
            continue

        try:
            cs = CryptoStatus.get(CryptoStatus.crypto == crypto)
        except CryptoStatus.DoesNotExist:
            # Initialize with the last 30 days
            cs = StopLossBot.initialize_crypto(crypto, data['Data'][-30:-1])

        # Update for just-closed daily candle
        StopLossBot.process_candle(data['Data'][-1], cs)

    (full_report, warnings) = StopLossBot.generate_reports(warning_threshold)

    # Send the daily full report
    sns.publish(
        TopicArn=sns_topic__full_report,
        Subject="StopLossBot Daily Full Report",
        Message=full_report
    )

    if warnings:
        print(warnings)
        sns.publish(
            TopicArn=sns_topic__warnings,
            Subject="StopLossBot Warnings",
            Message=warnings
        )
