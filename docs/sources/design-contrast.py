# Contrast check for design.md tokens. Method copied from /workspace/ui-review/ds/tokens.py
import math, json
def oklch_to_srgb(L,C,H):
    h=math.radians(H); a=C*math.cos(h); b=C*math.sin(h)
    l_=L+0.3963377774*a+0.2158037573*b
    m_=L-0.1055613458*a-0.0638541728*b
    s_=L-0.0894841775*a-1.2914855480*b
    l,m,s=l_**3,m_**3,s_**3
    r= 4.0767416621*l-3.3077115913*m+0.2309699292*s
    g=-1.2684380046*l+2.6097574011*m-0.3413193965*s
    bb=-0.0041960863*l-0.7034186147*m+1.7076147010*s
    return (r,g,bb)
def in_gamut(lin): return all(-1e-4<=c<=1+1e-4 for c in lin)
def fit(L,C,H):
    # reduce chroma until in gamut
    c=C
    while not in_gamut(oklch_to_srgb(L,c,H)) and c>0: c-=0.001
    return oklch_to_srgb(L,c,H), c
def enc(x):
    x=min(max(x,0),1)
    return 12.92*x if x<=0.0031308 else 1.055*x**(1/2.4)-0.055
def hexof(lin): return '#'+''.join(f'{round(enc(c)*255):02x}' for c in lin)
def lum_lin(lin):
    # luminance from linear clipped (use re-quantized 8-bit for realism)
    vals=[round(enc(c)*255)/255 for c in lin]
    def dec(v): return v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4
    r,g,b=[dec(v) for v in vals]
    return 0.2126*r+0.7152*g+0.0722*b
def hexlum(h):
    h=h.lstrip('#'); vals=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    def dec(v): return v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4
    r,g,b=[dec(v) for v in vals]; return 0.2126*r+0.7152*g+0.0722*b
def cr(l1,l2):
    a,b=max(l1,l2),min(l1,l2); return (a+0.05)/(b+0.05)


# Compliance copilot tokens. Neutral hue 255 (cool slate), accent indigo 272.
N=255
T={
 'light':{
  'bg':(0.985,0.002,N),'surface':(1.0,0,N),'surface-2':(0.968,0.004,N),'surface-3':(0.94,0.006,N),
  'border':(0.91,0.006,N),'border-strong':(0.62,0.012,N),
  'text':(0.21,0.015,N),'text-secondary':(0.40,0.015,N),'text-muted':(0.50,0.014,N),
  'accent':(0.50,0.17,272),'accent-hover':(0.44,0.16,272),'accent-fg':(0.99,0.003,272),
  'accent-text':(0.49,0.17,272),'accent-subtle':(0.955,0.025,272),'accent-subtle-fg':(0.40,0.15,272),
  'focus':(0.55,0.17,272),
  'critical':(0.50,0.19,25),'critical-solid':(0.50,0.19,25),'critical-on-solid':(0.99,0,0),'critical-subtle':(0.96,0.022,25),'critical-hl':(0.92,0.05,25),
  'high':(0.52,0.15,45),'high-solid':(0.55,0.16,45),'high-on-solid':(0.99,0,0),'high-subtle':(0.962,0.025,50),'high-hl':(0.92,0.06,55),
  'medium':(0.50,0.11,75),'medium-subtle':(0.965,0.04,90),'medium-hl':(0.93,0.08,92),
  'low':(0.50,0.10,220),'low-subtle':(0.962,0.02,220),'low-hl':(0.925,0.045,220),
  'info':(0.46,0.02,N),'info-subtle':(0.955,0.006,N),
  'success':(0.48,0.12,150),'success-subtle':(0.96,0.03,150),
  'pending':(0.46,0.02,N),'pending-subtle':(0.96,0.006,N),
  'ai-tint':(0.97,0.012,300),
 },
 'dark':{
  'bg':(0.16,0.008,N),'surface':(0.20,0.010,N),'surface-2':(0.235,0.011,N),'surface-3':(0.275,0.012,N),
  'border':(0.31,0.012,N),'border-strong':(0.56,0.015,N),
  'text':(0.965,0.004,N),'text-secondary':(0.82,0.010,N),'text-muted':(0.72,0.012,N),
  'accent':(0.76,0.13,272),'accent-hover':(0.82,0.11,272),'accent-fg':(0.18,0.04,272),
  'accent-text':(0.78,0.12,272),'accent-subtle':(0.29,0.06,272),'accent-subtle-fg':(0.88,0.07,272),
  'focus':(0.78,0.12,272),
  'critical':(0.74,0.15,25),'critical-solid':(0.70,0.17,25),'critical-on-solid':(0.17,0.03,25),'critical-subtle':(0.28,0.06,25),'critical-hl':(0.34,0.08,25),
  'high':(0.78,0.13,50),'high-solid':(0.76,0.14,50),'high-on-solid':(0.17,0.03,50),'high-subtle':(0.28,0.05,50),'high-hl':(0.34,0.07,50),
  'medium':(0.84,0.13,85),'medium-subtle':(0.28,0.05,80),'medium-hl':(0.35,0.07,85),
  'low':(0.80,0.10,220),'low-subtle':(0.28,0.04,220),'low-hl':(0.34,0.06,220),
  'info':(0.80,0.015,N),'info-subtle':(0.27,0.012,N),
  'success':(0.80,0.15,150),'success-subtle':(0.27,0.05,150),
  'pending':(0.80,0.015,N),'pending-subtle':(0.27,0.012,N),
  'ai-tint':(0.23,0.025,300),
 }}
