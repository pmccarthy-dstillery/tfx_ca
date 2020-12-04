from google.api_core import exceptions
from google.cloud import storage
import logging
import os
import threading
import queue

from tfx_ca import config

conf = config.load()


def stat_or_create_bucket(bucket):
    """
    Attempt to connect to a bucket, creating it
    if it does not exist.
    """
    
    client = storage.Client()

    try:
        client.get_bucket(bucket)

    except exceptions.NotFound:

        logging.warn("Bucket not found, attempting to create")

        bucket = client.bucket(bucket)
        bucket.storage_class = 'STANDARD'
        new_bucket = client.create_bucket(bucket, location='us')
        logging.info("Bucket %s created", bucket)


def list_bucket_contents(bucket):

    client = storage.Client()

    bucket = client.bucket(bucket)

    return client.list_blobs(bucket)


def delete_bucket_contents(bucket_id):
    """
    List everything in a bucket and then delete what
    is found.
    """

    client = storage.Client()
    bucket = client.bucket(bucket_id) 

    blobs = list_bucket_contents(bucket_id) 

    for blob in blobs:
        blob = bucket.blob(blob.name)
        blob.delete()
        logging.debug("%s deleted.", blob.name)




def single_uploader(local_file, bucket):

    stripped_file_name = local_file.split('/')[-1]

    client = storage.Client()
    bucket = client.bucket(bucket)
    blob = bucket.blob(stripped_file_name)
    blob.upload_from_filename(local_file)


def upload_directory_contents(local_path, bucket):
    """
    Create an uploader with the path to bucket baked in, 
    and then for every file in our local directory create
    a thread and upload it. 

    The batch() aspect of the cloud storage API doesn't support
    moving file ops so we do it this way.    
    """

    full_file_paths = [os.path.join(local_path, file) for file in os.listdir(local_path)]

    for file in full_file_paths:
        single_uploader(file, conf['visitdata_bucket'])
    # threads = []

    # for file in full_file_paths:
    #     thread = threading.Thread(target=single_uploader, args=(file, bucket,))
    #     threads.append(thread)

    #     thread.start()

    # for _, thread in enumerate(threads):
    #     thread.join()
