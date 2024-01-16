# Tools
A collection of tools that are useful for interfacing with the PADA / mavlink devices

## List Mavlink Message Types From Device
*File: message_list.py*

Listen to the Mavlink messages from a device and save all unique message types to a file. Run this script for 30-45 seconds to allow it to read messages from the Mavlink device and then press ctrl+c to save the file and exit.

Requirements: `python3 -m pip install pymavlink`

Usage: `python3 message_list.py <mavlink connection> <output file>`

Example: `python3 message_list.py /dev/ttyUSB0 msg_types.txt`

`msg_types.txt`:
```
STATUSTEXT {severity : 4, text : RC Short Failsafe: switched to CIRCLE, id : 0, chunk_seq : 0}
TIMESYNC {tc1 : 0, ts1 : 17291190001}
HEARTBEAT {type : 1, autopilot : 3, base_mode : 89, custom_mode : 11, system_status : 5, mavlink_version : 3}
ATTITUDE {time_boot_ms : 22091, roll : 0.025583945214748383, pitch : 0.004224652890115976, yaw : -1.395102858543396, rollspeed : 7.286392792593688e-05, pitchspeed : -0.0006350307376123965, yawspeed : 0.0010424134088680148}
VFR_HUD {airspeed : 0.0, groundspeed : 0.0, heading : 280, throttle : 0, alt : 0.3799999952316284, climb : -0.0}
AOA_SSA {time_usec : 22091392, AOA : 0.0, SSA : 0.0}
SYS_STATUS {onboard_control_sensors_present : 325188671, onboard_control_sensors_enabled : 4291631, onboard_control_sensors_health : 51444751, load : 55, voltage_battery : 0, current_battery : -1, battery_remaining : -1, drop_rate_comm : 0, errors_comm : 0, errors_count1 : 0, errors_count2 : 0, errors_count3 : 0, errors_count4 : 0}
POWER_STATUS {Vcc : 4497, Vservo : 4465, flags : 0}
MEMINFO {brkval : 0, freemem : 65535, freemem32 : 66096}
```

## Get Mavlink Source Code
*File: get_mavlink_src.py*

The Mavlink source code is auto-generated so it can be hard to see all the functions that can be called on a `mav` device (eg. `mavutil.mavlink_connection().mav.heartbeat_send()`). This script will load the Mavlink source python file and save its contents to the specified directory. 

Requirements: `python3 -m pip install pymavlink`

Usage: `python3 get_mavlink_src.py <output file>`

Example: `python3 message_list.py mavlink.py`


## Convert DJI Video Telemetry Metadata to Mavlink
*File: dji_exif_to_mavlink.py*

TODO: description

Requirements: `python3 -m pip install pyexiftool parse pymavlink`

Usage: `python3 dji_exif_to_mavlink.py <input video> <output filename>`

Example: `python3 dji_exif_to_mavlink.py ./video.mp4 ./video_mavlink.txt`
