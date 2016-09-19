from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import String, Integer, Float, Boolean, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy import func

from database import Base

# ----------------------------------------------------------------------
# Database models

class SNP(Base):
  __tablename__ = 'snps'
  id = Column( Integer, primary_key=True, nullable=False, autoincrement=True)
  rs_id           = Column( Integer, nullable=False, unique=True )
  interest        = Column( Integer )
  ref             = Column( String(50) )
  chrom           = Column( Integer )
  position        = Column( Integer )
  gene            = Column( String(50) )
  omim            = Column( Boolean )
  pharmgkb        = Column( Boolean )

  def __init__(self, id=None, rs_id=None, interest=None, ref=None, chrom=None, \
  position=None, gene=None, omim=None, pharmgkb=None):
    self.rs_id            = rs_id
    self.interest         = interest
    self.ref              = ref
    self.chrom            = chrom
    self.position         = position
    self.gene             = gene
    self.omim             = omim
    self.pharmgkb         = pharmgkb

  def __repr__(self):
    return '<SNP: id=%s rs_id=%s interest=%s ref=%s chrom=%s position=%s gene=%s omim=%s pharmgkb=%s>' \
    % (str(self.id), str(self.rs_id), self.interest, self.ref, str(self.chrom), \
      str(self.position), self.gene, self.omim, self.pharmgkb)

class Phenotype(Base):
  __tablename__ = 'phenotypes'
  id = Column( Integer, primary_key=True, nullable=False, autoincrement=True)
  name            = Column( String(1000), nullable=False )
  category        = Column( String(100) ) # disease, drug
  source          = Column( String(100), nullable=False ) # snpedia, gwas_catalog
  synonyms        = Column( String(1000) )
  ontology_ref    = Column( String(1000) )
  misc            = Column( String(1000) )

  def __init__(self, id=None, name=None, category=None, source=None, synonyms=None, \
  ontology_ref=None, misc=None):
    self.name             = name
    self.category         = category
    self.source           = source
    self.synonyms         = synonyms
    self.ontology_ref     = ontology_ref
    self.misc             = misc

  def __repr__(self):
    return '<Phenotype: name=%s category=%s source=%s synonyms=%s ontology_ref=%s misc=%s>' \
    % (self.name, self.category, self.source, self.synonyms, self.ontology_ref, self.misc)

class Association(Base):
  __tablename__ = 'associations'
  id = Column( Integer, primary_key=True, nullable=False, autoincrement=True)
  allele          = Column( String(10) )
  genotype        = Column( String(10) )
  repute          = Column( String(10) )
  description     = Column( String(100) )
  magnitude       = Column( Float )
  pvalue          = Column( Float )
  oddsratio       = Column( Float )
  beta            = Column( Float )
  beta_params     = Column( String(100) )
  freq            = Column( Float )
  population      = Column( String(100) )
  source          = Column( String(1000) ) # snpedia, gwas_catalog, extracted
  controls        = Column( Integer )
  cases           = Column( Integer )
  snp_id          = Column( Integer, ForeignKey('snps.id') )
  phenotype_id    = Column( Integer, ForeignKey('phenotypes.id') )
  paper_id        = Column( Integer, ForeignKey('papers.id') )
  snp             = relationship('SNP')
  phenotype       = relationship('Phenotype')
  paper           = relationship('Paper')

  def __init__(self, id=None, allele=None, genotype=None, repute=None, description=None, \
    magnitude=None, pvalue=None, oddsratio=None, beta=None, beta_params=None, freq=None, \
    population=None, source=None, controls=None, cases=None, snp_id=None, phenotype_id=None, \
    paper_id=None, snp=None, phenotype=None, paper=None):
    self.allele           = allele
    self.genotype         = genotype
    self.repute           = repute
    self.description      = description
    self.magnitude        = magnitude
    self.pvalue           = pvalue
    self.oddsratio        = oddsratio
    self.beta             = beta
    self.beta_params      = beta_params
    self.freq             = freq
    self.population       = population
    self.source           = source
    self.controls         = controls
    self.cases            = cases
    self.snp_id           = snp_id
    self.phenotype_id     = phenotype_id
    self.paper_id         = paper_id
    self.snp              = snp
    self.phenotype        = phenotype
    self.paper            = paper

  def __repr__(self):
    return '<Association: allele=%s genotype=%s repute=%s description=%s magnitude=%s pvalue=%s \
    oddsratio=%s beta=%s beta_params=%s freq=%s population=%s source=%s controls=%s cases=%s snp_id=%s \
    phenotype_id=%s paper_id=%s>' \
    % (self.allele, self.genotype, self.repute, self.description, str(self.magnitude), str(self.pvalue), \
      str(self.oddsratio), str(self.beta), self.beta_params, str(self.freq), self.population, self.source, \
      str(self.controls), str(self.cases), str(self.snp_id), str(self.phenotype_id), str(self.paper_id))

