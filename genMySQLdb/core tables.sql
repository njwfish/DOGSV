create table ref_variant (
variant_id tinyint(3) unsigned not null auto_increment comment 'The unique identifier of this variant, used for reference.',
variant varchar(3) not null comment 'Three letter abbreviation of the variant type, used in input and output VCF files.',
unabbreviated varchar(40) not null comment 'The unabbreviated name of this item.',
primary key(variant_id)) comment = 'This is a reference table to TYPE in the records table.';

INSERT INTO ref_variant(variant,unabbreviated) VALUES ('DEL','Deletion');
INSERT INTO ref_variant(variant,unabbreviated) VALUES ('DUP','Duplication');
INSERT INTO ref_variant(variant,unabbreviated) VALUES ('INS','Insertion');
INSERT INTO ref_variant(variant,unabbreviated) VALUES ('INV','Inversion');
INSERT INTO ref_variant(variant,unabbreviated) VALUES ('TRA','Translocation');
INSERT INTO ref_variant(variant,unabbreviated) VALUES ('SIN','SINE');
INSERT INTO ref_variant(variant,unabbreviated) VALUES ('LIN','LINE');
INSERT INTO ref_variant(variant,unabbreviated) VALUES ('BXP','Breakpoint');

create table ref_alignment_location (
location_id smallint(6) unsigned not null auto_increment comment 'The unique identifier of this location, used for reference.',
location varchar(20) not null comment 'The alignment location where the variant is found. Necessary to locate variants, this stores chromosomes and unplaced scaffolds.',
unabbreviated varchar(40) not null comment 'The unabbreviated name of this item.',
primary key(location_id)) comment = 'This is a reference table to CHROM and CHROM2 in the records table.';

create table ref_filter (
filter_id tinyint(3) unsigned not null auto_increment comment 'The unique identifier of this filter, used for reference.',
filter varchar(20) not null comment 'The filter used by whatever tool to determine pass or fail or whatever other metric is being utilized.',
primary key(filter_id)) comment = 'This is a reference table to FILTER in the records table.';

create table records (
CHROM smallint(6) unsigned not null comment 'This is a foreign key to the alignment_location table. This is done to optimize query speed while also dealing with unplaced scaffolds. It represents the chromosome of the POS where this variant was detected.',
POS int(11) unsigned not null comment 'Coordinate where the variant occurs.',
ID int(11) unsigned not null auto_increment comment 'The unique identifier of this record, used for reference.',
REF varchar(20) comment 'The reference allele.',
ALT varchar(50) comment 'The alternative alleles observed in the samples provided during VCF generation.',
QUAL varchar(12) comment 'The Phred-scaled probability that a REF/ALT polymorphism exists at this site given sequencing data. Often missing for structural variants.',
FILTER tinyint(3) unsigned comment 'This field contains the name of any filter that the variant fails to pass, or the value PASS if the variant passed all filters.',
TYPE tinyint(3) unsigned not null comment 'This is a foreign key to the variants table, this setup is used to allow for faster queries.',
CHROM2 smallint(6) unsigned not null comment 'This is a foreign key to the alignment_location table. This is done to optimize query speed while also dealing with unplaced scaffolds. It represents the chromosome of the POS2 where this variant was detected. Mostly only relevant for translocations.',
POS2 int(11) unsigned not null comment 'Either the end of the variant or the position of the translocation on the second chromosome.',
LEN int(11) not null comment 'The length of the structural variant.',
primary key(ID, CHROM, TYPE),
foreign key fk_vaiant(TYPE) references ref_variant(variant_id),
foreign key fk_alignment_location1(CHROM) references ref_alignment_location(location_id),
foreign key fk_alignment_location2(CHROM2) references ref_alignment_location(location_id),
foreign key fk_filter(filter) references ref_filter(filter_id)) comment = 'This is the core of the database. It stores all the records for all the variants.';

DELIMITER $$

  CREATE TRIGGER default_to_CHROM BEFORE INSERT ON records
  FOR EACH ROW BEGIN
    IF (NEW.CHROM2 IS NULL) THEN
          SET NEW.CHROM2 = NEW.CHROM;
    END IF;
  END$$

DELIMITER ;

create table ref_tool (
tool_id tinyint(3) unsigned not null comment 'The unique identifier of this tool, used for reference.',
tool varchar(4) not null comment 'Four letter abbreviation of the tool.',
unabbreviated varchar(40) not null comment 'The unabbreviated name of this item.',
primary key(tool_id)) comment = 'This is a reference table to tool in the tools_used table.';

