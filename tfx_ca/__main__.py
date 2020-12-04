import argparse
import datetime
import logging
import os

from tfx.orchestration.beam.beam_dag_runner import BeamDagRunner
from tfx.orchestration.kubeflow import kubeflow_dag_runner
from tfx.proto import trainer_pb2

from google.cloud import bigquery

from tfx_ca import config
# from tfx_ca import bigquery_actions, gcs_actions, hive_actions, pipeline_builder
from tfx_ca.local import pipeline_builder as local_pipeline_builder
from tfx_ca.kfp import pipeline_builder as kfp_pipeline_builder

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'service_worker.json'

logging.basicConfig(level='DEBUG')


conf = config.load()

timestamp = datetime.datetime.strftime(datetime.datetime.now(),'%Y%m%d%H%m')


parser = argparse.ArgumentParser()
parser.add_argument("-p","--platform",choices=['local','kfp'])

args = parser.parse_args()

if __name__ == "__main__":

    if args.platform == 'local':
        
        tfx_pipeline = local_pipeline_builder.build_pipeline(timestamp)
        BeamDagRunner().run(tfx_pipeline)


    if args.platform == 'kfp':
        metadata_config = kubeflow_dag_runner.get_default_kubeflow_metadata_config()

        ai_platform_training_args = {
            'project': conf['kfp']['google_cloud_project'],
            'region': conf['kfp']['region']
        }

        # This pipeline automatically injects the Kubeflow TFX image if the
        # environment variable 'KUBEFLOW_TFX_IMAGE' is defined. The tfx
        # cli tool exports the environment variable to pass to the pipelines.
        tfx_image = os.environ.get('KUBEFLOW_TFX_IMAGE', None)
        runner_config = kubeflow_dag_runner.KubeflowDagRunnerConfig(
            kubeflow_metadata_config=metadata_config,
            # Specify custom docker image to use.
            tfx_image=tfx_image)

        kfp_pipeline = kfp_pipeline_builder.create_pipeline(
            pipeline_name= conf['kfp']['pipeline_name'],
            pipeline_root= conf['pipeline_root_dir'],
            module_file= conf['module_file'],
            beam_pipeline_args=conf['beam']['args'],
            train_args=trainer_pb2.TrainArgs(num_steps=1000),
            eval_args=trainer_pb2.EvalArgs(num_steps=1000), # what do these do?
            ai_platform_training_args=ai_platform_training_args,
            ai_platform_serving_args=None,
            serving_model_dir=conf['serving_model_dir']
        )


        kubeflow_dag_runner.KubeflowDagRunner(config=runner_config).run(kfp_pipeline)

        print("KFP has been run")

    # print(create_project_dataset(project=conf['project'], dataset_id=conf['dataset_id']))

    # bigquery_actions.create_or_stat_visitdata_table()

    # hive_actions.copy_visitdata_to_hdfs()

    # hive_actions.copy_hdfs_to_local(conf['local_staging_dir'], conf['hdfs_staging_dir'])

    # gcs_actions.delete_bucket_contents(conf['visitdata_bucket'])
    # gcs_actions.upload_directory_contents('/tmp/tfxca_data','tfxca_visitdata')
    # bigquery_actions.populate_visitdata()

    # tfx_pipeline = builder.build_pipeline(timestamp)