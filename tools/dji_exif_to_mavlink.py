import argparse
import os
import exiftool
import parse
import json
from datetime import datetime, timedelta
from pymavlink.dialects.v20 import ardupilotmega as mavlink

def parse_args():
    parser = argparse.ArgumentParser(description="Convert EXIF Metadata telemetry from a DJI video file to Mavlink telemetry")
    parser.add_argument('INPUT', type=str, help="The DJI video file to read in")

    args = parser.parse_args()
    args.INPUT = os.path.realpath(args.INPUT)

    return args

def get_vals(lines):
    return [x[x.find(':')+1:-1].strip() for x in lines]

def parse_text(string):
    FORMAT_STR = 'F/{f}, SS {ss}, ISO {iso}, EV {ev}, DZOOM {dzoom}, GPS ({lat}, {lon}, {idk}), D {d}m, H {h}m, H.S {hs}m/s, V.S {vs}m/s'
    return parse.parse(FORMAT_STR, string)

def parse_datetime(string):
    return datetime.strptime(string, "%Y:%m:%d %H:%M:%S.%f")

def main():
    args = parse_args()
    input_name = os.path.splitext(os.path.basename(args.INPUT))[0]

    with exiftool.ExifTool() as et:
        ret = et.execute('-ee3',  args.INPUT)
        lines = ret.splitlines()
        texts = get_vals(list(filter(lambda x: ("Text" in x), lines)))
        datetimes = get_vals(list(filter(lambda x: ("GPS Date/Time" in x), lines)))
        
        if(len(texts) != len(datetimes)):
            print(f"Error: found {len(texts)} and {len(datetimes)} when they should be equal")
            exit()

        vals = []

        for timestamp, text in zip(datetimes, texts):
            val = parse_text(text).named
            val['timestamp'] = timestamp
            vals.append(val)

        with open(f"{input_name}.json", 'w') as file:
            json.dump(vals, file)

        mav_msgs = []
        start_time = parse_datetime(vals[0]['timestamp'])
        for x in vals:
            # time_boot_ms: int, lat: int, lon: int, alt: int, relative_alt: int, vx: int, vy: int, vz: int, hdg: int
            time_boot = (parse_datetime(x['timestamp'])-start_time) / timedelta(milliseconds=1)
            mav_msgs.append(mavlink.MAVLink_global_position_int_message(time_boot, x['lat'], x['lon'], x['h'], x['h'], 0, 0, x['vs'], x['idk']))
        
        with open(f"{input_name}.mav", 'w') as file:
            strs = [str(x) for x in mav_msgs]
            file.write('\n'.join(strs))




if __name__ == "__main__":
    main()