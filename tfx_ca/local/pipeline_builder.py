import importlib.resources as pkg_resources
import logging

from tfx.components import (
    ExampleValidator,    
    Pusher,
    SchemaGen,
    StatisticsGen,
    Trainer,
)
from tfx.components.base import executor_spec
from tfx.components.trainer.executor import GenericExecutor
from tfx.extensions.google_cloud_big_query.example_gen.component import BigQueryExampleGen
from tfx.orchestration import (
    metadata,
    pipeline
)
from tfx.proto import (pusher_pb2,trainer_pb2)

from tfx_ca import config
from tfx_ca import sql as sql_dir


conf = config.load()
src_qry = pkg_resources.read_text(sql_dir,'big_query_extract_dataset.sql')

beam_pipeline_args = conf['beam']['args']

def build_pipeline(timestamp: str) -> pipeline.Pipeline:
    """
    Declare pipeline components and assemble into Pipeline.
    """

    qry =  src_qry
    logging.debug(qry)

    conf['serving_model_dir'] = f"{conf['serving_model_dir']}/beam/OL/{timestamp}"
    conf['pipeline_root_dir'] = f"{conf['pipeline_root_dir']}/beam/OL/{timestamp}"
    conf['beam']['metadata_path'] = f"{conf['beam']['metadata_path']}/beam/OL"

    logging.info("Serving model dir is now %s",conf['serving_model_dir'])

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

    trainer = Trainer(
        module_file=conf['module_file'],
        custom_executor_spec=executor_spec.ExecutorClassSpec(GenericExecutor),
        examples=example_gen.outputs['examples'],
        schema=schema_gen.outputs['schema'],
        train_args=trainer_pb2.TrainArgs(),
        eval_args=trainer_pb2.EvalArgs())

    pusher = Pusher(
        model=trainer.outputs['model'],
        push_destination=pusher_pb2.PushDestination(
            filesystem=pusher_pb2.PushDestination.Filesystem(
                base_directory=conf['serving_model_dir'])))

    components = [
        example_gen,
        statistics_gen,
        schema_gen,
        example_validator,
        trainer,
        pusher
    ]
    
    tfx_pipeline = pipeline.Pipeline(
        pipeline_name=conf['beam']['pipeline_name'],
        pipeline_root=conf['pipeline_root_dir'],
        components=components,
        enable_cache=False,
        metadata_connection_config=(
            metadata.sqlite_metadata_connection_config(conf['beam']['metadata_path'])

        ),
        beam_pipeline_args=beam_pipeline_args
    )

    return tfx_pipeline