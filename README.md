# snpssite

notes to get started

commands:
source sqlalchemy-workspace/bin/activate && python snps/SNP-site.py

layout

  - databases (snpedia, gwas_catalog, auto) are in snps/tmp
  - user 23andMe.txt files are in snps/uploads, and are saved according to the user.id of the
    user management account system database (basic_app.sqlite)
  - user reports are in snps/templates/reports, also stored by user.id
  - snps/static/styles/classic.css controls the layout for the cards
  - __init__.py initializes the databases for snpedia and gwas_catalog
  - database.py initializes the auto.tsv file


important notes
  - there are three paths you need to change:
	1. in snps/__init__.py, change the snpedia and gwas_catalog paths
	2. in snps/database.py, change the auto path

  - in order to delete user files that are more than 30 days old, you currently have to
    visit the /delete page
  - generate_auto_results(user_rsids) currently takes about 2 minutes to run--not sure if
    there's a faster way, but optimization would be ideal
  - to change the types of snps that the report outputs, ctrl-f "change criteria later"
  - the modal functionality for info release is broken. see the upload.html file
  - from the report page, only the SNPSSITE link works--others do nothing
