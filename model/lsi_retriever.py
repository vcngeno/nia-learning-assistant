"""
LSI-based semantic retrieval for educational content
Uses Gensim for Latent Semantic Indexing
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple
from gensim import corpora, models, similarities
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

logger = logging.getLogger(__name__)

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)

class LSIRetriever:
    """LSI-based document retriever for educational content"""

    def __init__(self, corpus_path: str = "data_sources/sample_corpus.json"):
        self.corpus_path = corpus_path
        self.documents = []
        self.dictionary = None
        self.lsi_model = None
        self.index = None
        self.stop_words = set(stopwords.words('english'))

        self._load_corpus()
        self._build_index()

    def _preprocess(self, text: str) -> List[str]:
        """Tokenize and clean text"""
        tokens = word_tokenize(text.lower())
        return [t for t in tokens if t.isalnum() and t not in self.stop_words]

    def _load_corpus(self):
        """Load educational corpus"""
        try:
            if os.path.exists(self.corpus_path):
                with open(self.corpus_path, 'r') as f:
                    data = json.load(f)
                    self.documents = data.get('documents', [])
            else:
                logger.warning(f"Corpus not found: {self.corpus_path}, using empty corpus")
                self.documents = []
        except Exception as e:
            logger.error(f"Error loading corpus: {e}")
            self.documents = []

    def _build_index(self):
        """Build LSI index from corpus"""
        if not self.documents:
            logger.warning("No documents to index")
            return

        # Preprocess documents
        texts = [self._preprocess(doc['content']) for doc in self.documents]

        # Create dictionary and corpus
        self.dictionary = corpora.Dictionary(texts)
        corpus = [self.dictionary.doc2bow(text) for text in texts]

        # Build LSI model
        self.lsi_model = models.LsiModel(corpus, id2word=self.dictionary, num_topics=100)

        # Build similarity index
        self.index = similarities.MatrixSimilarity(self.lsi_model[corpus])

        logger.info(f"LSI index built with {len(self.documents)} documents")

    def retrieve(self, query: str, top_k: int = 3, grade_level: str = None) -> List[Dict]:
        """Retrieve most relevant documents for query"""
        if not self.lsi_model or not self.index:
            return []

        # Preprocess query
        query_tokens = self._preprocess(query)
        query_bow = self.dictionary.doc2bow(query_tokens)
        query_lsi = self.lsi_model[query_bow]

        # Get similarities
        sims = self.index[query_lsi]

        # Sort and get top results
        top_indices = sorted(enumerate(sims), key=lambda x: x[1], reverse=True)[:top_k * 2]

        # Filter by grade level if specified
        results = []
        for idx, score in top_indices:
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc['relevance_score'] = float(score)

                # Filter by grade level
                if grade_level:
                    doc_grade = doc.get('grade_level', '')
                    if not self._grade_matches(grade_level, doc_grade):
                        continue

                results.append(doc)

                if len(results) >= top_k:
                    break

        return results

    def _grade_matches(self, student_grade: str, doc_grade: str) -> bool:
        """Check if document grade level matches student grade"""
        grade_hierarchy = {
            'elementary': ['K', '1', '2', '3', '4', '5'],
            'middle': ['6', '7', '8'],
            'high': ['9', '10', '11', '12']
        }

        # Extract grade numbers
        student_num = ''.join(filter(str.isdigit, student_grade))
        doc_level = doc_grade.lower()

        # Check if student's grade falls in document's level
        if doc_level in grade_hierarchy:
            return student_num in grade_hierarchy[doc_level] if student_num else True

        return True
