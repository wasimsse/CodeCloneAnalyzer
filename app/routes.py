from flask import Blueprint, request, render_template, jsonify, redirect, url_for
from flask_socketio import emit
from .utils import clone_repo, preprocess_code, compute_similarity
from . import socketio

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/analyze', methods=['POST'])
def analyze():
    repo_url = request.form['repo_url']
    tag = request.form['tag']
    socketio.start_background_task(target=analyze_repo, repo_url=repo_url, tag=tag)
    return render_template('progress.html')

def analyze_repo(repo_url, tag):
    files = clone_repo(repo_url, tag)
    preprocessed_files = preprocess_code(files)
    similarity_results = compute_similarity(preprocessed_files)
    socketio.emit('analysis_complete', similarity_results)
    global last_results
    last_results = similarity_results

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@bp.route('/results')
def results():
    global last_results
    return render_template('results.html', results=last_results)
