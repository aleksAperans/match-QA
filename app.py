import os
import csv
import tempfile
import io
import json
import uuid
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from sayari.client import Sayari
from io import BytesIO
from pdf_generator import generate_pdf_report
import threading
from deep_translator import GoogleTranslator
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load environment variables
load_dotenv()

# Configuration
ALLOWED_EXTENSIONS = {'csv'}
UPLOAD_FOLDER = tempfile.gettempdir()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Global variables for progress tracking
current_row = 0
total_rows = 0
processed_results = []
results_summary = {}
results_summary_lock = Lock()
processing_complete = threading.Event()

# File-based storage for labels
LABEL_STORAGE_DIR = 'label_storage'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_label_storage_path(session_id):
    if not os.path.exists(LABEL_STORAGE_DIR):
        os.makedirs(LABEL_STORAGE_DIR)
    return os.path.join(LABEL_STORAGE_DIR, f'{session_id}_labels.json')

def save_label(session_id, result_id, category, value):
    storage_path = get_label_storage_path(session_id)
    try:
        with open(storage_path, 'r') as f:
            labels = json.load(f)
    except FileNotFoundError:
        labels = {}

    if result_id not in labels:
        labels[result_id] = {}

    if value is None:
        # Remove the label if value is None
        labels[result_id].pop(category, None)
    else:
        labels[result_id][category] = value

    with open(storage_path, 'w') as f:
        json.dump(labels, f)

