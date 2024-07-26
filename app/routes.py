from flask import Blueprint, request, render_template, jsonify
from flask_socketio import emit
from .utils import clone_repo, preprocess_code, compute_similarity, analyze_code
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
        file_urls = [
            f'{repo_url}/blob/{tag}/src/main/java/depends/extractor/ruby/jruby/JRubyVisitor.java',
            f'{repo_url}/blob/{tag}/src/main/java/depends/extractor/ruby/jruby/JRubyFileParser.java',
            f'{repo_url}/blob/{tag}/src/main/java/depends/extractor/python/BasePythonProcessor.java',
            f'{repo_url}/blob/{tag}/src/main/java/depends/extractor/cpp/CppProcessor.java'
        ]
        socketio.start_background_task(target=analyze_repo, file_urls=file_urls)
        return render_template('progress.html')
    except Exception as e:
        logging.error("Error during analysis: %s", e)
        return render_template('index.html', error=str(e))

def analyze_repo(file_urls):
    try:
        emit_progress("Analyzing code...", 50)
        wmd_results, fig = analyze_code(file_urls)
        
        emit_progress("Analysis complete.", 100)
        global last_results
        last_results = wmd_results
        fig.write_html("static/plot.html")
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

@bp.route('/view_plot')
def view_plot():
    return render_template('plot.html')

@bp.route('/view_preprocessed')
def view_preprocessed():
    global preprocessed_data
    return render_template('preprocessed.html', preprocessed_data=preprocessed_data)
