"""
Document ingestion optimized for short, structured CSV rows.
Implements one-row-one-document approach with canonical text layout and enhanced metadata.
Uses LangChain best practices with CSV loader and proper document processing.
"""

import asyncio
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4
import pandas as pd

from langchain_community.document_loaders import CSVLoader
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.logger import logger
from app.services.ai.config import ai_config
from app.services.ai.rag.schemas import DocumentChunk, IngestionResult


class DocumentIngester:
    """Handles document ingestion with one-row-one-document approach."""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=ai_config.openai_api_key,
            model=ai_config.openai_embedding_model,
            dimensions=ai_config.openai_embedding_dimension
        )
        
        self.qdrant_client = QdrantClient(
            url=ai_config.qdrant_url,
            api_key=ai_config.qdrant_api_key
        )
        
    async def ingest_csv_dataset(
        self, 
        csv_path: str, 
        tenant_id: str = "default",
        locale: str = "es_CR"
    ) -> IngestionResult:
        """
        Ingest CSV dataset with one-row-one-document approach using custom CSV processing.
        
        Args:
            csv_path: Path to CSV file
            tenant_id: Tenant identifier for multi-tenancy
            locale: Language locale (es_CR/en_US)
            
        Returns:
            IngestionResult with operation details
        """
        start_time = datetime.now()
        logger.info(f"Starting CSV ingestion from {csv_path}")
        
        try:
            # Load CSV data directly with pandas for better control
            df = await asyncio.to_thread(pd.read_csv, csv_path)
            logger.info(f"Loaded {len(df)} rows from CSV")
            
            # Ensure collection exists with proper indexes
            await self._ensure_collection_exists()
            
            # Process documents
            all_chunks = []
            documents_processed = 0
            
            for idx, row in df.iterrows():
                try:
                    chunks = await self._process_csv_row(row, tenant_id, locale, idx)
                    if chunks:  # Only add if chunks were created successfully
                        all_chunks.extend(chunks)
                        documents_processed += 1
                    
                    if documents_processed % 10 == 0:
                        logger.info(f"Processed {documents_processed} documents...")
                        
                except Exception as e:
                    logger.error(f"Error processing row {idx}: {str(e)}")
                    continue
            
            # Store chunks in Qdrant
            chunks_stored = await self._store_chunks(all_chunks)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            result = IngestionResult(
                success=True,
                documents_processed=documents_processed,
                chunks_created=len(all_chunks),
                chunks_stored=chunks_stored,
                processing_time_ms=int(processing_time),
                collection_name=ai_config.qdrant_collection_name
            )
            
            logger.info(f"Ingestion completed: {result.model_dump()}")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Ingestion failed: {str(e)}")
            
            return IngestionResult(
                success=False,
                documents_processed=0,
                chunks_created=0,
                chunks_stored=0,
                processing_time_ms=int(processing_time),
                errors=[str(e)],
                collection_name=ai_config.qdrant_collection_name
            )
    
    async def _process_csv_row(
        self, 
        row: pd.Series, 
        tenant_id: str, 
        locale: str, 
        row_idx: int
    ) -> List[DocumentChunk]:
        """Process a CSV row into one document with proper content extraction."""
        
        # Extract content and metadata from CSV row
        canonical_content = self._build_canonical_content_from_row(row)
        if not canonical_content.strip():
            return []
        
        # Generate stable doc_id
        doc_id = self._generate_doc_id_from_row(row, row_idx)
        
        # Generate version hash for content
        version_hash = hashlib.md5(canonical_content.encode()).hexdigest()
        
        # Extract enhanced metadata
        enhanced_metadata = self._extract_enhanced_metadata_from_row(row)
        
        # Split content only if it's too long (>800 chars)
        if len(canonical_content) > 800:
            chunks = self._split_large_content(canonical_content, row_idx)
        else:
            chunks = [canonical_content]
        
        # Create document chunks
        document_chunks = []
        for chunk_idx, chunk_text in enumerate(chunks):
            chunk = DocumentChunk(
                content=chunk_text.strip(),
                source=f"csv_row_{row_idx}",
                section=enhanced_metadata.get("section", "general"),
                subsection=enhanced_metadata.get("subsection"),
                tenant_id=tenant_id,
                locale=locale,
                version_hash=version_hash,
                updated_at=datetime.now(timezone.utc),
                pii=False,  # Assume no PII in knowledge base
                chunk_index=chunk_idx,
                # Enhanced metadata
                doc_id=doc_id,
                title=enhanced_metadata.get("title"),
                tags=enhanced_metadata.get("tags", []),
                price_crc=enhanced_metadata.get("price_crc"),
                price_text=enhanced_metadata.get("price_text"),
                url=enhanced_metadata.get("url"),
                contact_value=enhanced_metadata.get("contact_value"),
                channel_number=enhanced_metadata.get("channel_number"),
                is_faq=enhanced_metadata.get("is_faq", False),
                is_promo=enhanced_metadata.get("is_promo", False)
            )
            document_chunks.append(chunk)
        
        return document_chunks

    async def _process_document_row(
        self, 
        row: pd.Series, 
        tenant_id: str, 
        locale: str, 
        row_idx: int
    ) -> List[DocumentChunk]:
        """Process a single CSV row into one document with canonical layout."""
        
        # Extract content and metadata from CSV row
        canonical_content = self._build_canonical_content(row)
        if not canonical_content.strip():
            return []
        
        # Generate stable doc_id
        doc_id = self._generate_doc_id(row, row_idx)
        
        # Generate version hash for content
        version_hash = hashlib.md5(canonical_content.encode()).hexdigest()
        
        # Extract enhanced metadata
        metadata = self._extract_enhanced_metadata(row)
        
        # Split content only if it's too long (>800 chars)
        if len(canonical_content) > 800:
            chunks = self._split_large_content(canonical_content, row_idx)
        else:
            chunks = [canonical_content]
        
        # Create document chunks
        document_chunks = []
        for chunk_idx, chunk_text in enumerate(chunks):
            chunk = DocumentChunk(
                content=chunk_text.strip(),
                source=f"csv_row_{row_idx}",
                section=metadata.get("section", "general"),
                subsection=metadata.get("subsection"),
                tenant_id=tenant_id,
                locale=locale,
                version_hash=version_hash,
                updated_at=datetime.now(timezone.utc),
                pii=False,  # Assume no PII in knowledge base
                chunk_index=chunk_idx,
                # Enhanced metadata
                doc_id=doc_id,
                title=metadata.get("title"),
                tags=metadata.get("tags", []),
                price_crc=metadata.get("price_crc"),
                price_text=metadata.get("price_text"),
                url=metadata.get("url"),
                contact_value=metadata.get("contact_value"),
                channel_number=metadata.get("channel_number"),
                is_faq=metadata.get("is_faq", False),
                is_promo=metadata.get("is_promo", False)
            )
            document_chunks.append(chunk)
        
        return document_chunks
    
    def _safe_str(self, value: Any) -> str:
        """Safely convert any value to string, handling None and float values."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ""
        return str(value).strip()
    
    def _build_canonical_content_from_row(self, row: pd.Series) -> str:
        """
        Build canonical text layout from CSV row data.
        
        Format:
        [title]
        section > subsection (locale)
        details
        tags: t1, t2, ...
        precio: ₡xx (if present)
        <url> | <contact_value> (if present)
        """
        content_parts = []
        
        # Title
        title = self._safe_str(row.get("title"))
        if title and title != "":
            content_parts.append(f"[{title}]")
        
        # Section hierarchy
        section = self._safe_str(row.get("section", "general"))
        subsection = self._safe_str(row.get("subsection"))
        locale = self._safe_str(row.get("locale", "es_CR"))
        
        if subsection:
            content_parts.append(f"{section} > {subsection} ({locale})")
        else:
            content_parts.append(f"{section} ({locale})")
        
        # Details/content - THIS IS THE MAIN CONTENT
        details = self._safe_str(row.get("details"))
        if details:
            content_parts.append(details)
        
        # Tags
        tags_str = self._safe_str(row.get("tags"))
        if tags_str:
            # Clean up tags and split
            tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
            if tags:
                content_parts.append(f"tags: {', '.join(tags)}")
        
        # Price
        price_text = self._safe_str(row.get("price_text"))
        if price_text:
            content_parts.append(f"precio: {price_text}")
        
        # URL and contact info
        url = self._safe_str(row.get("url"))
        contact_value = self._safe_str(row.get("contact_value"))
        
        if url or contact_value:
            contact_parts = []
            if url:
                contact_parts.append(url)
            if contact_value:
                contact_parts.append(contact_value)
            content_parts.append(" | ".join(contact_parts))
        
        return "\n".join([part for part in content_parts if part])

    def _build_canonical_content(self, row: pd.Series) -> str:
        """
        Build canonical text layout for a CSV row.
        
        Format:
        [title]
        section > subsection (locale)
        details
        tags: t1, t2, ...
        precio: ₡xx (if present)
        <url> | <contact_value> (if present)
        """
        content_parts = []
        
        # Title
        title = self._extract_title(row)
        if title:
            content_parts.append(f"[{title}]")
        
        # Section hierarchy
        section = row.get("section", "general")
        subsection = row.get("subsection")
        if subsection:
            content_parts.append(f"{section} > {subsection}")
        else:
            content_parts.append(section)
        
        # Details/content
        details = self._extract_details(row)
        if details:
            content_parts.append(details)
        
        # Tags
        tags = self._extract_tags(row)
        if tags:
            content_parts.append(f"tags: {', '.join(tags)}")
        
        # Price
        price_text = self._extract_price_text(row)
        if price_text:
            content_parts.append(f"precio: {price_text}")
        
        # URL and contact info
        url = row.get("url") or row.get("link")
        contact = row.get("contact") or row.get("phone") or row.get("email")
        
        if url or contact:
            contact_parts = []
            if url:
                contact_parts.append(url)
            if contact:
                contact_parts.append(contact)
            content_parts.append(" | ".join(contact_parts))
        
        return "\n".join(content_parts)
    
    def _extract_title_from_metadata(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Extract title from metadata dictionary."""
        title_columns = ["title", "name", "plan", "service", "product"]
        for col in title_columns:
            if col in metadata:
                title = self._safe_str(metadata[col])
                if title:
                    return title
        return None
    
    def _extract_details_from_metadata(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Extract details/content from metadata dictionary."""
        detail_columns = [
            "content", "text", "description", "body", "message",
            "question", "answer", "info", "details", "features"
        ]
        
        details = []
        for col in detail_columns:
            if col in metadata:
                detail = self._safe_str(metadata[col])
                if detail:
                    details.append(detail)
        
        return "\n".join(details) if details else None
    
    def _extract_tags_from_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """Extract tags from metadata dictionary."""
        tags = []
        
        # Check for tags column
        if "tags" in metadata:
            tag_text = self._safe_str(metadata["tags"])
            if tag_text:
                if "," in tag_text:
                    tags.extend([tag.strip() for tag in tag_text.split(",") if tag.strip()])
                else:
                    tags.append(tag_text)
        
        # Check for category columns
        category_columns = ["category", "type", "service_type", "plan_type"]
        for col in category_columns:
            if col in metadata:
                category = self._safe_str(metadata[col])
                if category:
                    tags.append(category)
        
        return [tag for tag in tags if tag]
    
    def _extract_price_text_from_metadata(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Extract price as text from metadata dictionary."""
        price_columns = ["price", "costo", "tarifa", "valor"]
        for col in price_columns:
            if col in metadata:
                price = self._safe_str(metadata[col])
                if price:
                    # Add ₡ symbol if it's a number
                    if price.replace(".", "").replace(",", "").isdigit():
                        return f"₡{price}"
                    return price
        return None
    
    def _extract_enhanced_metadata_from_row(self, row: pd.Series) -> Dict[str, Any]:
        """Extract enhanced metadata from CSV row data."""
        enhanced_metadata = {}
        
        # Basic fields
        enhanced_metadata["title"] = self._safe_str(row.get("title"))
        enhanced_metadata["section"] = self._safe_str(row.get("section", "general"))
        enhanced_metadata["subsection"] = self._safe_str(row.get("subsection"))
        
        # Tags - extract from the tags column
        tags_str = self._safe_str(row.get("tags"))
        tags = []
        if tags_str:
            tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
        enhanced_metadata["tags"] = tags
        
        # Price information - use the CSV columns directly
        price_text = self._safe_str(row.get("price_text"))
        enhanced_metadata["price_text"] = price_text if price_text else None
        
        # Extract numeric price from price_crc column
        price_crc = row.get("price_crc")
        if price_crc and self._safe_str(price_crc):
            try:
                enhanced_metadata["price_crc"] = float(price_crc)
            except (ValueError, TypeError):
                enhanced_metadata["price_crc"] = None
        else:
            enhanced_metadata["price_crc"] = None
        
        # URLs and contact from CSV columns
        enhanced_metadata["url"] = self._safe_str(row.get("url")) or None
        enhanced_metadata["contact_value"] = self._safe_str(row.get("contact_value")) or None
        
        # Channel number from CSV
        channel_number = self._safe_str(row.get("channel_number"))
        enhanced_metadata["channel_number"] = channel_number if channel_number else None
        
        # Flags based on content analysis
        tags_lower = [tag.lower() for tag in tags]
        section_lower = enhanced_metadata["section"].lower()
        subsection_lower = (enhanced_metadata["subsection"] or "").lower()
        
        enhanced_metadata["is_faq"] = (
            "faq" in tags_lower or 
            "faq" in section_lower or 
            "faq" in subsection_lower
        )
        enhanced_metadata["is_promo"] = (
            "promo" in tags_lower or 
            "promocion" in tags_lower or
            "promociones" in subsection_lower
        )
        
        return enhanced_metadata
    
    def _generate_doc_id_from_row(self, row: pd.Series, row_idx: int) -> str:
        """Generate stable document ID from CSV row data."""
        # Use existing ID if available
        doc_id = self._safe_str(row.get("id"))
        if doc_id:
            return doc_id
        
        # Use title if available
        title = self._safe_str(row.get("title"))
        if title:
            return hashlib.md5(title.encode()).hexdigest()[:16]
        
        # Fallback to row index
        return f"doc_{row_idx}"

    def _extract_title(self, row: pd.Series) -> Optional[str]:
        """Extract title from row."""
        title_columns = ["title", "name", "plan", "service", "product"]
        for col in title_columns:
            if col in row.index and pd.notna(row[col]):
                title = self._safe_str(row[col])
                if title:
                    return title
        return None
    
    def _extract_details(self, row: pd.Series) -> Optional[str]:
        """Extract details/content from row."""
        detail_columns = [
            "content", "text", "description", "body", "message",
            "question", "answer", "info", "details", "features"
        ]
        
        details = []
        for col in detail_columns:
            if col in row.index and pd.notna(row[col]):
                detail = self._safe_str(row[col])
                if detail:
                    details.append(detail)
        
        return "\n".join(details) if details else None
    
    def _extract_tags(self, row: pd.Series) -> List[str]:
        """Extract tags from row."""
        tags = []
        
        # Check for tags column
        if "tags" in row.index and pd.notna(row["tags"]):
            tag_text = self._safe_str(row["tags"])
            if tag_text:
                if "," in tag_text:
                    tags.extend([tag.strip() for tag in tag_text.split(",") if tag.strip()])
                else:
                    tags.append(tag_text)
        
        # Check for category columns
        category_columns = ["category", "type", "service_type", "plan_type"]
        for col in category_columns:
            if col in row.index and pd.notna(row[col]):
                category = self._safe_str(row[col])
                if category:
                    tags.append(category)
        
        return [tag for tag in tags if tag]
    
    def _extract_price_text(self, row: pd.Series) -> Optional[str]:
        """Extract price as text."""
        price_columns = ["price", "costo", "tarifa", "valor"]
        for col in price_columns:
            if col in row.index and pd.notna(row[col]):
                price = self._safe_str(row[col])
                if price:
                    # Add ₡ symbol if it's a number
                    if price.replace(".", "").replace(",", "").isdigit():
                        return f"₡{price}"
                    return price
        return None
    
    def _extract_enhanced_metadata(self, row: pd.Series) -> Dict[str, Any]:
        """Extract enhanced metadata from row."""
        metadata = {}
        
        # Basic fields
        metadata["title"] = self._extract_title(row)
        metadata["section"] = row.get("section", "general")
        metadata["subsection"] = row.get("subsection")
        
        # Tags
        metadata["tags"] = self._extract_tags(row)
        
        # Price information
        price_text = self._extract_price_text(row)
        metadata["price_text"] = price_text
        
        if price_text:
            # Extract numeric price
            price_match = re.search(r'₡?([\d,]+\.?\d*)', price_text)
            if price_match:
                try:
                    price_str = price_match.group(1).replace(",", "")
                    metadata["price_crc"] = float(price_str)
                except ValueError:
                    pass
        
        # URLs and contact
        metadata["url"] = row.get("url") or row.get("link")
        metadata["contact_value"] = row.get("contact") or row.get("phone") or row.get("email")
        
        # Channel number for TV/radio
        metadata["channel_number"] = row.get("channel") or row.get("canal")
        
        # Flags
        metadata["is_faq"] = bool(row.get("is_faq", False) or "faq" in str(row.get("tags", "")).lower())
        metadata["is_promo"] = bool(row.get("is_promo", False) or "promo" in str(row.get("tags", "")).lower())
        
        return metadata
    
    def _generate_doc_id(self, row: pd.Series, row_idx: int) -> str:
        """Generate stable document ID."""
        # Use existing ID if available
        if "id" in row.index and pd.notna(row["id"]):
            return str(row["id"])
        
        # Use title if available
        title = self._extract_title(row)
        if title:
            return hashlib.md5(title.encode()).hexdigest()[:16]
        
        # Fallback to row index
        return f"row_{row_idx}"
    
    def _split_large_content(self, content: str, row_idx: int) -> List[str]:
        """Split large content into chunks if needed."""
        if len(content) <= 800:
            return [content]
        
        # Simple splitting by paragraphs
        paragraphs = content.split("\n\n")
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > 800:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def _ensure_collection_exists(self):
        """Ensure Qdrant collection exists with proper configuration and indexes."""
        collection_name = ai_config.qdrant_collection_name
        
        try:
            # Check if collection exists
            collections = await asyncio.to_thread(
                self.qdrant_client.get_collections
            )
            
            existing_names = [c.name for c in collections.collections]
            
            if collection_name not in existing_names:
                # Create collection with proper configuration
                await asyncio.to_thread(
                    self.qdrant_client.create_collection,
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=ai_config.openai_embedding_dimension,
                        distance=models.Distance.COSINE
                    )
                )
                
                logger.info(f"Created collection: {collection_name}")
                
                # Create payload indexes
                await self._create_payload_indexes(collection_name)
                
            else:
                logger.info(f"Collection already exists: {collection_name}")
                # Ensure indexes exist
                await self._create_payload_indexes(collection_name)
                
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {str(e)}")
            raise
    
    async def _create_payload_indexes(self, collection_name: str):
        """Create payload indexes for efficient filtering."""
        indexes_to_create = [
            ("tenant_id", "keyword"),
            ("locale", "keyword"),
            ("section", "keyword"),
            ("subsection", "keyword"),
            ("tags", "keyword"),
            ("doc_id", "keyword"),
            ("is_faq", "bool"),
            ("is_promo", "bool"),
        ]
        
        for field_name, field_type in indexes_to_create:
            try:
                if field_type == "keyword":
                    schema = models.PayloadFieldSchema.KEYWORD
                elif field_type == "bool":
                    schema = models.PayloadFieldSchema.BOOL
                else:
                    schema = models.PayloadFieldSchema.KEYWORD
                
                await asyncio.to_thread(
                    self.qdrant_client.create_payload_index,
                    collection_name=collection_name,
                    field_name=field_name,
                    field_schema=schema
                )
                logger.info(f"Created index for {field_name}")
            except Exception as e:
                # Index might already exist
                logger.debug(f"Index creation for {field_name} failed (might exist): {str(e)}")
    
    async def _store_chunks(self, chunks: List[DocumentChunk]) -> int:
        """Store document chunks in Qdrant."""
        if not chunks:
            return 0
        
        try:
            # Prepare documents for storage
            documents = []
            metadatas = []
            ids = []
            
            for chunk in chunks:
                # Create unique UUID for this chunk - Qdrant requires proper UUID format
                chunk_id = str(uuid4())
                
                documents.append(chunk.content)
                ids.append(chunk_id)
                
                # Prepare metadata
                metadata = {
                    "doc_id": chunk.doc_id,
                    "tenant_id": chunk.tenant_id,
                    "locale": chunk.locale,
                    "section": chunk.section,
                    "subsection": chunk.subsection,
                    "title": chunk.title,
                    "tags": chunk.tags,
                    "price_crc": chunk.price_crc,
                    "price_text": chunk.price_text,
                    "url": chunk.url,
                    "contact_value": chunk.contact_value,
                    "channel_number": chunk.channel_number,
                    "is_faq": chunk.is_faq,
                    "is_promo": chunk.is_promo,
                    "version_hash": chunk.version_hash,
                    "updated_at": chunk.updated_at.isoformat(),
                    "chunk_index": chunk.chunk_index,
                    "source": chunk.source
                }
                
                metadatas.append(metadata)
            
            # Store in Qdrant
            vector_store = QdrantVectorStore(
                client=self.qdrant_client,
                collection_name=ai_config.qdrant_collection_name,
                embedding=self.embeddings
            )
            
            await asyncio.to_thread(
                vector_store.add_texts,
                texts=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Stored {len(chunks)} chunks in Qdrant")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Error storing chunks: {str(e)}")
            raise


