from schema import SNP, Phenotype, Association, Paper, File, SnpediaEvidence
import re

class SnpediaEntry(object):
    # snpedia database
    source = "snpedia"
    description = None
    magnitude = None
    repute = None
    genotype = None
    snpedia_rsid = None

    # The class "constructor" - It's actually an initializer 
    def __init__(self, description, magnitude, repute, genotype, rsid):
        self.description = description
        self.magnitude = magnitude
        self.repute = repute
        self.genotype = genotype
        self.rsid = rsid

def make_snpedia_entry(db_object):
    entry = SnpediaEntry(db_object.description, db_object.magnitude, db_object.repute, db_object.genotype, db_object.snp.rs_id)
    return entry

class GwasCatalogEntry(object):
    # gwas catalog database
    source = "gwas_catalog"
    pvalue = None
    oddsratio = None
    synonyms = None
    name = None
    pmid = None
    title = None
    journal = None
    rsid_list = None # multiple rsids can be associated with a single gwas catalog entry

    # The class "constructor" - It's actually an initializer 
    def __init__(self, pvalue, oddsratio, synonyms, name, pmid, title, journal, rsid_list):
        self.pvalue = pvalue
        self.oddsratio = oddsratio
        self.synonyms = synonyms
        self.name = name
        self.pmid = pmid
        self.title = title
        self.journal = journal
        self.rsid_list = rsid_list

def make_gwas_catalog_entry(db_object):
    keywords = []
    if db_object.phenotype.synonyms is not None:
        keywords = re.split(r'\|+', db_object.phenotype.synonyms)
    entry = GwasCatalogEntry(db_object.pvalue, db_object.oddsratio, keywords, db_object.phenotype.name, db_object.paper.pubmed_id, db_object.paper.title, db_object.paper.journal, db_object.snp.rs_id)
    return entry

# for Volodymyr's automatically-curated database
class AutoEntry(object):
	source = "auto"
	pmid = None
	rsid = None
	simple_phenotype = None
	detailed_phenotype = None
	pvalue = None

	# The class "constructor" - It's actually an initializer 
	def __init__(self, pmid, rsid, simple_phenotype, detailed_phenotype, pvalue):
		self.pmid = pmid
		self.rsid = rsid
		self.simple_phenotype = simple_phenotype
		self.detailed_phenotype = detailed_phenotype
		self.pvalue = pvalue

def make_auto_entry(line):
    tokens = re.split(r'\t+', line.decode('utf-8'))
    keywords = re.split(r'\|+', tokens[2])
    if (tokens[3] == '-'):
        tokens[3] = None
    entry = AutoEntry(tokens[0], int((tokens[1])[2:]), keywords, tokens[3], tokens[4])
    return entry


# data structure for automatically-curated database
raw_auto_matches = []
f = open('/afs/cs.stanford.edu/u/zho/snpssite/snps/tmp/auto.tsv')
line = f.readline()
while (line != ""):
	raw_auto_matches.append(make_auto_entry(line))
	line = f.readline()
