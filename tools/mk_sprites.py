import re,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import smallfont as sf
S=os.path.abspath(sys.argv[1]).rstrip('/')+'/'   # carpeta de trabajo
os.makedirs(S+'pages_out',exist_ok=True)
# ---- sprite table
T={}; cur=None
for line in open(S+'spr/list.txt'):
    m=re.match(r'SPR (\S+) ',line)
    if m: cur=m.group(1); continue
    m=re.match(r'\s+F(\d+) page (\d+) src (\d+),(\d+) (\d+)x(\d+)',line)
    if m and cur:
        f,p,sx,sy,w,h=map(int,m.groups()); T[(cur,f)]=(p,sx,sy,w,h)
pages={}
def page(n):
    if n not in pages: pages[n]=Image.open(S+'pages/%d.png'%n).convert('RGBA')
    return pages[n]
def get(name,f):
    p,sx,sy,w,h=T[(name,f)]
    return page(p).crop((sx,sy,sx+w,sy+h))
import numpy as np, json
PK=33
_occ=None; META={}
def alloc(w,h):
    global _occ
    if _occ is None:
        _occ=np.array(page(PK))[:,:,3]>0
    H,W=_occ.shape; m=3
    for y in range(m,H-h-m,2):
        for x in range(m,W-w-m,2):
            if not _occ[y-m:y+h+m,x-m:x+w+m].any():
                _occ[y:y+h,x:x+w]=True; return x,y
    raise Exception('no space')
def put(name,f,img):
    p,sx,sy,w,h=T[(name,f)]
    assert img.size==(w,h),(name,f,img.size,(w,h))
    x,y=alloc(w,h)
    page(PK).paste(img,(x,y))
    META.setdefault(name,{})[f]=[x,y,w,h]
TXT=(162,186,255,255); CLR=(0,0,0,0)

# ---- text on small buttons using font_small
def draw_text(img,lines,cx,tops,color=TXT):
    px=img.load()
    for text,top in zip(lines,tops):
        pix,w=sf.render(text)
        x0=cx-w//2
        for (x,y) in pix:
            px[x0+x,top+y]=color
def clear(img,x0,y0,x1,y1):
    px=img.load()
    for y in range(y0,y1+1):
        for x in range(x0,x1+1): px[x,y]=CLR
def text_sprite(name,rect,lines,tops,cx):
    for f in (0,1):
        im=get(name,f); clear(im,*rect); draw_text(im,lines,cx,tops); put(name,f,im)
# 45x12 buttons: interior x2..42,y2..9 ; centre x=22
text_sprite('spr_control_config_return',(2,2,W:=28,9),['Volver'],[3],15)
text_sprite('spr_control_config_setall_button',(2,2,42,9),['Asignar'],[3],22)
text_sprite('spr_control_config_advanced_button',(2,2,42,9),['Avanzado'],[3],22)
text_sprite('spr_control_config_exit_button',(2,2,42,9),['Guardar'],[3],22)
# disable buttons 77x21: interior x17..74,y2..18 ; centre 46
text_sprite('spr_control_config_disable_lstick',(17,2,74,18),['Desactivar','stick izq.'],[4,12],46)
text_sprite('spr_control_config_disable_dpad',(17,2,74,18),['Desactivar','cruceta'],[4,12],46)
# reset all 62x21: interior x2..59,y2..18
text_sprite('spr_control_config_reset_all',(2,2,59,18),['Restablecer','controles'],[4,11],31)
# test 37x16: interior x2..34,y2..13
text_sprite('spr_controls_config_test',(2,2,34,13),['PROBAR','CONTROL'],[2,8],18)

