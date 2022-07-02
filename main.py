import alpaca_trade_api as tradeapi

API_KEY_ID=""
API_SECRET_KEY=""
BASE_URL=""


def main():
    global API_KEY_ID, API_SECRET_KEY, BASE_URL
    parse_var()
    api=tradeapi.REST(key_id=API_KEY_ID,secret_key=API_SECRET_KEY,api_version="v2",base_url=BASE_URL)
    api.submit_order(symbol="AMD",qty="1",side="buy",type="market",time_in_force="day")
    

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


