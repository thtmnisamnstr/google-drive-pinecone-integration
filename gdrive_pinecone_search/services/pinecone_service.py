"""Pinecone service for vector database operations."""

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


class PineconeService:
    """Service for Pinecone vector database operations."""
    
    def __init__(self, api_key: str, index_name: str):
        """
        Initialize Pinecone service.
        
        Args:
            api_key: Pinecone API key
            index_name: Name of the Pinecone index
        """
        self.api_key = api_key
        self.index_name = index_name
        self.index = None
        
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=api_key)
        
        # Check if index exists
        if not self.pc.has_index(index_name):
            raise IndexNotFoundError(f"Index '{index_name}' not found")
        
        # Get index
        self.index = self.pc.Index(index_name)
    
    def create_index(self, dimension: int = 1024, metric: str = "cosine") -> bool:
        """
        Create a new Pinecone index.
        
        Args:
            dimension: Vector dimension
            metric: Distance metric
            
        Returns:
            True if index was created successfully
        """
        try:
            if self.pc.has_index(self.index_name):
                return True  # Index already exists
            
            # Create index using ServerlessSpec for free tier
            from pinecone import ServerlessSpec
            
            self.pc.create_index(
                name=self.index_name,
                dimension=dimension,
                metric=metric,
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            
            # Wait for index to be ready
            while not self.pc.describe_index(self.index_name).status['ready']:
                import time
                time.sleep(1)
            
            self.index = self.pc.Index(self.index_name)
            return True
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to create index: {e}")
    
    @rate_limited(1000, 60)  # 1000 requests per minute
    def upsert_vectors(self, vectors: List[Dict[str, Any]], batch_size: int = 100) -> int:
        """
        Upsert vectors into the index.
        
        Args:
            vectors: List of vector dictionaries with 'id', 'values', and 'metadata'
            batch_size: Number of vectors to upsert per batch
            
        Returns:
            Number of vectors upserted
        """
        try:
            total_upserted = 0
            
            # Process in batches
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                
                # Prepare batch for Pinecone
                pinecone_vectors = []
                for vector in batch:
                    pinecone_vectors.append({
                        'id': vector['id'],
                        'values': vector['values'],
                        'metadata': vector['metadata']
                    })
                
                # Upsert batch
                self.index.upsert(vectors=pinecone_vectors)
                total_upserted += len(batch)
            
            return total_upserted
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to upsert vectors: {e}")
    
    @rate_limited(1000, 60)
    def query_vectors(self, 
                     query_vector: List[float], 
                     top_k: int = 10,
                     filter_dict: Optional[Dict[str, Any]] = None,
                     include_metadata: bool = True) -> List[Dict[str, Any]]:
        """
        Query vectors in the index.
        
        Args:
            query_vector: Query vector
            top_k: Number of results to return
            filter_dict: Metadata filter
            include_metadata: Whether to include metadata in results
            
        Returns:
            List of query results
        """
        try:
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                filter=filter_dict,
                include_metadata=include_metadata
            )
            
            return results.matches
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to query vectors: {e}")
    
    @rate_limited(1000, 60)
    def delete_vectors(self, vector_ids: List[str]) -> int:
        """
        Delete vectors from the index.
        
        Args:
            vector_ids: List of vector IDs to delete
            
        Returns:
            Number of vectors deleted
        """
        try:
            self.index.delete(ids=vector_ids)
            return len(vector_ids)
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to delete vectors: {e}")
    
    @rate_limited(1000, 60)
    def delete_by_metadata(self, filter_dict: Dict[str, Any]) -> int:
        """
        Delete vectors by metadata filter.
        
        Args:
            filter_dict: Metadata filter for deletion
            
        Returns:
            Number of vectors deleted
        """
        try:
            self.index.delete(filter=filter_dict)
            return 0  # Pinecone doesn't return count for filter-based deletion
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to delete vectors by metadata: {e}")
    
    @rate_limited(1000, 60)
    def fetch_vectors(self, vector_ids: List[str]) -> Dict[str, Any]:
        """
        Fetch specific vectors by ID.
        
        Args:
            vector_ids: List of vector IDs to fetch
            
        Returns:
            Dictionary mapping vector IDs to vector data
        """
        try:
            results = self.index.fetch(ids=vector_ids)
            return results.vectors
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to fetch vectors: {e}")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.
        
        Returns:
            Index statistics dictionary
        """
        try:
            stats = self.index.describe_index_stats()
            return stats
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to get index stats: {e}")
    
    def get_index_info(self) -> Dict[str, Any]:
        """
        Get detailed index information.
        
        Returns:
            Index information dictionary
        """
        try:
            info = self.pc.describe_index(self.index_name)
            return {
                'name': info.name,
                'dimension': info.dimension,
                'metric': info.metric,
                'status': info.status,
                'host': info.host
            }
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to get index info: {e}")
    
    def update_index_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        Update index metadata vector.
        
        Args:
            metadata: Metadata to store
            
        Returns:
            True if successful
        """
        try:
            # Create metadata vector (all zeros with metadata)
            metadata_vector = [0.0] * 1024  # 1024 dimensions
            
            self.index.upsert(
                vectors=[{
                    'id': '__index_metadata__',
                    'values': metadata_vector,
                    'metadata': metadata
                }]
            )
            
            return True
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to update index metadata: {e}")
    
    def get_index_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Get index metadata.
        
        Returns:
            Index metadata dictionary or None if not found
        """
        try:
            results = self.index.fetch(ids=['__index_metadata__'])
            if '__index_metadata__' in results.vectors:
                return results.vectors['__index_metadata__'].metadata
            return None
            
        except Exception:
            return None
    
    def list_file_ids(self) -> List[str]:
        """
        Get list of all file IDs in the index.
        
        Returns:
            List of unique file IDs
        """
        try:
            stats = self.get_index_stats()
            namespaces = stats.get('namespaces', {})
            
            file_ids = set()
            for namespace_data in namespaces.values():
                # Extract file IDs from vector IDs (format: file_id#chunk_index)
                for vector_id in namespace_data.get('vector_count', []):
                    if '#' in vector_id:
                        file_id = vector_id.split('#')[0]
                        file_ids.add(file_id)
            
            return list(file_ids)
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to list file IDs: {e}")
    
    def get_file_chunks(self, file_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific file.
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            List of chunk metadata
        """
        try:
            # Query for all vectors with this file_id
            results = self.index.query(
                vector=[0.0] * 1024,  # Dummy vector
                top_k=1000,  # Large number to get all chunks
                filter={'file_id': file_id},
                include_metadata=True
            )
            
            return results.matches
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to get file chunks: {e}")
    
    def cleanup_deleted_files(self, existing_file_ids: List[str]) -> int:
        """
        Remove vectors for files that no longer exist in Google Drive.
        
        Args:
            existing_file_ids: List of file IDs that still exist
            
        Returns:
            Number of files cleaned up
        """
        try:
            indexed_file_ids = set(self.list_file_ids())
            deleted_file_ids = indexed_file_ids - set(existing_file_ids)
            
            cleaned_count = 0
            for file_id in deleted_file_ids:
                # Delete all chunks for this file
                self.delete_by_metadata({'file_id': file_id})
                cleaned_count += 1
            
            return cleaned_count
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to cleanup deleted files: {e}") 