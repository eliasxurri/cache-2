# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: book_service.proto
# Protobuf Python Version: 4.25.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x12\x62ook_service.proto\x12\x04\x62ook\"(\n\x15GetBookDetailsRequest\x12\x0f\n\x07item_id\x18\x01 \x01(\x03\"O\n\x16GetBookDetailsResponse\x12\x0f\n\x07user_id\x18\x01 \x01(\x03\x12\x10\n\x08progress\x18\x02 \x01(\x05\x12\x12\n\ndb_latency\x18\x03 \x01(\x01\x32Z\n\x0b\x42ookService\x12K\n\x0eGetBookDetails\x12\x1b.book.GetBookDetailsRequest\x1a\x1c.book.GetBookDetailsResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'book_service_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_GETBOOKDETAILSREQUEST']._serialized_start=28
  _globals['_GETBOOKDETAILSREQUEST']._serialized_end=68
  _globals['_GETBOOKDETAILSRESPONSE']._serialized_start=70
  _globals['_GETBOOKDETAILSRESPONSE']._serialized_end=149
  _globals['_BOOKSERVICE']._serialized_start=151
  _globals['_BOOKSERVICE']._serialized_end=241
# @@protoc_insertion_point(module_scope)
