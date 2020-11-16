import logging


from tfx_ca import config
from tfx_ca import big_query_actions


logging.basicConfig(level='INFO')


conf = config.load()

# print(create_project_dataset(project=conf['project'], dataset_id=conf['dataset_id']))

big_query_actions.create_visitdata_table()