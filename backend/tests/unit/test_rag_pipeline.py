import pytest
import numpy as np
from modules.rag_pipeline import TextChunker, VectorStore

class TestTextChunker:
    def test_chunk_text_basic(self):
        chunker = TextChunker(chunk_size=10, overlap=2)
        text = "abcdefghij12345"
        chunks = chunker.chunk_text(text)
        assert len(chunks) > 1
        assert all('text' in c for c in chunks)
        assert chunks[0]['text'] == 'abcdefghij'
        assert chunks[1]['text'].startswith('ij1')

    def test_chunk_text_empty(self):
        chunker = TextChunker()
        chunks = chunker.chunk_text("")
        assert chunks == []

class TestVectorStore:
    def test_add_and_search(self):
        dim = 4
        store = VectorStore(dimension=dim, index_file=':memory:')
        chunks = [
            {"text": "hello world", "metadata": {"id": 1}},
            {"text": "foo bar", "metadata": {"id": 2}}
        ]
        embeddings = np.array([[1,0,0,0],[0,1,0,0]], dtype=np.float32)
        store.add_chunks(chunks, embeddings, doc_id="doc1")
        query = np.array([[1,0,0,0]], dtype=np.float32)
        results = store.search(query, top_k=1)
        assert len(results) == 1
        assert results[0][0]['text'] == 'hello world'

    def test_remove_document(self):
        dim = 4
        store = VectorStore(dimension=dim, index_file=':memory:')
        chunks = [
            {"text": "to remove", "metadata": {"id": 1}},
        ]
        embeddings = np.array([[1,0,0,0]], dtype=np.float32)
        store.add_chunks(chunks, embeddings, doc_id="doc2")
        store.remove_document("doc2")
        assert all(c['metadata'].get('id') != 1 for c in store.chunks)
