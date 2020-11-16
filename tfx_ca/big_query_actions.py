from google.cloud import bigquery
import google
import importlib.resources as pkg_resources
import logging

from tfx_ca import config
from tfx_ca import sql as sql_dir

conf = config.load()


def create_project_dataset(project, dataset_id):
    """
    Create the specified dataset on a project. 
    """

    if dataset_id not in list_project_datasets(project):
        client = bigquery.Client()

        fully_qualified_dataset = f"{project}.{dataset_id}"

        dataset = bigquery.Dataset(fully_qualified_dataset)

        dataset.location = "US"

        dataset = client.create_dataset(dataset, timeout=30)  # Make an API request.
        logging.info("Created dataset %s.%s", client.project, dataset.dataset_id)

        client.close()


def list_project_datasets(project):
    """
    List all the datasets (like hive schemas) in 
    a Google Cloud project
    """

    client = bigquery.Client()

    datasets = list(client.list_datasets())  # Make an API request.
    project = client.project
    
    if datasets:
        logging.info("%s datasets found", len(datasets))
        datasets = [dataset.dataset_id for dataset in datasets]
    else:
        datasets = []

    client.close()
    return datasets


def run_query_from_file(client, sql_file):
    """
    Read a file containing a SQL query and execute it
    """

    qry = pkg_resources.read_text(sql_dir, sql_file)

    return client.query(qry)


def create_visitdata_table():

    create_project_dataset(project=conf['project'], dataset_id=conf['dataset_id'])

    client = bigquery.Client()

    try:
        run_query_from_file(client, 'big_query_create_visitdata.sql')

    except google.api_core.exceptions.Conflict as e:
        logging.error("There was a conflict")
        logging.error(e)

    finally:
        client.close()