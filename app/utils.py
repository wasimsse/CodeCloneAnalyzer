import requests
import re
import gensim
import gensim.downloader as api
from gensim import corpora
from sklearn.manifold import MDS
import numpy as np
import pandas as pd
import json
import os
import fasttext

# Fetch files from GitHub
def fetch_file_from_github(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

# Preprocess text data, excluding programming keywords
def preprocess_content(content):
    programming_keywords = {
        'import', 'class', 'def', 'return', 'public', 'private', 'protected',
        'package', 'static', 'void', 'new', 'extends', 'implements', 'int',
        'float', 'double', 'char', 'boolean', 'if', 'else', 'switch', 'case',
        'default', 'while', 'for', 'do', 'break', 'continue', 'goto', 'const',
        'enum', 'struct', 'typedef', 'union', 'this', 'super', 'throw', 'throws',
        'try', 'catch', 'finally', 'abstract', 'synchronized', 'volatile', 'transient',
        'final', 'native', 'strictfp', 'interface', 'lambda', 'module', 'requires',
        'exports', 'instanceof', 'async', 'await', 'var', 'let', 'const',
        'function', 'yield', 'null', 'true', 'false', 'undefined', 'delete',
        'typeof', 'void', 'new', 'in', 'of', 'from', 'export', 'import', 'as',
        'with', 'yield', 'assert', 'pass', 'global', 'nonlocal', 'del', 'exec',
        'print', 'lambda', 'raise', 'yield', 'except', 'finally', 'try',
        'java', 'python', 'c++', 'ruby', 'javascript', 'typescript', 'scala',
        'kotlin', 'swift', 'go', 'rust', 'php', 'perl', 'bash', 'shell','string'
    }

    return [token.lower() for token in re.split(r'\W+', content) if (len(token) > 2 and token.lower() not in programming_keywords)]

# Perform analysis
def analyze_code(file_urls):
    # Extract file names from URLs
    sheet_names = [url.split('/')[-1].replace('.java', '') for url in file_urls]
    
    # Fetch and preprocess the text documents
    files_content = [preprocess_content(fetch_file_from_github(url)) for url in file_urls]

    # Create a dictionary and corpus for LDA analysis
    dictionary = corpora.Dictionary(files_content) 
    corpus = [dictionary.doc2bow(text) for text in files_content]

    # Load a pretrained word embedding model from gensim
    model = api.load("glove-wiki-gigaword-50")

    # Calculate Word Mover's Distance between each pair of documents and label them with sheet names
    wmd_results = []
    for i in range(len(files_content)):
        for j in range(i + 1, len(files_content)):
            distance = model.wmdistance(files_content[i], files_content[j])
            wmd_results.append((f'{sheet_names[i]} vs {sheet_names[j]}', distance))

    # Generate a scatter plot using Multidimensional Scaling (MDS)
    mds = MDS(n_components=2, dissimilarity="precomputed", random_state=6)
    wmd_distances = [[model.wmdistance(doc1, doc2) for doc2 in files_content] for doc1 in files_content]
    mds_coords = mds.fit_transform(wmd_distances)
    fig = px.scatter(x=mds_coords[:, 0], y=mds_coords[:, 1], text=sheet_names)
    fig.update_traces(marker=dict(size=12, line=dict(width=2, color='DarkSlateGrey')),
                      selector=dict(mode='markers+text'))
    return wmd_results, fig
