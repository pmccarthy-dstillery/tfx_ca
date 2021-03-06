# Lint as: python2, python3
# Copyright 2019 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Generic TFX BigQueryExampleGen executor."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from typing import Any, Dict, Optional, Text

import apache_beam as beam

from apache_beam.io.gcp import bigquery as beam_bigquery
from apache_beam.options import value_provider
import tensorflow as tf

from tfx.components.example_gen import base_example_gen_executor
from tfx.proto import example_gen_pb2
from tfx.utils import telemetry_utils
from google.cloud import bigquery

from google.protobuf import json_format
from tfx.utils import json_utils
from tfx_ca.bigquery_example_gen.proto import bigquery_example_gen_pb2

def load_custom_config(exec_properties):

  seed_config = example_gen_pb2.CustomConfig()
  json_format.Parse(exec_properties['custom_config'], seed_config)

  big_query_seed = bigquery_example_gen_pb2.BigQuerySeed()
  seed_config.custom_config.Unpack(big_query_seed)

  return json_utils.loads(big_query_seed.seed)


class _BigQueryConverter(object):
  """Help class for bigquery result row to tf example conversion."""

  def __init__(self, query: Text, project_id: Optional[Text] = None):
    """Instantiate a _BigQueryConverter object.

    Args:
      query: the query statement to get the type information.
      project_id: optional. The GCP project ID to run the query job. Default to
        the GCP project ID set by the gcloud environment on the machine.
    """
    client = bigquery.Client(project=project_id)
    # Dummy query to get the type information for each field.
    query_job = client.query('SELECT * FROM ({}) LIMIT 0'.format(query))
    results = query_job.result()
    self._type_map = {}
    for field in results.schema:
      self._type_map[field.name] = field.field_type

  def RowToExample(self, instance: Dict[Text, Any]) -> tf.train.Example:
    """Convert bigquery result row to tf example."""
    feature = {}
    for key, value in instance.items():
      data_type = self._type_map[key]

      if value is None:
        feature[key] = tf.train.Feature()
        continue

      value_list = value if isinstance(value, list) else [value]
      if data_type in ('INTEGER', 'BOOLEAN'):
        feature[key] = tf.train.Feature(
            int64_list=tf.train.Int64List(value=value_list))
      elif data_type == 'FLOAT':
        feature[key] = tf.train.Feature(
            float_list=tf.train.FloatList(value=value_list))
      elif data_type == 'STRING':
        feature[key] = tf.train.Feature(
            bytes_list=tf.train.BytesList(
                value=[tf.compat.as_bytes(elem) for elem in value_list]))
      else:
        # TODO(jyzhao): support more types.
        raise RuntimeError(
            'BigQuery column type {} is not supported.'.format(data_type))

    return tf.train.Example(features=tf.train.Features(feature=feature))


# Create this instead of inline in _BigQueryToExample for test mocking purpose.
@beam.ptransform_fn
@beam.typehints.with_input_types(beam.Pipeline)
@beam.typehints.with_output_types(beam.typehints.Dict[Text, Any])
def _ReadFromBigQueryImpl(  # pylint: disable=invalid-name
    pipeline: beam.Pipeline,
    query: Text,
    use_bigquery_source: bool = False) -> beam.pvalue.PCollection:
  """Read from BigQuery.

  Args:
    pipeline: beam pipeline.
    query: a BigQuery sql string.
    use_bigquery_source: Whether to use BigQuerySource instead of experimental
      `ReadFromBigQuery` PTransform.

  Returns:
    PCollection of dict.
  """
  # TODO(b/155441037): Consolidate to ReadFromBigQuery once its performance
  # on dataflow runner is on par with BigQuerySource.
  if use_bigquery_source:
    return (pipeline
            | 'ReadFromBigQuerySource' >> beam.io.Read(
                beam.io.BigQuerySource(query=query, use_standard_sql=True)))

  return (pipeline
          | 'ReadFromBigQuery' >> beam_bigquery.ReadFromBigQuery(
              query=query,
              use_standard_sql=True,
              bigquery_job_labels=telemetry_utils.get_labels_dict()))


@beam.ptransform_fn
@beam.typehints.with_input_types(beam.Pipeline)
@beam.typehints.with_output_types(tf.train.Example)
def _BigQueryToExample(  # pylint: disable=invalid-name
    pipeline: beam.Pipeline,
    exec_properties: Dict[Text, Any],  # pylint: disable=unused-argument
    split_pattern: Text) -> beam.pvalue.PCollection:
  """Read from BigQuery and transform to TF examples.

  Args:
    pipeline: beam pipeline.
    exec_properties: A dict of execution properties.
    split_pattern: Split.pattern in Input config, a BigQuery sql string.

  Returns:
    PCollection of TF examples.
  """

  beam_pipeline_args = exec_properties['_beam_pipeline_args']
  pipeline_options = beam.options.pipeline_options.PipelineOptions(
      beam_pipeline_args)
  # Try to parse the GCP project ID from the beam pipeline options.
  project = pipeline_options.view_as(
      beam.options.pipeline_options.GoogleCloudOptions).project
  if isinstance(project, value_provider.ValueProvider):
    project = project.get()
  converter = _BigQueryConverter(split_pattern, project)

  # seed_runtime_param = load_custom_config(exec_properties)

  # split_pattern = split_pattern.replace('CONTENT_PATTERN', seed_runtime_param)

  return (pipeline
          | 'QueryTable' >> _ReadFromBigQueryImpl(  # pylint: disable=no-value-for-parameter
              query=split_pattern)
          | 'ToTFExample' >> beam.Map(converter.RowToExample))


class Executor(base_example_gen_executor.BaseExampleGenExecutor):
  """Generic TFX BigQueryExampleGen executor."""

  def GetInputSourceToExamplePTransform(self) -> beam.PTransform:
    """Returns PTransform for BigQuery to TF examples."""
    return _BigQueryToExample