# Convenience functions
async def ingest_documents(
    csv_path: str = "app/services/ai/datasets/adn_rag_base_full_v1_3.csv",
    tenant_id: str = "default",
    locale: str = "es_CR"
) -> IngestionResult:
    """Convenience function to ingest documents."""
    ingester = DocumentIngester()
    return await ingester.ingest_csv_dataset(csv_path, tenant_id, locale)


async def check_collection_health() -> Dict[str, Any]:
    """Check the health of the Qdrant collection."""
    try:
        client = QdrantClient(
            url=ai_config.qdrant_url,
            api_key=ai_config.qdrant_api_key
        )
        
        collection_name = ai_config.qdrant_collection_name
        
        # Check if collection exists
        collections = await asyncio.to_thread(client.get_collections)
        collection_exists = collection_name in [c.name for c in collections.collections]
        
        if not collection_exists:
            return {
                "collection_exists": False,
                "vectors_count": 0,
                "status": "missing"
            }
        
        # Get collection info
        collection_info = await asyncio.to_thread(
            client.get_collection,
            collection_name=collection_name
        )
        
        return {
            "collection_exists": True,
            "vectors_count": collection_info.points_count,
            "status": "healthy",
            "collection_name": collection_name
        }
        
    except Exception as e:
        logger.error(f"Error checking collection health: {str(e)}")
        return {
            "collection_exists": False,
            "vectors_count": 0,
            "status": "error",
            "error": str(e)
        }
