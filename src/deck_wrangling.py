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

from anki.collection import Collection


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, path)
            ziph.write(file_path, arcname=arcname)


class ApkgUnzippingManager:
    """
    handles zipping/unzipping of apkg files and locating of important files within. other classes actually interface with these files
    """

    def __init__(self, name, proceed_if_unzipped=False):
        self.name, _ = os.path.splitext(name)  # ignore extension
        self.proceed_if_unzipped = proceed_if_unzipped

    def __enter__(self):
        self._saved = False
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

        return self

    def oh_shit_wrong_db_path():
        self.db_path = os.path.join(self.base_path, "collection.anki2")

    def save(self, with_name: Optional[str] = None, overwrite: bool = False):
        self._saved = True
        pkg_name = with_name or self.name
        if not pkg_name.endswith(".apkg"):
            pkg_name += ".apkg"
        if os.path.exists(pkg_name):
            if overwrite:
                os.remove(pkg_name)
            else:
                raise Exception("Tried to save over existing .apkg")
        if self.uses_zstd:
            with (
                open(self.zstd_db_path, "wb") as compressed_file,
                open(self.db_path, "rb") as decompressed_file,
            ):
                compressed_file.write(pyzstd.compress(decompressed_file.read()))
        with zipfile.ZipFile(pkg_name, "w", zipfile.ZIP_DEFLATED) as zip_f:
            zipdir(self.name, zip_f)

    def __exit__(self, exc_type, exc_value, traceback):
        if not self._saved:
            print("ApkgHandler exiting without saving...")
        shutil.rmtree(self.name)

        if exc_type is not None:
            print(
                f'An exception occurred with "{self.name}" open (closed succesfully).'
            )
            return False  # Propagate the exception


class SQLPandasInterface:
    """
    just a workaround to be able to use SQAlchemy+pd instead of the anki specific db proxy
    """

    def __init__(self, apkg_manager: ApkgUnzippingManager):
        self.apkg_manager = apkg_manager

    def __enter__(self):
        url = "sqlite:///" + self.apkg_manager.db_path
        self.engine = sqlalchemy.create_engine(url)
        try:
            self.notes = pd.read_sql(f"SELECT * FROM notes", con=self.engine)
        except:
            # ugh
            self.engine.dispose()
            self.apkg_manager.oh_shit_wrong_path()
            url = "sqlite:///" + self.db_path
            self.engine = sqlalchemy.apkg_handler.create_engine(url)
            self.notes = pd.read_sql(f"SELECT * FROM notes", con=self.engine)
        self.cards = pd.read_sql(f"SELECT * FROM cards", con=self.engine)

        return self

    def commit(self):
        self.notes.to_sql(
            name="notes", con=self.engine, if_exists="replace", index=False
        )
        self.cards.to_sql(
            name="cards", con=self.engine, if_exists="replace", index=False
        )

    def commit_and_save(self, with_name: Optional[str] = None, overwrite: bool = False):
        self.commit()
        self.apkg_manager.save(with_name=with_name, overwrite=overwrite)

    def __exit__(self, exc_type, exc_value, traceback):
        self.engine.dispose()

        if exc_type is not None:
            return False  # Propagate the exception


class AnkiColInterface:
    """
    opens an unzipped apkg as an actual anki Collection
    """

    def __init__(self, apkg_manager: ApkgUnzippingManager):
        self.apkg_manager = apkg_manager

    def __enter__(self):
        self.col = Collection(self.apkg_manager.db_path)

        return self

    def notes(self):
        yield from map(self.col.get_note, self.col.find_notes(""))

    def cards(self):
        yield from map(self.col.get_card, self.col.find_cards(""))

    def apply_to_notes(self, fun):
        for note in self.notes():
            if fun(note) is not None:
                raise Exception("function applied to notes must be NoneType")
            note.flush()

    def apply_to_cards(self, fun):
        for card in self.cards():
            if fun(card) is not None:
                raise Exception("function applied to notes must be NoneType")
            card.flush()

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

    def commit(self):
        self.col.save(trx=False)

    def commit_and_save(self, with_name: Optional[str] = None, overwrite: bool = False):
        self.commit()
        self.apkg_manager.save(with_name=with_name, overwrite=overwrite)

    def __exit__(self, exc_type, exc_value, traceback):
        self.col.close()

        if exc_type is not None:
            return False  # Propagate the exception


def compose_with_apkg_unzipper(cls, name):
    class ComposedClass:
        def __init__(self, name, proceed_if_unzipped=False):
            self.apkg_manager = ApkgUnzippingManager(
                name, proceed_if_unzipped=proceed_if_unzipped
            )

        def __enter__(self):
            self.apkg_manager.__enter__()
            self.interface = cls(self.apkg_manager)
            self.interface.__enter__()
            return self.interface

        def __exit__(self, exc_type, exc_value, traceback):
            # is this right?
            self.interface.__exit__(exc_type, exc_value, traceback)
            self.apkg_manager.__exit__(exc_type, exc_value, traceback)
            if exc_type is not None:
                return False

    ComposedClass.__name__ = name
    return ComposedClass


ApkgAsPandas = compose_with_apkg_unzipper(SQLPandasInterface, "ApkgAsPandas")
ApkgAsAnki = compose_with_apkg_unzipper(AnkiColInterface, "ApkgAsAnki")


if __name__ == "__main__":
    # with ApkgUnzippingManager('Dictionary of Japanese Grammar', proceed_if_unzipped=True) as apkg_handler:
    #    with AnkiColInterface(apkg_handler) as deck:
    with ApkgAsAnki("Dictionary of Japanese Grammar", proceed_if_unzipped=True) as deck:
        if 1:

            def addrm_bals(note):
                if note.fields[0].endswith("bals"):
                    note.fields[0] = note.fields[0][:-4]
                else:
                    note.fields[0] += "bals"

            for note in list(deck.notes())[:5]:
                print(note.fields[0])
            deck.apply_to_notes(addrm_bals)
            for note in list(deck.notes())[:5]:
                print(note.fields[0])
            deck.commit_and_save(overwrite=True)
