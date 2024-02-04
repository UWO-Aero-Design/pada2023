import subprocess
import os
import json
import csv
import argparse
import math
import shutil
import pandas as pd
from datetime import datetime, timezone
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# aero-pada % find /Users/jeff/Desktop/2024-01-31/*.tlog -type f -print0 | xargs -0 -I {} python3 telemetry_processor/telemetry_processor.py -m ~/code/pymavlink/tools/mavlogdump.py --all --overwrite "{}"

def parse_args():
    parser = argparse.ArgumentParser(description="Analyze PADA video and telemetry to attempt lamding at markers")
    parser.add_argument('INPUT', type=str, help="The telemetry log to process (.tlog file)")
    parser.add_argument('-o', '--output', type=str, help="The path directory to output the files to")
    parser.add_argument('-m', '--mavlogdump', type=str, default='mavlogdump.py', help="The path to the mavlogdump.py executable")
    parser.add_argument('-t', '--no-copy-tlog', action='store_true', help="Don't copy the .tlog file to the output directory")
    parser.add_argument('-w', '--overwrite', action='store_true', help="Allow overwriting of the output directory")
    parser.add_argument('-a', '--all', action='store_true', help="Enable all export formats")
    parser.add_argument('-c', '--csv', action='store_true', help="Output a csv for each mavlink message")
    parser.add_argument('-e', '--excel', action='store_true', help="Output an Excel file with the data")
    parser.add_argument('-r', '--report', action='store_true', help="Output an HTML report")

    args = parser.parse_args()
    
    if(args.output is None):
        input_name = os.path.splitext(os.path.basename(args.INPUT))[0]
        output_name = input_name.replace(' ', '_')
        args.output = os.path.join(os.path.dirname(args.INPUT), output_name)

    if(args.all):
        args.csv = True
        args.excel = True
        args.report = True

    args.INPUT = os.path.expanduser(args.INPUT)
    args.output = os.path.expanduser(args.output)
    args.mavlogdump = os.path.expanduser(args.mavlogdump)

    return args

def tlog2lists(file, mavlogdump):
    cmd = ['python3', mavlogdump, file, '--format', 'json']
    try:
        ret = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        print(f"{exc.output}\n\nMavlogdump failed with above error while processing input: {file}")
        return None
    else:
        json_lines = ret.decode().split('\n')
        tlm_lines = [json.loads(x) for x in json_lines if len(x.strip()) > 0]

        messages = {}
        for tlm_value in tlm_lines:
            msg_type, timestamp, data = tlm_value['meta']['type'], tlm_value['meta']['timestamp'], tlm_value['data']
            if msg_type not in messages:
                messages[msg_type] = []
            messages[msg_type].append((timestamp, data))

        return messages

def export_csv(output_dir, messages):
    os.makedirs(output_dir, exist_ok=True)
    for msg_type in messages.keys():
        with open(os.path.join(output_dir, f"{msg_type.lower()}.csv"), 'w') as file:
            writer = csv.writer(file)
            headers = ['timestamp'] + list(messages[msg_type][0][1].keys())
            writer.writerow(headers)
            for tlm_value in messages[msg_type]:
                row = [tlm_value[0]] + list(tlm_value[1].values())
                writer.writerow(row)

def message2df(message):
    rows = []
    for timestamp, metrics in message:
        row = {'timestamp': timestamp}
        row.update(metrics)
        rows.append(row)

    return pd.DataFrame(rows)

def export_excel(output_dir, messages):
    os.makedirs(output_dir, exist_ok=True)

    with pd.ExcelWriter(os.path.join(output_dir, f"data.xlsx")) as writer:
        for message in messages.keys():
            data = message2df(messages[message])
            data.to_excel(writer, sheet_name=message.lower(), index=None)


