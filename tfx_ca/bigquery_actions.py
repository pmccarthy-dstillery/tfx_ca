import datetime
from google.cloud import bigquery
import google
import importlib.resources as pkg_resources
import logging
import time

from tfx_ca import config, gcs_actions
from tfx_ca import sql as sql_dir

conf = config.load()


def create_or_stat_project_dataset(project, dataset_id):
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


def run_query(client, qry):
    """
    Read a file containing a SQL query and execute it
    """

    return client.query(qry)


def create_or_stat_visitdata_table():

    create_or_stat_project_dataset(project=conf['project'], dataset_id=conf['dataset_id'])

    client = bigquery.Client()

    try:

        full_table_name = ".".join([conf['dataset_id'], conf['bigquery_table']])

        qry = (
            pkg_resources.read_text(sql_dir, 'big_query_create_visitdata.sql')
            .replace('TABLENAME',full_table_name)
            )
        
        run_query(client, qry)
        logging.debug("Created BigQuery table %s", full_table_name)

    except google.api_core.exceptions.Conflict as e:
        logging.warn("There was a conflict, table probably exists")
        logging.warn(e)

    finally:
        client.close()


def load_data_from_gcs_to_bigquery(bucket_file_uri, table_id, schema):

    client = bigquery.Client()

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        field_delimter=',',
        max_bad_rows=10
    )

    load_job = client.load_table_from_uri(
      bucket_file_uri, table_id, job_config=job_config
    ) 

    return load_job


def populate_visitdata():

    available_blobs = gcs_actions.list_bucket_contents(conf['visitdata_bucket'])

    schema = [
        bigquery.SchemaField("deviceid", "STRING"),
        bigquery.SchemaField("devicetype","STRING"),
        bigquery.SchemaField("content", "STRING"),
        bigquery.SchemaField("hit_date","DATE")
    ]

    bucket_uri = "gs://"+conf['visitdata_bucket']

    load_jobs = []

    for blob in available_blobs:
        load_job = load_data_from_gcs_to_bigquery(bucket_file_uri=bucket_uri + "/" + blob.name,
                                       table_id=conf['dataset_id']+'.'+conf['bigquery_table'],
                                       schema=schema)
        load_jobs.append(load_job)

    
    while not all([x.done() for x in load_jobs]):
        
        logging.info("All files not loaded to BigQuery yet...")
        time.sleep(5)

