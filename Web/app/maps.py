from MySQL_Utils import executeSQL, querySQL, insertSQL

class Maps:

	def __init__(self, db, cursor):
		self.sample_mapping = {}
		self.breed_mapping = {}
		self.variant_mapping = {}
		self.alignment_location_mapping = {}
		self.tool_mapping = {}
		self.tool_name_mapping = {}
		self.genotype_mapping = {}
		self.db = db
		self.cursor = cursor

	def genBreedMap(self):
		sql = "SELECT breed_id, unabbreviated FROM ref_breed"
		breeds = querySQL(sql, self.db, self.cursor)
		for breed in breeds:
			self.breed_mapping.update({breed[1]:breed[0]})

	def genSampleMap(self):
		sql = "SELECT sample_id, sample FROM ref_sample"
		samples = querySQL(sql, self.db, self.cursor)
		for sample in samples:
			self.sample_mapping.update({sample[1]:sample[0]})

	def genVariantMap(self):
		sql = "SELECT variant_id, type FROM ref_variant"
		variants = querySQL(sql, self.db, self.cursor)
		for variant in variants:
			self.variant_mapping.update({variant[1]:variant[0]})
			

	def genAlignmentLocationMap(self):
		sql = "SELECT location_id, type FROM ref_alignment_location"
		locations = querySQL(sql, self.db, self.cursor)
		for location in locations:
			self.alignment_location_mapping.update({location[1]:location[0]})

	def genToolMap(self):
		sql = "SELECT tool_id, tool FROM ref_tool"
		tools = querySQL(sql, self.db, self.cursor)
		for tool in tools:
			self.tool_mapping.update({tool[1]:tool[0]})

	def genToolNameMap(self):
		sql = "SELECT tool, unabbreviated FROM ref_tool"
		tools = querySQL(sql, self.db, self.cursor)
		for tool in tools:
			self.tool_name_mapping.update({tool[1]:tool[0]})

	def genGenotypeMap(self):
		sql = "SELECT genotype_id, genotype FROM ref_genotype"
		gts = querySQL(sql, self.db, self.cursor)
		for gt in gts:
			self.genotype_mapping.update({gt[1]:gt[0]})

	def genDicts(self):
		self.genBreedMap()
		self.genSampleMap()
		self.genVariantMap()
		self.genAlignmentLocationMap()
		self.genToolMap()
		self.genToolNameMap()
		self.genGenotypeMap()