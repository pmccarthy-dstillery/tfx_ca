import logging
import os

from google.cloud import bigquery

from tfx_ca import config
from tfx_ca import bigquery_actions, gcs_actions, hive_actions

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'service_worker.json'

logging.basicConfig(level='DEBUG')


conf = config.load()

# print(create_project_dataset(project=conf['project'], dataset_id=conf['dataset_id']))

bigquery_actions.create_or_stat_visitdata_table()

# hive_actions.copy_visitdata_to_hdfs()

# hive_actions.copy_hdfs_to_local(conf['local_staging_dir'], conf['hdfs_staging_dir'])

# gcs_actions.delete_bucket_contents(conf['visitdata_bucket'])
# gcs_actions.upload_directory_contents('/tmp/tfxca_data','tfxca_visitdata')
bigquery_actions.populate_visitdata()