"""Flask application for novel crawler"""
import os
import logging
import json
from flask import Flask, render_template, jsonify, request, send_file, make_response
from werkzeug.exceptions import HTTPException
import config
from services.search_service import search_novel
from services.download_service import download_novel, get_download_status, get_download_history, pause_download, resume_download, stop_download
from services.health_service import check_sources_health
from services.metrics_service import metrics_store

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True


@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')


@app.route('/api/search', methods=['GET'])
def api_search():
    """
    Search API endpoint

    Query params:
        keyword: Search keyword

    Returns:
        JSON response with search results
    """
    try:
        keyword = request.args.get('keyword', '').strip()

        if not keyword:
            return jsonify({
                'success': False,
                'error': 'Please enter a novel name'
            }), 400

        source_id = request.args.get('source_id', '').strip() or None
        limit = int(request.args.get('limit', 30))
        only_available = request.args.get('only_available', '0').strip().lower() in {'1', 'true', 'yes'}

        logger.info(
            f"Search request: {keyword} (source={source_id or 'all'}, limit={limit}, only_available={only_available})"
        )
        result = search_novel(
            keyword,
            source_id=source_id,
            limit=limit,
            only_available=only_available,
        )

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404

    except Exception as e:
        logger.error(f"Search API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/download', methods=['POST'])
def api_download():
    """
    Download API endpoint

    JSON body:
        novel_url: URL of the novel
        start_chapter: Starting chapter number (optional, default 1)
        end_chapter: Ending chapter number (optional, default all)
        source_id: Preferred source identifier (optional)

    Returns:
        JSON response with task ID
    """
    try:
        data = request.get_json()

        if not data or 'novel_url' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing novel_url parameter'
            }), 400

        novel_url = data['novel_url']
        start_chapter = int(data.get('start_chapter', 1))
        end_chapter = data.get('end_chapter')
        source_id = data.get('source_id')
        if end_chapter:
            end_chapter = int(end_chapter)

        logger.info(
            f"Download request: {novel_url} (source={source_id or 'auto'}, chapters: {start_chapter}-{end_chapter or 'all'})"
        )

        task_id = download_novel(novel_url, start_chapter, end_chapter, source_id)

        return jsonify({
            'success': True,
            'task_id': task_id
        })

    except ValueError as e:
        logger.error(f"Download API error (invalid parameter): {e}")
        return jsonify({
            'success': False,
            'error': f'Invalid parameter: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Download API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/pause/<task_id>', methods=['POST'])
def api_pause():
    """
    Pause download API endpoint

    Path params:
        task_id: Download task ID

    Returns:
        JSON response
    """
    try:
        pause_download(task_id)
        return jsonify({
            'success': True,
            'message': 'Download paused'
        })
    except Exception as e:
        logger.error(f"Pause API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/resume/<task_id>', methods=['POST'])
def api_resume():
    """
    Resume download API endpoint

    Path params:
        task_id: Download task ID

    Returns:
        JSON response
    """
    try:
        resume_download(task_id)
        return jsonify({
            'success': True,
            'message': 'Download resumed'
        })
    except Exception as e:
        logger.error(f"Resume API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/stop/<task_id>', methods=['POST'])
def api_stop():
    """
    Stop download API endpoint

    Path params:
        task_id: Download task ID

    Returns:
        JSON response
    """
    try:
        stop_download(task_id)
        return jsonify({
            'success': True,
            'message': 'Download stopped'
        })
    except Exception as e:
        logger.error(f"Stop API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/status/<task_id>', methods=['GET'])
def api_status(task_id):
    """
    Download status API endpoint

    Path params:
        task_id: Download task ID

    Returns:
        JSON response with download status
    """
    try:
        status = get_download_status(task_id)

        if not status:
            return jsonify({
                'success': False,
                'error': 'Task not found'
            }), 404

        return jsonify({
            'success': True,
            'status': status
        })

    except Exception as e:
        logger.error(f"Status API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/history', methods=['GET'])
def api_history():
    """
    Download history API endpoint

    Returns:
        JSON response with download history
    """
    try:
        history = get_download_history()
        return jsonify(history)

    except Exception as e:
        logger.error(f"History API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/sources', methods=['GET'])
def api_sources():
    """List configured source metadata for frontend filtering and diagnostics."""
    try:
        sources = []
        for source_id, source_cfg in config.SOURCES.items():
            sources.append({
                'source_id': source_id,
                'source_name': source_cfg.get('display_name', source_id),
                'enabled': bool(source_cfg.get('enabled', True)),
                'weight': int(source_cfg.get('weight', 0)),
            })

        return jsonify({
            'success': True,
            'sources': sorted(sources, key=lambda item: item.get('weight', 0), reverse=True)
        })
    except Exception as e:
        logger.error(f"Sources API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/health/sources', methods=['GET'])
def api_source_health():
    """Run source-level health checks."""
    try:
        keyword = request.args.get('keyword', '武动').strip() or '武动'
        result = check_sources_health(keyword)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Source health API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/metrics', methods=['GET'])
def api_metrics():
    """Expose in-memory metrics for observability."""
    try:
        return jsonify({
            'success': True,
            'metrics': metrics_store.snapshot(),
        })
    except Exception as e:
        logger.error(f"Metrics API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/api/download/<filename>', methods=['GET'])
def api_file_download(filename):
    """
    File download API endpoint

    Path params:
        filename: Name of the file to download

    Returns:
        File for download
    """
    try:
        # Security: only allow files from downloads directory
        safe_filename = os.path.basename(filename)
        filepath = os.path.join(config.DOWNLOAD_DIR, safe_filename)

        if not os.path.exists(filepath) or not os.path.isfile(filepath):
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404

        return send_file(
            filepath,
            as_attachment=True,
            download_name=safe_filename,
            mimetype='text/plain'
        )

    except Exception as e:
        logger.error(f"File download API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Handle HTTP exceptions"""
    response = {
        'success': False,
        'error': e.description,
        'status_code': e.code
    }
    return jsonify(response), e.code


@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {e}")
    response = {
        'success': False,
        'error': 'Internal server error'
    }
    return jsonify(response), 500


def create_app():
    """Application factory function"""
    return app


if __name__ == '__main__':
    logger.info(f"Starting novel crawler application on {config.FLASK_HOST}:{config.FL_PORT}")
    logger.info(f"Download directory: {config.DOWNLOAD_DIR}")
    logger.info(f"Log file: {config.LOG_FILE}")

    app.run(
        host=config.FLASK_HOST,
        port=config.FL_PORT,
        debug=config.FLASK_DEBUG
    )