insert into ref_tool(tool_id, tool, unabbreviated) values (1, 'DLY', 'Delly2');
insert into ref_tool(tool_id, tool, unabbreviated) values (2, 'LMP', 'Lumpy');

create table tools_used (
record_id int(11) unsigned not null comment 'The unique identifier of this record, used for reference.',
tool tinyint(3) unsigned not null comment 'The unique identifier of this tool, used for reference.',
primary key(record_id, tool),
foreign key fk_tool_used_record_id(record_id) references records(ID),
foreign key fk_tool(tool) references ref_tool(tool_id)) comment = 'Stores the tools used to generate or corroborate a given variant.';

create table ref_breed (
breed_id smallint(6) unsigned not null comment 'The unique identifier of this breed, used for reference.',
breed varchar(4) not null comment 'Four letter abbreviation of the breed.',
unabbreviated varchar(40) not null comment 'The unabbreviated name of this item.',
primary key(breed_id)) comment = 'This is a reference table to breed_type in the individuals table.';

create table individuals (
individual_id mediumint(8) unsigned not null auto_increment comment 'The unique identifier of this individual, used for reference.',
breed_type smallint(6) unsigned comment 'The unique identifier of this breed, used for reference.',
sex boolean comment 'The boolean sex of the individual. True is female, false is male.',
disease_status varchar(255) comment 'Information on any diseases the individual might have.',
primary key(individual_id),
foreign key fk_breed(breed_type) references ref_breed(breed_id)) comment = 'Information on the individual from which the sample(s) were collected.';

create table ref_tissue (
tissue_id tinyint(3) unsigned not null comment 'The unique identifier of this tissue type, used for reference.',
tissue varchar(4) not null comment 'Four letter abbreviation of the tissue type.',
unabbreviated varchar(40) not null comment 'The unabbreviated name of this item.',
primary key(tissue_id)) comment = 'This is a reference table to tissue_type in the samples table.';

create table ref_sequencer (
sequencer_id tinyint(3) unsigned not null comment 'The unique identifier of this breed, used for reference.',
sequencer varchar(4) not null comment 'Four letter abbreviation of the sequencing platform.',
unabbreviated varchar(40) not null comment 'The unabbreviated name of this item.',
primary key(sequencer_id)) comment = 'This is a reference table to sequencer in the samples sequencer.';

create table ref_sample (
sample_id mediumint(8) unsigned not null auto_increment comment 'The unique identifier of this samples, used for reference.',
sample varchar(40) not null comment 'The file name of this sample.',
primary key(sample_id)) comment = 'This is a reference table to sample in the sample table.';

create table samples(
sample_id mediumint(8) unsigned not null comment 'The unique identifier of this sample, used for reference.',
individual_id mediumint(8) unsigned not null comment 'The unique identifier of this individual, used for reference.',
tissue_type tinyint(3) unsigned comment 'The unique identifier of this tissue type, used for reference.',
tumor boolean comment 'True if this is a tumor, false if it is not.',
mean_read_depth float comment 'Read  depth of this sample across the genome.',
insert_size smallint(5) unsigned comment 'The length of the make pair library.',
sequencer tinyint(3) unsigned comment 'The unique identifier of this sequencing platform, used for reference.',
mapped_reads int(11) unsigned comment 'Number of reads confidently mapped to the reference genome.',
unmapped_reads int(11) unsigned comment 'Number of reads unable to be mapped to the reference genome.',
primary key(sample_id),
foreign key fk_sample_id(sample_id) references ref_sample(sample_id),
foreign key fk_individual_id(individual_id) references individuals(individual_id),
foreign key fk_tissue(tissue_type) references ref_tissue(tissue_id),
foreign key fk_sequencing(sequencer) references ref_sequencer (sequencer_id)) comment = 'Information on the sample from which the variant calls were generated.';

create table ref_genotype (
genotype_id tinyint(3) unsigned not null comment 'The unique identifier of this genotype, used for reference.',
genotype varchar(3) not null comment 'The three letter code describing the genotype.',
primary key(genotype_id)) comment = 'This is a reference table to GT in the genotypes table.';

