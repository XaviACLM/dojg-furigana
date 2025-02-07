import os

def rename_files_in_directory(directory_path):
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        
        if not os.path.isfile(file_path): continue
        name, extension = os.path.splitext(filename)
        if extension==".py" or name.startswith("dojg_audio."): continue
        assert len(name)==64

        new_name = "dojg_audio." + name[:32] + extension
        new_file_path = os.path.join(directory_path, new_name)
        os.rename(file_path, new_file_path)
        # print(f"Renamed: {filename} to {new_name}")


rename_files_in_directory(os.getcwd())