PAIRS=[]
for bg in ['bg','surface','surface-2','surface-3']:
    PAIRS+= [('text',bg,'body'),('text-secondary',bg,'body'),('text-muted',bg,'body')]
PAIRS+=[('accent-fg','accent','body'),('accent-fg','accent-hover','body'),('accent-text','bg','body'),('accent-text','surface','body'),
 ('accent-subtle-fg','accent-subtle','body'),('text','accent-subtle','body')]
for s in ['critical','high','medium','low','info','success','pending']:
    PAIRS+=[(s,'bg','body'),(s,'surface','body'),(s,s+'-subtle','body'),('text',s+'-subtle','body')]
for s in ['critical','high','medium','low']:
    PAIRS+=[('text',s+'-hl','body')]
PAIRS+=[('critical-on-solid','critical-solid','body'),('high-on-solid','high-solid','body')]
PAIRS+=[('text','ai-tint','body'),('text-secondary','ai-tint','body')]
# non-text 3:1: focus ring, strong borders, severity icons/shape markers on surfaces, highlight underline vs surface
for bg in ['bg','surface','surface-2','surface-3','accent-subtle']:
    PAIRS.append(('focus',bg,'ui'))
PAIRS+=[('border-strong','bg','ui'),('border-strong','surface','ui'),('accent','surface','ui'),
 ('critical-solid','surface','ui'),('high-solid','surface','ui')]
for s in ['critical','high','medium','low']:
    PAIRS.append((s,s+'-hl','ui'))  # underline/edge marker vs its own highlight
out={}
for theme,toks in T.items():
    res={}
    for k,(L,C,H) in toks.items():
        lin,c=fit(L,C,H)
        res[k]={'oklch':f'oklch({L*100:.1f}% {c:.3f} {H})','hex':hexof(lin),'lum':lum_lin(lin)}
    out[theme]=res
rows=[];fails=[]
for theme in T:
    for fg,bg,kind in PAIRS:
        r=cr(out[theme][fg]['lum'],out[theme][bg]['lum']); need=4.5 if kind=='body' else 3.0
        rows.append((theme,fg,bg,kind,round(r,2),need,r>=need))
        if r<need: fails.append(rows[-1])
json.dump({'tokens':out,'rows':rows},open('design-contrast.json','w'),indent=1)
print(len(rows),'pairs; fails:',len(fails))
for f in fails: print(f)
for th in ['light','dark']:
  for k in ['body','ui']:
    r=[x for x in rows if x[0]==th and x[3]==k]; print(th,k,min(r,key=lambda x:x[4]))
