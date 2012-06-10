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


NAMESPACES = ('Wikipedia:', 'File:', 'MediaWiki:', 'Template:', 'Help:',
              'Category:', 'Portal:', 'Book:', 'List of')

def is_namespace(title):
    return any(title.startswith(ns) for ns in NAMESPACES)

class WikiDumpHandler(xml.sax.ContentHandler):
    def __init__(self, db, parse='all', query=False, f=None):
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
        self.answer = None
        self.f = f
        self.rejected = ['foo']

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
            title = to_ascii(''.join(self.title))
            self.title = title

        if name == 'text':
            self.text_flag = False
            txt = to_ascii(''.join(self.text))

            if txt is None:
                txt = ' '

            if self.parse == 'all' and not is_namespace(self.title) \
                and txt.count('#REDIRECT') == 0 \
                and txt.count('#redirect') == 0 \
                and self.title.count('(disambiguation)') == 0:
                #try:
                self.db[self.title] = self.f_name[3:8]
                #except dbm.error:
                #    print 'Error adding %s -> %s' % (self.title, self.f_name)
                #    self.rejected.append(self.title)
                self.f.write('%s, %s\n' % (self.title, self.f_name[3:8]))
                if self.n % 1000 == 0:
                    print 'Adding article', self.n

            if self.parse == 'query':
                if self.title == self.query:
                    self.answer = txt
            
            self.n += 1


def make_db():
    fn_db = 'articles_block'
    articles_db = dbm.open(fn_db, 'n')

    split_dir = 'split'
    blocks = ((f, bz2.BZ2File(os.path.join(split_dir, f))) 
              for f in sorted(os.listdir(split_dir))[:1000])

    f = open('list.txt', 'w')
    parser = xml.sax.make_parser()
    sax_handler = WikiDumpHandler(articles_db, f=f)
    parser.setContentHandler(sax_handler)
    for f_name, block in blocks:
        sax_handler.f_name = f_name
        parser.feed(''.join(block.readlines()))
    f.close()
    print '%d articles added to %s' % (len(articles_db), fn_db)
    articles_db.close()
    
    f = open('rejected.txt','w')
    f.write('\n'.join(sax_handler.rejected))
    print 'Rejected:'
    print sax_handler.rejected
    f.close()

def query(query, db):

    try:
        block = db[query]
    except KeyError:
        return None

    parser = xml.sax.make_parser()
    sax_handler = WikiDumpHandler(articles_db, 'query', query)
    parser.setContentHandler(sax_handler)
    parser.feed(xml_header)

    n = 0
    while n < 3:
        fn = os.path.join('split', block)
        dump = ''.join(bz2.BZ2File(fn).readlines())

        if n == 0:
            parser.feed(dump[dump.index('<page>'):])
        else:
            parser.feed(dump)
            
        if sax_handler.answer:
            return sax_handler.answer
        n += 1

        block = block[:3] + ('%05d' % (int(block[3:8]) + 1)) + block[8:]
        
        

if __name__ == '__main__x':
    fn_db = 'articles_block'
    articles_db = dbm.open(fn_db, 'r')

    #print query('April', articles_db)
    
    txt = query('Ethnic group', articles_db)
    txt = query('Microsoft', articles_db)
    print txt

if __name__ == '__main__':
    make_db()



