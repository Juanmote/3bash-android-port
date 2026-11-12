import re,sys,os
from PIL import Image
S=os.path.abspath(sys.argv[1]).rstrip('/')+'/'
_tex=Image.open(S+'fg/font_small_tex.png').convert('RGBA')
_g={}
_on=False
for line in open(S+'fg/list.txt'):
    if line.startswith('FONT '):
        _on = line.startswith('FONT font_small ')
        continue
    if _on:
        m=re.match(r'\s+G (\d+) (\d+),(\d+) (\d+)x(\d+) shift (\d+) off (-?\d+)',line)
        if m:
            c,sx,sy,w,h,sh,off=map(int,m.groups())
            _g[c]=(sx,sy,w,h,sh,off)
def glyph(ch):
    sx,sy,w,h,sh,off=_g[ord(ch)]
    pix=set()
    for y in range(h):
        for x in range(w):
            if _tex.getpixel((sx+x,sy+y))[3]>128: pix.add((x+off,y))
    return pix,sh
def render(text):
    """returns set of (x,y) pixels, width (px), height 5"""
    out=set(); x=0
    for ch in text:
        if ch==' ': x+=4; continue
        p,sh=glyph(ch)
        for (a,b) in p: out.add((a+x,b))
        x+=sh
    return out,x-1
