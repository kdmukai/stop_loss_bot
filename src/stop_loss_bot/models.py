import datetime
import os
import pytz
import sqlite3
import time

from datetime import timedelta
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
    # Unique together CompositeKey fields
    crypto = CharField()                      # e.g. 'XLM'
    date_tracking_started = DateTimeField()   # e.g. 1554595200

    high = DecimalField()
    date_high_set = DateTimeField(null=True)     # e.g. 1554595200

    current_percentage = DecimalField(null=True)     # e.g. 0.83 (> 1.0 means new high was just set)
    date_last_update = DateTimeField(null=True)      # e.g. 1554595200

    # class Meta:
        # Enforce 'unique together' constraint
        # primary_key = CompositeKey('market', 'interval', 'timestamp')


    def __str__(self):
        return f"{self.id}: {self.market} {self.interval} {self.timestamp}"

    @property
    def timestamp_utc(self):
        return time.ctime(self.timestamp)

    def update_with_candle(self, candle_price, candle_timestamp):
        # Compare previous CS high vs most recent candle price
        self.current_percentage = self.high / candle_price   # Will be > 1.0 if new high is set
        if candle_price > self.high:
            self.high = candle_price
            date_high_set = candle_timestamp

        self.date_last_update = candle_timestamp
        self.save()

if not CryptoStatus.table_exists():
    CryptoStatus.create_table(True)
