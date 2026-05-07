import argparse
import sys

from common.registry.registry import class_registry
from client import upbit_client

TRADE_PLATFORM = {
    "upbit"
}

def make_object(name: str, *args, **kwargs):
    try:
        cls = class_registry[name]
    except KeyError:
        raise ValueError(f"Unknown class: {name}")
    return cls(*args, **kwargs)


def main():
    p = argparse.ArgumentParser(description="코인 및 주식 자동매매")
    p.add_argument("-p", "--platform", help=f"거래할 플랫폼.\n{TRADE_PLATFORM}", required=True)
    p.add_argument("-n", "--no", help=f"알고리즘 번호.", default=1)
    args = p.parse_args()

    if args.platform.lower() not in TRADE_PLATFORM:
        print("지원하는 플랫폼을 선택해주세요.")
        print(f"지원목록: {', '.join(TRADE_PLATFORM)}")
        sys.exit(1)

    obj = make_object(args.platform, args.no)

if __name__ == "__main__":
    main()



