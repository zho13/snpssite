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

from database import auto_matches, make_snpedia_entry, make_gwas_catalog_entry, make_auto_entry
import re


app = create_app()
# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return redirect(url_for('home'))

@app.route('/test', methods=['GET', 'POST'])
def test():
#    top_SNPs = db1_session.query(Association).filter(Association.magnitude > 3).order_by(Association.magnitude.desc()).limit(10)
#    for e in top_SNPs:
#        sys.stdout.write("%s\n" % type(e.snp.rs_id))
    return render_template('reports/1.html')
    #return send_from_directory('uploads', '1.txt')

# for testing purposes only
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
    #user_manager =  current_app.user_manager
    #db_adapter = user_manager.db_adapter
    #users = db_adapter.UserClass.query.all()
    #for user in users:
    #    sys.stdout.write("\n\n\n%s\n\n\n" % user.__dict__)
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template('home.html')

# Access granted only to account holders
@app.route('/report')
@login_required
def report():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(BASE_DIR, 'templates/reports/' + str(current_user.id) + '.html')
    if (os.path.exists(filename) == True):
        return render_template('reports/' + str(current_user.id) + '.html')
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
    top_SNPs = db1_session.query(Association).filter(Association.magnitude > 3).order_by(Association.magnitude.desc()).limit(1000)
    for e in top_SNPs:
        filename.write(str(e.snp.rs_id) + ' ' + str(e.id) + '\n')

def generate_gwas_catalog_results(user_rsids):
    #phenotype_ids = [x for x in db_session.query(Phenotype).filter(Phenotype.synonyms.isnot(None)).all()]
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
        for e in results:
            matches.append((query, e))
            i = i + 1
    return matches

# Opens the specified file generated beforehand to save searches through the
# database. Finds the rsids that are both important and in the user file, and
# queries the database for entries matching the user's genotype
def generate_snpedia_results(filename, user_rsids, rsid_genotype_map):
    f = open(filename)
    top_SNPs = []
    line = f.readline()
    rsid_id_map = {}
    while (line != ""):
        tokens = line.split()
        rsid = (tokens[0])    # tokens[0] = rsid, tokens[1] = Association.id
        top_SNPs.append(int(rsid))
        rsid_id_map[int(rsid)] = tokens[1]
        line = f.readline()
   
    # Intersect the user's list of rsids with the important rsids
    query_rsids = set(top_SNPs).intersection(user_rsids)
    matches = []

    # Build the list of matching objects from the database
    for e in query_rsids:
        result = db1_session.query(Association).filter(Association.id == rsid_id_map[e]).filter(Association.genotype == rsid_genotype_map[e])
        if result.count() != 0:
            matches.append(result.first())
    return matches

# Route that will process the file upload
@app.route('/upload', methods=['POST'])
def upload():
    # A map containing important entries associated with rsids
    rsid_map = {}
    # Remove existing report
    #if os.path.exists('templates/reports/1.html'):    
    #    os.remove('templates/reports/1.html')
    # Get the name of the uploaded file
    file = request.files['file']
    # Check if the file is one of the allowed types/extensions
    if file and allowed_file(file.filename):
        # The user's SNP file is stored in the uploads folder as the user id
        filename = str(current_user.id) + '.txt'
        
        # Move the file form the temporal folder to
        # the upload folder we setup
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        user_rsids, rsid_genotype_map = parse_23andMe(filename)

        # Choose a filename to save the most important SNPS (rsid, Association.id)
        top_filename = 'top_SNPs.txt'

        if (os.path.exists(top_filename) == False):
            create_important_SNPS_file(top_filename)
        
        snpedia_matches = generate_snpedia_results(top_filename, user_rsids, rsid_genotype_map)
        for match in snpedia_matches:
            if match.snp.rs_id not in rsid_map:
                sys.stdout.write("%s\n", type(match.snp.rs_id))
                # create new entry
                rsid_map[match.snp.rs_id] = []
            temp = rsid_map[match.snp.rs_id]
            temp.append(make_snpedia_entry(match))
            rsid_map[match.snp.rs_id] = temp
        
        gwas_catalog_matches = generate_gwas_catalog_results(user_rsids)
        for match in gwas_catalog_matches:
            rsid = match[0]
            entry = match[1]
            # there may be multiple rsids associated with a single gwas catalog entry
            rsids = re.findall(r'rs\d+', entry.snp.rs_id, flags=re.IGNORECASE)
            for rsid in rsids:
                rsid = int(rsid[2:]) # filter initial 'rs', leaving just the number
            if rsid not in rsid_map:
                # create new entry
                rsid_map[rsid] = []
            temp = rsid_map[rsid]
            temp.append(make_gwas_catalog_entry(entry, rsids))
            rsid_map[rsid] = temp
        
        #rsids = zip(range(len(auto_matches)), [int(x.rsid) for x in auto_matches])
        #auto_overlap = set(top_SNPs).intersection(user_rsids)

        #for match in auto_matches:
        #overlap = [match for match in auto_matches if int(match.rsid) in user_rsids]

        #sys.stdout.write("%s\n" % len(overlap))
        
        # note that this for loop takes about 2 min--sorry i didn't have time find a shortcut!
        for match in auto_matches:
            rsid = int(match.rsid)
            if rsid in user_rsids:
                if rsid not in rsid_map:
                    # create new entry
                    rsid_map[rsid] = []
                temp = rsid_map[rsid]
                temp.append(match)
                rsid_map[rsid] = temp
        
        rsids = [rsid for rsid in rsid_map]

        # change display criteria later--it currently keeps only the snps with 3+ entries
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
        return render_template('reports/' + str(current_user.id) + '.html')
    else:
        return render_template('retry.html')

@app.teardown_appcontext
def shutdown_session(exception=None):
    db1_session.remove()
    db2_session.remove()

if __name__ == '__main__':
    app.run(
        #host='0.0.0.0',
        debug=True
    )
