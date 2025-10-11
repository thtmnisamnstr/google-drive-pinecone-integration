"""Tests for SearchService cleanup helpers."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest


def _make_vector(metadata):
    return SimpleNamespace(metadata=metadata)


def _setup_service_with_indexes(list_side_effect, fetch_side_effect):
    from gdrive_pinecone_search.services.search_service import SearchService
    import gdrive_pinecone_search.services.search_service as search_service

    dense_index = Mock()
    sparse_index = Mock()

    dense_index.list.side_effect = list_side_effect
    dense_index.fetch.side_effect = fetch_side_effect

    pc_instance = Mock()
    pc_instance.has_index.return_value = True
    pc_instance.Index.side_effect = [dense_index, sparse_index]

    search_service.Pinecone = Mock(return_value=pc_instance)

    service = SearchService('api-key', 'dense', 'sparse')
    service.delete_by_metadata = Mock()
    return service, dense_index, sparse_index


def test_cleanup_deleted_files_invokes_delete():
    list_responses = [
        SimpleNamespace(vector_ids=['file-keep#0', '__index_metadata__'], pagination_token='token-1'),
        SimpleNamespace(vector_ids=['file-delete#0'], pagination_token=None),
    ]

    fetch_responses = [
        SimpleNamespace(vectors={
            'file-keep#0': _make_vector({'file_id': 'file-keep'}),
            '__index_metadata__': _make_vector({'file_id': '__index_metadata__'})
        }),
        SimpleNamespace(vectors={
            'file-delete#0': _make_vector({'file_id': 'file-delete'})
        })
    ]

    service, _, _ = _setup_service_with_indexes(list_responses, fetch_responses)

    cleaned = service.cleanup_deleted_files(['file-keep'])

    assert cleaned == 1
    service.delete_by_metadata.assert_called_once_with({'file_id': 'file-delete'})


def test_list_file_ids_handles_empty_pages():
    service, _, _ = _setup_service_with_indexes(
        [SimpleNamespace(vector_ids=[], pagination_token=None)],
        [SimpleNamespace(vectors={})]
    )

    assert service.list_file_ids() == []

