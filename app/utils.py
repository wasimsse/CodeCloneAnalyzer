import os
import git
import requests
import re
import gensim
import gensim.downloader as api
from gensim import corpora
from sklearn.manifold import MDS
import pandas as pd
import plotly.express as px
from flask_socketio import emit
import zipfile
import io

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
            if filename.endswith('.java') or filename.endswith('.py') or filename.endswith('.cpp'):
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

# Function to analyze code from URLs
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

# Function to fetch GitHub releases
def fetch_github_releases(repo_name):
    url = f'https://api.github.com/repos/{repo_name}/releases'
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# Function to analyze code from a repo URL and tag
def analyze_code_repo(repo_url, tag):
    zip_url = f'https://codeload.github.com/{repo_url}/zip/refs/tags/{tag}'
    response = requests.get(zip_url)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall('repo')

    repo_dir = f'repo/{tag}'
    file_contents = []

    for root, _, files in os.walk(repo_dir):
        for file in files:
            if file.endswith('.py') or file.endswith('.java') or file.endswith('.cpp'):
                with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                    file_contents.append(f.read())

    model = FastText(sentences=[content.split() for content in file_contents], vector_size=100, window=3, min_count=1, workers=4)
    embeddings = [model.wv[word] for content in file_contents for word in content.split() if word in model.wv]
    mds = MDS(n_components=2, random_state=0)
    coords = mds.fit_transform(embeddings)

    df = pd.DataFrame(coords, columns=['x', 'y'])
    df.to_csv('data/analysis_result.csv', index=False)

    fig = px.scatter(df, x='x', y='y', title='Code Analysis Result')
    fig.write_html('templates/results.html')

    return 'Analysis complete. See results.html for the visualization.'

# Function to compare reference file with comparison files
def compare_files(ref_file_url, comp_file_urls):
    ref_file = requests.get(ref_file_url).text
    comp_files = [requests.get(url).text for url in comp_file_urls]

    ref_words = ref_file.split()
    ref_word_count = len(ref_words)
    ref_word_set = set(ref_words)

    comparison_results = []

    for url, comp_file in zip(comp_file_urls, comp_files):
        comp_words = comp_file.split()
        comp_word_count = len(comp_words)
        common_words = ref_word_set.intersection(comp_words)
        similarity = len(common_words) / ref_word_count

        comparison_results.append({
            "file": url,
            "similarity": similarity,
            "common_words": len(common_words),
            "ref_word_count": ref_word_count,
            "comp_word_count": comp_word_count
        })

    df = pd.DataFrame(comparison_results)
    df.to_csv('data/comparison_results.csv', index=False)

    fig = px.bar(df, x='file', y='similarity', title='File Comparison Results')
    fig.write_html('templates/comparison_results.html')

    return comparison_results
