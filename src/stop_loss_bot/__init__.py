from decimal import Decimal

from .models import CryptoStatus


class StopLossBot():

    @staticmethod
    def process_candle(candle, cs, is_current_candle=True):
        candle_timestamp = candle['time']
        if is_current_candle:
            candle_price = Decimal(candle['open'])
        else:
            candle_price = Decimal(candle['close'])

        # print("%s: $%0.8f" % (crypto, candle_price))

        cs.update_with_candle(candle_price, candle_timestamp)

    @staticmethod
    def initialize_crypto(crypto, candles):
        cs = CryptoStatus.create(
            crypto=crypto,
            date_tracking_started=candles[-1]['time'],
            high=Decimal('0.0')
        )

        # Seed db with past 30 days
        for candle in candles:
            StopLossBot.process_candle(candle, cs, is_current_candle=False)

        return cs

    @staticmethod
    def generate_reports(percent_threshold):
        str_full_report = ""
        str_warnings = ""
        for cs in CryptoStatus.select().order_by(CryptoStatus.current_percentage.desc(), CryptoStatus.crypto):
            status = "%5s: %6.2f%% | %s\n" % (cs.crypto, cs.current_percentage * Decimal('100.00'), cs.date_high_set_str)
            str_full_report += status
            if cs.current_percentage < percent_threshold:
                str_warnings += status

        return (str_full_report, str_warnings)
