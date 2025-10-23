#!/usr/bin/env python3
"""
rag_manager.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.
"""

RAG Manager for Reflexia LLM implementation
Handles Retrieval-Augmented Generation using ChromaDB
"""
import os
import sys
import time
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Union, Tuple

# Force CPU for embeddings to avoid Metal issues on Apple Silicon
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['USE_MPS'] = '0'

logger = logging.getLogger("reflexia-tools.rag")

class RAGManager:
    """RAG Manager for Reflexia LLM"""
    
    def __init__(self, config, model_manager=None):
        """Initialize the RAG manager
        
        Args:
            config: Configuration object
            model_manager: Model manager for generation (optional)
        """
        self.config = config
        self.model_manager = model_manager
        
        # Get configuration
        self.chunk_size = config.get("rag", "chunk_size", default=1000)
        self.chunk_overlap = config.get("rag", "chunk_overlap", default=200)
        self.similarity_top_k = config.get("rag", "similarity_top_k", default=3)
        self.embedding_model = config.get("rag", "embedding_model", default="all-MiniLM-L6-v2")
        
        # Vector database path
        self.vector_db_path = Path(config.get("paths", "vector_db_dir", default="vector_db"))
        
        # Initialize embedding function and vector database
        self._initialize_vector_db()
        
        logger.info("RAG manager initialized")
    
    def _initialize_vector_db(self):
        """Initialize the vector database"""
        try:
            # Import here to allow optional dependency
            import chromadb
            from chromadb.utils import embedding_functions
            
            # Create vector database directory if it doesn't exist
            os.makedirs(self.vector_db_path, exist_ok=True)
            
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(path=str(self.vector_db_path))
            
            # Initialize embedding function
            logger.info(f"Using {self.embedding_model} for embeddings")
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model,
                device="cpu"  # Force CPU for Apple Silicon compatibility
            )
            
            logger.info(f"Vector database initialized at {self.vector_db_path}")
            return True
        except ImportError:
            logger.warning("ChromaDB or sentence-transformers not installed. RAG functionality will be limited.")
            logger.warning("Install with: pip install chromadb sentence-transformers")
            self.chroma_client = None
            self.embedding_function = None
            return False
        except Exception as e:
            logger.error(f"Error initializing vector database: {e}")
            self.chroma_client = None
            self.embedding_function = None
            return False
    
    def is_available(self) -> bool:
        """Check if RAG is available"""
        return self.chroma_client is not None and self.embedding_function is not None
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to the vector database
        
        Args:
            documents: List of documents with id, text, and metadata
            
        Returns:
            bool: Success status
        """
        if not self.is_available():
            logger.error("Vector database is not available")
            return False
        
        try:
            # Get or create collection
            collection_name = "documents"
            try:
                collection = self.chroma_client.get_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function
                )
            except Exception:
                collection = self.chroma_client.create_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function,
                    metadata={"description": "Documents for RAG"}
                )
            
            # Prepare documents for insertion
            texts = []
            ids = []
            metadatas = []
            
            for doc in documents:
                texts.append(doc["text"])
                ids.append(doc.get("id", f"doc_{len(texts)}"))
                metadatas.append(doc.get("metadata", {}))
            
            # Add to collection
            collection.add(
                documents=texts,
                ids=ids,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(texts)} documents to collection '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Error adding documents to vector database: {e}")
            return False
    
    def chunk_text(self, text: str) -> List[str]:
        """Chunk text into smaller pieces
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        if not text.strip():
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # Find a good chunk end (preferably at paragraph or sentence)
            end = min(start + self.chunk_size, text_length)
            
            # If not at the end of text, try to find a good breakpoint
            if end < text_length:
                # Try to break at paragraph
                paragraph_end = text.rfind("\n\n", start, end)
                if paragraph_end > start + self.chunk_size // 2:
                    end = paragraph_end + 2
                else:
                    # Try to break at sentence (period + space)
                    sentence_end = text.rfind(". ", start, end)
                    if sentence_end > start + self.chunk_size // 2:
                        end = sentence_end + 2
            
            # Add the chunk
            chunks.append(text[start:end])
            
            # Move start position, with overlap
            start = end - self.chunk_overlap
            if start <= 0 or start >= text_length:
                break
        
        return chunks
    
    def load_file(self, file_path: Union[str, Path], metadata: Dict[str, Any] = None) -> bool:
        """Load a file into the vector database"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return False
            
            # Basic file type handling
            suffix = file_path.suffix.lower()
            
            if suffix in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json']:
                # Simple text files
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            elif suffix in ['.pdf']:
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(file_path)
                    text = ""
                    for page in doc:
                        text += page.get_text()
                    doc.close()
                except ImportError:
                    logger.error("PDF support requires PyMuPDF. Install with: pip install pymupdf")
                    print("PDF support requires additional libraries. Install with: pip install pymupdf")
                    return False
            else:
                logger.error(f"Unsupported file type: {suffix}")
                return False
            
            # Create base metadata
            base_metadata = {
                "source": str(file_path),
                "filename": file_path.name,
                "filetype": suffix[1:],
                "added_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Add custom metadata
            if metadata:
                base_metadata.update(metadata)
            
            # Chunk the text
            chunks = self.chunk_text(text)
            
            # Prepare documents
            documents = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = base_metadata.copy()
                chunk_metadata["chunk_id"] = i
                chunk_metadata["chunk_total"] = len(chunks)
                
                documents.append({
                    "id": f"{file_path.stem}-{i}",
                    "text": chunk,
                    "metadata": chunk_metadata
                })
            
            # Add to vector database
            success = self.add_documents(documents)
            
            if success:
                logger.info(f"Loaded {file_path} into vector database ({len(chunks)} chunks)")
                return True
            else:
                logger.error(f"Failed to add documents to vector database")
                return False
                
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            return False
    
    def query(self, query_text: str, collection_name: str = "documents", 
             n_results: int = None, filter_criteria: Dict = None) -> List[Dict]:
        """Query the vector database"""
        try:
            # Try to get the requested collection
            try:
                collection = self.chroma_client.get_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function
                )
                logger.info(f"Using collection: {collection_name}")
            except Exception:
                # Try alternative collection name as fallback
                fallback_name = "default" if collection_name == "documents" else "documents"
                try:
                    collection = self.chroma_client.get_collection(
                        name=fallback_name,
                        embedding_function=self.embedding_function
                    )
                    logger.info(f"Using fallback collection: {fallback_name}")
                except Exception as e:
                    logger.error(f"No collections found: {e}")
                    return []
            
            # Use default if not specified
            if n_results is None:
                n_results = self.similarity_top_k
            
            # Query the collection
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=filter_criteria
            )
            
            # Format results
            formatted_results = []
            if results and "documents" in results and len(results["documents"]) > 0:
                docs = results["documents"][0]
                metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
                distances = results.get("distances", [[]])[0] if results.get("distances") else []
                
                for i, doc in enumerate(docs):
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    distance = distances[i] if i < len(distances) else 1.0
                    similarity = 1.0 - distance/2.0
                    
                    formatted_results.append({
                        "text": doc,
                        "metadata": metadata,
                        "similarity": similarity
                    })
                
                logger.info(f"Found {len(formatted_results)} relevant documents")
            else:
                logger.warning(f"No documents found for query: {query_text}")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error querying vector database: {e}")
            return []
    
    def generate_rag_response(self, query_text: str, system_prompt: str = None,
                            collection_name: str = "documents") -> Dict:
        """Generate a response using RAG
        
        Args:
            query_text: User query
            system_prompt: System prompt to use
            collection_name: Name of collection to query
            
        Returns:
            Dict with response and context information
        """
        try:
            # 1. Query the vector database
            context_docs = self.query(query_text, collection_name)
            
            if not context_docs:
                logger.warning("No relevant documents found for query")
                # Fall back to regular generation
                response = self.model_manager.generate_response(
                    query_text,
                    system_prompt=system_prompt
                )
                return {
                    "response": response,
                    "context_used": False,
                    "sources": [],
                    "context_docs": []
                }
            
            # 2. Prepare context
            context_text = "\n\n".join([f"Context {i+1}:\n{doc['text']}" for i, doc in enumerate(context_docs)])
            
            # 3. Create a RAG prompt
            rag_system_prompt = system_prompt or "You are a helpful assistant that answers based on the provided context."
            rag_system_prompt += "\nAnswer the question based on the context provided. If the context doesn't contain relevant information, say so."
            
            rag_prompt = f"Context Information:\n{context_text}\n\nQuestion: {query_text}\n\nAnswer:"
            
            # 4. Generate response
            response = self.model_manager.generate_response(
                rag_prompt,
                system_prompt=rag_system_prompt
            )
            
            # 5. Prepare result with sources
            sources = []
            for doc in context_docs:
                if "metadata" in doc and "source" in doc["metadata"]:
                    source = doc["metadata"]["source"]
                    if source not in sources:
                        sources.append(source)
            
            return {
                "response": response,
                "context_used": True,
                "sources": sources,
                "context_docs": context_docs
            }
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            # Fall back to regular generation
            try:
                response = self.model_manager.generate_response(
                    query_text,
                    system_prompt=system_prompt
                )
                return {
                    "response": response,
                    "context_used": False,
                    "sources": [],
                    "context_docs": [],
                    "error": str(e)
                }
            except Exception as e2:
                logger.error(f"Error with fallback generation: {e2}")
                return {
                    "response": "Error generating response.",
                    "context_used": False,
                    "sources": [],
                    "context_docs": [],
                    "error": f"{e}; Fallback error: {e2}"
                }
    
    def _process_dataset_directory(self, dir_path, output_file):
        """Process a directory of dataset files"""
        with open(output_file, 'w') as f_out:
            # Process each JSON or JSONL file
            for file_path in dir_path.glob('**/*.json*'):
                try:
                    with open(file_path, 'r') as f_in:
                        # Determine file format
                        if file_path.suffix == '.json':
                            # JSON array
                            data = json.load(f_in)
                            
                            for item in data:
                                prompt = item.get('instruction', item.get('prompt', item.get('input', '')))
                                response = item.get('output', item.get('response', item.get('completion', '')))
                                
                                if prompt and response:
                                    example = {"prompt": prompt, "response": response}
                                    f_out.write(json.dumps(example) + '\n')
                        
                        elif file_path.suffix == '.jsonl':
                            # JSONL format
                            for line in f_in:
                                if line.strip():
                                    item = json.loads(line)
                                    prompt = item.get('instruction', item.get('prompt', item.get('input', '')))
                                    response = item.get('output', item.get('response', item.get('completion', '')))
                                    
                                    if prompt and response:
                                        example = {"prompt": prompt, "response": response}
                                        f_out.write(json.dumps(example) + '\n')
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
