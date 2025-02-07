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

def convert(input_file, output_file, target_bitrate, overwrite_by_default=False):
    subprocess.run(
        ['ffmpeg',
         '-y' if overwrite_by_default else ''
         '-i', input_file,
         '-b:a', target_bitrate,
         output_file],
        shell=True, startupinfo=startupinfo
    )

def wav_to_mp3_directory(directory, target_bitrate='256k'):
    for filename in os.listdir(directory):
        if not filename.endswith('.wav'): continue
        file_path = os.path.join(directory, filename)
        
        output = os.path.join(directory, filename[:-3]+'mp3')
        convert(file_path, output, target_bitrate, overwrite_by_default=False)
        os.remove(file_path)

wav_to_mp3_directory(os.getcwd(), target_bitrate='256k')
