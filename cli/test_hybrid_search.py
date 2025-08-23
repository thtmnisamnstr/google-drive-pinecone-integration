#!/usr/bin/env python3
"""
Test script for hybrid search functionality with integrated embedding.

This script tests the hybrid search implementation including:
- Configuration loading
- Service initialization
- Index creation with integrated embedding
- Query processing with integrated embedding and reranking
"""

import os
import sys
from typing import Dict, Any

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from gdrive_pinecone_search.utils.config_manager import ConfigManager
from gdrive_pinecone_search.services.search_service import SearchService
from gdrive_pinecone_search.utils.exceptions import ConfigurationError


def test_hybrid_search():
    """Test the complete hybrid search functionality with integrated embedding."""
    print("🧪 Testing Hybrid Search Implementation with Integrated Embedding")
    print("=" * 60)
    
    # Test 1: Configuration Loading
    print("\n1. Testing Configuration Loading...")
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        print(f"   ✅ Configuration loaded successfully")
        print(f"   📋 Dense Index: {config_manager.get_dense_index_name()}")
        print(f"   📋 Sparse Index: {config_manager.get_sparse_index_name()}")
        print(f"   📋 Reranking Model: {config.settings.reranking_model}")
        print(f"   📋 Chunk Size: {config.settings.chunk_size}")
        print(f"   📋 Chunk Overlap: {config.settings.chunk_overlap}")
        
    except ConfigurationError as e:
        print(f"   ❌ Configuration Error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected Error: {e}")
        return False
    
    # Test 2: Service Initialization
    print("\n2. Testing Service Initialization...")
    try:
        api_key = config_manager.get_pinecone_api_key()
        dense_index_name = config_manager.get_dense_index_name()
        sparse_index_name = config_manager.get_sparse_index_name()
        reranking_model = config.settings.reranking_model
        
        search_service = SearchService(
            api_key,
            dense_index_name,
            sparse_index_name,
            reranking_model
        )
        
        print(f"   ✅ SearchService initialized successfully")
        
    except Exception as e:
        print(f"   ❌ Service Initialization Error: {e}")
        return False
    
    # Test 3: Index Statistics
    print("\n3. Testing Index Statistics...")
    try:
        stats = search_service.get_index_stats()
        total_vectors = stats.get('total_vectors', 0)
        
        print(f"   ✅ Index statistics retrieved successfully")
        print(f"   📊 Total Vectors: {total_vectors}")
        
        if total_vectors == 0:
            print(f"   ⚠️  Warning: Indexes are empty. Run 'gdrive-pinecone-search owner index' to populate them.")
        
    except Exception as e:
        print(f"   ❌ Index Statistics Error: {e}")
        return False
    
    # Test 4: Test Vector Upserting with Integrated Embedding
    print("\n4. Testing Vector Upserting with Integrated Embedding...")
    try:
        # Test data
        test_vectors = [
            {
                'id': 'test_doc_1#0',
                'chunk_text': 'This is a test document about artificial intelligence and machine learning.',
                # Flatten metadata fields
                'file_id': 'test_doc_1',
                'file_name': 'Test Document 1',
                'file_type': 'docs',
                'chunk_index': 0,
                'modified_time': '2024-01-15T10:30:00.000Z',
                'web_view_link': 'https://docs.google.com/test1'
            },
            {
                'id': 'test_doc_2#0',
                'chunk_text': 'The quarterly budget report shows increased spending on technology infrastructure.',
                # Flatten metadata fields
                'file_id': 'test_doc_2',
                'file_name': 'Test Document 2',
                'file_type': 'docs',
                'chunk_index': 0,
                'modified_time': '2024-01-15T10:30:00.000Z',
                'web_view_link': 'https://docs.google.com/test2'
            }
        ]
        
        # Upsert test vectors (integrated embedding will handle vector generation)
        upserted_count = search_service.upsert_hybrid_vectors(test_vectors)
        print(f"   ✅ Test vectors upserted successfully: {upserted_count} vectors")
        
    except Exception as e:
        print(f"   ❌ Vector Upserting Error: {e}")
        return False
    
    # Test 5: Hybrid Query with Integrated Embedding
    print("\n5. Testing Hybrid Query with Integrated Embedding...")
    try:
        test_query = "artificial intelligence and machine learning applications"
        
        results = search_service.hybrid_query(
            query_text=test_query,
            top_k=5
        )
        
        print(f"   ✅ Hybrid query with integrated embedding completed successfully")
        print(f"   📊 Results returned: {len(results)}")
        
        if results:
            print(f"   📈 Top result score: {results[0].get('score', 0):.4f}")
            print(f"   📈 Top result reranked score: {results[0].get('reranked_score', 0):.4f}")
            print(f"   📈 Top result original score: {results[0].get('original_score', 0):.4f}")
        
    except Exception as e:
        print(f"   ❌ Hybrid Query Error: {e}")
        return False
    
    # Test 6: Cleanup Test Vectors
    print("\n6. Testing Vector Cleanup...")
    try:
        # Delete test vectors
        test_ids = ['test_doc_1#0', 'test_doc_2#0']
        deleted_count = search_service.delete_vectors(test_ids)
        print(f"   ✅ Test vectors cleaned up successfully: {deleted_count} vectors deleted")
        
    except Exception as e:
        print(f"   ❌ Vector Cleanup Error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("\n🎉 Hybrid search implementation with integrated embedding is working correctly!")
    print("\nNext steps:")
    print("1. Run 'gdrive-pinecone-search owner index' to populate your indexes")
    print("2. Try searching with 'gdrive-pinecone-search search \"your query\"'")
    print("3. Use 'gdrive-pinecone-search status' to check your configuration")
    
    return True


if __name__ == "__main__":
    print("🚀 Starting Hybrid Search Tests with Integrated Embedding")
    print("This will test the complete hybrid search implementation with integrated embedding.")
    print("Make sure you have configured your Pinecone API key and index names.\n")
    
    success = test_hybrid_search()
    
    if success:
        print("\n🎯 All tests passed! Your hybrid search implementation with integrated embedding is ready to use.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check your configuration and try again.")
        sys.exit(1)
