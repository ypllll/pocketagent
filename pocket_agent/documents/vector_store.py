"""现在到了RAG工作流的第四步，就是把第三步embedding好的向量存到向量数据库里面"""
import chromadb
from pocket_agent.documents.embedder import Embedder

class Vector_store:
    def __init__(self,persist_dir:str,collection_name:str,embedder:Embedder):
        self.embedder=embedder
        self.client=chromadb.PersistentClient(path=persist_dir)
        self.collection=self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space":"cosine"}
        )

    def add_chunks(self,chunks:list[dict])->int:
        if not chunks:
            return 0
        count=0
        texts=[chunk["text"] for chunk in chunks]
        vectors=self.embedder.embed(texts)
        ids=[f"{chunk['source']}:{chunk['index']}" for chunk in chunks]
        metadatas=[
            {
                "source":chunk["source"],
                "index":chunk["index"],
                "embedding_model":self.embedder.name
            }
            for chunk in chunks
        ]
        self.collection.add(
            ids=ids,
            embeddings=vectors,
            metadatas=metadatas,
            documens=texts
        )
        return len(chunks) 

    def search(self,query:str,top_k:int=10)->list[dict]:
        if not query:
            return []
        query_vector=self.embedder.embed([query])
        res=self.collection.query(
            query_embeddings=query_vector,
            n_results=top_k
        )
        results=[]
        for i in range(len(res["ids"][0])):
            meta=res["metadatas"][0][i]
            results.append(
                {
                    "text":res["documents"][0][i],
                    "source":meta.get("source"),
                    "index":meta.get("index"),
                    "distance":res["distances"][0][i]
                }
            )
        return results

    def count(self)->int:
        return self.collection.count()