import os
import re
import json
from typing import List, Dict, Any
import logging
from tqdm import tqdm
import time
import traceback
import gc

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Environment
from dotenv import load_dotenv

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vector_store_creation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()


class JSONDocumentProcessor:
    """Document processor for JSON formatted legal documents with metadata extraction"""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=500,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self.supported_languages = ['EN', 'HI']  # English and Hindi only

    def extract_metadata_from_filename(self, filename: str) -> Dict[str, Any]:
        """Extract metadata from filename patterns"""
        metadata = {}

        # Extract year from filename (various patterns)
        year_patterns = [
            r'(\d{4})',  # 4-digit year
            r'Act.*?(\d{4})',  # Act followed by year
            r'(\d{4}).*?Act',  # Year followed by Act
        ]

        for pattern in year_patterns:
            match = re.search(pattern, filename)
            if match:
                metadata['year'] = int(match.group(1))
                break

        # Extract act name (remove file extension and common prefixes)
        act_name = filename.replace('.pdf', '').replace('.PDF', '')
        act_name = re.sub(r'^(The\s+)?', '', act_name)  # Remove "The" prefix
        metadata['act_name'] = act_name
        metadata['filename'] = filename

        return metadata

    def extract_metadata_from_content(self, text: str) -> Dict[str, Any]:
        """Extract additional metadata from document content"""
        metadata = {}

        # Extract act number if present
        act_number_pattern = r'Act\s+No\.?\s*(\d+)'
        match = re.search(act_number_pattern, text, re.IGNORECASE)
        if match:
            metadata['act_number'] = int(match.group(1))

        # Extract date patterns
        date_patterns = [
            # DD/MM/YYYY or DD-MM-YYYY
            r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})',
            # YYYY/MM/DD or YYYY-MM-DD
            r'(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})',
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Convert tuples to strings and store first 5 dates
                date_strings = ['/'.join(match) for match in matches[:5]]
                metadata['dates_mentioned'] = ', '.join(date_strings)
                break

        # Extract keywords related to the document type
        keywords = []
        keyword_patterns = [
            r'\b(amendment|repeal|modification|property|land|revenue)\b',
            r'\b(section|chapter|clause|subsection|paragraph)\b',
            r'\b(court|tribunal|authority|commission|board)\b'
        ]

        for pattern in keyword_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            keywords.extend(matches)

        if keywords:
            metadata['keywords'] = ', '.join(set(keywords))  # Remove duplicates

        return metadata

    def load_processed_documents(self, json_file_path: str) -> List[Dict[str, Any]]:
        """Load processed documents from JSON file"""
        logger.info(f"Loading processed documents from: {json_file_path}")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            
            logger.info(f"Loaded {len(documents)} documents from JSON file")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to load JSON file {json_file_path}: {e}")
            logger.debug(traceback.format_exc())
            raise

    def filter_documents_by_language(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter documents to only include English and Hindi languages"""
        logger.info("Filtering documents by language (en, hi only)...")
        
        filtered_docs = []
        language_counts = {}
        
        for doc in documents:
            metadata = doc.get('metadata', {})
            language = metadata.get('language', '')
            
            # Track language distribution
            language_counts[language] = language_counts.get(language, 0) + 1
            
            # Only include English and Hindi documents
            if language in self.supported_languages:
                filtered_docs.append(doc)
        
        logger.info(f"Language distribution in original documents: {language_counts}")
        logger.info(f"Filtered documents: {len(filtered_docs)} (from {len(documents)} total)")
        
        return filtered_docs

    def process_json_documents(self, json_file_path: str) -> List[Document]:
        """Process documents from JSON file into LangChain Document objects"""
        logger.info(f"Starting to process documents from JSON file: {json_file_path}")
        
        start_time = time.time()
        
        try:
            # Load documents from JSON
            raw_documents = self.load_processed_documents(json_file_path)
            
            # Filter by language
            filtered_documents = self.filter_documents_by_language(raw_documents)
            
            if not filtered_documents:
                logger.warning("No documents found with supported languages (en, hi)")
                return []
            
            processed_documents = []
            
            # Process each document
            for idx, doc_data in enumerate(tqdm(filtered_documents, desc="Processing documents")):
                try:
                    page_content = doc_data.get('page_content', '')
                    original_metadata = doc_data.get('metadata', {})
                    
                    if not page_content.strip():
                        logger.warning(f"Empty content in document {idx}")
                        continue
                    
                    # Extract filename from source path
                    source_path = original_metadata.get('source', '')
                    filename = os.path.basename(source_path) if source_path else f"document_{idx}"
                    
                    # Extract metadata from filename
                    filename_metadata = self.extract_metadata_from_filename(filename)
                    
                    # Extract metadata from content
                    content_metadata = self.extract_metadata_from_content(page_content)
                    
                    # Combine all metadata
                    combined_metadata = {
                        **original_metadata,
                        **filename_metadata,
                        **content_metadata,
                        'document_id': idx,
                        'content_length': len(page_content)
                    }
                    
                    # Check if content needs to be split into chunks
                    if len(page_content) > self.text_splitter._chunk_size:
                        # Split into chunks
                        chunks = self.text_splitter.split_text(page_content)
                        logger.debug(f"Split document {idx} into {len(chunks)} chunks")
                        
                        # Create documents for each chunk
                        for chunk_idx, chunk in enumerate(chunks):
                            chunk_metadata = combined_metadata.copy()
                            chunk_metadata.update({
                                'chunk_id': chunk_idx,
                                'total_chunks': len(chunks),
                                'chunk_size': len(chunk),
                                'is_chunked': True
                            })
                            
                            processed_documents.append(Document(
                                page_content=chunk,
                                metadata=chunk_metadata
                            ))
                    else:
                        # Use as single document
                        combined_metadata.update({
                            'chunk_id': 0,
                            'total_chunks': 1,
                            'chunk_size': len(page_content),
                            'is_chunked': False
                        })
                        
                        processed_documents.append(Document(
                            page_content=page_content,
                            metadata=combined_metadata
                        ))
                        
                except Exception as e:
                    logger.error(f"Failed to process document {idx}: {e}")
                    logger.debug(traceback.format_exc())
                    continue
            
            processing_time = time.time() - start_time
            logger.info(f"Document processing completed in {processing_time:.2f} seconds")
            logger.info(f"Created {len(processed_documents)} document chunks from {len(filtered_documents)} original documents")
            
            return processed_documents
            
        except Exception as e:
            logger.error(f"Failed to process JSON documents: {e}")
            logger.debug(traceback.format_exc())
            return []


class VectorStoreManager:
    """Manages the vector store creation and updates"""

    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.document_processor = JSONDocumentProcessor()
        self.embeddings = self._initialize_embeddings()

    def _initialize_embeddings(self):
        """Initialize embedding model using sentence-transformers"""
        logger.info("Initializing sentence-transformers embeddings...")
        
        try:
            # Using all-MiniLM-L6-v2 model - good balance of speed and quality
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},  # Change to 'cuda' if you have GPU
                encode_kwargs={'normalize_embeddings': True}
            )
            
            logger.info("Sentence-transformers embeddings initialized successfully")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            logger.debug(traceback.format_exc())
            raise

    def create_vector_store(self, json_file_path: str, batch_size: int = 100):
        """Create vector store from processed JSON documents"""
        logger.info(f"Creating vector store from JSON file: {json_file_path}")
        
        if not os.path.exists(json_file_path):
            raise ValueError(f"JSON file not found: {json_file_path}")

        try:
            # Process documents from JSON
            logger.info("Processing documents from JSON...")
            all_documents = self.document_processor.process_json_documents(json_file_path)
            
            if not all_documents:
                raise ValueError("No documents were processed successfully")
            
            logger.info(f"Total documents to be added to vector store: {len(all_documents)}")
            
            # Create vector store in batches
            vector_store = None
            total_processed = 0
            
            # Process documents in batches to manage memory
            for i in tqdm(range(0, len(all_documents), batch_size), desc="Creating vector store"):
                batch = all_documents[i:i + batch_size]
                batch_num = i//batch_size + 1
                total_batches = (len(all_documents) + batch_size - 1) // batch_size
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} documents)")
                batch_start_time = time.time()
                
                try:
                    if vector_store is None:
                        logger.info("Creating new vector store...")
                        vector_store = Chroma.from_documents(
                            documents=batch,
                            embedding=self.embeddings,
                            persist_directory=self.persist_directory,
                            collection_name="indian_law_acts"
                        )
                        logger.info("Vector store created successfully")
                    else:
                        logger.info("Adding documents to existing vector store...")
                        vector_store.add_documents(batch)
                        logger.info("Documents added successfully")
                    
                    total_processed += len(batch)
                    batch_time = time.time() - batch_start_time
                    logger.info(f"Batch {batch_num} completed in {batch_time:.2f} seconds")
                    
                except Exception as e:
                    logger.error(f"Failed to process batch {batch_num}: {e}")
                    logger.debug(traceback.format_exc())
                    continue
                
                # Force garbage collection to free memory
                gc.collect()
                
                # Add a small delay between batches
                time.sleep(1)
            
            logger.info(f"Vector store creation completed!")
            logger.info(f"Total documents processed: {total_processed}")
            
            if all_documents:
                # Save metadata summary
                self._save_metadata_summary(all_documents)
            
            return vector_store
            
        except Exception as e:
            logger.error(f"Failed to create vector store: {e}")
            logger.debug(traceback.format_exc())
            raise

    def _save_metadata_summary(self, documents: List[Document]):
        """Save summary of processed documents"""
        logger.info("Saving metadata summary...")
        
        try:
            summary = {
                'total_documents': len(documents),
                'languages': {},
                'acts_by_year': {},
                'act_names': [],
                'keywords': [],
                'sources': []
            }

            for doc in documents:
                metadata = doc.metadata

                # Group by language
                language = metadata.get('language', 'unknown')
                summary['languages'][language] = summary['languages'].get(language, 0) + 1

                # Group by year
                year = metadata.get('year')
                if year:
                    summary['acts_by_year'][year] = summary['acts_by_year'].get(year, 0) + 1

                # Collect act names
                act_name = metadata.get('act_name')
                if act_name and act_name not in summary['act_names']:
                    summary['act_names'].append(act_name)

                # Collect keywords (parse from comma-separated string)
                keywords_str = metadata.get('keywords', '')
                if keywords_str:
                    keywords = [k.strip() for k in keywords_str.split(',')]
                    summary['keywords'].extend(keywords)

                # Collect sources
                source = metadata.get('source')
                if source and source not in summary['sources']:
                    summary['sources'].append(source)

            # Remove duplicate keywords
            summary['keywords'] = list(set(summary['keywords']))

            # Ensure directory exists
            os.makedirs(self.persist_directory, exist_ok=True)

            # Save summary
            summary_path = os.path.join(self.persist_directory, 'metadata_summary.json')
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

            logger.info(f"Metadata summary saved to {summary_path}")
            logger.info(f"Summary statistics:")
            logger.info(f"  Total documents: {summary['total_documents']}")
            logger.info(f"  Languages: {summary['languages']}")
            logger.info(f"  Unique acts: {len(summary['act_names'])}")
            logger.info(f"  Unique sources: {len(summary['sources'])}")
            
        except Exception as e:
            logger.error(f"Failed to save metadata summary: {e}")
            logger.debug(traceback.format_exc())


def main():
    """Main function to set up vector store from JSON"""
    
    logger.info("Starting vector store creation from JSON process...")

    JSON_FILE_PATH = os.getenv("JSON_FILE_PATH", "./processed_documents_acts.json")
    PERSIST_DIR = os.getenv("PERSIST_DIR", "./chroma_db")
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", 500))

    logger.info(f"Configuration:")
    logger.info(f"  JSON File Path: {JSON_FILE_PATH}")
    logger.info(f"  Persist Directory: {PERSIST_DIR}")
    logger.info(f"  Batch Size: {BATCH_SIZE}")

    if not os.path.exists(JSON_FILE_PATH):
        raise ValueError(f"JSON file not found: {JSON_FILE_PATH}")

    try:
        # Create vector store manager
        logger.info("Creating vector store manager...")
        manager = VectorStoreManager(persist_directory=PERSIST_DIR)

        # Create vector store
        logger.info("Starting vector store creation...")
        start_time = time.time()
        
        vector_store = manager.create_vector_store(
            json_file_path=JSON_FILE_PATH,
            batch_size=BATCH_SIZE
        )
        
        total_time = time.time() - start_time

        if vector_store:
            logger.info("Vector store creation completed successfully!")
            logger.info(f"Total processing time: {total_time:.2f} seconds")
            logger.info(f"Vector store saved to: {PERSIST_DIR}")
            
            # Test the vector store
            logger.info("Testing vector store...")
            try:
                # Perform a simple similarity search to verify the vector store works
                test_results = vector_store.similarity_search("property rights", k=3)
                logger.info(f"Test search returned {len(test_results)} results")
                for i, result in enumerate(test_results):
                    logger.info(f"  Result {i+1}: {result.metadata.get('act_name', 'Unknown')} (language: {result.metadata.get('language', 'Unknown')})")
            except Exception as e:
                logger.warning(f"Vector store test failed: {e}")
                
        else:
            logger.error("Failed to create vector store - no documents were processed successfully")
            
    except Exception as e:
        logger.error(f"Vector store creation failed: {e}")
        logger.debug(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()