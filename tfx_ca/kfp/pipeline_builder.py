import importlib.resources as pkg_resources
import logging
from typing import Any, Dict, List, Optional, Text

from ml_metadata.proto import metadata_store_pb2
from tfx.components import (
    ExampleValidator,    
    Pusher,
    SchemaGen,
    StatisticsGen,
    Trainer,
)
# from tfx.components.base import executor_spec
from tfx.dsl.components.base import executor_spec
# from tfx.components.base import executor_spec
from tfx.components.trainer.executor import GenericExecutor
from tfx.extensions.google_cloud_big_query.example_gen.component import BigQueryExampleGen
from tfx.extensions.google_cloud_ai_platform.pusher import executor as ai_platform_pusher_executor
from tfx.extensions.google_cloud_ai_platform.trainer import executor as ai_platform_trainer_executor
from tfx.orchestration import pipeline
from tfx.proto import (pusher_pb2,trainer_pb2)

from tfx_ca import config
from tfx_ca import sql as sql_dir

conf = config.load()

def create_pipeline(
    pipeline_name: Text,
    pipeline_root: Text,
    module_file: Text,
    train_args: trainer_pb2.TrainArgs,
    eval_args: trainer_pb2.EvalArgs,
    serving_model_dir: Text,
    metadata_connection_config: Optional[
        metadata_store_pb2.ConnectionConfig] = None,
    beam_pipeline_args: Optional[List[Text]] = None,
    ai_platform_training_args: Optional[Dict[Text, Text]] = None,
    ai_platform_serving_args: Optional[Dict[Text, Any]] = None,
) -> pipeline.Pipeline:

    qry = pkg_resources.read_text(sql_dir,'big_query_extract_dataset.sql')

    example_gen = BigQueryExampleGen(query=qry)

    statistics_gen = StatisticsGen(examples=example_gen.outputs['examples'])

    schema_gen = SchemaGen(
        statistics=statistics_gen.outputs['statistics'],
        infer_feature_shape=False
    )

    example_validator = ExampleValidator(
        statistics=statistics_gen.outputs['statistics'],
        schema=schema_gen.outputs['schema']
    )


    trainer_args = {
       'module_file': module_file,
       'custom_executor_spec':
           executor_spec.ExecutorClassSpec(GenericExecutor),
       'examples': example_gen.outputs['examples'],
       'schema': schema_gen.outputs['schema'],
       'train_args': train_args,
       'eval_args': eval_args,
    }

    if ai_platform_training_args is not None:
      trainer_args.update({
          'custom_executor_spec':
              executor_spec.ExecutorClassSpec(
                  ai_platform_trainer_executor.GenericExecutor
              ),
          'custom_config': {
              ai_platform_trainer_executor.TRAINING_ARGS_KEY:
                  ai_platform_training_args,
          }
      })
    trainer = Trainer(**trainer_args)

    # Checks whether the model passed the validation steps and pushes the model
    # to a file destination if check passed.
    pusher_args = {
        'model':
            trainer.outputs['model'],
        'push_destination':
            pusher_pb2.PushDestination(
                filesystem=pusher_pb2.PushDestination.Filesystem(
                    base_directory=serving_model_dir)),
    }
    if ai_platform_serving_args is not None:
      pusher_args.update({
          'custom_executor_spec':
              executor_spec.ExecutorClassSpec(ai_platform_pusher_executor.Executor
                                             ),
          'custom_config': {
              ai_platform_pusher_executor.SERVING_ARGS_KEY:
                  ai_platform_serving_args
          },
      })
    pusher = Pusher(**pusher_args)  # pylint: disable=unused-variable

    components = [
        example_gen,
        statistics_gen,
        schema_gen,
        example_validator,
        trainer,
        pusher
    ]

    return pipeline.Pipeline(
        pipeline_name=pipeline_name,
        pipeline_root=pipeline_root,
        components=components,
        enable_cache=True,
        metadata_connection_config=metadata_connection_config,
        beam_pipeline_args=beam_pipeline_args,
    )
