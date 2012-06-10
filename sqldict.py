import sqlite3
from UserDict import DictMixin

def get_db_connection(file_name):
    dt = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    conn = sqlite3.connect(file_name, detect_types=dt)
    return conn

def create_db(file_name):
    conn = get_db_connection(file_name)
    c = conn.cursor()

    table_name = 'keyvalues'
    c.execute("SELECT name FROM sqlite_master WHERE "
              "type='table' AND name=?", (table_name,))
    if c.fetchone():
        c.execute('drop table %s' % table_name)
        print 'Table %s dropped.' % table_name
    #c.execute('create table keyvalues (key text primary key, value text)')
    c.execute('create table keyvalues (key text, value text)')
    print 'Table %s created.' % table_name
    conn.commit()
    c.close()
    print 'Create database %s.' % file_name
    
class SQLDict(DictMixin):
    def __init__(self, db_connector):
        self.conn = db_connector

    def __getitem__(self, item):
        c = self.conn.cursor()
        c.execute("select value from keyvalues where key=?", (item,))
        value = c.fetchone()
        c.close()
        if value:
            return value[0]
        else:
            raise KeyError('Key %s does not exist' % item)
    
    def __setitem__(self, item, value):
        c = self.conn.cursor()
        c.execute("insert into keyvalues values (?,?)", (item, value))
        self.conn.commit()
        c.close()
        
    def __delitem__(self, item):
        c = self.conn.cursor()
        c.execute('delete from keyvalues where key=?', item)
        self.conn.commit()
        c.close()
        
    def keys(self):
        c = self.conn.cursor()
        c.execute('select key from keyvalues')
        keys = c.fetchall()
        c.close()
        return [keys[0] for keys in keys]
    
if __name__ == '__main__':
    print 'Testing sqlite3 based dictionary'
    db_file_name = 'articles.sqlite'
    create_db(db_file_name)
    conn = get_db_connection(db_file_name)
    d = SQLDict(conn)
    d['a'] = 'hola'
    d['b'] = 'chao'
    print d['a']
    try:
        print d['c']
    except KeyError:
        print 'Key does not exist'
    
    print d.keys()
    del d['a']
    print d.keys()
