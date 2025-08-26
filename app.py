from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
import os
from io import BytesIO
from services.data_service import process_csv, filter_data, paginate_data, generate_summary
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB

dataframe = None  # in-memory storage
PER_PAGE = 50     # rows per page


# --- Routes ---

# Landing page
@app.route('/')
def index():
    return render_template('index.html')


# Upload CSV page
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    global dataframe

    if request.method == 'GET':
        return render_template('upload.html')

    if 'file' not in request.files:
        flash("No file uploaded", "error")
        return redirect(url_for('upload_file'))

    file = request.files['file']
    if file.filename == '':
        flash("No file selected", "error")
        return redirect(url_for('upload_file'))

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)

    # Save to disk immediately (prevents memory leak for large files)
    file.save(filepath)

    try:
        # Process CSV safely
        dataframe = process_csv(filepath)

        # Cleanup uploaded file after processing
        try:
            os.remove(filepath)
        except OSError:
            pass

    except ValueError as e:
        flash(f"Error processing file: {str(e)}", "error")
        return redirect(url_for('upload_file'))

    flash(f"File '{file.filename}' uploaded successfully!", "success")
    return redirect(url_for('data_view'))


# Data viewing page
@app.route('/data')
def data_view():
    global dataframe
    if dataframe is None:
        return redirect(url_for('index'))

    classes = sorted([str(c) for c in dataframe['Student_Class'].dropna().unique()])
    summary = generate_summary(dataframe.copy())
    return render_template('data.html', classes=classes, summary=summary)


# Data API endpoint with pagination
@app.route('/data_page')
def data_page():
    global dataframe
    if dataframe is None:
        return jsonify({"data": [], "total": 0, "page_size": PER_PAGE, "summary": {}})

    username = request.args.get('username')
    class_name = request.args.get('class')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = int(request.args.get('page', 1))

    filtered = filter_data(dataframe.copy(), username, class_name, start_date, end_date)
    paged = paginate_data(filtered, page, PER_PAGE).copy()
    if "Last_Visit_Time" in paged.columns:
        paged['Last_Visit_Time'] = paged['Last_Visit_Time'].dt.strftime('%Y-%m-%d %H:%M:%S')

    summary = generate_summary(filtered)

    return jsonify({
        "data": paged.to_dict(orient='records'),
        "total": len(filtered),
        "page_size": PER_PAGE,
        "summary": summary
    })


# Export CSV
@app.route('/export_csv')
def export_csv():
    global dataframe
    if dataframe is None:
        return redirect(url_for('index'))

    username = request.args.get('username')
    class_name = request.args.get('class')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    filtered = filter_data(dataframe.copy(), username, class_name, start_date, end_date)

    buffer = BytesIO()
    filtered.to_csv(buffer, index=False)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="student_data.csv", mimetype="text/csv")


# Export PDF
@app.route('/export_pdf')
def export_pdf():
    global dataframe
    if dataframe is None:
        return redirect(url_for('index'))

    username = request.args.get('username')
    class_name = request.args.get('class')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    filtered = filter_data(dataframe.copy(), username, class_name, start_date, end_date)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)

    data = [filtered.columns.tolist()] + filtered.fillna("").values.tolist()
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))

    doc.build([table])
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="student_data.pdf", mimetype="application/pdf")


# Analytics page
@app.route('/analytics')
def analytics():
    global dataframe
    if dataframe is None:
        return redirect(url_for('index'))

    summary = generate_summary(dataframe.copy())
    classes = sorted([str(c) for c in dataframe['Student_Class'].dropna().unique()])
    return render_template('analytics.html', summary=summary, classes=classes, analytics_data=summary)


# Analytics filtered data endpoint
@app.route('/analytics_data')
def analytics_data():
    global dataframe
    if dataframe is None:
        return jsonify({})

    username = request.args.get('username')
    class_name = request.args.get('class')

    filtered = filter_data(dataframe.copy(), username, class_name)
    summary = generate_summary(filtered)

    return jsonify(summary)


# --- Main ---
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, use_reloader=False)
