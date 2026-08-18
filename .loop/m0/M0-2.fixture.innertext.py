#!/usr/bin/env python3
"""Browser-faithful innerText, offline and deterministic.

BeautifulSoup.get_text(" ") inserts a separator at EVERY element boundary, so <sup>[66]</sup>
comes out as ' [ 66 ] ' and '<a>models</a>,' as 'models ,'. A browser does neither: inline
elements concatenate with no separator, and only block-level boxes force a line break.
Modelling that is what makes the "text the human copied" proxy honest.
"""
from bs4 import BeautifulSoup, NavigableString, Tag

BLOCK = {"address","article","aside","blockquote","details","dialog","dd","div","dl","dt",
         "fieldset","figcaption","figure","footer","form","h1","h2","h3","h4","h5","h6",
         "header","hgroup","hr","li","main","nav","ol","p","pre","section","table","tbody",
         "thead","tfoot","tr","td","th","ul","video","caption","body","html"}
SKIP = {"script","style","noscript","template","head","meta","link"}

def inner_text(html):
    soup = BeautifulSoup(html, "lxml")
    out = []

    def walk(node):
        if isinstance(node, NavigableString):
            out.append(str(node))
            return
        if not isinstance(node, Tag):
            return
        name = (node.name or "").lower()
        if name in SKIP:
            return
        if name == "br":
            out.append("\n")
            return
        blk = name in BLOCK
        if blk:
            out.append("\n")
        for c in node.children:
            walk(c)
        if blk:
            out.append("\n")

    walk(soup)
    txt = "".join(out)
    # collapse runs of spaces/tabs the way CSS white-space:normal does, keep line breaks
    lines = [" ".join(l.split()) for l in txt.split("\n")]
    return "\n".join(l for l in lines if l)
