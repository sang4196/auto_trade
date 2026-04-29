from common.util import can_convert_to_int

TRADE_PLATFORM = {
    1: "Upbit",
    2: "Binance"
}

if __name__ == "__main__":

    for key, flatform in TRADE_PLATFORM.items():
        print(f"{key} : {flatform}")

    selected_key = 0
    while True:
        select_key = input("Select the platform to trade : ")

        if can_convert_to_int(select_key) and int(select_key) > 0:
            break


