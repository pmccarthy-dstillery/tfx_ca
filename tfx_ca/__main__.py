import logging


from tfx_ca import config
from tfx_ca import big_query_actions, gcs_actions, hive_actions


logging.basicConfig(level='DEBUG')


conf = config.load()

# print(create_project_dataset(project=conf['project'], dataset_id=conf['dataset_id']))

# big_query_actions.create_visitdata_table()

# hive_actions.copy_visitdata_to_file()

# hive_actions.copy_hdfs_to_local(conf['local_staging_dir'],conf['hdfs_staging_dir'])

gcs_actions.upload_directory_contents('/tmp/tfxca_data','tfxca_visitdata')

# gcs_actions.delete_bucket_contents(conf['visitdata_bucket'])