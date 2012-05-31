'''Parsing the wikipedia dump using the SAX model.'''
import bz2
import sys
import unicodedata
import xml.sax

import dbm
import shelve

def to_ascii(s):
    try:
        s_ascii = unicodedata.normalize('NFKD', s).encode('ascii','ignore')
    except TypeError:
        s_ascii = None
    return s_ascii


class WikiDumpHandler(xml.sax.ContentHandler):
    def __init__(self, db):
        xml.sax.ContentHandler.__init__(self)
        self.title_flag = False
        self.text_flag = False
        self.n = 0
        self.db = db
        
    def startElement(self, name, attrs):
        if name == 'title':
            self.title_flag = True
            self.title = []
        if name == 'text':
            self.text_flag = True
            self.text = []

    def characters(self, content):
        if self.title_flag :
            self.title.append(content)

        if self.text_flag:
            self.text.append(content)

    def endElement(self, name):
        if name == 'title':
            self.title_flag = False
        if name == 'text':
            self.text_flag = False
            title = to_ascii(''.join(self.title))
            txt = to_ascii(''.join(self.text))

            if title is None or txt is None:
                print title
                print txt
                txt = ' '
                
            self.db[title] = txt
            
            self.n += 1

            if self.n % 1000 == 0:
                print 'Adding article', self.n

                 
if __name__ == '__main__':
    fn_db = 'articles'
    articles_db = dbm.open(fn_db, 'c')
    
    fn = 'simplewiki-20120313-pages-articles.xml.bz2'
    parser = xml.sax.make_parser()
    parser.setContentHandler(WikiDumpHandler(articles_db))
    parser.parse(bz2.BZ2File(fn))

    print '%d articles added to %s' % (len(articles_db), fn_db)
    articles_db.close()
