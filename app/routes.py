from flask import Blueprint, render_template, request, jsonify
from flask import current_app as app
from flask_socketio import emit
from app.utils import fetch_github_releases, analyze_code, fetch_file_from_github, preprocess_content, compute_similarity

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/get_releases', methods=['POST'])
def get_releases():
    repo_url = request.form['repo_url']
    repo_name = repo_url.split('github.com/')[1].replace('.git', '')
    try:
        releases = fetch_github_releases(repo_name)
        return jsonify(releases)
    except Exception as e:
        return render_template('error.html', error=str(e))

@bp.route('/analyze', methods=['POST'])
def analyze():
    repo_url = request.form['repo_url']
    tag = request.form['tag']
    try:
        result = analyze_code(repo_url, tag)
        return render_template('results.html', result=result)
    except Exception as e:
        return render_template('error.html', error=str(e))

@bp.route('/compare', methods=['POST'])
def compare():
    ref_file_url = request.form['reference_url']
    comp_file_urls = request.form['comparison_urls'].split(',')
    try:
        reference_content = preprocess_content(fetch_file_from_github(ref_file_url))
        comparison_contents = [preprocess_content(fetch_file_from_github(url.strip())) for url in comp_file_urls]

        all_contents = [reference_content] + comparison_contents
        wmd_df, mds_coords = compute_similarity(all_contents)

        return render_template('comparison_results.html', wmd_df=wmd_df.to_dict(orient='records'), mds_coords=mds_coords.tolist())
    except Exception as e:
        return render_template('error.html', error=str(e))
