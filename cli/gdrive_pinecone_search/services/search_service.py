"""Search service for managing hybrid search with dense and sparse vector operations."""

import time
from pinecone import Pinecone
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ..utils.rate_limiter import rate_limited, PINECONE_RATE_LIMITER
from ..utils.exceptions import (
    AuthenticationError, 
    IndexNotFoundError, 
    IncompatibleIndexError,
    DocumentProcessingError
)


class SearchService:
    """Service for hybrid search with dense and sparse indexes."""
    
    def __init__(self, api_key: str, dense_index_name: str, sparse_index_name: str, reranking_model: str = "pinecone-rerank-v0"):
        """
        Initialize hybrid service.
        
        Args:
            api_key: Pinecone API key
            dense_index_name: Name of the dense Pinecone index
            sparse_index_name: Name of the sparse Pinecone index
            reranking_model: Name of the reranking model to use
        """
        self.api_key = api_key
        self.dense_index_name = dense_index_name
        self.sparse_index_name = sparse_index_name
        self.reranking_model = reranking_model
        self.dense_index = None
        self.sparse_index = None
        
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=api_key)
        
        # Check if indexes exist
        if not self.pc.has_index(dense_index_name):
            raise IndexNotFoundError(f"Dense index '{dense_index_name}' not found")
        if not self.pc.has_index(sparse_index_name):
            raise IndexNotFoundError(f"Sparse index '{sparse_index_name}' not found")
        
        # Get indexes
        self.dense_index = self.pc.Index(dense_index_name)
        self.sparse_index = self.pc.Index(sparse_index_name)
    
    def create_indexes(self, dense_dimension: int = 1024, metric: str = "cosine") -> bool:
        """
        Create dense and sparse indexes with integrated embedding models.
        
        Args:
            dense_dimension: Vector dimension for dense index
            metric: Distance metric
            
        Returns:
            True if indexes were created successfully
        """
        try:
            # Create dense index with integrated embedding
            if not self.pc.has_index(self.dense_index_name):
                self.pc.create_index_for_model(
                    name=self.dense_index_name,
                    cloud="aws",
                    region="us-east-1",
                    embed={
                        "model": "multilingual-e5-large",
                        "field_map": {"text": "chunk_text"}
                    }
                )
                
                # Wait for index to be ready
                while not self.pc.describe_index(self.dense_index_name).status['ready']:
                    time.sleep(1)
                
                self.dense_index = self.pc.Index(self.dense_index_name)
            
            # Create sparse index with integrated embedding
            if not self.pc.has_index(self.sparse_index_name):
                self.pc.create_index_for_model(
                    name=self.sparse_index_name,
                    cloud="aws",
                    region="us-east-1",
                    embed={
                        "model": "pinecone-sparse-english-v0",
                        "field_map": {"text": "chunk_text"}
                    }
                )
                
                # Wait for index to be ready
                while not self.pc.describe_index(self.sparse_index_name).status['ready']:
                    time.sleep(1)
                
                self.sparse_index = self.pc.Index(self.sparse_index_name)
            
            return True
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to create indexes: {e}")
    
    @rate_limited(1000, 60)  # 1000 requests per minute
    def upsert_hybrid_vectors(self, vectors: List[Dict[str, Any]], batch_size: int = 96) -> int:
        """
        Upsert vectors into both dense and sparse indexes using integrated embedding.
        
        Args:
            vectors: List of vector dictionaries with '_id', 'chunk_text', and metadata fields
            batch_size: Number of vectors to upsert per batch
            
        Returns:
            Number of vectors upserted
        """
        try:
            total_upserted = 0
            
            # Process in batches
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                
                # Prepare batches for both indexes (same format for both)
                dense_vectors = []
                sparse_vectors = []
                
                for vector in batch:
                    # Prepare records for both indexes (integrated embedding handles the rest)
                    # For integrated embedding, use upsert_records with text field
                    record = {
                        '_id': vector['id'],
                        'text': vector['chunk_text']  # Use 'text' as specified in field_map
                    }
                    
                    # Add metadata fields directly to the record
                    if 'metadata' in vector:
                        record.update(vector['metadata'])
                    
                    dense_vectors.append(record)
                    sparse_vectors.append(record)
                
                # Upsert to both indexes using upsert_records (integrated embedding will generate vectors automatically)
                self.dense_index.upsert_records("__default__", dense_vectors)  # Use default namespace
                self.sparse_index.upsert_records("__default__", sparse_vectors)  # Use default namespace
                total_upserted += len(batch)
            
            return total_upserted
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to upsert hybrid vectors: {e}")
    
    @rate_limited(1000, 60)
    def hybrid_query(self, 
                    query_text: str,
                    top_k: int = 10,
                    filter_dict: Optional[Dict[str, Any]] = None,
                    include_metadata: bool = True) -> List[Dict[str, Any]]:
        """
        Perform hybrid search using both dense and sparse indexes with integrated embedding.
        
        Args:
            query_text: Query text (embedding will be generated automatically)
            top_k: Number of results to return
            filter_dict: Metadata filter
            include_metadata: Whether to include metadata in results
            
        Returns:
            List of reranked query results
        """
        try:
            # Step 1: Query both indexes separately using integrated embedding
            # Get 4x the limit to ensure we have enough results after deduplication
            query_params = {
                "top_k": top_k * 4,  # Get 4x more results to merge
                "inputs": {
                    "text": query_text
                }
            }
            
            # Add filter to query if provided
            if filter_dict:
                query_params["filter"] = filter_dict
            
            dense_results = self.dense_index.search(
                namespace="__default__",
                query=query_params
            )

            
            sparse_results = self.sparse_index.search(
                namespace="__default__",
                query=query_params
            )
            


            
            # Step 2: Extract matches from the search results
            # Based on the debug output, the results are in the response object itself
            dense_matches = []
            sparse_matches = []
            
            # Extract dense results - new Pinecone API structure
            if hasattr(dense_results, 'result') and dense_results.result:
                if hasattr(dense_results.result, 'hits'):
                    dense_matches = dense_results.result.hits
                elif hasattr(dense_results.result, 'matches'):
                    dense_matches = dense_results.result.matches
            elif hasattr(dense_results, 'hits'):
                dense_matches = dense_results.hits
            elif hasattr(dense_results, 'matches'):
                dense_matches = dense_results.matches
            elif hasattr(dense_results, 'results'):
                dense_matches = dense_results.results
            
            # Extract sparse results - new Pinecone API structure
            if hasattr(sparse_results, 'result') and sparse_results.result:
                if hasattr(sparse_results.result, 'hits'):
                    sparse_matches = sparse_results.result.hits
                elif hasattr(sparse_results.result, 'matches'):
                    sparse_matches = sparse_results.result.matches
            elif hasattr(sparse_results, 'hits'):
                sparse_matches = sparse_results.hits
            elif hasattr(sparse_results, 'matches'):
                sparse_matches = sparse_results.matches
            elif hasattr(sparse_results, 'results'):
                sparse_matches = sparse_results.results
            
            merged_results = self._merge_and_deduplicate_results(dense_matches, sparse_matches)
            
            # Step 3: File-level deduplication BEFORE reranking (more efficient)
            if merged_results:
                # Deduplicate by file_id and select best chunks using smart scoring
                deduplicated_for_rerank = self._deduplicate_by_document_before_rerank(merged_results, top_k * 2)
                
                # Step 4: Rerank the deduplicated results
                reranked_results = self._rerank_results(deduplicated_for_rerank, query_text, top_k)
                
                return reranked_results
            else:
                return []
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to perform hybrid query: {e}")
    
    def _merge_and_deduplicate_results(self, dense_matches: List[Dict], sparse_matches: List[Dict]) -> List[Dict]:
        """
        Merge and deduplicate results from dense and sparse searches.
        Follows Pinecone's recommended approach for hybrid search.
        
        Args:
            dense_matches: Results from dense search
            sparse_matches: Results from sparse search
            
        Returns:
            Merged and deduplicated results with individual scores tracked
        """
        # Deduplicate by _id (vector ID)
        deduped_hits = {}
        
        # Add dense results
        for hit in dense_matches:
            if hit is None:
                continue

            hit_id = hit.get('_id') or hit.get('id')
            hit_score = hit.get('_score') or hit.get('score')
            hit_metadata = hit.get('fields') or hit.get('metadata', {})
            
            if hit_id and hit_score is not None:
                deduped_hits[hit_id] = {
                    '_id': hit_id,
                    '_score': hit_score,
                    'dense_score': hit_score,
                    'sparse_score': 0.0,
                    'chunk_text': hit_metadata.get('text', ''),
                    'metadata': hit_metadata
                }
        
        # Add sparse results (overwrite if higher score)
        for hit in sparse_matches:
            if hit is None:
                continue
            hit_id = hit.get('_id') or hit.get('id')
            hit_score = hit.get('_score') or hit.get('score')
            hit_metadata = hit.get('fields') or hit.get('metadata', {})
            
            if hit_id and hit_score is not None:
                if hit_id in deduped_hits:
                    # Update sparse score and keep the higher combined score
                    deduped_hits[hit_id]['sparse_score'] = hit_score
                    if hit_score > deduped_hits[hit_id]['_score']:
                        deduped_hits[hit_id]['_score'] = hit_score
                else:
                    # New result
                    deduped_hits[hit_id] = {
                        '_id': hit_id,
                        '_score': hit_score,
                        'dense_score': 0.0,
                        'sparse_score': hit_score,
                        'chunk_text': hit_metadata.get('text', ''),
                        'metadata': hit_metadata
                    }
        
        # Sort by score descending
        sorted_hits = sorted(deduped_hits.values(), key=lambda x: x['_score'], reverse=True)
        return sorted_hits
    
    @rate_limited(100, 60)  # 100 reranking requests per minute
    def _rerank_results(self, merged_results: List[Dict], query_text: str, top_k: int) -> List[Dict]:
        """
        Rerank results using Pinecone's hosted reranking model.
        Follows Pinecone's recommended approach for reranking.
        
        Args:
            merged_results: Merged and deduplicated results
            query_text: Original query text
            top_k: Number of results to return
            
        Returns:
            Reranked results
        """
        try:
            if not merged_results:
                return []
            
            # Transform to format expected by reranking API
            # Truncate text to fit within token limits
            documents_for_rerank = []
            for hit in merged_results:
                # Truncate text to roughly 400 tokens (safe limit)
                chunk_text = hit['chunk_text']
                if len(chunk_text) > 1600:  # Roughly 4 chars per token
                    chunk_text = chunk_text[:1600] + "..."
                
                documents_for_rerank.append({
                    '_id': hit['_id'], 
                    'text': chunk_text
                })
            
            # Use Pinecone's hosted reranking model
            # Pinecone reranking has a limit of 100 documents
            max_rerank_documents = min(100, len(documents_for_rerank))
            rerank_response = self.pc.inference.rerank(
                model=self.reranking_model,
                query=query_text,
                documents=documents_for_rerank[:max_rerank_documents],  # Limit to 100 documents
                top_n=max_rerank_documents,  # Rerank all documents we send
                return_documents=True
            )
            
            # Map reranked results back to original format
            reranked_results = []
            for rerank_result in rerank_response.data:
                # Find the original result
                original_result = next(
                    (hit for hit in merged_results if hit['_id'] == rerank_result.document['_id']), 
                    None
                )
                
                if original_result:
                    reranked_result_dict = {
                        'id': original_result['_id'],
                        'score': rerank_result.score,
                        'metadata': original_result['metadata'],
                        'reranked_score': rerank_result.score,
                        'original_score': original_result['_score'],
                        'dense_score': original_result.get('dense_score', 0.0),
                        'sparse_score': original_result.get('sparse_score', 0.0)
                    }
                    reranked_results.append(reranked_result_dict)
            
            # Return only the requested number of results
            return reranked_results[:top_k]
            
        except Exception as e:
            # If reranking fails, return original results
            print(f"Warning: Reranking failed, returning original results: {e}")
            return [
                {
                    'id': hit['_id'],
                    'score': hit['_score'],
                    'metadata': hit['metadata'],
                    'reranked_score': hit['_score'],
                    'original_score': hit['_score'],
                    'dense_score': hit.get('dense_score', 0.0),
                    'sparse_score': hit.get('sparse_score', 0.0)
                }
                for hit in merged_results[:top_k]
            ]
    
    def _deduplicate_by_document_before_rerank(self, merged_results: List[Dict], max_results: int) -> List[Dict]:
        """
        Deduplicate results by document (file_id) BEFORE reranking using smart scoring.
        This is more efficient as it reduces the number of documents sent to the reranker.
        
        Args:
            merged_results: List of merged results from dense and sparse searches
            max_results: Maximum number of results to return (typically top_k * 2)
            
        Returns:
            Document-level deduplicated results optimized for reranking
        """
        # Group results by file_id
        document_groups = {}
        
        for result in merged_results:
            file_id = result.get('metadata', {}).get('file_id')
            if not file_id:
                continue
                
            if file_id not in document_groups:
                document_groups[file_id] = []
            
            document_groups[file_id].append(result)
        
        # For each document, select the best chunk using smart scoring
        deduplicated_results = []
        for file_id, results in document_groups.items():
            # Use smart scoring to predict which chunk will perform best after reranking
            best_result = self._select_best_chunk_for_reranking(results)
            if best_result:
                deduplicated_results.append(best_result)
        
        # Sort by combined score (highest first) and return up to max_results
        deduplicated_results.sort(key=lambda x: x.get('_score', 0), reverse=True)
        return deduplicated_results[:max_results]
    
    def _select_best_chunk_for_reranking(self, chunks: List[Dict]) -> Optional[Dict]:
        """
        Select the best chunk from a document for reranking using smart scoring.
        
        Strategy:
        1. Normalize sparse scores to 0-1 range (typically 0-100)
        2. Calculate weighted combined score: (2 * dense_score + sparse_score) / 3
        3. Prefer earlier chunks (lower chunk_index) as they often contain more relevant content
        4. Fallback to dense score if sparse score is 0
        
        Args:
            chunks: List of chunks from the same document
            
        Returns:
            Best chunk for reranking, or None if no valid chunks
        """
        if not chunks:
            return None
        
        best_chunk = None
        best_score = -1
        
        for chunk in chunks:
            dense_score = chunk.get('dense_score', 0.0)
            sparse_score = chunk.get('sparse_score', 0.0)
            chunk_index = chunk.get('metadata', {}).get('chunk_index', 999)
            
            # Normalize sparse score to 0-1 range (dot product scores can vary widely)
            # Based on our observations, sparse scores are typically 0-10 range
            # Use a more conservative normalization to avoid over-weighting sparse scores
            normalized_sparse_score = min(sparse_score / 10.0, 1.0) if sparse_score > 0 else 0.0
            
            # Calculate weighted combined score (dense gets 2x weight)
            # Formula: (2*dense + sparse) / 3 gives us proper weighted average
            if sparse_score > 0:
                combined_score = (2.0 * dense_score + normalized_sparse_score) / 3.0
            else:
                # Fallback to dense score if no sparse score
                combined_score = dense_score
            
            # Apply chunk position bonus (earlier chunks get slight preference)
            # This helps prioritize introduction/overview content
            position_bonus = max(0, (10 - chunk_index) * 0.01)  # Small bonus for early chunks
            final_score = combined_score + position_bonus
            
            if final_score > best_score:
                best_score = final_score
                best_chunk = chunk
        
        return best_chunk
    
    def _deduplicate_by_document(self, reranked_results: List[Dict], top_k: int) -> List[Dict]:
        """
        Deduplicate results by document (file_id), keeping the highest scoring chunk from each document.
        This method is kept for backward compatibility but is no longer used in the main flow.
        
        Args:
            reranked_results: List of reranked results
            top_k: Number of results to return
            
        Returns:
            Document-level deduplicated results
        """
        # Group results by file_id
        document_groups = {}
        
        for result in reranked_results:
            file_id = result.get('metadata', {}).get('file_id')
            if not file_id:
                continue
                
            if file_id not in document_groups:
                document_groups[file_id] = []
            
            document_groups[file_id].append(result)
        
        # For each document, keep the highest scoring result
        deduplicated_results = []
        for file_id, results in document_groups.items():
            # Sort by score (highest first) and take the best one
            best_result = max(results, key=lambda x: x.get('score', 0))
            deduplicated_results.append(best_result)
        
        # Sort by score (highest first) and return top_k
        deduplicated_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return deduplicated_results[:top_k]
    
    @rate_limited(1000, 60)
    def delete_vectors(self, vector_ids: List[str]) -> int:
        """
        Delete vectors from both indexes.
        
        Args:
            vector_ids: List of vector IDs to delete
            
        Returns:
            Number of vectors deleted
        """
        try:
            # Delete from both indexes
            self.dense_index.delete(ids=vector_ids)
            self.sparse_index.delete(ids=vector_ids)
            return len(vector_ids)
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to delete vectors: {e}")
    
    @rate_limited(1000, 60)
    def delete_by_metadata(self, filter_dict: Dict[str, Any]) -> int:
        """
        Delete vectors by metadata filter from both indexes.
        
        Args:
            filter_dict: Metadata filter for deletion
            
        Returns:
            Number of vectors deleted
        """
        try:
            # Delete from both indexes
            self.dense_index.delete(filter=filter_dict)
            self.sparse_index.delete(filter=filter_dict)
            return 0  # Pinecone doesn't return count for filter-based deletion
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to delete vectors by metadata: {e}")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics from both indexes.
        
        Returns:
            Combined index statistics dictionary
        """
        try:
            dense_stats = self.dense_index.describe_index_stats()
            sparse_stats = self.sparse_index.describe_index_stats()
            
            dense_vectors = dense_stats.get('total_vector_count', 0)
            sparse_vectors = sparse_stats.get('total_vector_count', 0)
            
            # For hybrid search with integrated embedding, both indexes should have the same count
            # Use the greater of the two (or either if they're equal)
            total_vectors = max(dense_vectors, sparse_vectors)
            
            return {
                'dense_index': dense_stats,
                'sparse_index': sparse_stats,
                'total_vectors': total_vectors,
                'dense_vectors': dense_vectors,
                'sparse_vectors': sparse_vectors,
                'dense_namespaces': dense_stats.get('namespaces', {}),
                'sparse_namespaces': sparse_stats.get('namespaces', {}),
                'namespaces': dense_stats.get('namespaces', {})  # Keep for backward compatibility
            }
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to get index stats: {e}")
    
    def get_detailed_index_stats(self) -> Dict[str, Any]:
        """
        Get detailed statistics from both indexes for debugging.
        
        Returns:
            Detailed index statistics dictionary
        """
        try:
            dense_stats = self.dense_index.describe_index_stats()
            sparse_stats = self.sparse_index.describe_index_stats()
            
            dense_vectors = dense_stats.get('total_vector_count', 0)
            sparse_vectors = sparse_stats.get('total_vector_count', 0)
            
            return {
                'dense_vectors': dense_vectors,
                'sparse_vectors': sparse_vectors,
                'total_vectors': max(dense_vectors, sparse_vectors),
                'vectors_match': dense_vectors == sparse_vectors,
                'dense_index_stats': dense_stats,
                'sparse_index_stats': sparse_stats
            }
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to get detailed index stats: {e}")
    
    def get_index_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Get index metadata from both indexes.
        
        Returns:
            Index metadata dictionary or None if not found
        """
        try:
            dense_metadata = None
            sparse_metadata = None
            
            # Try to fetch metadata from dense index
            try:
                dense_response = self.dense_index.fetch(ids=['__index_metadata__'])
                # Handle new Pinecone API response format
                if hasattr(dense_response, 'vectors'):
                    vectors = dense_response.vectors
                else:
                    vectors = dense_response['vectors']
                
                if '__index_metadata__' in vectors:
                    vector_data = vectors['__index_metadata__']
                    if hasattr(vector_data, 'metadata'):
                        dense_metadata = vector_data.metadata
                    else:
                        dense_metadata = vector_data['metadata']
            except Exception:
                pass
            
            # Try to fetch metadata from sparse index
            try:
                sparse_response = self.sparse_index.fetch(ids=['__index_metadata__'])
                # Handle new Pinecone API response format
                if hasattr(sparse_response, 'vectors'):
                    vectors = sparse_response.vectors
                else:
                    vectors = sparse_response['vectors']
                
                if '__index_metadata__' in vectors:
                    vector_data = vectors['__index_metadata__']
                    if hasattr(vector_data, 'metadata'):
                        sparse_metadata = vector_data.metadata
                    else:
                        sparse_metadata = vector_data['metadata']
            except Exception:
                pass
            
            # Return the most complete metadata (prefer dense if both exist)
            if dense_metadata:
                return dense_metadata
            elif sparse_metadata:
                return sparse_metadata
            else:
                return None
            
        except Exception as e:
            # If metadata doesn't exist, return None
            return None
    
    def get_index_models(self) -> Dict[str, str]:
        """
        Get the actual model names from both indexes.
        
        Returns:
            Dictionary with 'dense_model' and 'sparse_model' keys
        """
        try:
            # Get index descriptions
            dense_desc = self.pc.describe_index(self.dense_index_name)
            sparse_desc = self.pc.describe_index(self.sparse_index_name)
            
            dense_model = dense_desc.get('embed', {}).get('model', 'Unknown')
            sparse_model = sparse_desc.get('embed', {}).get('model', 'Unknown')
            
            return {
                'dense_model': dense_model,
                'sparse_model': sparse_model
            }
            
        except Exception as e:
            # Fallback to default models if we can't get the info
            return {
                'dense_model': 'multilingual-e5-large',
                'sparse_model': 'pinecone-sparse-english-v0'
            }
    
    def update_index_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        Update index metadata in both indexes.
        
        Args:
            metadata: Metadata to store
            
        Returns:
            True if successful
        """
        try:
            # For integrated embedding indexes, use upsert_records with simple text
            metadata_record = {
                '_id': '__index_metadata__',
                'text': 'Index metadata record for hybrid search configuration and statistics.'
            }
            
            # Add all metadata fields directly to the record
            metadata_record.update(metadata)
            
            # Upsert to both indexes using upsert_records
            self.dense_index.upsert_records("__default__", [metadata_record])
            self.sparse_index.upsert_records("__default__", [metadata_record])
            
            return True
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to update index metadata: {e}")
    
    def cleanup_deleted_files(self, existing_file_ids: List[str]) -> int:
        """
        Remove vectors for files that no longer exist in Google Drive.
        
        Args:
            existing_file_ids: List of file IDs that still exist
            
        Returns:
            Number of files cleaned up
        """
        try:
            # Get indexed file IDs using the list_file_ids method
            indexed_file_ids = set(self.list_file_ids())
            
            deleted_file_ids = indexed_file_ids - set(existing_file_ids)
            
            cleaned_count = 0
            for file_id in deleted_file_ids:
                # Delete all chunks for this file from both indexes
                self.delete_by_metadata({'file_id': file_id})
                cleaned_count += 1
            
            return cleaned_count
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to cleanup deleted files: {e}")
    
    def list_file_ids(self) -> List[str]:
        """
        Get list of all file IDs in the index.
        
        Returns:
            List of unique file IDs
        """
        try:
            # Use a query to get all vectors and extract file IDs from their metadata
            # We'll use a dummy vector and a large top_k to get as many results as possible
            response = self.dense_index.query(
                vector=[0.0] * 1024,  # Dummy vector for query
                top_k=10000,  # Get a large number of results
                include_metadata=True
            )
            
            file_ids = set()
            
            # Extract hits from the response
            if hasattr(response, 'matches'):
                hits = response.matches
            elif hasattr(response, 'result') and response.result:
                hits = response.result.hits if hasattr(response.result, 'hits') else []
            elif hasattr(response, 'hits'):
                hits = response.hits
            else:
                hits = []
            
            # Extract file IDs from metadata
            for hit in hits:
                metadata = hit.get('metadata', {})
                file_id = metadata.get('file_id')
                if file_id:
                    file_ids.add(file_id)
            
            return list(file_ids)
            
        except Exception as e:
            # If the query approach fails, return an empty list
            # This means the refresh command will rely on the last_refresh_time from metadata
            return []
    
    def validate_metadata_size(self, metadata: Dict[str, Any]) -> Tuple[bool, int]:
        """
        Validate metadata size against Pinecone limits.
        
        Args:
            metadata: Metadata dictionary to validate
            
        Returns:
            Tuple of (is_valid, size_in_bytes)
        """
        import json
        metadata_json = json.dumps(metadata)
        size_bytes = len(metadata_json.encode('utf-8'))
        return size_bytes <= 40960, size_bytes
