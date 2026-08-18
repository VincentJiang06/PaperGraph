import pymupdf, classify, renderdiff2 as rd
path='corpus/deepseek-v3.pdf'
doc=pymupdf.open(path); off=classify.off_layer_names(doc)
for c in doc.layer_ui_configs(): doc.set_layer_ui_config(c['number'],action=0)
n=0
for pno,page in enumerate(doc):
    for row in classify.classify_page(page,off):
        if row['channel']!='non_rendered_text' or not row['text'].strip(): continue
        ch,mx,_=rd.ink_delta(path,pno,row['bbox'])
        if rd.verdict(ch,mx)=='INVISIBLE':
            n+=1
            print('TP p%-3s %-40r reasons=%s' % (pno, row['text'][:40], ';'.join(row['reasons'])))
print('total TP', n)
