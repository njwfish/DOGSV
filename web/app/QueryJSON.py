from flask.json import JSONEncoder, JSONDecoder
from Query import Query


def decode_query(d):
    # This is a really weird if statement, but otherwise it throws an error
    necessary_vars = {'columns', 'table', 'joins', 'requirements', 'order', 'tid', 'process', 'process_vars'}
    if necessary_vars > set(d.keys()):
        return d
    query = Query(d['columns'], d['table'], d['joins'], d['requirements'], d['order'],
                  process=d['process'], process_vars=d['process_vars'], tid=d['tid'])
    return query


def encode_query(obj):
    query_dict = {
        'columns': obj.columns,
        'table': obj.table,
        'joins': obj.joins,
        'requirements': obj.requirements,
        'order': obj.order,
        'tid': obj.tid,
        'process': obj.process,
        'process_vars': obj.process_vars
    }
    return query_dict


class QueryJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Query):
            return encode_query(obj)
        else:
            JSONEncoder.default(self, obj)


class QueryJSONDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        self.orig_obj_hook = kwargs.pop("object_hook", None)
        super(QueryJSONDecoder, self).__init__(*args, object_hook=self.query_obj_hook, **kwargs)

    def query_obj_hook(self, d):
        # Calling custom decode function:
        if 'query' in d:
            d['query'] = decode_query(d['query'])
            return d
        if self.orig_obj_hook:  # Do we have another hook to call?
            return self.orig_obj_hook(d)  # Yes: then do it
        return d  # No: just return the decoded dict
