from pytz import timezone
import traceback
import alpaca_trade_api as tradeapi
import tools
import datetime

API_KEY_ID=""
API_SECRET_KEY=""
BASE_URL=""


def main():
    global API_KEY_ID, API_SECRET_KEY, BASE_URL
    parse_var()
    while True:
        try:
            stocks_list = ["AAPL", "MSFT","TSLA"]  
            st = timezone('EST')
            if tools.is_trading_hours():
                for stock in stocks_list:
                    now = datetime.datetime.now(st)
                    current_stock = stock
                    print(f"trading hours is on!! stock is: {current_stock}")
                    api=tradeapi.REST(key_id=API_KEY_ID,secret_key=API_SECRET_KEY,api_version="v2",base_url=BASE_URL)
                    tools.wait_time(60)
                    trading_strategy_1(api,current_stock)

                    if not tools.is_trading_hours():
                        break

            if not tools.is_trading_hours():
                now = datetime.datetime.now(st)
                print(f"Turns out it isn't trading time. Time is: {now}")
                tools.wait_time(seconds=1200)

        except Exception as e:
            # Save error in .txt file
            with open("log.txt", 'a') as f:  # Use file to refer to the file object

                f.write("\n \n")
                f.write(f"Stock ticker was {current_stock}")
                f.write("\n \n")
                f.write(f"Time is: {datetime.datetime.now()}")
                f.write(f"'exception_type: '{type(e).__name__}, \nerror_reason': {e.args}, \n\n")
                f.write(f"Traceback is: {traceback.format_exc()}")
                print(f"Breaking because of an error: {e}")




def trading_strategy_1(api, stock):
    account = api.get_account()
    currently_own_this_stock = tools.currently_own_this_stock(api, stock)
    api.submit_order(symbol=stock,qty="1",side="buy",type="market",time_in_force="day")


def parse_var(f="keys.txt"):
    global API_KEY_ID, API_SECRET_KEY, BASE_URL
    with open(f,"r") as file:
        content=file.read()
        env_var=content.split("\n")
        API_KEY_ID=env_var[0].split("=")[1]
        API_SECRET_KEY=env_var[1].split("=")[1]
        BASE_URL=env_var[2].split("=")[1]

if __name__=="__main__":
    main()


