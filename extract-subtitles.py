import ffmpeg

input_file = 'data-set\90degree_2.mp4'
output_file = 'data-set\90degree_2_telemetry.srt'

try:
    (
        ffmpeg
        .input(input_file)
        .output(output_file, map='0:s:0', scodec='srt')
        .run()
    )
except ffmpeg.Error as e:
    print('Error:', e)