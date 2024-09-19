from datasets import load_dataset
from transformers import BartTokenizer, BartForConditionalGeneration, T5Tokenizer, T5ForConditionalGeneration
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.tokenize import sent_tokenize
from rouge_score import rouge_scorer
import time
import psutil
import os
import matplotlib.pyplot as plt
import pandas as pd

# Load CNN/DailyMail dataset (first 100 for testing, but we'll only use 10)
dataset = load_dataset('cnn_dailymail', '3.0.0', split='test[:100]')
articles = dataset['article'][:10]  # Limit to first 10 articles
reference_summaries = dataset['highlights'][:15]

# Load BART model and tokenizer
bart_tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
bart_model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")

def bart_summarize(text):
    inputs = bart_tokenizer(text, max_length=1024, return_tensors="pt", truncation=True)
    summary_ids = bart_model.generate(inputs["input_ids"], max_length=150, min_length=40, length_penalty=2.0, num_beams=4, early_stopping=True)
    return bart_tokenizer.decode(summary_ids[0], skip_special_tokens=True)

# Load T5 model and tokenizer
t5_tokenizer = T5Tokenizer.from_pretrained("t5-base")
t5_model = T5ForConditionalGeneration.from_pretrained("t5-base")

def t5_summarize(text):
    inputs = t5_tokenizer.encode("summarize: " + text, return_tensors="pt", max_length=1024, truncation=True)
    summary_ids = t5_model.generate(inputs, max_length=150, min_length=40, length_penalty=2.0, num_beams=4, early_stopping=True)
    return t5_tokenizer.decode(summary_ids[0], skip_special_tokens=True)

def tfidf_summarize(text, num_sentences=5):
    sentences = sent_tokenize(text)
    if len(sentences) <= num_sentences:
        return text
    
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(sentences)
    
    sentence_scores = X.sum(axis=1).flatten()
    ranked_sentences = [(score, sentence) for sentence, score in zip(sentences, sentence_scores)]
    ranked_sentences.sort(reverse=True, key=lambda x: x[0])
    
    summary = ' '.join([sentence for _, sentence in ranked_sentences[:num_sentences]])
    return summary

def calculate_rouge(prediction, reference):
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = scorer.score(reference, prediction)
    return scores

def measure_performance(model_fn, text):
    start_time = time.time()
    generated_summary = model_fn(text)
    exec_time = time.time() - start_time

    process = psutil.Process(os.getpid())
    mem_usage = process.memory_info().rss / 1024 / 1024  # Convert to MB

    return generated_summary, exec_time, mem_usage

# Performance evaluation (only 10 articles)
results = {"model": [], "rouge1": [], "rouge2": [], "rougeL": [], "exec_time": [], "mem_usage": [], "summary_length": []}

for i, article in enumerate(articles):
    reference_summary = reference_summaries[i]
    print(f"Processing article {i + 1} of 10")

    # Evaluate BART
    bart_summary, bart_time, bart_mem = measure_performance(bart_summarize, article)
    bart_rouge = calculate_rouge(bart_summary, reference_summary)
    results["model"].append("BART")
    results["rouge1"].append(bart_rouge['rouge1'].fmeasure)
    results["rouge2"].append(bart_rouge['rouge2'].fmeasure)
    results["rougeL"].append(bart_rouge['rougeL'].fmeasure)
    results["exec_time"].append(bart_time)
    results["mem_usage"].append(bart_mem)
    results["summary_length"].append(len(bart_summary.split()))

    # Evaluate T5
    t5_summary, t5_time, t5_mem = measure_performance(t5_summarize, article)
    t5_rouge = calculate_rouge(t5_summary, reference_summary)
    results["model"].append("T5")
    results["rouge1"].append(t5_rouge['rouge1'].fmeasure)
    results["rouge2"].append(t5_rouge['rouge2'].fmeasure)
    results["rougeL"].append(t5_rouge['rougeL'].fmeasure)
    results["exec_time"].append(t5_time)
    results["mem_usage"].append(t5_mem)
    results["summary_length"].append(len(t5_summary.split()))

    # Evaluate TF-IDF
    tfidf_summary, tfidf_time, tfidf_mem = measure_performance(lambda x: tfidf_summarize(x, num_sentences=5), article)
    tfidf_rouge = calculate_rouge(tfidf_summary, reference_summary)
    results["model"].append("TF-IDF")
    results["rouge1"].append(tfidf_rouge['rouge1'].fmeasure)
    results["rouge2"].append(tfidf_rouge['rouge2'].fmeasure)
    results["rougeL"].append(tfidf_rouge['rougeL'].fmeasure)
    results["exec_time"].append(tfidf_time)
    results["mem_usage"].append(tfidf_mem)
    results["summary_length"].append(len(tfidf_summary.split()))

# Convert results to DataFrame
df_results = pd.DataFrame(results)
print(df_results)
df_results.to_csv('result.csv')
# Plot performance metrics
df_results.groupby("model")[["rouge1", "rouge2", "rougeL"]].mean().plot(kind="bar", title="ROUGE Scores")
df_results.groupby("model")[["exec_time", "mem_usage"]].mean().plot(kind="bar", title="Execution Time & Memory Usage")
df_results.groupby("model")[["summary_length"]].mean().plot(kind="bar", title="Summary Length")
plt.show()
