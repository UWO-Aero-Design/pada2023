#!/usr/bin/python3

import inspect
import argparse
import os

from pymavlink.dialects.v20 import ardupilotmega as mavlink

def parse_args():
    parser = argparse.ArgumentParser(description="Get the generated mavlink python source file")
    parser.add_argument('OUT', type=str, help="The file to save the returned python source file to")

    args = parser.parse_args()
    args.OUT = os.path.realpath(args.OUT)

    return args

def main():
    args = parse_args()

    src = inspect.getsource(mavlink)

    with open(args.OUT, 'w') as file:
        file.write(src)

    print(f"Wrote mavlink source to {args.OUT}")


if __name__ == "__main__":
    main()