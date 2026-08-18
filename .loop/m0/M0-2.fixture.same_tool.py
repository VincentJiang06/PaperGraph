# Control: sample quotes from the SAME extraction the gate compares against (what
# 01-CONTRACTS §8.6.2.1 actually specifies: judgement happens inside the fetch tool over
# the full extracted text). If this is not 100%, the guarantee is broken on its own terms.
import random, re, pymupdf, norm, quote_pdf2
SEED=20260817; N=120
for spec in ["attention.pdf=EN-attention","corpus/bert.pdf=EN-bert","corpus/qwen2.pdf=EN-qwen2",
             "corpus/deepseek-v3.pdf=EN-deepseek","corpus/jos6712.pdf=ZH-jos6712",
             "corpus/jos6890.pdf=ZH-jos6890","corpus/jos7000.pdf=ZH-jos7000"]:
    path,label=spec.split("=")
    snap="\n".join(p.get_text() for p in pymupdf.open(path))
    rnd=random.Random(SEED)
    qs=quote_pdf2.sample_quotes(snap,N,rnd)     # quotes copied OUT OF our own extraction
    ok_raw=sum(1 for q in qs if q in snap)
    ok_v1=sum(1 for q in qs if norm.quote_faithful(q,snap,True,norm.compare_key))
    ok_v3=sum(1 for q in qs if norm.quote_faithful(q,snap,True,norm.compare_key_v3))
    print("%-20s n=%-4s | raw=%6.1f%% | as_written=%6.1f%% | fix_adjacent_cjk=%6.1f%%"
          % (label,len(qs),100.0*ok_raw/len(qs),100.0*ok_v1/len(qs),100.0*ok_v3/len(qs)))
