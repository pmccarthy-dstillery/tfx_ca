# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: bigquery_example_gen.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='bigquery_example_gen.proto',
  package='tfx_ca.bigquery_example_gen',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x1a\x62igquery_example_gen.proto\x12\x1btfx_ca.bigquery_example_gen\"\x1c\n\x0c\x42igQuerySeed\x12\x0c\n\x04seed\x18\x01 \x01(\tb\x06proto3'
)




_BIGQUERYSEED = _descriptor.Descriptor(
  name='BigQuerySeed',
  full_name='tfx_ca.bigquery_example_gen.BigQuerySeed',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='seed', full_name='tfx_ca.bigquery_example_gen.BigQuerySeed.seed', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=59,
  serialized_end=87,
)

DESCRIPTOR.message_types_by_name['BigQuerySeed'] = _BIGQUERYSEED
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

BigQuerySeed = _reflection.GeneratedProtocolMessageType('BigQuerySeed', (_message.Message,), {
  'DESCRIPTOR' : _BIGQUERYSEED,
  '__module__' : 'bigquery_example_gen_pb2'
  # @@protoc_insertion_point(class_scope:tfx_ca.bigquery_example_gen.BigQuerySeed)
  })
_sym_db.RegisterMessage(BigQuerySeed)


# @@protoc_insertion_point(module_scope)