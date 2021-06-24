#! /usr/bin/env python
import os
import os.path
import shutil
import io
import glob
import datetime

from typing import Union, List

import sqlite3
from multiprocessing import Pool

# if set to True, the program will always annotate,
# regardless of what the user specifies
ANNOTATE = True

class ImageExtractor:
    """
    A class to interact with a single sqlite3 file produced by an ethoscope
    """

    def __init__(self, path):

        self.path = path
        self.filename = os.path.basename(path)
        self.experiment_folder = os.path.dirname(path)
        self.img_snapshots = os.path.join(self.experiment_folder, "IMG_SNAPSHOTS")
        os.makedirs(self.img_snapshots, exist_ok=True)
        self.t0 = self.get_t0()

    def list_snapshots(self):
        return glob.glob(os.path.join(self.img_snapshots , "*.jpg"))


    def get_t0(self):
        """
        Get the start timestamp of the ethoscope experiment
        The result is the number of seconds since 1970-01-01 00:00:00 
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql_metadata = 'SELECT * from METADATA;'
            conn.commit()
            cursor.execute(sql_metadata)
            t0 = 0
            for field, value in cursor:
                if field == "date_time":
                    t0 = float(value)
        
        return t0



    def get_connection(self):
        return sqlite3.connect(self.path, check_same_thread=False)


    def save_frame(self, id, t, blob):
        """
        Save a blob in the experiment_folder with a filename based on id and t
        and return the filename
        """
        file_name_raw = os.path.join(self.experiment_folder, "IMG_SNAPSHOTS", "%05d_%i_raw.jpg" % (id, t))
        file_name = os.path.join(self.experiment_folder, "IMG_SNAPSHOTS", "%05d_%i.jpg" % (id, t))
        if os.path.exists(file_name) or os.path.exists(file_name_raw):
            return file_name_raw
        file_like = io.BytesIO(blob)
        out_file = open(file_name_raw, "wb")
        file_like.seek(0)
        shutil.copyfileobj(file_like, out_file)
        return file_name_raw

    def make_criteria(self, column: str, value: Union[List, int]):
        """
        Make criteria based on column using value
        """

        if isinstance(value, List):
            value = [str(e) for e in value]
            criteria = f"{column} in ({','.join(value)})"

        elif isinstance(value, Integer):
            criteria = f"{column} = {value}"
        
        else:
            raise Exception("Please provide either a list of integers or a single integer as value")

        return criteria

    def get_frame(self, criteria):
        """
        Get one or more frames from the databse based on some criteria
        Return the resulting filenames 
        """

        filenames = []
        if criteria is None:
            # return self.list_snapshots()
            return None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            statement = f"SELECT id, t, img FROM IMG_SNAPSHOTS WHERE {criteria}"
            cursor.execute(statement)
            for i, c in enumerate(cursor):
                id, t, blob = c
                filenames.append(self.save_frame(id, t, blob))

        return filenames


    def clean(self):
        """
        Emtpy the IMG_SNAPSHOTS folder
        """
        shutil.rmtree(self.img_snapshots)
        os.mkdir(self.img_snapshots)


class Annotator:
    """
    A mixin to add annotation capabilities

    Owning class must:

      * define self.t0
      * define list_snapshots()
    """

    def make_pool(self, filenames, cores=4):
        """
        Set up a parallel processing pool of threads
        """
        pool = Pool(cores)
        pool_args = []
        for f in filenames:
            t = int(os.path.basename(f).split("_")[1].split(".")[0])
            pool_args.append((f,t))

        return pool, pool_args

    def annotate_image(self, args):
        """
        Write a banner stating the date time of the snapshot using image magick
        """
        filename, time = args

        # shutil.move(filename, os.path.join(self.img_snapshots, "annotation"))
        # annotation_filename = os.path.join(
        #     os.path.dirname(filename),
        #     "annotation",
        #     os.path.basename(filename)
        # )

        time_s = time/1000
        label = datetime.datetime.fromtimestamp(time_s + self.t0).strftime('%Y-%m-%d %H:%M:%S')
        out = filename.replace("_raw", "")

        if os.path.exists(out):
            return None

        command = "convert %s -pointsize 50  -font FreeMono -background Khaki  label:'%s' +swap -gravity Center -append %s" % (filename, label, out)
        os.system(command)
        os.remove(filename)
        # shutil.move(out, filename)


    def annotate(self, filenames=None, cores=4):
        """
        Annotate the snapshots stored in the IMG_SNAPSHOTS folder
        using a parallel pool
        """

        if filenames is None:
            return

        pool, pool_args = self.make_pool(filenames, cores)
        # print(pool_args)
        pool.map(self.annotate_image, pool_args)

        # TODO Can I receive this as output of the pool.map call?
        filenames = [f.replace("_raw", "") for f in filenames]
        return filenames


class VideoMaker:
    """
    Produce a video from a collection of image files in a directory

    ffmpeg must be installed and findable in the PATH
    
    Owning class must:

        * define self.img_snapshots
    """

    def make_video(self, fps=10):
        output = os.path.join(self.img_snapshots, self.filename + ".mp4")
        command = "ffmpeg -loglevel panic -y -framerate %i -pattern_type glob -i '%s/*.jpg' -c:v libx264 %s" % (fps, self.img_snapshots, output)
        os.system(command)
        return output


class EthoscopeImager(VideoMaker, Annotator, ImageExtractor):


    def get_criteria(self, id, t):
        
        if not id is None:
            id_criteria = self.make_criteria("id", id)
        
        if not t is None:
            t_criteria = self.make_criteria("t", t)

        if id is None and t is None:
            return None
            
        elif not id is None and not t is None:
            criteria = "{id_criteria} {flag} {t_criteria}"

        elif id is None and not t is None:
            criteria = t_criteria

        else:
            criteria = id_criteria

        return criteria

    
    def run(self, id=None, t=None, flag = "OR", annotate=False, video=None, **kwargs):

        criteria = self.get_criteria(id, t)
        filenames = self.get_frame(criteria)

        if (annotate or ANNOTATE) and filenames:
            filenames = self.annotate(filenames)

        if video:
            filenames = [self.make_video(**kwargs)]

        if filenames is None:
            return self.list_snapshots()

        return filenames

def main(path, **kwargs):
    etho_imager = EthoscopeImager(path = path)
    filenames = etho_imager.run(**kwargs)
    for f in filenames:
        print(f)


if __name__ == "__main__":

    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True)
    ap.add_argument("--fps", default=10, type=int)
    ap.add_argument("--id", nargs="+", type=int, required=False, default=None)
    ap.add_argument("--t", nargs="+", type=int, required=False, default=None)
    # ap.add_argument("--video", default=None, type=str)
    ap.add_argument("--annotate", action="store_true", default=False)
    ap.add_argument("--video", action="store_true", default=False)
    args = ap.parse_args()

    main(**vars(args))


            









