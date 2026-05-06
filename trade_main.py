import argparse
import sys

import upbit.upbit
from common.registry.registry import class_registry

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
    args = p.parse_args()

    if args.platform.lower() not in TRADE_PLATFORM:
        print("지원하는 플랫폼을 선택해주세요.")
        print(f"지원목록: {', '.join(TRADE_PLATFORM)}")
        sys.exit(1)

    obj = make_object(args.platform)

if __name__ == "__main__":
    main()



