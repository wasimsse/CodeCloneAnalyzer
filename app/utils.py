import os
import git
import requests
import re
import gensim
import gensim.downloader as api
from gensim import corpora
from sklearn.manifold import MDS
import pandas as pd
import plotly.express as px  # Correct the import here

# Function to fetch files from GitHub
def fetch_file_from_github(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

# Function to preprocess text data
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

# Function to preprocess code
def preprocess_code(files):
    return [preprocess_content(file) for file in files]

# Function to clone a repo
def clone_repo(repo_url, tag):
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    repo_path = os.path.join('data', 'repositories', repo_name)
    
    if os.path.exists(repo_path):
        repo = git.Repo(repo_path)
        repo.git.checkout(tag)
    else:
        repo = git.Repo.clone_from(repo_url, repo_path)
        repo.git.checkout(tag)
    
    files = []
    for root, dirs, filenames in os.walk(repo_path):
        for filename in filenames:
            if filename.endswith('.java'):
                with open(os.path.join(root, filename), 'r', encoding='utf-8') as f:
                    files.append(f.read())
    return files

# Function to compute similarity
def compute_similarity(files_content):
    dictionary = corpora.Dictionary(files_content)
    corpus = [dictionary.doc2bow(text) for text in files_content]
    model = api.load("glove-wiki-gigaword-50")
    
    wmd_results = []
    for i in range(len(files_content)):
        for j in range(i + 1, len(files_content)):
            distance = model.wmdistance(files_content[i], files_content[j])
            wmd_results.append((f'{i} vs {j}', distance))
    
    wmd_df = pd.DataFrame(wmd_results, columns=['Document Pair', 'WMD Distance'])
    
    mds = MDS(n_components=2, dissimilarity="precomputed", random_state=6)
    wmd_distances = [[model.wmdistance(doc1, doc2) for doc2 in files_content] for doc1 in files_content]
    mds_coords = mds.fit_transform(wmd_distances)
    
    return wmd_df, mds_coords

# Function to analyze code
def analyze_code():
    file_urls = [
        'https://raw.githubusercontent.com/multilang-depends/depends/933150b0263ad30b633314eba66a29037ef6e884/src/main/java/depends/extractor/ruby/jruby/JRubyVisitor.java',
        'https://raw.githubusercontent.com/multilang-depends/depends/933150b0263ad30b633314eba66a29037ef6e884/src/main/java/depends/extractor/ruby/jruby/JRubyFileParser.java',
        'https://raw.githubusercontent.com/multilang-depends/depends/933150b0263ad30b633314eba66a29037ef6e884/src/main/java/depends/extractor/python/BasePythonProcessor.java',
        'https://raw.githubusercontent.com/multilang-depends/depends/933150b0263ad30b633314eba66a29037ef6e884/src/main/java/depends/extractor/cpp/CppProcessor.java'
    ]
    
    files_content = [preprocess_content(fetch_file_from_github(url)) for url in file_urls]
    wmd_df, mds_coords = compute_similarity(files_content)
    
    fig = px.scatter(x=mds_coords[:, 0], y=mds_coords[:, 1])
    fig.update_traces(marker=dict(size=12, line=dict(width=2, color='DarkSlateGrey')),
                      selector=dict(mode='markers+text'))
    fig.show()

    return wmd_df
