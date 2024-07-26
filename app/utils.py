import os
import json
from git import Repo
import fasttext
import numpy as np
import scipy.spatial
import glob

def clone_repo(repo_url, tag):
    dir_name = f'repo_{tag}'
    if not os.path.exists(dir_name):
        repo = Repo.clone_from(repo_url, dir_name)
        repo.git.checkout(tag)
    return dir_name

def preprocess_code(directory):
    cache_file = os.path.join(directory, 'preprocessed.json')
    
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            file_contents = json.load(f)
        return file_contents

    file_contents = {}
    for extension in ["*.java", "*.py", "*.cpp", "*.h"]:
        for file_path in glob.glob(f"{directory}/**/{extension}", recursive=True):
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                file_contents[file_path] = content

    with open(cache_file, 'w') as f:
        json.dump(file_contents, f)
    
    return file_contents

def compute_similarity(files):
    model_path = 'models/cc.en.300.bin'
    model = fasttext.load_model(model_path)
    
    def get_embedding(text):
        words = text.split()
        word_embeddings = [model[word] for word in words if word in model]
        if word_embeddings:
            return np.mean(word_embeddings, axis=0)
        return np.zeros(model.get_dimension())

    embeddings = {path: get_embedding(content) for path, content in files.items()}
    similarities = {}
    paths = list(embeddings.keys())
    
    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            sim = 1 - scipy.spatial.distance.cosine(embeddings[paths[i]], embeddings[paths[j]])
            similarities[f"{paths[i]} vs {paths[j]}"] = sim
    
    return similarities
