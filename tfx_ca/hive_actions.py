import datetime
import importlib.resources as pkg_resources
import logging
import os
import pyarrow
from pyhive import hive as phive
import shutil
from TCLIService.ttypes import TOperationState

from tfx_ca import config
from tfx_ca import sql as sql_dir

conf = config.load()
os.environ['HADOOP_HOME'] = '/opt/hadoop-hadrs2'

class HiveWrapper:
    """
    Context manager for hive, patterned after SparkWrapper.
    """

    def __init__(self, host='hivers2.hadoop.pvt', conf={}):
        self._hivecon = None
        self._host = host
        self._conf = conf

    # def __del__(self):
    #     self._hivecon.close()

    def __enter__(self):
        self._hivecon = phive.connect(self._host, configuration=self._conf)
        self._hivecur = self._hivecon.cursor()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._hivecon.close()

    def execute(self, arg, **kwargs):
        self._hivecur.execute(arg, **kwargs)

    def fetchall(self):
        return self._hivecur.fetchall()


def get_max_di_snapdate():
    """
    The hive query produces a list of single-item tuples like

    
    [('snap_date=20201015/device_id_type_category=DISPLAY',),
     ('snap_date=20201015/device_id_type_category=OTHER',),
     ('snap_date=20201016/device_id_type_category=DISPLAY',),
     ('snap_date=20201016/device_id_type_category=OTHER',),
     ('snap_date=20201017/device_id_type_category=DISPLAY',),
     ('snap_date=20201017/device_id_type_category=OTHER',),
     ...

    The horrendous one-liner splits the first element of the tuple
    by a forward slash, then by an =, then converts to int and 
    takes the max.
    """

    with HiveWrapper() as hw:
        hw.execute('show partitions di_device_behavior_metrics.device_data')
        partition_list = hw.fetchall()
            
    return max(
        map(lambda row_item: int(row_item.split('=')[1]),
        [
            row[0].split('/')[0] 
            for row 
            in partition_list]))
    

def copy_visitdata_to_hdfs():
    """

    """

    qry = pkg_resources.read_text(sql_dir,'hive_visitdata_to_ext.sql')

    print(qry)

    with HiveWrapper(conf={
                            'hive.execution.engine':'tez',
                            'hive.merge.tezfiles':'true',
                            'hive.merge.size.per.task':'1073741824',                            
                            'mapred.output.compress':'true',
                            'hive.exec.compress.output':'true',
                            'mapred.output.compression.codec':'org.apache.hadoop.io.compress.GzipCodec',
                            'io.compression.codecs':'org.apache.hadoop.io.compress.GzipCodec'
    }) as hw:
        hw.execute(
            (qry
            .replace('SNAP_DATE', str(get_max_di_snapdate()))
            .replace('STAGING_DIR', conf['hdfs_staging_dir'])))

    logging.info("Copy visitdata to file complete")


def list_hdfs_files(dir):
    """
    Given a staging dir, enumerate all the files in it
    """
    fs = pyarrow.hdfs.connect()

    w = fs.walk(dir)

    walk_tree = [(x[0], x[1], x[2]) for x in w]

    files = {}

    for elem in walk_tree:
        if elem[2] != [] and elem[2] != ['_SUCCESS']:
            files[elem[0]] = elem[2]

    logging.debug("Found files in hdfs:")
    logging.debug(files)
    return files


def clear_working_dir(dir):
    """
    Delete and recreate the place where the files
    from hdfs will go before loading to google cloud. 
    Intended to be disposable, in /tmp or similar.
    """

    if os.path.isdir(dir):
        shutil.rmtree(dir)
        logging.debug("deleting %s", dir)
    os.mkdir(dir)
    logging.debug("(re)creating %s", dir)


def copy_hdfs_to_local(local_dir, hadoop_dir):
    """
    Copy files from hdfs staging dir to local
    """

    start_time = datetime.datetime.now()
    logging.info(f"Downloading files from {hadoop_dir} to {local_dir}...")

    clear_working_dir(local_dir)

    hadoop_files = list_hdfs_files(hadoop_dir)

    fs = pyarrow.hdfs.connect()

    for k in hadoop_files.keys():
        
        for f in hadoop_files[k]:

            hdfs_file = os.path.join(k,f)               
            dest_file = os.path.join(local_dir, f)
            
            with open(dest_file, 'wb') as outfile:
                logging.debug("Downloading %s to %s", hdfs_file, dest_file)
                fs.download(hdfs_file, outfile)
    fs.close()

    logging.info("Done coping files to local, time elapsed: %s", (datetime.datetime.now() - start_time))
    logging.info("Files transferred: %s", len(hadoop_files))
        