def export_report(output_dir, messages):
    os.makedirs(output_dir, exist_ok=True)

    fig = make_subplots(
        rows=3, 
        cols=2, 
        subplot_titles=[
            "X", 
            "X", 
            "X", 
            "X",
            "X"
            ]
        )
    
    min_timestamp = None
    max_timestamp = None

    for key in messages:
        timestamps = [item[0] for item in messages[key]]
        if timestamps:
            min_key_timestamp = min(timestamps)
            max_key_timestamp = max(timestamps)
            min_timestamp = min(min_timestamp, min_key_timestamp) if min_timestamp is not None else min_key_timestamp
            max_timestamp = max(max_timestamp, max_key_timestamp) if max_timestamp is not None else max_key_timestamp

    flight_time = max_timestamp-min_timestamp

    fig.update_layout(title_text=f"Flight on {os.path.basename(output_dir)} (Duration: {flight_time:.1f}s)")

    if('VFR_HUD' in messages.keys()):
        vfr = message2df(messages['VFR_HUD'])

        vfr['localtime'] = [datetime.utcfromtimestamp(t).replace(tzinfo=timezone.utc).astimezone() for t in vfr['timestamp']]
        maximum = vfr.max()
        fig.layout.annotations[0].update(text=f"Altitude (VFR_HUD) - Max: {maximum['alt']:.2f}m")

        # Altitude
        fig.layout.annotations[0].update(text=f"Altitude - Max: {maximum['alt']:.2f}m")
        fig.add_trace(go.Scatter(x=vfr['localtime'], y=vfr['alt'], mode='lines', name='Altitude'), row=1, col=1)
        fig.update_yaxes(title_text=f"Altitude (m)", row=1, col=1)
        fig.update_xaxes(title_text="Timestamp", row=1, col=1)

        # Air speed
        fig.layout.annotations[1].update(text=f"Airspeed vs Time (VFR_HUD) - Max: {maximum['airspeed']:.2f}m/s")
        fig.add_trace(go.Scatter(x=vfr['localtime'], y=vfr['airspeed'], mode='lines', name='Airspeed'), row=1, col=2)
        fig.update_yaxes(title_text="Airspeed (m/s)", row=1, col=2)
        fig.update_xaxes(title_text="Timestamp", row=1, col=2)

        # Ground speed
        fig.layout.annotations[2].update(text=f"Groundspeed vs Time (VFR_HUD) - Max: {maximum['groundspeed']:.2f}m/s")
        fig.add_trace(go.Scatter(x=vfr['localtime'], y=vfr['groundspeed'], mode='lines', name='Groundspeed'), row=2, col=1)
        fig.update_yaxes(title_text="Groundspeed (m/s)", row=2, col=1)
        fig.update_xaxes(title_text="Timestamp", row=2, col=1)

    if('AHRS2' in messages.keys()):
        ahrs = message2df(messages['AHRS2'])

        ahrs['localtime'] = [datetime.utcfromtimestamp(t).replace(tzinfo=timezone.utc).astimezone() for t in ahrs['timestamp']]
        ahrs['yaw'] = ahrs['yaw'].apply(lambda x: math.degrees(x))
        ahrs['pitch'] = ahrs['pitch'].apply(lambda x: math.degrees(x))
        ahrs['roll'] = ahrs['roll'].apply(lambda x: math.degrees(x))

        fig.layout.annotations[3].update(text=f"Attitude vs Time (AHRS2)")
        fig.add_trace(go.Scatter(x=ahrs['localtime'], y=ahrs['yaw'], mode='lines', name='Yaw'), row=2, col=2)
        fig.add_trace(go.Scatter(x=ahrs['localtime'], y=ahrs['pitch'], mode='lines', name='Pitch'), row=2, col=2)
        fig.add_trace(go.Scatter(x=ahrs['localtime'], y=ahrs['roll'], mode='lines', name='Roll'), row=2, col=2)

        fig.update_yaxes(title_text=f"Attitude (degrees)", row=2, col=2)
        fig.update_xaxes(title_text="Timestamp", row=2, col=2)

    if('HEARTBEAT' in messages.keys()):
        MAV_TYPE_FIXED_WING = 1
        hb = message2df(messages['HEARTBEAT'])

        hb = hb.drop(hb[hb['type'] != MAV_TYPE_FIXED_WING].index)
        hb['mode_auto'] = [1 if (x & (1 << 2)) else 0 for x in hb['base_mode']]
        hb['mode_guided'] = [1 if (x & (1 << 3)) else 0 for x in hb['base_mode']]
        hb['mode_stabilize'] = [1 if (x & (1 << 4)) else 0 for x in hb['base_mode']]
        hb['mode_manual'] = [1 if (x & (1 << 6)) else 0 for x in hb['base_mode']]
        hb['mode_safety'] = [1 if (x & (1 << 7)) else 0 for x in hb['base_mode']]

        hb['localtime'] = [datetime.utcfromtimestamp(t).replace(tzinfo=timezone.utc).astimezone() for t in hb['timestamp']]

        fig.layout.annotations[4].update(text=f"Mode (HEARTBEAT)")
        fig.add_trace(go.Scatter(x=hb['localtime'], y=hb['mode_auto'], mode='lines', name='Auto'), row=3, col=1)
        fig.add_trace(go.Scatter(x=hb['localtime'], y=hb['mode_guided'], mode='lines', name='Guided'), row=3, col=1)
        fig.add_trace(go.Scatter(x=hb['localtime'], y=hb['mode_stabilize'], mode='lines', name='Stabilize'), row=3, col=1)
        fig.add_trace(go.Scatter(x=hb['localtime'], y=hb['mode_manual'], mode='lines', name='Manual'), row=3, col=1)
        fig.add_trace(go.Scatter(x=hb['localtime'], y=hb['mode_safety'], mode='lines', name='Safety'), row=3, col=1)

        fig.update_yaxes(title_text=f"Mode", row=3, col=1)
        fig.update_xaxes(title_text="Timestamp", row=3, col=1)

    fig.write_html(os.path.join(output_dir, "report.html"))

def main():
    args = parse_args()

    if(args.INPUT == args.output):
        print(f"Error: Input file and output file is the same: {args.INPUT}")

    if(not os.path.exists(args.INPUT)):
        print(f"Error: Input file does not exist: f{args.INPUT}")
        exit()

    if(not os.path.isfile(args.INPUT)):
        print(f"Error: Input file is not a file: f{args.INPUT}")
        exit()

    if(os.path.exists(args.output) and not args.overwrite):
        print(f"Error: Output directory already exists {args.output}")
        exit()

    messages = tlog2lists(args.INPUT, args.mavlogdump)
    if(messages is None):
        exit()

    exported = []

    if(args.csv):
        exported.append('CSV')
        export_csv(args.output, messages)

    if(args.excel):
        exported.append('Excel')
        export_excel(args.output, messages)

    if(args.report):
        exported.append('Report')
        export_report(args.output, messages)

    if(not exported):
        print("Warning: no export formats were chosen")
    else:
        if(not args.no_copy_tlog):
            shutil.copy2(args.INPUT, args.output)
        print(f"Exported formats: {', '.join(exported)} to '{args.output}'")


if __name__ == "__main__":
    main()
