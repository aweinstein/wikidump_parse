'''Parsing the wikipedia dump using the SAX model.

Assume the original XML file was split using bzip2recover as in

$ bzip2recover simplewiki-20120313-pages-articles.xml.bz2
$ mv rec*simplewiki-20120313-pages-articles.xml.bz2 split

See http://users.softlab.ece.ntua.gr/~ttsiod/buildWikipediaOffline.html
for the motivation of doing this.
'''
import bz2
import dbm
import os
import sys
import unicodedata
import xml.sax

xml_header = '''
<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.6/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.mediawiki.org/xml/export-0.6/ http://www.mediawiki.org/xml/export-0.6.xsd" version="0.6" xml:lang="en">
'''

def to_ascii(s):
    try:
        s_ascii = unicodedata.normalize('NFKD', s).encode('ascii','ignore')
    except TypeError:
        s_ascii = None
    return s_ascii


class WikiDumpHandler(xml.sax.ContentHandler):
    def __init__(self, db, parse='all', query=False):
        '''
        parse: 'all' parse all the articles
               'query'  
        '''
        xml.sax.ContentHandler.__init__(self)
        self.title_flag = False
        self.text_flag = False
        self.n = 0
        self.db = db 
        self.parse = parse
        self.query = query
        
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
                txt = ' '

            if self.parse == 'all':
                self.db[title] = self.f_name
                if self.n % 1000 == 0:
                    print 'Adding article', self.n
            else:
                if title == self.query:
                    self.answer = txt
            
            self.n += 1

    
def query(query, db):

    try:
        fn = os.path.join('split', db[query])
    except KeyError:
        return None
    
    dump = ''.join(bz2.BZ2File(fn).readlines())

    parser = xml.sax.make_parser()
    sax_handler = WikiDumpHandler(articles_db, 'query', query)
    parser.setContentHandler(sax_handler)
    parser.feed(xml_header)
    parser.feed(dump[dump.index('<page>'):])
    
    return sax_handler.answer

if __name__ == '__main__':
    fn_db = 'articles_block'
    articles_db = dbm.open(fn_db, 'r')
    txt = query('A', articles_db)
    print txt


if __name__ == '__main__x':
    fn_db = 'articles_block'
    articles_db = dbm.open(fn_db, 'n')

    split_dir = 'split'
    
    blocks = ((f, bz2.BZ2File(os.path.join(split_dir, f))) 
              for f in sorted(os.listdir(split_dir)))

    parser = xml.sax.make_parser()
    sax_handler = WikiDumpHandler(articles_db)
    parser.setContentHandler(sax_handler)
    for f_name, block in blocks:
        sax_handler.f_name = f_name
        parser.feed(''.join(block.readlines()))

    print '%d articles added to %s' % (len(articles_db), fn_db)
    articles_db.close()

