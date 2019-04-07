# stop_loss_bot

## Purpose
Despite conventional wisdom, a pure HODL mindset is not all that wise when assets can drop as much as 95% in a typical crypto bear market. So we need to be vigilant about when a bear reversal is taking hold and take action to prevent further losses. Unfortunately it's inconvenient to constantly reset target alarms for individual assets while they are rising in a bull market. So the `stop_loss_bot` will track assets' higher highs and keep an eye on them as they start falling off those highs.

## Overview
The `stop_loss_bot` is meant to be run each day after the daily candle closes at 00:00 UTC. It will keep track of the highest daily closing price, starting when an asset is added to the watch list, and calculate the percent difference from that high to the just-closed day's closing price. If this percent difference is below a specified threshold, the `stop_loss_bot` will issue a warning notification.

## TODO: Automated stop-loss orders
Ideally the `stop_loss_bot` would live up to its name and actually place sell orders to liquidate falling assets. However, this would only work if you kept your assets on exchanges, which we know to be an unsafe practice.

But this may change with semi-centralized DEXes such as Binance's upcoming DEX. Hopefully an API will be available that will allow `stop_bot_loss` to initiate sell orders directly from owners' own secure wallets. It's not clear yet what kinds of permissions or preauthorizations might be needed to make this possible (or if it'll be possible at all).
