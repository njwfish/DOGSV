import os, sys
import pickle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cement.core.foundation import CementApp
from cement.core.controller import CementBaseController, expose
import tabulate
import MySQLdb
import re
import Query
import VCFQuery


class DOGSVController(CementBaseController):
    class Meta:
        label = 'base'
        description = "Interface to a DOGSV database."

    @expose(hide=True)
    def default(self):
        self.app.log.info('Inside MyBaseController.default()')


class QueryController(CementBaseController):
    class Meta:
        label = 'query'
        stacked_on = 'base'
        stacked_type = 'embedded'
        description = "Interface to query an instance of a DOGSV database."
        arguments = \
            [
                (['-c', '--columns'], dict(action='store', help='Columns to display from query.')),
                (['--requirements'], dict(nargs='+', action='store', help='SQL formatted where clause.')),
                (['-n', '--lines'], dict(action='store', help='Number of rows to print, default 500.')),
                (['-q', '--query'], dict(action='store', help='Previous query id, used for sub querying.')),
                (['-s', '--sub'], dict(action='store', help='Binary value (0, 1), where 1 means subquery, only use if this is a query that has been run using the cli beofre.')),

            ]

    @expose(hide=True)
    def query(self):
        self.app.log.info('Inside query.query()')
        columns = self.app.pargs.columns
        table = 'records'
        requirements = self.app.pargs.requirements
        joins = None
        curr = None
        if requirements is not None:
            print requirements
            column_tables = [col.split('.') for col in columns.split(',')]
            requirements = [req.split(',') for req in requirements]
            print requirements
            joins = ['inner join {0} on records.id=record_id'.format(table)
                     for table, _ in requirements + column_tables if table != 'records']
            requirements = ['{0}.{1}'.format(table, field) for table, field in requirements]
            if table is not None:
                curr = Query.Query(columns, table, joins, requirements, None)
            else:
                if self.app.pargs.sub == '1':
                    with open("tmp/{0}.p".format(self.app.pargs.query), "r") as pfile:
                        curr_vars = pickle.load(pfile)
                        curr = Query.Query(*curr_vars)
                    curr.sub_query(columns, joins, requirements)
                else:
                    curr = Query.Query(columns, table, joins, requirements, None, tid=self.app.pargs.query)
        if curr is None:
            return
        results, fields = curr.get_results()
        with open("tmp/{0}.p".format(curr.tid), "w") as pfile:
            curr_vars = (curr.columns, curr.table, curr.joins, curr.requirements,
                         curr.order, curr.process, curr.process_vars, curr.tid)
            pickle.dump(curr_vars, pfile, protocol=pickle.HIGHEST_PROTOCOL)
        self.app.render(results, headers=fields)
        print curr.tid


class ExportController(CementBaseController):
    class Meta:
        label = 'export'
        stacked_on = 'base'
        stacked_type = 'embedded'
        description = "Export a table."
        arguments = \
            [
                (['-t', '--table'], dict(action='store', help='The query id of the query to subquery.')),
                (['-o', '--outfile'], dict(action='store', help='The name of the file to write to.')),
                (['-p', '--prefix'], dict(action='store', help='Binary value (0, 1), 1 includes chr before the '
                                                               'chromosome number, like chrX, 0 does not.')),
                (['-i', '--info'], dict(action='store', help='Binary value (0, 1), 1 includes all of the info fields, '
                                                             'across all tools, 0 is only the core fields.')),

            ]

    @expose(hide=True)
    def export(self):
        with open("tmp/{0}.p".format(self.app.pargs.table), "r") as pfile:
            curr_vars = pickle.load(pfile)
            curr = Query.Query(*curr_vars)
            print pfile
        output, prefix_chrom, all_info = self.app.pargs.outfile, self.app.pargs.prefix, self.app.pargs.info

        VCFQuery.VCFQuery(curr, 'tmp/', output, prefix_chrom, all_info).sql_to_vcf()


class QueryInterface(CementApp):
    class Meta:
        label = 'interface'
        base_controller = 'base'
        extensions = ['tabulate']
        output_handler = 'tabulate'
        handlers = [DOGSVController, QueryController, ExportController]


with QueryInterface() as interface:
    interface.run()