def get_labels(session_id):
    storage_path = get_label_storage_path(session_id)
    try:
        with open(storage_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_sayari_client(environment):
    if environment == 'production':
        return Sayari(
            client_id=os.getenv('client_id'),
            client_secret=os.getenv('client_secret'),
            base_url='https://api.sayari.com'
        )
    elif environment == 'develop':
        return Sayari(
            client_id=os.getenv('dev_client_id'),
            client_secret=os.getenv('dev_client_secret'),
            base_url='https://api.develop.sayari.com'
        )
    elif environment == 'internal':
        return Sayari(
            client_id=os.getenv('internal_client_id'),
            client_secret=os.getenv('internal_client_secret'),
            base_url='https://api.internal.sayari.com'
        )
    else:
        raise ValueError(f"Invalid environment: {environment}")

@app.route('/export_pdf_report')
def export_pdf_report():
    # Prepare the data for the PDF report
    summary = results_summary

    # Calculate country summary (you'll need to implement this based on your data structure)
    country_summary = calculate_country_summary(processed_results)

    # Calculate name quality details (you'll need to implement this based on your data structure)
    name_quality = calculate_name_quality(processed_results)

    # Calculate address quality details (you'll need to implement this based on your data structure)
    address_quality = calculate_address_quality(processed_results)

    # Generate the PDF
    pdf = generate_pdf_report(summary, country_summary, name_quality, address_quality)

    # Serve the PDF
    return send_file(
        BytesIO(pdf),
        mimetype='application/pdf',
        as_attachment=True,
        download_name='match_resolution_report.pdf'
    )

def calculate_country_summary(results):
    country_summary = {}
    for result in results:
        country = result['input'].get('country', 'Unknown')
        match_strength = result['output'].get('match_strength', 'No match')

        if country not in country_summary:
            country_summary[country] = {'strong': 0, 'weak': 0, 'no_match': 0, 'total': 0}

        country_summary[country]['total'] += 1
        if match_strength == 'strong':
            country_summary[country]['strong'] += 1
        elif match_strength == 'weak':
            country_summary[country]['weak'] += 1
        else:
            country_summary[country]['no_match'] += 1

    # Calculate percentages
    for country, data in country_summary.items():
        total = data['total']
        data['strong_percent'] = (data['strong'] / total) * 100 if total > 0 else 0
        data['weak_percent'] = (data['weak'] / total) * 100 if total > 0 else 0
        data['no_match_percent'] = (data['no_match'] / total) * 100 if total > 0 else 0

    return country_summary

def calculate_name_quality(results):
    name_quality = {
        'strong_matches': {'true': 0, 'false': 0, 'na': 0, 'total': 0},
        'weak_matches': {'true': 0, 'false': 0, 'na': 0, 'total': 0}
    }

    for result in results:
        match_strength = result['output'].get('match_strength', 'No match')
        high_quality_match_name = result['output'].get('high_quality_match_name', 'N/A')

        if match_strength in ['strong', 'weak']:
            category = f"{match_strength}_matches"
            name_quality[category]['total'] += 1
            if high_quality_match_name == 'true':
                name_quality[category]['true'] += 1
            elif high_quality_match_name == 'false':
                name_quality[category]['false'] += 1
            else:
                name_quality[category]['na'] += 1

    # Calculate percentages
    for category, data in name_quality.items():
        total = data['total']
        data['true_percent'] = (data['true'] / total) * 100 if total > 0 else 0
        data['false_percent'] = (data['false'] / total) * 100 if total > 0 else 0
        data['na_percent'] = (data['na'] / total) * 100 if total > 0 else 0

    return name_quality

def calculate_address_quality(results):
    address_quality = {'high': 0, 'medium': 0, 'low': 0, 'na': 0, 'total': 0}

    for result in results:
        address_match_quality = result['output'].get('address_match_quality', 'N/A')
        address_quality['total'] += 1

        if address_match_quality == 'high':
            address_quality['high'] += 1
        elif address_match_quality == 'medium':
            address_quality['medium'] += 1
        elif address_match_quality == 'low':
            address_quality['low'] += 1
        else:
            address_quality['na'] += 1

    # Calculate percentages
    total = address_quality['total']
    for key in ['high', 'medium', 'low', 'na']:
        address_quality[f"{key}_percent"] = (address_quality[key] / total) * 100 if total > 0 else 0

    return address_quality

@app.route('/', methods=['GET', 'POST'])
def index():
    global processed_results, results_summary
    if request.method == 'POST':
        environment = request.form.get('environment', 'production')
        profile = request.form.get('profile', 'corporate')
        name_min_percentage = request.form.get('name_min_percentage')
        name_min_tokens = request.form.get('name_min_tokens')
        minimum_score_threshold = request.form.get('minimum_score_threshold')
        search_fallback = request.form.get('search_fallback')
        cutoff_threshold = request.form.get('cutoff_threshold')
        skip_post_process = request.form.get('skip_post_process')

        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            processed_results = process_file(filepath, environment, profile, name_min_percentage, name_min_tokens, minimum_score_threshold, search_fallback)

            logging.info(f"Debug - Summary after process_file: {results_summary}")

            return redirect(url_for('results'))

    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    global current_row, total_rows, processing_complete

    environment = request.form.get('environment', 'production')
    profile = request.form.get('profile', 'corporate')
    name_min_percentage = request.form.get('name_min_percentage')
    name_min_tokens = request.form.get('name_min_tokens')
    minimum_score_threshold = request.form.get('minimum_score_threshold')
    search_fallback = request.form.get('search_fallback')
    cutoff_threshold = request.form.get('cutoff_threshold')
    skip_post_process = request.form.get('skip_post_process')

    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Count total rows
        with open(filepath, 'r') as csvfile:
            total_rows = sum(1 for row in csv.DictReader(csvfile))

        current_row = 0
        processing_complete.clear()  # Reset the event

        # Start processing in a background thread
        thread = threading.Thread(target=process_file, args=(filepath, environment, profile, name_min_percentage, name_min_tokens, minimum_score_threshold, search_fallback, 3))
        thread.start()

        return jsonify({'total_rows': total_rows})

    return redirect(url_for('index'))

@app.route('/progress')
def progress():
    global current_row, total_rows
    return jsonify({'current_row': current_row, 'total_rows': total_rows})

@app.route('/results')
def results():
    global processed_results, results_summary, processing_complete

    if not processing_complete.wait(timeout=30):
        flash("Processing is taking longer than expected. Please try refreshing the page.")

    with results_summary_lock:
        summary = results_summary.copy()

    session_id = session.get('id', str(uuid.uuid4()))
    session['id'] = session_id

    return render_template('results.html', results=processed_results, summary=summary, session_id=session_id)

@app.route('/update_label', methods=['POST'])
def update_label():
    session_id = session.get('id', str(uuid.uuid4()))
    result_id = request.form['result_id']
    category = request.form['category']
    value = request.form['value']

    # If value is an empty string, set it to None
    if value == '':
        value = None

    save_label(session_id, result_id, category, value)

    return jsonify({'success': True})

@app.route('/export_labels')
def export_labels():
    session_id = session.get('id', str(uuid.uuid4()))
    labels = get_labels(session_id)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'input_name', 'input_address', 'input_country',
        'output_name', 'output_address', 'output_country',
        'match_strength', 'high_quality_match_name', 'address_match_quality',
        'entity_id', 'name_label', 'address_label', 'overall_label', 'profile', 'note'
    ])

    writer.writeheader()

    for index, result in enumerate(processed_results):
        row = {
            'input_name': result['input'].get('name', ''),
            'input_address': result['input'].get('address', ''),
            'input_country': result['input'].get('country', ''),
            'output_name': result['output'].get('name', ''),
            'output_address': result['output'].get('address', ''),
            'output_country': result['output'].get('country', ''),
            'match_strength': result['output'].get('match_strength', ''),
            'high_quality_match_name': result['output'].get('high_quality_match_name', ''),
            'address_match_quality': result['output'].get('address_match_quality', ''),
            'entity_id': result['output'].get('entity_id', ''),
            'name_label': labels.get(str(index), {}).get('name', ''),
            'address_label': labels.get(str(index), {}).get('address', ''),
            'overall_label': labels.get(str(index), {}).get('overall', ''),
            'profile': result['output'].get('profile', ''),
            'note': labels.get(str(index), {}).get('note', '')
        }
        writer.writerow(row)

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='output_labels.csv'
    )

