import os
import shutil

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# ----------------------------------------------------------------------------

# create sqlite database
if os.environ.get('DATABASE_URL') is None:
	# in scail
  #engine = create_engine('sqlite://///afs/cs.stanford.edu/u/zho/snpssite/snps/tmp/gwas-snpedia-genotypes.sql', convert_unicode=True)
  #engine2 = create_engine('sqlite://///afs/cs.stanford.edu/u/zho/snpssite/snps/tmp/gwas-catalog.sql', convert_unicode=True)
  engine = create_engine('sqlite://///Users/zandraho/Desktop/CURIS-copy/snps/tmp/gwas-snpedia-genotypes.sql', convert_unicode=True)
  engine2 = create_engine('sqlite://///Users/zandraho/Desktop/CURIS-copy/snps/tmp/gwas-catalog.sql', convert_unicode=True)
else:
  engine = create_engine(os.environ['DATABASE_URL'], convert_unicode=True)
  engine2 = create_engine(os.environ['DATABASE_URL'], convert_unicode=True)

# create folder to store papers
if os.environ.get('DATABASE_FILE_DIR') is None:
  db_dir = '/tmp/gwasdb/'
else:
  db_dir = os.environ.get('DATABASE_FILE_DIR') + '/'
if os.path.exists(db_dir):
  shutil.rmtree(db_dir)
db_dir = os.makedirs(db_dir)


# create session to database
db1_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
db2_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine2))
Base = declarative_base()
Base2 = declarative_base()
Base.query = db1_session.query_property()
Base2.query = db2_session.query_property()

Base.metadata.create_all(bind=engine)
Base2.metadata.create_all(bind=engine2)