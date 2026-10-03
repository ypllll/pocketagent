"""文档切块，把长文本切成小块，这是RAG流程的第二步"""

def chunk_text(text:str,source:str,chunk_size:int=400,chunk_overlap:int=50)->list[dict]:
    chunks=[]
    start=0
    index=0
    if not text:
        return []
    if chunk_overlap>=chunk_size:
        raise ValueError("chunk_overlap必须小于chunk_size")
    if len(text)<=chunk_size:
        chunks.append({"text":text,"source":source,"index":index})
        return chunks
    while start<len(text):
        end=start+chunk_size
        chunk=text[start:end]
        chunks.append({"text":chunk,"source":source,"index":index})
        index+=1
        start+=chunk_size-chunk_overlap
    return chunks