@app.route('/preview_json/<int:result_id>')
def preview_json(result_id):
    if 0 <= result_id < len(processed_results):
        return jsonify(processed_results[result_id]['full_response'])
    else:
        return jsonify({'error': 'Result not found'}), 404

@app.route('/translate', methods=['POST'])
def translate_result():
    result_id = int(request.form['result_id'])
    result = processed_results[result_id]

    translated = {
        'input': {
            'name': translate_text(result['input'].get('name', '')),
            'address': translate_text(result['input'].get('address', '')),
        },
        'output': {
            'name': translate_text(result['output'].get('name', '')),
            'address': translate_text(result['output'].get('address', '')),
        }
    }

    return jsonify({'translated': translated})

def translate_text(text, target_language='en'):
    if not text or text == 'N/A':
        return text

    try:
        translator = GoogleTranslator(source='auto', target=target_language)
        return translator.translate(text)
    except Exception as e:
        logging.error(f"Translation error: {e}")
        return text  # Return original text if translation fails

def process_file(filepath, environment, profile, name_min_percentage, name_min_tokens, minimum_score_threshold, search_fallback, num_workers=3):
    global current_row, total_rows, results_summary, processed_results, processing_complete
    client = get_sayari_client(environment)
    processed_results = []
    summary = {
        'total_rows': 0,
        'strong_matches': 0,
        'weak_matches': 0,
        'no_matches': 0,
        'errors': 0
    }

    def process_row(row):
        try:
            logging.info(f"Processing row: {row}")
            params = {k: v for k, v in row.items() if v}
            params['profile'] = profile
            if name_min_percentage:
                params['name_min_percentage'] = int(name_min_percentage)
            if name_min_tokens:
                params['name_min_tokens'] = int(name_min_tokens)
            if minimum_score_threshold:
                params['minimum_score_threshold'] = int(minimum_score_threshold)
            if search_fallback is not None:
                params['search_fallback'] = search_fallback.lower() == 'true'

            resolution = client.resolution.resolution(**params)

            if resolution.data:
                result = resolution.data[0]
                match_strength = result.match_strength.value if result.match_strength else 'N/A'
                name_exp = result.explanation.get('name', [{}])[0]
                address_exp = result.explanation.get('address', [{}])[0]

                return {
                    'input': row,
                    'output': {
                        'name': result.label,
                        'address': result.addresses[0] if result.addresses else 'N/A',
                        'country': result.countries[0] if result.countries else 'N/A',
                        'match_strength': match_strength,
                        'high_quality_match_name': getattr(name_exp, 'high_quality_match_name', 'N/A'),
                        'address_match_quality': getattr(address_exp, 'match_quality', 'N/A'),
                        'entity_id': result.entity_id,
                        'profile': result.profile
                    }
                }
            else:
                return {
                    'input': row,
                    'output': {
                        'name': 'No match found',
                        'entity_id': 'N/A',
                        'address': 'N/A',
                        'country': 'N/A',
                        'match_strength': 'No match',
                        'high_quality_match_name': 'N/A',
                        'address_match_quality': 'N/A',
                        'profile': 'N/A'
                    }
                }
        except Exception as e:
            logging.error(f"Error processing row: {row}")
            logging.error(f"Exception: {str(e)}")
            return {
                'input': row,
                'output': {
                    'name': 'Error',
                    'entity_id': 'N/A',
                    'address': 'N/A',
                    'country': 'N/A',
                    'match_strength': 'Error',
                    'high_quality_match_name': 'N/A',
                    'address_match_quality': 'N/A',
                    'profile': 'N/A'
                }
            }

    with open(filepath, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        total_rows = len(rows)

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_row = {executor.submit(process_row, row): row for row in rows}
        for future in as_completed(future_to_row):
            result = future.result()
            processed_results.append(result)
            current_row += 1

            match_strength = result['output']['match_strength']
            if match_strength.lower() == 'strong':
                summary['strong_matches'] += 1
            elif match_strength.lower() == 'weak':
                summary['weak_matches'] += 1
            elif match_strength == 'No match':
                summary['no_matches'] += 1
            elif match_strength == 'Error':
                summary['errors'] += 1

    summary['total_rows'] = total_rows

    # Calculate percentages
    total = summary['total_rows']
    if total > 0:
        summary['strong_matches_percent'] = (summary['strong_matches'] / total) * 100
        summary['weak_matches_percent'] = (summary['weak_matches'] / total) * 100
        summary['no_matches_percent'] = (summary['no_matches'] / total) * 100
        summary['errors_percent'] = (summary['errors'] / total) * 100
    else:
        summary['strong_matches_percent'] = 0
        summary['weak_matches_percent'] = 0
        summary['no_matches_percent'] = 0
        summary['errors_percent'] = 0

    logging.info(f"Debug - Final summary: {summary}")
    with results_summary_lock:
        global results_summary
        results_summary = summary

    os.remove(filepath)
    processing_complete.set()  # Set the event to signal processing is complete
    return processed_results

if __name__ == '__main__':
    app.run(debug=True, port=8080)
