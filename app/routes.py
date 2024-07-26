from flask import Blueprint, request, render_template, jsonify
from flask_socketio import emit
from .utils import clone_repo, preprocess_code, compute_similarity
from . import socketio
import logging

bp = Blueprint('main', __name__)
last_results = {}
preprocessed_data = {}

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
        emit_progress("Cloning repository...", 10)
        files = clone_repo(repo_url, tag)
        
        emit_progress("Preprocessing code...", 30)
        preprocessed_files = preprocess_code(files)
        
        emit_progress("Computing similarities...", 70)
        similarity_results = compute_similarity(preprocessed_files)
        
        emit_progress("Analysis complete.", 100)
        global last_results
        last_results = similarity_results
        global preprocessed_data
        preprocessed_data = preprocessed_files
        socketio.emit('analysis_complete', {'status': 'complete'})
    except Exception as e:
        logging.error("Error in background analysis task: %s", e)
        emit_progress(f"Error: {str(e)}", 100)

def emit_progress(message, percentage):
    socketio.emit('progress_update', {'message': message, 'percentage': percentage})

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@bp.route('/results')
def results():
    global last_results
    return render_template('results.html', results=last_results)

@bp.route('/view_preprocessed')
def view_preprocessed():
    global preprocessed_data
    return render_template('preprocessed.html', preprocessed_data=preprocessed_data)