class Paper(Base):
  __tablename__ = 'papers'
  id = Column( Integer, primary_key=True, nullable=False, autoincrement=True)
  pubmed_id       = Column( Integer, nullable=False, unique=True )
  pmc_id          = Column( Integer )
  authors         = Column( String(1000) )
  journal         = Column( String(1000) )
  open_access     = Column( Boolean )
  snpedia_open    = Column( Boolean )
  title           = Column( String(1000) )
  abstract        = Column( String(10000) )
  pdf_id          = Column( Integer, ForeignKey('files.id') )
  pdf             = relationship('File', primaryjoin='Paper.pdf_id==File.id', post_update=True)
  files           = relationship('File', primaryjoin='Paper.id==File.paper_id')
  associations    = relationship(Association, backref='papers')

  def __init__(self, id=None, pubmed_id=None, pmc_id=None, authors=None, journal=None, \
    open_access=None, snpedia_open=None, title=None, abstract=None, pdf_id=None):
    self.pubmed_id        = pubmed_id
    self.pmc_id           = pmc_id
    self.authors          = authors
    self.journal          = journal
    self.open_access      = open_access
    self.snpedia_open     = snpedia_open
    self.title            = title
    self.abstract         = abstract
    self.pdf_id           = pdf_id
    self.pdf              = pdf
    self.files            = files
    self.associations     = associations

  def __repr__(self):
    return '<Paper: pubmed_id=%s pmc_id=%s authors=%s journal=%s open_access=%s snpedia_open=%s title=%s \
    abstract=%s pdf_id=%s>' \
    % (str(self.pubmed_id), str(self.pmc_id), self.authors, self.journal, self.open_access, self.snpedia_open, \
    self.title, self.abstract, str(self.pdf_id))

class File(Base):
  __tablename__ = 'files'
  id = Column( Integer, primary_key=True, nullable=False, autoincrement=True)
  paper_id        = Column(Integer, ForeignKey('papers.id'))
  paper           = relationship('Paper', primaryjoin='Paper.id==File.paper_id')
  filename        = Column( String(1000) ) # relative to db_dir
  format          = Column( String(5) ) # pdf, excel, tgz

  def __init__(self, id=None, paper_id=None, paper=None, filename=None, format=None):
    self.paper_id         = paper_id
    self.paper            = paper
    self.filename         = filename
    self.format           = format

  def __repr__(self):
    return '<File: paper_id=%s filename=%s format=%s>' % (str(self.paper_id), self.filename, self.format)

class SnpediaEvidence(Base):
  __tablename__ = 'snpedia_evidence'
  id = Column( Integer, primary_key=True, nullable=False, autoincrement=True)
  snp_id          = Column( Integer, ForeignKey('snps.id') )
  paper_id        = Column( Integer, ForeignKey('papers.id') )
  snp             = relationship('SNP')
  paper           = relationship('Paper')
  snpedia_open    = Column( Boolean )
  automatic       = Column( Boolean )

  def __init__(self, id=None, snp_id=None, paper_id=None, snpedia_open=None, automatic=None):
    self.snp_id           = snp_id
    self.paper_id         = paper_id
    self.snp              = snp
    self.paper            = paper
    self.snpedia_open     = snpedia_open
    self.automatic        = automatic

  def __repr__(self):
    return '<SnpediaEvidence: snp_id=%s paper_id=%s snpedia_open=%s automatic=%s>' \
    % (str(self.snp_id), str(self.paper_id), self.snpedia_open, self.automatic)