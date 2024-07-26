from flask import Blueprint, request, render_template, jsonify
from flask_socketio import emit
from .utils import clone_repo, preprocess_code, compute_similarity, analyze_code
from . import socketio
import logging

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/analyze', methods=['POST'])
def analyze():
    try:
        repo_url = request.form['repo_url']
        tag = request.form['tag']
        socketio.start_background_task(target=analyze_repo, repo_url=repo_url, tag=tag)
        return render_template('progress.html')
    except Exception as e:
        logging.error("Error during analysis: %s", e)
        return render_template('index.html', error=str(e))

def analyze_repo(repo_url, tag):
    try:
        files = clone_repo(repo_url, tag)
        preprocessed_files = preprocess_code(files)
        similarity_results, mds_coords = compute_similarity(preprocessed_files)
        socketio.emit('analysis_complete', {'results': similarity_results.to_json(), 'coords': mds_coords.tolist()})
        global last_results
        last_results = similarity_results
    except Exception as e:
        logging.error("Error in background analysis task: %s", e)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@bp.route('/results')
def results():
    global last_results
    return render_template('results.html', results=last_results.to_html())
