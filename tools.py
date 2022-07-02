
from pytz import timezone
import datetime
import time
import sqlite3 as lite


def is_trading_hours(zone='EST', start=datetime.time(9, 30, 0), end=datetime.time(16, 0, 0)):
    st = timezone(zone)
    now = datetime.datetime.time(datetime.datetime.now(st))
    day = datetime.datetime.today().strftime('%A')

    if day.lower() == "saturday" or day.lower() == 'sunday':
        return False

    if start <= end:
        return start <= now <= end
    else:
        return start <= now or now <= end


def submit_trade(limit_price, api, stock_ticker, quantity,  side='buy', trade_type='limit', time_in_force='gtc',
                 stop_price=None, client_order_id=None, extended_hours=None):
    st = timezone('EST')
    now = datetime.datetime.now(st)

    record_trades(stock_ticker, quantity, side, trade_type, now, limit_price)

    api.submit_order(stock_ticker, quantity, side, trade_type, time_in_force, limit_price=limit_price,
                     stop_price=stop_price, client_order_id=client_order_id, extended_hours=extended_hours)

    print(f"Ok, decided to submit a limit {side} order for {quantity} {stock_ticker} stocks with a limit price of "
          f"{limit_price}")
    print(f"Time is: {now}")


def trade_in_time_period(api, stock_ticker, trade_type, day_range, zone='UTC', result_limit=200):

    # Check for pending orders
    pending_orders = check_for_pending(api, stock_ticker, trade_type, day_range)

    if pending_orders:
        return True

    # Check closed
    all_orders = api.list_orders(status='all', limit=result_limit)

    for orders in all_orders:

        if str(trade_type).lower() == 'both':
            # Check if order went through
            is_not_failed = orders.failed_at is None

            # Check if same stock ticker
            is_same_sym = str(orders.symbol).lower() == stock_ticker.lower()

            if is_not_failed and is_same_sym:
                if orders.filled_at is not None:

                    # Check order was filled in range
                    is_in_range = in_range(orders.filled_at, days=day_range, zone=zone)
                    if is_in_range:
                        return True

        if str(trade_type).lower() == 'sell' or str(trade_type).lower() == 'buy':

            # Filter for trade type
            is_trade_type = str(orders.side).lower() == str(trade_type).lower()

            # Check if order went through
            is_not_failed = orders.failed_at is None

            # Check if same stock ticker
            is_same_sym = str(orders.symbol).lower() == stock_ticker.lower()

            if is_trade_type and is_not_failed and is_same_sym:
                if orders.filled_at is not None:

                    # Check order was filled in range
                    is_in_range = in_range(orders.filled_at, days=day_range, zone=zone)
                    if is_in_range:
                        return True

    return False


def check_for_pending(api, stock_ticker, trade_type, day_range, zone='UTC', result_limit=200):

    all_orders = api.list_orders(status='open', limit=result_limit)

    for orders in all_orders:

        if str(trade_type).lower() == 'both':

            # Check if same stock ticker
            is_same_sym = str(orders.symbol).lower() == stock_ticker.lower()

            if is_same_sym:
                if orders.submitted_at is not None:

                    # Check order was submitted in range
                    is_in_range = in_range(orders.submitted_at, days=day_range, zone=zone)
                    if is_in_range:
                        return True

        if str(trade_type).lower() == 'sell' or str(trade_type).lower() == 'buy':

            # Filter for trade type
            is_trade_type = str(orders.side).lower() == str(trade_type).lower()

            # Check if same stock ticker
            is_same_sym = str(orders.symbol).lower() == stock_ticker.lower()

            if is_trade_type and is_same_sym:
                if orders.submitted_at is not None:

                    # Check order was filled in range
                    is_in_range = in_range(orders.submitted_at, days=day_range, zone=zone)
                    if is_in_range:
                        return True

    return False


def in_range(timestamp, days, zone):

    st = timezone(zone)
    now = datetime.datetime.now(st)
    difference = now - timestamp

    # If checking to see if a trade happened today, check for differences less than 1 day
    if days == 1:
        if difference.days >= days:
            return False

    # If checking for more than a day, include that day in range
    if difference.days <= days:
        return True

    return False


def record_trades(stock_ticker, quantity, side, trade_type, now, limit_price, txt_file="./trades.txt",
                  sqlite_db="trades.db"):
    # Insert into database
    con = lite.connect(sqlite_db)

    init_query = "CREATE TABLE IF NOT EXISTS record_trades(stock_ticker TEXT, quantity_traded INT, side TEXT," \
                 " trade_type TEXT, date TEXT, price TEXT)"

    query = "INSERT INTO record_trades (stock_ticker, quantity_traded, side, trade_type, date, price) VALUES" \
            " (?, ?, ?, ?, ?, ?)"

    with con:
        cur = con.cursor()
        cur.execute(init_query)
        cur.execute(query, (stock_ticker, quantity, side, trade_type, now, limit_price))

    # Save query in .txt file as well
    with open(f"{txt_file}", 'a') as file:  # Use file to refer to the file object
        txt_query = f"INSERT INTO record_trades (stock_ticker, quantity_traded, side, trade_type, date, price) " \
                f"VALUES({stock_ticker}, {quantity}, {side}, {trade_type}, {now}, {limit_price})"

        file.write(f"Query was {txt_query}")
        file.write("\n \n")


def get_last_bought_price(api, stock_ticker, result_limit=200):

    bought_price = 0
    num_of_shares_owned = 0

    # Find last bought price
    all_orders = api.list_orders(status='all', limit=result_limit, direction='desc')

    for orders in all_orders:

        # Filter for trade type
        is_trade_type = str(orders.side).lower() == 'buy'

        # Check if same stock ticker
        is_same_sym = str(orders.symbol).lower() == stock_ticker.lower()

        if is_trade_type and is_same_sym:

            # Only proceed if the order was filled
            if orders.filled_at is not None:
                bought_price = orders.filled_avg_price
                break

    # Find number of shares currently owned
    current_positions = api.list_positions()

    for positions in current_positions:
        sym = positions.symbol

        if str(sym).lower() == stock_ticker.lower():
            num_of_shares_owned = positions.qty

    return float(bought_price), float(num_of_shares_owned)


def currently_own_this_stock(api, stock_ticker):

    current_positions = api.list_positions()

    for positions in current_positions:
        sym = positions.symbol

        if str(sym).lower() == stock_ticker.lower():
            return True

    return False


def wait_time(seconds=300):

    timer = 0
    sleep_time = seconds
    left_to_go = sleep_time

    while True:
        if left_to_go <= 0:
            break

        if left_to_go >= 60:
            for x in range(60):
                print(f"Sleeping, on minute {timer + 1} out of {int(sleep_time / 60)}. Progress: {int((x / 60) * 100)}"
                      f"%\r", end="")

                time.sleep(1)

        if left_to_go < 60:
            time.sleep(left_to_go)

        left_to_go = left_to_go - 60

        timer += 1
