from __future__ import print_function # In python 2.7
import os, time, sys
import os.path
from settings import APP_STATIC
import schema
from __init__ import db1_session, db2_session

from schema import SNP, Phenotype, Association, Paper, File, SnpediaEvidence

from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug import secure_filename

from accounts import create_app
from flask import Flask, render_template_string
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_user import login_required, UserManager, UserMixin, SQLAlchemyAdapter


from flask import current_app
from flask.ext.login import current_user

from sqlalchemy import *

import database

from database import raw_auto_matches, make_snpedia_entry, make_gwas_catalog_entry, make_auto_entry
import re


app = create_app()
# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    return render_template('home.html')

# visiting this page will remove users' 23andMe.txt files that are more than 30 days old
@app.route('/delete')
def delete():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(BASE_DIR, 'uploads')
    now = time.time()
    for f in os.listdir(path):
        filename = os.path.join(path, f)
        sys.stdout.write("\n\n%s\n\n" % filename)
        # User SNP files expire after 30 days
        EXPIRATION_TIME = 30 * 86400
        if os.stat(filename).st_mtime < now - EXPIRATION_TIME:
            if os.path.isfile(filename):
                os.remove(filename)
    return redirect(url_for('home'))

# Access to report granted only to account holders
@app.route('/report')
@login_required
def report():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(BASE_DIR, 'templates/reports/' + str(current_user.id) + '.html')
    if (os.path.exists(filename) == True):
        return render_template('reports/' + str(current_user.id) + '.html')
    else:
        return render_template('upload.html')

# Parses the 23andMe.txt file and stores the rsids identified in the file
# along with an rsid-genotype map for later use
def parse_23andMe(filename):
    # 23andMe.txt file format:
    # tokens[0] = rsid, tokens[1] = chrom, tokens[2] = pos, tokens[3] = genotype
    f = open(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # ignore file comments
    line = f.readline()
    while (line[0] == '#'):
        line = f.readline()

    # generate a set of all rsids contained in the file along with a map of the user's
    # genotype for each rsid
    user_rsids = []
    rsid_genotype_map = {}
    
    while (line != ""):
        tokens = line.split()
        rsid = int((tokens[0])[2:])
        user_rsids.append(rsid)
        rsid_genotype_map[rsid] = tokens[3]
        line = f.readline()

    return user_rsids, rsid_genotype_map

def generate_gwas_catalog_results(user_rsids):
    results = [x for x in db2_session.query(SNP).all()]
    updated = []
    # map each rsid to the snp id
    mymap = {}
    for e in results:
        line = e.rs_id
        rsids = re.findall(r'rs\d+', line, flags=re.IGNORECASE)
        for rsid in rsids:
            updated.append(int(rsid[2:]))
            mymap[int(rsid[2:])] = e.id
    query_rsids = set(updated).intersection(user_rsids)

    # change criteria later
    matches = []
    i = 0
    for query in query_rsids:
        if i > 1000:
            return matches
        results = db2_session.query(Association).filter(Association.snp_id == mymap[query]).all()
        for result in results:
            matches.append((query, result))
            i = i + 1
    return matches

# Opens the specified file generated beforehand to save searches through the
# database. Finds the rsids that are both important and in the user file, and
# queries the database for entries matching the user's genotype
def generate_snpedia_results(user_rsids, rsid_genotype_map):
    # change criteria later
    top_SNPs = db1_session.query(Association).filter(Association.magnitude > 3).order_by(Association.magnitude.desc()).limit(1000)

    # Intersect the user's list of rsids with the important rsids
    query_rsids = set(top_SNPs).intersection(user_rsids)
    matches = []

    # Build the list of matching objects from the database
    for query in query_rsids:
        results = db1_session.query(Association).filter(Association.id == rsid_id_map[e]).filter(Association.genotype == rsid_genotype_map[e]).all()
        for result in results:
            matches.append((query, result))
    return matches

# Takes the raw entries from database.py and creates a list that can be used 
# to update the rsid map
def generate_auto_results(user_rsids):
    matches = []
    for match in raw_auto_matches:
        if match.rsid in user_rsids:
            matches.append((match.rsid, match))
    return matches

# the rsid_map uses rsids as keys and each rsid key corresponds to a list
# of entries associated with the rsid
def update_rsid_map(db_type, rsid_map, matches):
    for match in matches:
        sys.stdout.write("here\n")
        rsid = match[0]
        entry = match[1]
        if rsid not in rsid_map:
            rsid_map[rsid] = []
        temp = rsid_map[rsid]
        if db_type == 'snpedia':
            temp.append(make_snpedia_entry(entry))
        elif db_type == 'gwas_catalog':
            temp.append(make_gwas_catalog_entry(entry))
        elif db_type == 'auto':
            temp.append(entry)
        rsid_map[rsid] = temp

# creates a report specific to the user and stores the report in
# snps/templates/reports
def generate_report(filename):
    user_rsids, rsid_genotype_map = parse_23andMe(filename)

    snpedia_matches = generate_snpedia_results(user_rsids, rsid_genotype_map)
    gwas_catalog_matches = generate_gwas_catalog_results(user_rsids)
    # note that this for loop takes about 2 min--sorry i didn't have time find a shortcut!
    auto_matches = generate_auto_results(user_rsids)

    rsid_map = {}

    update_rsid_map('snpedia', rsid_map, snpedia_matches)
    update_rsid_map('gwas_catalog', rsid_map, gwas_catalog_matches)
    update_rsid_map('auto', rsid_map, auto_matches)
    # change criteria later--it currently keeps only the snps with 3+ entries
    rsids = [rsid for rsid in rsid_map]
    for rsid in rsids:
        if len(rsid_map[rsid]) < 3:
            del rsid_map[rsid]
    # Save a copy of the dynamically-generated html for later use (if user wants
    # to navigate the website and come back to it later)
    generated_report = render_template('report.html', rsid_genotype_map=rsid_genotype_map, rsid_map=rsid_map)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    new_filename = os.path.join(BASE_DIR, 'templates/reports/' + str(current_user.id) + '.html')
    with open(new_filename, 'w+') as f:
        f.write(generated_report.encode('utf-8'))
    return 'reports/' + str(current_user.id) + '.html'

# Route that will process the file upload
@app.route('/upload', methods=['POST'])
def upload():
    # Get the name of the uploaded file
    file = request.files['file']
    # Check if the file is one of the allowed types/extensions
    if file and allowed_file(file.filename):
        # The user's SNP file is stored in the uploads folder as the user id
        filename = str(current_user.id) + '.txt'
        # Move the file form the temporal folder to
        # the upload folder we setup
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return render_template(generate_report(filename))
    
    else:
        return render_template('retry.html')

@app.teardown_appcontext
def shutdown_session(exception=None):
    db1_session.remove()
    db2_session.remove()

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        debug=True
    )
