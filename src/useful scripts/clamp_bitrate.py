import os
import subprocess
import tempfile
import sys

if sys.platform == "win32":
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
else:
    startupinfo = None

def get_bitrate(file_path):
    result = subprocess.run(
        [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'a:0',
            '-show_entries', 'stream=bit_rate',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path
        ],
        shell=True, startupinfo=startupinfo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    bitrate = result.stdout.decode().strip()
    return int(bitrate) if bitrate else None

def convert_bitrate(input_file, output_file, target_bitrate='128k', overwrite_by_default=False):
    subprocess.run(
        ['ffmpeg',
         '-y' if overwrite_by_default else ''
         '-i', input_file,
         '-b:a', target_bitrate,
         output_file]
    )

def clamp_bitrates_in_directory(directory, target_bitrate='128k'):
    max_bitrate = int(1.5*1000*int(target_bitrate[:-1]))
    for filename in os.listdir(directory):
        if not filename.endswith('.mp3'): continue
        file_path = os.path.join(directory, filename)
        bitrate = get_bitrate(file_path)
        if bitrate is None:
            raise Exception(f"Failed to get bitrate of {filename}")
        
        if bitrate > max_bitrate:


            temp_file = os.path.join(directory,'temp.'+filename)
            
            output_file = os.path.join(directory, filename)
            convert_bitrate(file_path, temp_file, target_bitrate=target_bitrate, overwrite_by_default=False)
            os.remove(file_path)
            os.rename(temp_file, file_path)
            if os.path.exists(temp_file):
                os.remove(temp_file)
            print(f'Converted {filename} to {target_bitrate}.')
        else:
            print(f'{filename} does not require conversion.')

clamp_bitrates_in_directory(os.getcwd(), target_bitrate='64k')
