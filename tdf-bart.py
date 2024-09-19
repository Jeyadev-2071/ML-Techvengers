import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from transformers import BartTokenizer, BartForConditionalGeneration
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.tokenize import sent_tokenize
import nltk

# Download necessary NLTK data
#nltk.download('punkt_tab',download_dir='/root/nltk_data')

# Load the BART model and tokenizer
@st.cache_resource
def load_bart_model():
    
    tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
    model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")
    return tokenizer, model

tokenizer, model = load_bart_model()

def fetch_text_from_url(url):
    """
    Fetches text from a given URL.

    Args:
        url (str): URL of the webpage to scrape.

    Returns:
        str: Raw text extracted from the webpage.
    """
    response = requests.get(url)
    article = response.text
    soup = BeautifulSoup(article, 'lxml')
    paragraphs = soup.find_all('p')
    return " ".join([p.text for p in paragraphs])

def clean_text(text):
    """
    Cleans the input text by removing references, extra spaces, and non-alphabet characters.

    Args:
        text (str): The raw text to be cleaned.

    Returns:
        str: Cleaned text.
    """
    text = re.sub(r'\[[0-9]*\]', '', text)  # Remove reference numbers
    text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
    text = re.sub('[^a-zA-Z\s]', ' ', text)  # Keep only alphabets and spaces
    return text

# TF-IDF Based Extractive Summarization
def extract_sentences_with_keywords(text, keywords):
    """
    Extracts sentences that contain specific keywords.

    Args:
        text (str): The text to search for keywords.
        keywords (set): A set of keywords to look for in the text.

    Returns:
        list: A list of sentences that contain the keywords.
    """
    sentences = sent_tokenize(text)
    keyword_sentences = [sentence for sentence in sentences if any(keyword.lower() in sentence.lower() for keyword in keywords)]
    return keyword_sentences

def extractive_summary_with_keywords(text, keywords, num_sentences=7):
    """
    Generates an extractive summary from the given text using TF-IDF and keyword boosting.

    Args:
        text (str): The text to summarize.
        keywords (set): A set of keywords to prioritize in the summary.
        num_sentences (int): Number of sentences to include in the summary.

    Returns:
        str: Extractive summary focusing on keywords.
    """
    # Clean and tokenize sentences
    cleaned_text = clean_text(text)
    sentences = sent_tokenize(text)
    
    # Generate TF-IDF matrix for sentences
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(sentences)

    # Calculate sentence scores based on TF-IDF
    sentence_scores = tfidf_matrix.sum(axis=1).flatten().tolist()[0]
    
    # Boost scores for sentences containing keywords
    keyword_sentences = extract_sentences_with_keywords(text, keywords)
    for i, sentence in enumerate(sentences):
        if sentence in keyword_sentences:
            sentence_scores[i] *= 1.5  # Boost score by 50% if the sentence contains a keyword

    # Get top N sentences for the summary
    ranked_sentences = sorted(((sentence_scores[i], s) for i, s in enumerate(sentences)), reverse=True)
    summary = ' '.join([ranked_sentences[i][1] for i in range(min(num_sentences, len(ranked_sentences)))])

    return summary

# BART Abstractive Summarization
def divide_into_chunks(text, max_length=1024):
    """
    Divides a long text into smaller chunks for processing by BART.

    Args:
        text (str): The raw text to divide.
        max_length (int): Maximum number of tokens per chunk.
    
    Returns:
        list: List of tokenized chunks.
    """
    # Tokenize the text
    tokenized_text = tokenizer.encode(text, return_tensors='pt', truncation=True)
    
    # Split the tokenized text into chunks of max_length
    chunks = [tokenized_text[:, i:i+max_length] for i in range(0, tokenized_text.size(1), max_length)]
    
    return chunks

def summarize_chunk(chunk, max_length=1024, min_length=50):
    """
    Summarizes a tokenized chunk using BART.
    
    Args:
        chunk (tensor): A tokenized chunk of text.
        max_length (int): Maximum length of the summary.
        min_length (int): Minimum length of the summary.
    
    Returns:
        str: The summarized chunk as text.
    """
    summary_ids = model.generate(
        chunk,
        max_length=max_length,
        min_length=min_length,
        length_penalty=2.0,
        num_beams=4,
        early_stopping=True,
        pad_token_id=tokenizer.eos_token_id
    )
    
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

def summarize_text_with_bart(text):
    """
    Summarizes long text by splitting it into chunks and generating summaries for each using BART.

    Args:
        text (str): The raw text to summarize.

    Returns:
        str: Final summary after processing all chunks.
    """
    chunks = divide_into_chunks(text, max_length=1024)
    summaries = [summarize_chunk(chunk) for chunk in chunks]
    return ' '.join(summaries)

# Streamlit Frontend
st.title("Policy Summarizer & Keyword Extractor")

# Create two tabs for URL and text input
tab1, tab2 = st.tabs(["Summarize from URL", "Summarize from Copy-Pasted Text"])

# Predefined keywords for extractive summary
keywords = {'interest', 'ROI', 'principal', 'policy', 'insurance'}

with tab1:
    # Input fields for URL
    url = st.text_input("Enter the policy URL:")
    num_sentences_url = st.number_input("Number of sentences for the summary (URL):", min_value=1, max_value=100, value=7)
    method_url = st.selectbox("Choose summarization method (URL):", ("TF-IDF Extractive", "BART Abstractive"))

    if st.button("Summarize from URL"):
        if url:
            raw_text = fetch_text_from_url(url)
            
            if method_url == "TF-IDF Extractive":
                summary = extractive_summary_with_keywords(raw_text, keywords, num_sentences=num_sentences_url)
            else:
                summary = summarize_text_with_bart(raw_text)
                
            st.subheader(f"Summary from URL ({method_url}):")
            st.write(summary)
        else:
            st.write("Please provide a valid URL.")

with tab2:
    # Input fields for copy-pasted text
    text_input = st.text_area("Paste your policy text here:")
    num_sentences_text = st.number_input("Number of sentences for the summary (Text):", min_value=1, max_value=100, value=7, key='text_summary')
    method_text = st.selectbox("Choose summarization method (Text):", ("TF-IDF Extractive", "BART Abstractive"), key='method_text')

    if st.button("Summarize from Text"):
        if text_input:
            if method_text == "TF-IDF Extractive":
                summary = extractive_summary_with_keywords(text_input, keywords, num_sentences=num_sentences_text)
            else:
                summary = summarize_text_with_bart(text_input)
                
            st.subheader(f"Summary from Text ({method_text}):")
            st.write(summary)
        else:
            st.write("Please paste some text for summarization.")
