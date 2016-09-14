from __future__ import print_function # In python 2.7
import sys
import os
import os.path
from settings import APP_STATIC

from database import init_db, db_session
from schema import SNP, Phenotype, Association, Paper, File, SnpediaEvidence

from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug import secure_filename

from accounts import create_app
from flask import Flask, render_template_string
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_user import login_required, UserManager, UserMixin, SQLAlchemyAdapter

app = create_app()
# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    # Remove existing report
    if os.path.exists('templates/new_report.html'):
        os.remove('templates/new_report.html')
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template('home.html')

# Access granted only to account holders
@app.route('/report')
@login_required
def report():
    if (os.path.exists('templates/new_report.html') == True):
        return render_template('new_report.html')
    else:
        return render_template('upload.html')
        #return render_template('no_report.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# Parses the 23andMe.txt file and stores the rsids identified in the file
# along with an rsid-genotype map for later use
def parse_23andMe(filename):
    f = open(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    line = f.readline()
    while (line[0] == '#'):
        line = f.readline()

    user_rsids = []
    rsid_genotype_map = {}

    while (line != ""):
        tokens = line.split()
        # tokens[0] = rsid, tokens[1] = chrom, tokens[2] = pos, tokens[3] = genotype
        rsid = (tokens[0])[2:]
        user_rsids.append(int(rsid))
        rsid_genotype_map[int(rsid)] = tokens[3]
        line = f.readline()

    return user_rsids, rsid_genotype_map

# Creates a file containing the snp.rsid followed by the association.id (uniquely
# identifies SNPS) per line. This function filters out the uninteresting SNPs and
# only needs to be run once, saving time during the user's query.
def create_important_SNPS_file(filename):
    filename = open(filename, 'w')
    # Find the rsids that correspond to the SNPs of highest magnitude (most importance) in the database
    top_SNPs = db_session.query(Association).filter(Association.magnitude > 0).order_by(Association.magnitude.desc()).limit(1000000)
    for e in top_SNPs:
        filename.write(str(e.snp.rs_id) + ' ' + str(e.id) + '\n')

# Opens the specified file generated beforehand to save searches through the
# database. Finds the rsids that are both important and in the user file, and
# queries the database for entries matching the user's genotype
def generate_results(filename, user_rsids, rsid_genotype_map):
    f = open(filename)
    top_SNPs = []
    line = f.readline()
    rsid_id_map = {}
    while (line != ""):
        tokens = line.split()
        rsid = tokens[0]    # tokens[0] = rsid, tokens[1] = Association.id
        top_SNPs.append(int(rsid))
        rsid_id_map[int(rsid)] = tokens[1]
        line = f.readline()
   
    # Intersect the user's list of rsids with the important rsids
    query_rsids = set(top_SNPs).intersection(user_rsids)
    matches = []

    # Build the list of matching objects from the database
    for e in query_rsids:
        result = db_session.query(Association).filter(Association.id == rsid_id_map[e]).filter(Association.genotype == rsid_genotype_map[e])
        if result.count() != 0:
            matches.append(result.first())
    return matches

# Route that will process the file upload
@app.route('/upload', methods=['POST'])
def upload():
    # Remove existing report
    if os.path.exists('templates/new_report.html'):
        os.remove('templates/new_report.html')
    # Get the name of the uploaded file
    file = request.files['file']
    # Check if the file is one of the allowed types/extensions
    if file and allowed_file(file.filename):
        # Make the filename safe, remove unsupported chars
        filename = secure_filename(file.filename)
        
        # Move the file form the temporal folder to
        # the upload folder we setup
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        user_rsids, rsid_genotype_map = parse_23andMe(filename)

        # Choose a filename to save the most important SNPS (rsid, Association.id)
        top_filename = 'top_SNPs.txt'

        if (os.path.exists(top_filename) == False):
            create_important_SNPS_file(top_filename)

        matches = generate_results(top_filename, user_rsids, rsid_genotype_map)

        # Save a copy of the dynamically-generated html for later use (if user wants
        # to navigate the website and come back to it later)
        generated_report = render_template('report.html', matches=matches)
        with open('templates/new_report.html', 'wb') as f:
            f.write(generated_report)
        return generated_report

    else:
        return render_template('retry.html')

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

if __name__ == '__main__':
    app.run(
        debug=True
    )
