def execute_sql(sql, db, cursor):
    """This executes a passed string via cursor
        :param sql: the query to be executed
        :type sql: string
    """
    try:
        cursor.execute(sql)
        db.commit()
    except db.Error as e:
        # Rollback (undo changes) in case there is any error
        print "Error: rolling back"
        print e
        print sql
        db.rollback()


def query_sql(sql, db, cursor):
    try:
        cursor.execute(sql)
        return cursor.fetchall()
    except:
        print sql
        print "Error: unable to fecth data"
    return None


def insert_sql(table, cols, vals, db, cursor):
    """Attempt to add val to col in table in database via cursor
        :param table: a table in the connected MySQL database
        :type table: string
        :param col: the columns in the selected table
        :type col: string list
        :param vals: the vals, in the same order as the columns, for the table
        :type vals: string list
    """
    sql = "INSERT INTO %s(%s) VALUES ('%s');" % (
            table, ', '.join(cols), '\', \''.join(str(v) for v in vals))
    execute_sql(sql, db, cursor)