insert into ref_genotype(genotype_id,genotype) values (1,'./.');
insert into ref_genotype(genotype_id,genotype) values (2,'0/0');
insert into ref_genotype(genotype_id,genotype) values (3,'0/1');
insert into ref_genotype(genotype_id,genotype) values (4,'1/1');

create table genotype (
sample_id mediumint(8) unsigned not null comment 'The unique identifier of this individual, used for reference.',
record_id int(11) unsigned not null comment 'The unique identifier of this record, used for reference.',
GT tinyint(3) unsigned comment 'The unique identifier of this genotype, used for reference.',
primary key(sample_id, record_id),
foreign key fk_genotype_sample_id(sample_id) references samples(sample_id),
foreign key fk_genotype_record_id(record_id) references records(ID),
foreign key fk_genotype(GT) references ref_genotype(genotype_id)) comment = 'Allows querying of genotype sample data regardless of tool.';

create table ref_gene (
gene_id mediumint(8) unsigned not null comment 'The unique identifier of this individual, used for reference.',
gene_name varchar(16) comment 'The unique identifier of this record, used for reference.',
chrom smallint(6) unsigned not null comment 'This is a foreign key to the alignment_location table. This is done to optimize query speed while also dealing with unplaced scaffolds. It represents the chromosome of this gene.',
pos1 int(11) unsigned not null comment 'Coordinate where the gene starts.',
pos2 int(11) unsigned not null comment 'Coordinate where the gene ends.',
primary key(gene_id, chrom),
foreign key fk_alignment_location1(CHROM) references ref_alignment_location(location_id)) comment = 'Allows checking variant to see if it is inside a genomic feature.';

create table ref_exon (
gene_id mediumint(8) unsigned not null comment 'The unique identifier of this individual, used for reference.',
transcript_id mediumint(8) unsigned not null comment 'The unique identifier of this individual, used for reference.',
exon_id mediumint(8) unsigned not null comment 'The unique identifier of this individual, used for reference.',
chrom smallint(6) unsigned not null comment 'This is a foreign key to the alignment_location table. This is done to optimize query speed while also dealing with unplaced scaffolds. It represents the chromosome of this gene.',
pos1 int(11) unsigned not null comment 'Coordinate where the gene starts.',
pos2 int(11) unsigned not null comment 'Coordinate where the gene ends.',
primary key (transcript_id, exon_id, chrom),
foreign key fk_alignment_location(CHROM) references ref_alignment_location(location_id),
foreign key fk_gene_id(gene_id) references ref_gene(gene_id)) comment = 'Allows checking variant to see if it is inside a genomic feature.';

create table ref_utr (
gene_id mediumint(8) unsigned not null comment 'The unique identifier of this individual, used for reference.',
transcript_id mediumint(8) unsigned not null comment 'The unique identifier of this individual, used for reference.',
utr_id mediumint(8) unsigned not null auto_increment comment 'The unique identifier of this individual, used for reference.',
type tinyint(3) unsigned not null comment 'The unique identifier of this record, used for reference.',
chrom smallint(6) unsigned not null comment 'This is a foreign key to the alignment_location table. This is done to optimize query speed while also dealing with unplaced scaffolds. It represents the chromosome of this gene.',
pos1 int(11) unsigned not null comment 'Coordinate where the gene starts.',
pos2 int(11) unsigned not null comment 'Coordinate where the gene ends.',
primary key(utr_id, transcript_id, type, chrom),
foreign key fk_alignment_location(CHROM) references ref_alignment_location(location_id),
foreign key fk_gene_id(gene_id) references ref_gene(gene_id)) comment = 'Allows checking variant to see if it is inside a genomic feature.';

create table ref_rna (
rna_id varchar(24) not null comment 'The unique identifier of this individual, used for reference.',
known tinyint(3) unsigned not null comment 'Is this a known microrna.',
mature tinyint(3) unsigned not null comment 'Is this a mature microrna (as opposed to precursor).',
chrom smallint(6) unsigned not null comment 'This is a foreign key to the alignment_location table. This is done to optimize query speed while also dealing with unplaced scaffolds. It represents the chromosome of this gene.',
pos1 int(11) unsigned not null comment 'Coordinate where the gene starts.',
pos2 int(11) unsigned not null comment 'Coordinate where the gene ends.',
primary key(rna_id, known, mature, chrom),
foreign key fk_alignment_location1(CHROM) references ref_alignment_location(location_id)) comment = 'Allows checking variant to see if it is inside a genomic feature.';
