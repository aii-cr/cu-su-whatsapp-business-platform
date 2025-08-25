# NEW CODE
"""
Carga JSONL (text + metadata) a LangChain Documents.
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
import json
from langchain_core.documents import Document
from app.core.logger import logger


def load_jsonl_documents(paths: list[str]) -> List[Document]:
    """Carga JSONL a Document(page_content=text, metadata=metadata)."""
    try:
        logger.info(f"📂 [JSONL] Loading documents from {len(paths)} JSONL files")
        
        docs: List[Document] = []
        
        for file_idx, p in enumerate(paths, 1):
            path = Path(p)
            
            if not path.exists():
                logger.warning(f"⚠️ [JSONL] File {file_idx} not found: {p}")
                continue
                
            logger.info(f"📂 [JSONL] Processing file {file_idx}/{len(paths)}: {path.name}")
            
            file_docs = 0
            with path.open("r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                        
                    try:
                        obj: Dict[str, Any] = json.loads(line)
                        text = obj.get("text", "")
                        meta = obj.get("metadata", {})
                        
                        if text:  # Only add documents with content
                            docs.append(Document(page_content=text, metadata=meta))
                            file_docs += 1
                        else:
                            logger.debug(f"📂 [JSONL] Skipping empty text at line {line_num} in {path.name}")
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ [JSONL] Invalid JSON at line {line_num} in {path.name}: {str(e)}")
                        continue
                        
            logger.info(f"✅ [JSONL] Loaded {file_docs} documents from {path.name}")
            
        total_docs = len(docs)
        logger.info(f"🎉 [JSONL] Total documents loaded: {total_docs}")
        
        return docs
        
    except Exception as e:
        logger.error(f"❌ [JSONL] Failed to load JSONL documents: {str(e)}")
        return []
