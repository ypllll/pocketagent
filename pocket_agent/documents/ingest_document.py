from pocket_agent.documents.loaders import load_document
from pocket_agent.documents.chunker import chunk_text
from pocket_agent.documents.vector_store import Vector_store
from pathlib import Path

def ingest_document(path,store:Vector_store)->int:
    text=load_document(path)
    chunks=chunk_text(text,Path(path).name)
    return store.add_chunks(chunks)
