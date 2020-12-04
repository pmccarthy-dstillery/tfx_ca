import os
import pickle
from typing import Text, Tuple

import absl
import numpy as np
from sklearn.neural_network import MLPClassifier

from tfx.components.trainer.executor import TrainerFnArgs
from tfx.components.trainer.fn_args_utils import DataAccessor
from tfx.dsl.io import fileio
from tfx.utils import io_utils
from tfx_bsl.tfxio import dataset_options

from tensorflow_metadata.proto.v0 import schema_pb2

from sklearn.pipeline import Pipeline
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import CountVectorizer

import numpy as np
from typing import Text, Tuple

_LABEL_KEY = 'label'
_FEATURE_KEYS = ['content']

def _input_fn(
    file_pattern: Text,
    data_accessor: DataAccessor,
    schema: schema_pb2.Schema,
    batch_size: int = 20,
) -> Tuple[np.ndarray, np.ndarray]:
  """Generates features and label for tuning/training.

  Args:
    file_pattern: input tfrecord file pattern.
    data_accessor: DataAccessor for converting input to RecordBatch.
    schema: schema of the input data.
    batch_size: An int representing the number of records to combine in a single
      batch.

  Returns:
    A (features, indices) tuple where features is a matrix of features, and
      indices is a single vector of label indices.
  """
  record_batch_iterator = data_accessor.record_batch_factory(
      file_pattern,
      dataset_options.RecordBatchesOptions(batch_size=batch_size, num_epochs=1),
      schema)

  feature_list = []
  label_list = []
  for record_batch in record_batch_iterator:
    record_dict = {}
    for column, field in zip(record_batch, record_batch.schema):
      record_dict[field.name] = column.flatten()

    label_list.append(record_dict[_LABEL_KEY])
    features = [record_dict[key] for key in _FEATURE_KEYS]
    feature_list.append(np.stack(features, axis=-1))

  return np.concatenate(feature_list), np.concatenate(label_list)

def run_fn(fn_args: TrainerFnArgs):
    
    schema = io_utils.parse_pbtxt_file(fn_args.schema_file, schema_pb2.Schema())    

    x_train, y_train = _input_fn(fn_args.train_files, 
        fn_args.data_accessor, 
        schema)

    cls = SGDClassifier(loss='log',
        penalty='elasticnet',
        learning_rate='adaptive',
        eta0=2,
        verbose=1,
        tol=1e-2)

    count_vectorizer = CountVectorizer()

    pipeline = Pipeline([
        ('vect', count_vectorizer),
        ('cls', cls)
        ])
    
    grid = {'cls__alpha':[0.01,0.5,0.99,2,5], 
            'cls__l1_ratio':[0.01,0.5,0.99]}

    grid_search_cv = GridSearchCV(pipeline, param_grid=grid, scoring='roc_auc')

    print(x_train.shape)
    print(x_train[0:2,:])
    # ravel here 
    # model = grid_search_cv.fit(X=x_train.ravel(), y=y_train)
    model = pipeline.fit(X=x_train.ravel(), y=y_train)

    x_eval, y_eval = _input_fn(fn_args.eval_files, fn_args.data_accessor, schema)

    score = model.score(x_eval.ravel(), y_eval)
    absl.logging.info('Accuracy: %f', score)

    os.makedirs(fn_args.serving_model_dir)

    model_path = os.path.join(fn_args.serving_model_dir, 'model.pkl')
    with fileio.open(model_path, 'wb+') as f:
        pickle.dump(model, f)