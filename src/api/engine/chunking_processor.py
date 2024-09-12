import nltk
from nltk.corpus import wordnet

nltk.download('wordnet')

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import openai
openai.api_key = "your_openai_api_key"

def chunk_text(text, max_chunk_size=500):
    words = text.split()
    chunks = []
    current_chunk = []
    current_chunk_size = 0
    for word in words:
        current_chunk.append(word)
        current_chunk_size += len(word) + 1  # +1 for space
        if current_chunk_size >= max_chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_chunk_size = 0
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks

def expand_query_with_synonyms(query):
    """Expands query using synonyms."""
    words = query.split()
    expanded_words = []
    for word in words:
        synonyms = wordnet.synsets(word)
        lemmas = set()
        for syn in synonyms:
            for lemma in syn.lemmas():
                lemmas.add(lemma.name())
        expanded_words.append(f"({word} {' '.join(lemmas)})")
    return ' '.join(expanded_words)

def retrieve_relevant_chunks(query, chunks, top_k=3):
    """
    Retrieve the top K most relevant chunks for the given query using TF-IDF and cosine similarity.
    """
    # Query expansion for better retrieval
    expanded_query = query_expansion(query)
    
    # Combine query and chunks into a corpus
    corpus = [expanded_query] + chunks
    
    # Use TF-IDF vectorizer to convert the text into vectors
    vectorizer = TfidfVectorizer().fit_transform(corpus)
    
    # Compute cosine similarity between the query and document chunks
    similarities = cosine_similarity(vectorizer[0:1], vectorizer[1:]).flatten()
    
    # Get the top K most relevant chunks based on similarity
    top_k_indices = similarities.argsort()[-top_k:][::-1]
    
    relevant_chunks = [chunks[i] for i in top_k_indices]
    return relevant_chunks

def generate_answer(query, relevant_chunks):
    """
    Generate an answer using the retrieved relevant chunks as context for the language model.
    """
    # Combine the relevant chunks into a single context
    context = "\n".join(relevant_chunks)
    
    # Construct the prompt with the question and context
    prompt = f"Context: {context}\n\nQuestion: {query}\nAnswer:"
    
    # Generate the answer using OpenAI's GPT
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150,
        temperature=0.2,  # Lower temperature to reduce hallucinations
    )
    
    # Return the model's answer
    return response.choices[0].text.strip()