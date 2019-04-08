import os
import pytz
import sqlite3
import time

from datetime import datetime
from decimal import Decimal
from io import StringIO

from peewee import (fn, SqliteDatabase, Model, CharField, SmallIntegerField,
                    TimestampField, FloatField, CompositeKey, TextField,
                    BooleanField, DateTimeField, SQL, DecimalField, IntegerField)


db = SqliteDatabase(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data.db'))


class BaseModel(Model):
    class Meta:
        database = db


class CryptoStatus(BaseModel):
    crypto = CharField(unique=True)           # e.g. 'XLM'
    date_tracking_started = DateTimeField()   # e.g. 1554595200

    high = DecimalField()
    date_high_set = DateTimeField(null=True)

    last_price = DecimalField(null=True)
    current_percentage = DecimalField(null=True)
    date_last_update = DateTimeField(null=True)

    @property
    def date_high_set_str(self):
        dt = datetime.fromtimestamp(self.date_high_set)
        return dt.strftime("%Y-%m-%d")

    def update_with_candle(self, candle_price, candle_timestamp):
        # Standardize precision
        candle_price = candle_price.quantize(Decimal('.000001'))

        # Compare previous CS high vs most recent candle price
        if candle_price > self.high:
            # print("New high found: %0.6f > %0.6f" % (candle_price, self.high))
            self.high = candle_price
            self.date_high_set = candle_timestamp

        self.last_price = candle_price
        self.current_percentage = (candle_price / self.high).quantize(Decimal('.0001'))
        self.date_last_update = candle_timestamp
        self.save()


if not CryptoStatus.table_exists():
    CryptoStatus.create_table(True)