# ---- title: drop trailing S
for f in range(9):
    im=get('spr_controls_config_title',f); px=im.load(); W,H=im.size
    occ=[any(px[x,y][3]>0 for y in range(H)) for x in range(W)]
    x=W-1
    while not occ[x]: x-=1
    while occ[x]: x-=1      # x = gap col before S
    s0=x+1
    while not occ[x]: x-=1
    end=x+1                 # content end (exclusive) before S
    new=Image.new('RGBA',(W,H),CLR)
    new.paste(im.crop((0,0,end,H)),((W-end)//2,0))
    put('spr_controls_config_title',f,new)

# ---- control labels (spr_control_menu_frame)
BG=(48,81,130,255); SH=(178,16,48,255)
src0=get('spr_control_menu_frame',0); p0=src0.load()
LABEL_COL={'JUMP':(97,162,255,255),'ATTACK':(255,121,48,255),'FLASH':(255,243,146,255),'SWITCH':(73,162,105,255),'START':(227,81,0,255)}
def slot(y0,x,w,c):
    out=[]
    for y in range(y0+2,y0+10):
        r=''
        for xx in range(x,x+w+1):
            p=p0[xx,y]
            r+='#' if p==c else ('+' if p==SH else '.')
        out.append(r)
    return out
JC=LABEL_COL
G={
 'S':slot(96,41,4,JC['START']),'A':slot(60,36,4,JC['ATTACK']),'L':slot(72,20,4,JC['FLASH']),
 'T':slot(96,46,4,JC['START']),'R':slot(96,56,4,JC['START']),'C':slot(60,56,4,JC['ATTACK']),
 'I':slot(72,46,4,JC['FLASH']),'i':slot(84,14,2,JC['SWITCH']),'N':slot(84,61,4,JC['SWITCH']),
 'E':slot(84,41,4,JC['SWITCH']),'M':slot(48,54,6,JC['JUMP']),'O':slot(84,56,4,JC['SWITCH']),
}
G['B']=["###..","#+##.","#+##+","###++","#+##.","#+##+","###..",".+++."]
def build_row(word,color,i4=True):
    cols=[]  # list of columns, each 8 chars
    for ch in word:
        if ch==' ':
            cols += ['........']*2; continue
        g=G['i'] if (ch=='I' and not i4) else G[ch]
        for c in range(len(g[0])): cols.append(''.join(g[r][c] for r in range(8)))
    return cols
ROWS=[(48,'SALTAR','JUMP',True),(60,'ATACAR','ATTACK',True),(72,'LINTERNA','FLASH',True),(84,'CAMBIAR ARMA','SWITCH',False),(96,'INICIO','START',True)]
ORIGX={48:42,60:34,72:13,84:0,96:39}
for f in range(10):
    im=get('spr_control_menu_frame',f); px=im.load()
    for (y0,word,key,i4) in ROWS:
        xo=ORIGX[y0]; Wo=68-xo
        box=im.crop((xo,y0,68,y0+12)); bp=box.load()
        cols=build_row(word,JC[key],i4); w=len(cols)+4; assert w<=68,(word,w)
        # clear old region
        for y in range(y0,y0+12):
            for x in range(xo,68): px[x,y]=CLR
        xl=68-w
        for j in range(w):
            for r in range(12):
                if j<2: c=bp[j,r]
                elif j>=w-2: c=bp[Wo-(w-j),r]
                elif r in (0,1,10,11): c=bp[2,r]
                else:
                    ch=cols[j-2][r-2]
                    c=JC[key] if ch=='#' else (SH if ch=='+' else BG)
                px[xl+j,y0+r]=c
    put('spr_control_menu_frame',f,im)

# ---- pause menu with custom font
GL={
'R':["####.","#...#","#...#","####.","#.#..","#..#.","#...#"],
'M':["#...#","##.##","#.#.#","#...#","#...#","#...#","#...#"],
'S':[".####","#....","#....",".###.","....#","....#","####."],
'e':[".##.","#..#","####","#...",".###"],
'a':[".##.","...#",".###","#..#",".###"],
'n':["###.","#..#","#..#","#..#","#..#"],
'u':["#..#","#..#","#..#","#..#",".###"],
'r':["#.##","##..","#...","#...","#..."],
'd':["...#","...#",".###","#..#","#..#","#..#",".###"],
'p':["###.","#..#","#..#","#..#","###.","#...","#..."],
'l':["##.",".#.",".#.",".#.",".#.",".#.",".##"],
'i':["#",".","#","#","#","#","#"],
}
BASE={k:(len(v)-1) for k,v in GL.items()}
BASE['e']=BASE['a']=BASE['n']=BASE['u']=BASE['r']=4; BASE['p']=4
def render_pause(word):
    # returns list of (x,y_from_baseline(<=0 above), isbase)
    x=0; px=[]
    for ch in word:
        g=GL[ch]; b=BASE[ch]
        for ry,row in enumerate(g):
            for rx,c in enumerate(row):
                if c=='#': px.append((x+rx,ry-b))
        x+=len(g[0])+1
    return px,x-1
for f in range(3):
    im=get('spr_pause_menu_frame',f); px=im.load()
    for top,word in ((59,'Reanudar'),(77,'Mapa'),(95,'Salir')):
        # detect colours
        cnt={}
        rows={}
        for y in range(top+1,top+15):
            for x in range(25,71):
                if px[x,y][3]>0:
                    rows.setdefault(y,{}); rows[y][px[x,y]]=rows[y].get(px[x,y],0)+1
        ys=sorted(rows); first=ys[0]; last=ys[-1]
        light=max(rows[first],key=rows[first].get)
        # dark: most common colour in the last row that has >=3 pixels
        lr=[y for y in ys if sum(rows[y].values())>=3][-1]
        dark=max(rows[lr],key=rows[lr].get)
        for y in range(top+1,top+15):
            for x in range(25,71): px[x,y]=CLR
        pts,w=render_pause(word)
        x0=25+(46-w)//2
        base=top+11
        for (x,dy) in pts:
            col=dark if dy==0 else light
            if dy>0: col=dark
            px[x0+x,base+dy]=col
    put('spr_pause_menu_frame',f,im)

page(PK).save(S+'pages_out/%d.png'%PK)
with open(S+'meta.txt','w') as fh:
    for name,fr in META.items():
        for f,(x,y,w,h) in sorted(fr.items()): fh.write('%s %d %d %d %d %d\n'%(name,f,x,y,w,h))
print('sprites en castellano:',sum(len(v) for v in META.values()),'fotogramas')
