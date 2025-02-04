"""
export relevant libraries from anki, as .apkg, with all extra information, to this folder.
"""

from typing import Optional
import zipfile
import os, shutil
import json
import pyzstd
import tempfile

import sqlalchemy
import pandas as pd


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, path)
            ziph.write(file_path, arcname=arcname)


class DeckWrangler:
    def __init__(self, name, proceed_if_unzipped=False):
        self.name = name
        self.proceed_if_unzipped = proceed_if_unzipped

    def __enter__(self):
        local_dir_objects = os.listdir()
        pkg_name = self.name + ".apkg"

        if pkg_name not in local_dir_objects:
            raise Exception(f"{pkg_name} was not found in working directory")
        if self.name in local_dir_objects:
            if self.proceed_if_unzipped:
                print(f"{self.name} already exists in working dir. Continuing...")
            else:
                raise Exception(f"{self.name} already exists in working dir.")
        else:
            with zipfile.ZipFile(pkg_name, "r") as zip_f:
                zip_f.extractall(self.name)

        self.base_path = ".\\{}".format(self.name)

        self.zstd_db_path = os.path.join(self.base_path, "collection.anki21b")
        if os.path.exists(self.zstd_db_path):
            self.uses_zstd = True
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, dir=self.base_path, suffix=".anki21"
            )
            with (
                open(self.zstd_db_path, "rb") as compressed_file,
                open(temp_file.name, "wb") as decompressed_file,
            ):
                decompressed_file.write(pyzstd.decompress(compressed_file.read()))
            self.db_path = temp_file.name  # Set the decompressed file path
        else:
            self.uses_zstd = False
            self.db_path = os.path.join(self.base_path, "collection.anki21")

        self.media_path = ".\\{}\\media".format(self.name)

        url = "sqlite:///" + self.db_path
        self.engine = sqlalchemy.create_engine(url)
        try:
            self.notes = pd.read_sql(f"SELECT * FROM notes", con=self.engine)
        except:
            # ugh
            self.engine.dispose()
            self.db_path = os.path.join(self.base_path, "collection.anki2")
            url = "sqlite:///" + self.db_path
            self.engine = sqlalchemy.create_engine(url)
            self.notes = pd.read_sql(f"SELECT * FROM notes", con=self.engine)
        self.cards = pd.read_sql(f"SELECT * FROM cards", con=self.engine)

        return self

    def add_media(self, media_files: list[str]):
        """
        Add media files to the deck.

        :param media_files: A list of paths to media files to include in the deck.
        """
        raise Exception(
            "This method doesn't work currently. Might be fixable by doing a closer imitation of ankilib"
        )
        if os.path.exists(self.media_path):
            os.remove(self.media_path)

        media_json = {
            idx: os.path.basename(path) for idx, path in enumerate(media_files)
        }
        with open(self.media_path, "w") as media_file:
            json.dump(media_json, media_file)

        # Copy media files to the folder
        for idx, path in enumerate(media_files):
            dest_path = os.path.join(self.base_path, str(idx))
            shutil.copy(path, dest_path)

    def commit(self, with_name: Optional[str] = None, overwrite: bool = False):
        pkg_name = with_name or self.name
        if not pkg_name.endswith(".apkg"):
            pkg_name += ".apkg"
        if os.path.exists(pkg_name):
            if overwrite:
                os.remove(pkg_name)
            else:
                raise Exception("Tried to save over existing .apkg")
        self.notes.to_sql(
            name="notes", con=self.engine, if_exists="replace", index=False
        )
        self.cards.to_sql(
            name="cards", con=self.engine, if_exists="replace", index=False
        )
        if self.uses_zstd:
            with (
                open(self.zstd_db_path, "wb") as compressed_file,
                open(self.db_path, "rb") as decompressed_file,
            ):
                compressed_file.write(pyzstd.compress(decompressed_file.read()))
        with zipfile.ZipFile(pkg_name, "w", zipfile.ZIP_DEFLATED) as zip_f:
            zipdir(self.name, zip_f)

    def __exit__(self, exc_type, exc_value, traceback):
        self.engine.dispose()
        shutil.rmtree(self.name)

        if exc_type is not None:
            print(
                f'An exception occurred with "{self.name}" open (closed succesfully).'
            )
            return False  # Propagate the exception
