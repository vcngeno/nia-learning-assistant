import gensim
from gensim import corpora
from gensim.models import LsiModel
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import re

class NiaSummarizer:
    """Educational content summarizer using LSI"""
    
    def __init__(self):
        try:
            self.stop_words = set(stopwords.words('english'))
        except:
            nltk.download('stopwords')
            self.stop_words = set(stopwords.words('english'))
        self.lsi_model = None
        self.dictionary = None
        
    def preprocess_text(self, text: str) -> list:
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = text.lower()
        tokens = word_tokenize(text)
        tokens = [
            word for word in tokens 
            if word not in self.stop_words and len(word) > 2
        ]
        return tokens
    
    def create_lsi_model(self, documents: list, num_topics: int = 5):
        processed_docs = [self.preprocess_text(doc) for doc in documents]
        self.dictionary = corpora.Dictionary(processed_docs)
        corpus = [self.dictionary.doc2bow(doc) for doc in processed_docs]
        self.lsi_model = LsiModel(
            corpus=corpus,
            id2word=self.dictionary,
            num_topics=num_topics
        )
        return self.lsi_model
    
    def extract_key_sentences(self, text: str, num_sentences: int = 3) -> list:
        sentences = sent_tokenize(text)
        
        if len(sentences) <= num_sentences:
            return sentences
        
        if not self.lsi_model or not self.dictionary:
            return sentences[:num_sentences]
        
        processed_sentences = [self.preprocess_text(sent) for sent in sentences]
        bow_sentences = [self.dictionary.doc2bow(sent) for sent in processed_sentences]
        lsi_sentences = [self.lsi_model[bow] for bow in bow_sentences]
        
        sentence_scores = []
        for idx, lsi_rep in enumerate(lsi_sentences):
            score = sum(abs(weight) for _, weight in lsi_rep)
            sentence_scores.append((idx, score, sentences[idx]))
        
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        top_sentences = sentence_scores[:num_sentences]
        top_sentences.sort(key=lambda x: x[0])
        
        return [sent[2] for sent in top_sentences]
    
    def summarize_for_age(self, text: str, age: int, grade: int) -> dict:
        if grade <= 3:
            num_sentences = 2
            max_words_per_sentence = 15
        elif grade <= 5:
            num_sentences = 3
            max_words_per_sentence = 20
        elif grade <= 8:
            num_sentences = 4
            max_words_per_sentence = 25
        else:
            num_sentences = 5
            max_words_per_sentence = 30
        
        key_sentences = self.extract_key_sentences(text, num_sentences)
        
        simplified_sentences = []
        for sentence in key_sentences:
            words = sentence.split()
            if len(words) > max_words_per_sentence:
                sentence = ' '.join(words[:max_words_per_sentence]) + '...'
            simplified_sentences.append(sentence)
        
        summary = ' '.join(simplified_sentences)
        
        return {
            'summary': summary,
            'original_length': len(text.split()),
            'summary_length': len(summary.split()),
            'compression_ratio': len(summary.split()) / len(text.split()) if len(text.split()) > 0 else 0,
            'grade_level': grade,
            'num_sentences': len(simplified_sentences)
        }
    
    def simplify_vocabulary(self, text: str, target_grade: int) -> str:
        replacements = {
            'utilize': 'use',
            'demonstrate': 'show',
            'comprehend': 'understand',
            'acquire': 'get',
            'attempt': 'try',
            'sufficient': 'enough',
            'commence': 'start',
            'terminate': 'end',
        }
        
        if target_grade <= 5:
            words = text.split()
            simplified_words = [
                replacements.get(word.lower(), word) for word in words
            ]
            return ' '.join(simplified_words)
        
        return text

nia_summarizer = NiaSummarizer()

sample_corpus = [
    "Photosynthesis is how plants make food using sunlight, water, and carbon dioxide.",
    "The water cycle describes how water moves between the earth and atmosphere.",
    "Cells are the basic building blocks of all living things.",
]

try:
    nia_summarizer.create_lsi_model(sample_corpus)
except:
    pass
