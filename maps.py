from MySQL_Utils import query_sql


class Maps:

    def __init__(self, db, cursor, get_id):
        self.sample_mapping = {}
        self.breed_mapping = {}
        self.variant_mapping = {}
        self.alignment_location_mapping = {}
        self.tool_mapping = {}
        self.tool_name_mapping = {}
        self.genotype_mapping = {}
        self.filter_mapping = {}
        self.db = db
        self.cursor = cursor
        self.get_id = get_id

    def gen_breed_map(self):
        sql = "SELECT breed_id, unabbreviated FROM ref_breed"
        breeds = query_sql(sql, self.db, self.cursor)
        for breed in breeds:
            self.breed_mapping.update({breed[self.get_id]: breed[1-self.get_id]})

    def gen_sample_map(self):
        sql = "SELECT sample_id, sample FROM ref_sample"
        samples = query_sql(sql, self.db, self.cursor)
        for sample in samples:
            self.sample_mapping.update({sample[self.get_id]: sample[1-self.get_id]})

    def gen_variant_map(self):
        sql = "SELECT variant_id, variant FROM ref_variant"
        variants = query_sql(sql, self.db, self.cursor)
        for variant in variants:
            self.variant_mapping.update({variant[self.get_id]: variant[1-self.get_id]})

    def gen_alignment_location_map(self):
        sql = "SELECT location_id, location FROM ref_alignment_location"
        locations = query_sql(sql, self.db, self.cursor)
        for location in locations:
            self.alignment_location_mapping.update({location[self.get_id]:location[1-self.get_id]})

    def gen_tool_map(self):
        sql = "SELECT tool_id, tool FROM ref_tool"
        tools = query_sql(sql, self.db, self.cursor)
        for tool in tools:
            self.tool_mapping.update({tool[self.get_id]: tool[1-self.get_id]})

    def gen_tool_name_map(self):
        sql = "SELECT tool, unabbreviated FROM ref_tool"
        tools = query_sql(sql, self.db, self.cursor)
        for tool in tools:
            self.tool_name_mapping.update({tool[self.get_id]: tool[1-self.get_id]})

    def gen_genotype_map(self):
        sql = "SELECT genotype_id, genotype FROM ref_genotype"
        gts = query_sql(sql, self.db, self.cursor)
        for gt in gts:
            self.genotype_mapping.update({gt[self.get_id]: gt[1-self.get_id]})

    def gen_filter_map(self):
        sql = "SELECT filter_id, filter FROM ref_filter"
        filters = query_sql(sql, self.db, self.cursor)
        for f in filters:
            self.filter_mapping.update({f[self.get_id]: f[1-self.get_id]})

    def gen_dicts(self):
        self.gen_breed_map()
        self.gen_sample_map()
        self.gen_variant_map()
        self.gen_alignment_location_map()
        self.gen_tool_map()
        self.gen_tool_name_map()
        self.gen_genotype_map()
        self.gen_filter_map()