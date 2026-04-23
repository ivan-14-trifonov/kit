"""
Kit Runner Web Server
Provides web interface to Kit Runner functionality.
"""

import os
import sys
import json
import time
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_from_directory

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from runner.job import JobStatus, StepStatus
from runner.main import KitRunner

app = Flask(__name__)

# Global runner instance
runner: KitRunner = None
runner_lock = threading.Lock()

# HTML Template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kit Runner Web</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #333; margin-bottom: 20px; }
        h2 { color: #555; margin: 20px 0 10px; }
        
        .card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: 600; color: #555; }
        input[type="text"], input[type="number"], textarea, select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        textarea { min-height: 100px; resize: vertical; }
        
        button {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-right: 10px;
        }
        button:hover { background: #0056b3; }
        button.secondary { background: #6c757d; }
        button.secondary:hover { background: #545b62; }
        button.success { background: #28a745; }
        button.success:hover { background: #1e7e34; }
        
        .status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .status-pending { background: #ffc107; color: #000; }
        .status-running { background: #17a2b8; color: white; }
        .status-completed { background: #28a745; color: white; }
        .status-failed { background: #dc3545; color: white; }
        .status-paused { background: #6c757d; color: white; }
        .status-cancelled { background: #6c757d; color: white; }
        .status-skipped { background: #e9ecef; color: #495057; }
        
        .job-list { list-style: none; }
        .job-item {
            padding: 15px;
            border: 1px solid #eee;
            border-radius: 4px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .job-item:hover { background: #f8f9fa; }
        .job-id { font-family: monospace; color: #007bff; }
        .job-goal { margin: 5px 0; }
        .job-meta { font-size: 12px; color: #888; }
        
        .step {
            border-left: 3px solid #ddd;
            padding-left: 15px;
            margin: 10px 0;
        }
        .step-completed { border-left-color: #28a745; }
        .step-failed { border-left-color: #dc3545; }
        .step-running { border-left-color: #17a2b8; }
        .step-pending { border-left-color: #ffc107; }
        
        .step-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }
        .step-name { font-weight: 600; }
        
        .output-files {
            margin-top: 10px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
            font-family: monospace;
            font-size: 13px;
        }
        .output-files a {
            color: #007bff;
            text-decoration: none;
            margin-right: 10px;
        }
        .output-files a:hover { text-decoration: underline; }
        
        .tools-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
        }
        .tool-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #eee;
        }
        .tool-name { font-weight: 600; color: #007bff; }
        .tool-desc { font-size: 13px; color: #666; margin: 5px 0; }
        .tool-modes { font-size: 12px; color: #888; }
        
        .tabs { display: flex; border-bottom: 2px solid #ddd; margin-bottom: 20px; }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            margin-bottom: -2px;
        }
        .tab.active {
            border-bottom-color: #007bff;
            color: #007bff;
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        .error { background: #f8d7da; color: #721c24; padding: 10px; border-radius: 4px; margin-bottom: 15px; }
        .success { background: #d4edda; color: #155724; padding: 10px; border-radius: 4px; margin-bottom: 15px; }
        
        pre {
            background: #f4f4f4;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 13px;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #888;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Kit Runner Web</h1>
        
        <div class="tabs">
            <div class="tab active" data-tab="new-job">Новая задача</div>
            <div class="tab" data-tab="jobs">Задачи</div>
            <div class="tab" data-tab="tools">Инструменты</div>
        </div>
        
        <!-- New Job Tab -->
        <div id="new-job" class="tab-content active">
            <div class="card">
                <h2>Запуск новой задачи</h2>
                <form id="run-goal-form">
                    <div class="form-group">
                        <label for="goal">Цель (на естественном языке)</label>
                        <textarea id="goal" name="goal" placeholder="Например: Скачать видео с YouTube и конвертировать в MP3" required></textarea>
                    </div>
                    <div class="form-group">
                        <label for="input_params">Входные параметры (JSON, необязательно)</label>
                        <textarea id="input_params" name="input_params" placeholder='{"url": "https://...", "format": "best[height<=1080]"}'></textarea>
                    </div>
                    <div class="form-group">
                        <label for="cookies_file">Cookies файл (для YouTube, необязательно)</label>
                        <input type="file" id="cookies_file" name="cookies_file" accept=".txt">
                        <small style="color: #666; display: block; margin-top: 5px;">
                            Формат: Netscape cookies.txt. Нужно для доступа к возрастным видео.
                            <a href="https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies" target="_blank">Как получить?</a>
                        </small>
                    </div>
                    <button type="submit" class="success">Запустить задачу</button>
                </form>
                <div id="run-result"></div>
            </div>
        </div>
        
        <!-- Jobs Tab -->
        <div id="jobs" class="tab-content">
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h2>Список задач</h2>
                    <button onclick="loadJobs()">Обновить</button>
                </div>
                <ul id="job-list" class="job-list">
                    <li class="loading">Загрузка...</li>
                </ul>
            </div>
            
            <div id="job-detail" class="card" style="display: none;">
                <h2>Детали задачи <span id="detail-job-id"></span></h2>
                <div id="job-detail-content"></div>
            </div>
        </div>
        
        <!-- Tools Tab -->
        <div id="tools" class="tab-content">
            <div class="card">
                <h2>Доступные инструменты</h2>
                <div id="tools-list" class="tools-grid">
                    <div class="loading">Загрузка...</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById(tab.dataset.tab).classList.add('active');
                
                if (tab.dataset.tab === 'jobs') loadJobs();
                if (tab.dataset.tab === 'tools') loadTools();
            });
        });
        
        // Load jobs
        async function loadJobs() {
            try {
                const resp = await fetch('/api/jobs');
                const jobs = await resp.json();
                const list = document.getElementById('job-list');
                
                if (jobs.length === 0) {
                    list.innerHTML = '<li class="loading">Задач пока нет</li>';
                    return;
                }
                
                list.innerHTML = jobs.map(job => `
                    <li class="job-item" onclick="showJobDetail('${job.job_id}')">
                        <div>
                            <span class="status status-${job.status}">${job.status}</span>
                            <span class="job-id">${job.job_id.slice(0, 8)}...</span>
                        </div>
                        <div class="job-goal">${job.goal}</div>
                        <div class="job-meta">
                            ${new Date(job.created_at).toLocaleString()} | 
                            Шагов: ${job.steps ? job.steps.length : 0}
                        </div>
                    </li>
                `).join('');
            } catch (e) {
                document.getElementById('job-list').innerHTML = '<li class="error">Ошибка загрузки: ' + e.message + '</li>';
            }
        }
        
        // Show job detail
        async function showJobDetail(jobId) {
            try {
                const resp = await fetch('/api/jobs/' + jobId);
                const job = await resp.json();
                
                document.getElementById('detail-job-id').textContent = jobId;
                document.getElementById('job-detail-content').innerHTML = `
                    <p><strong>Цель:</strong> ${job.goal}</p>
                    <p><strong>Статус:</strong> <span class="status status-${job.status}">${job.status}</span></p>
                    <p><strong>Создана:</strong> ${new Date(job.created_at).toLocaleString()}</p>
                    ${job.completed_at ? '<p><strong>Завершена:</strong> ' + new Date(job.completed_at).toLocaleString() + '</p>' : ''}
                    ${job.error_message ? '<div class="error">Ошибка: ' + job.error_message + '</div>' : ''}
                    
                    <h3>Шаги</h3>
                    ${(job.steps || []).map((step, i) => `
                        <div class="step step-${step.status}">
                            <div class="step-header">
                                <span class="step-name">${i + 1}. ${step.step_name}</span>
                                <span class="status status-${step.status}">${step.status}</span>
                            </div>
                            <div><strong>Инструмент:</strong> ${step.tool} | <strong>Режим:</strong> ${step.mode}</div>
                            ${step.duration_seconds ? '<div><strong>Длительность:</strong> ' + step.duration_seconds.toFixed(1) + 's</div>' : ''}
                            ${step.error_message ? '<div class="error">' + step.error_message + '</div>' : ''}
                            ${step.output_files && step.output_files.length > 0 ? `
                                <div class="output-files">
                                    <strong>Файлы:</strong><br>
                                    ${step.output_files.map(f => `<a href="/api/files/${encodeURIComponent(f)}" target="_blank">${f}</a>`).join('<br>')}
                                </div>
                            ` : ''}
                            ${step.preview ? '<pre>' + escapeHtml(step.preview) + '</pre>' : ''}
                        </div>
                    `).join('')}
                    
                    ${job.status === 'paused' || job.status === 'failed' ? `
                        <button onclick="resumeJob('${job.job_id}')" class="success" style="margin-top: 15px;">Возобновить задачу</button>
                    ` : ''}
                `;
                
                document.getElementById('job-detail').style.display = 'block';
                document.getElementById('job-detail').scrollIntoView({ behavior: 'smooth' });
            } catch (e) {
                alert('Ошибка загрузки деталей: ' + e.message);
            }
        }
        
        // Resume job
        async function resumeJob(jobId) {
            if (!confirm('Возобновить задачу ' + jobId + '?')) return;
            
            try {
                const resp = await fetch('/api/jobs/' + jobId + '/resume', { method: 'POST' });
                const result = await resp.json();
                alert(result.message || 'Задача возобновлена');
                loadJobs();
            } catch (e) {
                alert('Ошибка: ' + e.message);
            }
        }
        
        // Load tools
        async function loadTools() {
            try {
                const resp = await fetch('/api/tools');
                const tools = await resp.json();
                
                document.getElementById('tools-list').innerHTML = tools.map(tool => `
                    <div class="tool-card">
                        <div class="tool-name">${tool.name}</div>
                        <div class="tool-desc">${tool.description || 'Нет описания'}</div>
                        <div class="tool-modes">Режимы: ${(tool.modes || []).join(', ')}</div>
                    </div>
                `).join('');
            } catch (e) {
                document.getElementById('tools-list').innerHTML = '<div class="error">Ошибка загрузки: ' + e.message + '</div>';
            }
        }
        
        // Run goal form with file upload
        document.getElementById('run-goal-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const goal = document.getElementById('goal').value;
            let inputData = {};
            
            try {
                const inputStr = document.getElementById('input_params').value.trim();
                if (inputStr) {
                    inputData = JSON.parse(inputStr);
                }
            } catch (e) {
                document.getElementById('run-result').innerHTML = '<div class="error">Неверный JSON в параметрах: ' + e.message + '</div>';
                return;
            }
            
            const cookiesFile = document.getElementById('cookies_file').files[0];
            
            try {
                let resp;
                if (cookiesFile) {
                    // Upload with file
                    const formData = new FormData();
                    formData.append('goal', goal);
                    formData.append('input_data', JSON.stringify(inputData));
                    formData.append('cookies_file', cookiesFile);
                    
                    resp = await fetch('/api/run', {
                        method: 'POST',
                        body: formData
                    });
                } else {
                    // Upload without file
                    resp = await fetch('/api/run', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ goal, input_data: inputData })
                    });
                }
                
                const result = await resp.json();
                
                if (resp.ok) {
                    document.getElementById('run-result').innerHTML = `
                        <div class="success">
                            Задача запущена!<br>
                            ID: <span class="job-id">${result.job_id}</span><br>
                            <button onclick="showJobDetail('${result.job_id}')" style="margin-top: 10px;">Просмотреть</button>
                        </div>
                    `;
                    document.getElementById('goal').value = '';
                    document.getElementById('input_params').value = '';
                    document.getElementById('cookies_file').value = '';
                } else {
                    document.getElementById('run-result').innerHTML = '<div class="error">Ошибка: ' + (result.error || 'Неизвестная ошибка') + '</div>';
                }
            } catch (e) {
                document.getElementById('run-result').innerHTML = '<div class="error">Ошибка: ' + e.message + '</div>';
            }
        });
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Initial load
        loadJobs();
    </script>
</body>
</html>
"""


def get_runner():
    """Get or create runner instance"""
    global runner
    with runner_lock:
        if runner is None:
            runner = KitRunner()
            runner.initialize()
        return runner


@app.route('/')
def index():
    """Serve main page"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/run', methods=['POST'])
def run_goal():
    """Run a new goal"""
    try:
        # Handle both JSON and FormData (for file upload)
        if request.content_type and 'multipart/form-data' in request.content_type:
            goal = request.form.get('goal')
            input_data_str = request.form.get('input_data', '{}')
            input_data = json.loads(input_data_str) if input_data_str else {}
            cookies_file = request.files.get('cookies_file')
        else:
            data = request.get_json()
            goal = data.get('goal')
            input_data = data.get('input_data', {})
            cookies_file = None
        
        if not goal:
            return jsonify({'error': 'Goal is required'}), 400
        
        runner_instance = get_runner()
        
        # Handle cookies file upload
        if cookies_file and cookies_file.filename:
            # Save cookies file to job directory
            import tempfile
            from pathlib import Path
            
            # Get base storage directory
            base_dir = Path(runner_instance.config.get('storage', {}).get('base_dir', '~/.kit')).expanduser()
            cookies_dir = base_dir / 'cookies'
            cookies_dir.mkdir(parents=True, exist_ok=True)
            
            # Save with unique name
            import uuid
            cookies_filename = f"{uuid.uuid4().hex}_{cookies_file.filename}"
            cookies_path = cookies_dir / cookies_filename
            
            cookies_file.save(str(cookies_path))
            
            # Add cookies_file path to input_data
            input_data['cookies_file'] = str(cookies_path)
        
        # Run in background thread
        def run_async():
            try:
                runner_instance.run_goal(goal, input_data)
            except Exception as e:
                print(f"Error running goal: {e}")
        
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()
        
        # Wait a moment for job to be created
        time.sleep(0.1)
        
        # Get the job (it's created immediately)
        jobs = runner_instance.list_jobs(limit=1)
        job = jobs[0] if jobs else None
        
        return jsonify({
            'job_id': job.job_id if job else None,
            'message': 'Job started'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all jobs"""
    try:
        runner_instance = get_runner()
        limit = request.args.get('limit', 50, type=int)
        jobs = runner_instance.list_jobs(limit=limit)
        
        return jsonify([{
            'job_id': job.job_id,
            'goal': job.goal,
            'status': job.status.value,
            'created_at': job.created_at,
            'completed_at': job.completed_at,
            'steps': [{
                'step_name': s.step_name,
                'tool': s.tool,
                'mode': s.mode,
                'status': s.status.value if s.status else None,
                'duration_seconds': s.duration_seconds,
                'error_message': s.error_message,
                'output_files': s.output_files,
                'preview': s.preview,
            } for s in job.steps]
        } for job in jobs])
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get job by ID"""
    try:
        runner_instance = get_runner()
        job = runner_instance.get_job(job_id)
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify({
            'job_id': job.job_id,
            'goal': job.goal,
            'status': job.status.value,
            'created_at': job.created_at,
            'completed_at': job.completed_at,
            'error_message': job.error_message,
            'input_data': job.input_data,
            'steps': [{
                'step_name': s.step_name,
                'tool': s.tool,
                'mode': s.mode,
                'status': s.status.value if s.status else None,
                'duration_seconds': s.duration_seconds,
                'error_message': s.error_message,
                'output_params': s.output_params,
                'output_files': s.output_files,
                'preview': s.preview,
            } for s in job.steps]
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/jobs/<job_id>/resume', methods=['POST'])
def resume_job(job_id):
    """Resume a paused/failed job"""
    try:
        runner_instance = get_runner()
        
        def resume_async():
            try:
                runner_instance.resume_job(job_id)
            except Exception as e:
                print(f"Error resuming job: {e}")
        
        thread = threading.Thread(target=resume_async, daemon=True)
        thread.start()
        
        return jsonify({'message': 'Job resume started'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tools', methods=['GET'])
def list_tools():
    """List available tools"""
    try:
        runner_instance = get_runner()
        tools = runner_instance.get_available_tools()
        return jsonify(tools)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/files/<path:filepath>', methods=['GET'])
def get_file(filepath):
    """Serve output file"""
    try:
        runner_instance = get_runner()
        
        # Get base outputs directory
        base_dir = Path(runner_instance.config.get('storage', {}).get('base_dir', '~/.kit')).expanduser()
        outputs_dir = base_dir / runner_instance.config.get('storage', {}).get('outputs_dir', 'outputs')
        
        full_path = outputs_dir / filepath
        
        if not full_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_from_directory(full_path.parent, full_path.name)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def status():
    """Get server status"""
    try:
        runner_instance = get_runner()
        jobs = runner_instance.list_jobs(limit=100)
        
        status_counts = {}
        for job in jobs:
            status = job.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return jsonify({
            'status': 'ok',
            'total_jobs': len(jobs),
            'by_status': status_counts,
            'tools_count': len(runner_instance.get_available_tools())
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def main():
    """Run web server"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Kit Runner Web Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind')
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', 7700)), help='Port to bind')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--config', '-c', help='Path to config file')
    
    args = parser.parse_args()
    
    # Initialize runner with config
    global runner
    runner = KitRunner(config_path=args.config)
    runner.initialize()
    
    print(f"🚀 Kit Runner Web Server")
    print(f"📍 Running on http://{args.host}:{args.port}")
    print(f"🔧 Debug mode: {args.debug}")
    print(f"\nPress Ctrl+C to stop")
    
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


if __name__ == '__main__':
    main()
