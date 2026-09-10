"""此板專用格點佈線；結果必須再通過 KiCad DRC，不能代替製造檢查。"""
from pathlib import Path
import heapq, math, json
import pcbnew as p

ROOT=Path(__file__).resolve().parent
b=p.LoadBoard(str(ROOT/'unrouted.kicad_pcb'))
mm=p.FromMM
v=lambda x,y:p.VECTOR2I(mm(x),mm(y))
STEP=.05; N=801; TOTAL=N*N
CLEAR=.22
layers=[p.F_Cu,p.B_Cu]
netobjects={n.GetNetname().removeprefix('/'):n for n in b.GetNetInfo().NetsByNetcode().values() if n.GetNetCode()}
pads=[]; tracks=[]; vias=[]; points={}; padlookup={}
def cell(x,y):return (round(x/STEP),round(y/STEP))
def index(x,y):return y*N+x
for fp in b.GetFootprints():
    for pad in fp.Pads():
        x,y=p.ToMM(pad.GetPosition().x),p.ToMM(pad.GetPosition().y)
        w,h=p.ToMM(pad.GetSize().x),p.ToMM(pad.GetSize().y)
        if round(pad.GetOrientationDegrees())%180: w,h=h,w
        net=pad.GetNetname().removeprefix('/')
        ls=[i for i,l in enumerate(layers) if pad.IsOnLayer(l)]
        drill=max(p.ToMM(pad.GetDrillSize().x),p.ToMM(pad.GetDrillSize().y))
        pads.append((net,x,y,w,h,ls,drill))
        padlookup[fp.GetReference(),pad.GetNumber()]=(x,y)
        if net:points.setdefault(net,set()).update((*cell(x,y),l) for l in ls)

def addtrack(net,xy,width=.25,layer=0):
    for a,z in zip(xy,xy[1:]):
        if math.dist(a,z)<1e-7:continue
        t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*z));t.SetWidth(mm(width));t.SetLayer(layers[layer]);t.SetNet(netobjects[net]);b.Add(t)
        tracks.append((net,*a,*z,width,layer))

# WSON 0.5mm 腳距處短距離細線引出，再加寬馬達主幹。
escape={
 ('U3','1'):('VCC',[(22.65,19.75),(22.65,20.65)]),
 ('U3','8'):('VCC',[(20.75,19.75),(20.75,20.7)]),
 ('U3','7'):('VCC',[(20.75,19.25),(19.8,19.25),(19.8,20.2),(20.3,20.7),(20.75,20.7)]),
 ('U3','2'):('M2',[(22.65,19.25),(23.6,19.25),(23.85,19.5)]),
 ('U3','3'):('M1',[(22.65,18.75),(24.5,18.75)]),
}
# 與 F 版保持同方向封裝，將引出線隨 U3 平移。
escape={key:(net,[(round(x+9.3,4),round(y+1,4)) for x,y in xy])
        for key,(net,xy) in escape.items()}
escape['U3','2']=('M2',[(31.95,20.25),(32.9,20.25),(33.15,20.5),(33.15,21.5)])
escape['U3','6']=('REV',[(30.05,19.75),(28.8,19.75),(28.55,19.5)])
for key,(net,xy) in escape.items():
    assert math.dist(padlookup[key],xy[0])<.001,(key,padlookup[key])
    addtrack(net,xy,.2)
    points[net].discard((*cell(*xy[0]),0));points[net].add((*cell(*xy[-1]),0))

def rectangle(mask,x,y,w,h,extra):
    x0=max(0,math.ceil((x-w/2-extra)/STEP));x1=min(N-1,math.floor((x+w/2+extra)/STEP))
    y0=max(0,math.ceil((y-h/2-extra)/STEP));y1=min(N-1,math.floor((y+h/2+extra)/STEP))
    for iy in range(y0,y1+1):mask[iy*N+x0:iy*N+x1+1]=b'\1'*(x1-x0+1)

def capsule(mask,ax,ay,bx,by,radius):
    x0=max(0,math.ceil((min(ax,bx)-radius)/STEP));x1=min(N-1,math.floor((max(ax,bx)+radius)/STEP))
    y0=max(0,math.ceil((min(ay,by)-radius)/STEP));y1=min(N-1,math.floor((max(ay,by)+radius)/STEP))
    dx,dy=bx-ax,by-ay;length=dx*dx+dy*dy
    for iy in range(y0,y1+1):
        y=iy*STEP
        for ix in range(x0,x1+1):
            x=ix*STEP
            t=min(1,max(0,((x-ax)*dx+(y-ay)*dy)/length)) if length else 0
            if (x-ax-t*dx)**2+(y-ay-t*dy)**2<=radius*radius:mask[index(ix,iy)]=1

def masks(net,width):
    blocked=[bytearray(TOTAL),bytearray(TOTAL)];vm=[bytearray(TOTAL),bytearray(TOTAL)]
    for target,radius in [(blocked,width/2),(vm,.3)]:
        margin=math.ceil((.31+radius)/STEP)
        for mask in target:
            for iy in range(N):
                if iy<margin or iy>=N-margin:mask[iy*N:(iy+1)*N]=b'\1'*N
                else:mask[iy*N:iy*N+margin]=b'\1'*margin;mask[(iy+1)*N-margin:(iy+1)*N]=b'\1'*margin
        for other,x,y,w,h,ls,drill in pads:
            if other!=net:
                for l in ls:rectangle(target[l],x,y,w,h,CLEAR+radius)
            if target is vm:
                # 避免過孔落在 SMD 焊盤或任何現有鑽孔上。
                for mask in target:rectangle(mask,x,y,max(w,drill),max(h,drill),.3 if drill else .1)
        for other,ax,ay,bx,by,w,l in tracks:
            if other!=net:capsule(target[l],ax,ay,bx,by,w/2+CLEAR+radius)
        for other,x,y in vias:
            if other!=net:
                for mask in target:capsule(mask,x,y,x,y,.3+CLEAR+radius)
            if target is vm:
                for mask in target:capsule(mask,x,y,x,y,.56)
    via_mask=bytearray(a|z for a,z in zip(*vm))
    return blocked,via_mask

DIRS=[(1,0,10),(1,1,14),(0,1,10),(-1,1,14),(-1,0,10),(-1,-1,14),(0,-1,10),(1,-1,14)]
def route(start,goal,blocked,via_mask):
    sx,sy,sl=start;gx,gy,gl=goal
    if blocked[sl][index(sx,sy)] or blocked[gl][index(gx,gy)]:
        print('端點受阻',start,blocked[sl][index(sx,sy)],goal,blocked[gl][index(gx,gy)],flush=True)
        return None
    def heuristic(x,y,l):
        dx,dy=abs(x-gx),abs(y-gy)
        return 10*max(dx,dy)+4*min(dx,dy)+(80 if l!=gl else 0)
    first=(sx,sy,sl,8);queue=[(heuristic(sx,sy,sl),0,first)];cost={first:0};parent={}
    while queue:
        _,g,state=heapq.heappop(queue)
        if g!=cost[state]:continue
        x,y,l,direction=state
        if (x,y,l)==goal:
            path=[state]
            while state in parent:state=parent[state];path.append(state)
            return [(x,y,l) for x,y,l,d in reversed(path)]
        for nd,(dx,dy,stepcost) in enumerate(DIRS):
            # 相鄰銅線最多轉 45 度，沒有尖角或直角轉彎。
            if direction<8 and min((nd-direction)%8,(direction-nd)%8)>1:continue
            nx,ny=x+dx,y+dy
            if not 0<nx<N-1 or not 0<ny<N-1:continue
            if blocked[l][index(nx,ny)]:continue
            if dx and dy and (blocked[l][index(nx,y)] or blocked[l][index(x,ny)]):continue
            ns=(nx,ny,l,nd);ng=g+stepcost+(2 if direction!=nd else 0)
            if ng<cost.get(ns,10**12):
                cost[ns]=ng;parent[ns]=state;heapq.heappush(queue,(ng+heuristic(nx,ny,l),ng,ns))
        if not via_mask[index(x,y)] and not blocked[1-l][index(x,y)]:
            ns=(x,y,1-l,8);ng=g+180
            if ng<cost.get(ns,10**12):
                cost[ns]=ng;parent[ns]=state;heapq.heappush(queue,(ng+heuristic(x,y,1-l),ng,ns))
    return None

def output(net,path,width):
    for a,z in zip(path,path[1:]):
        if a[2]!=z[2]:
            x,y=a[0]*STEP,a[1]*STEP
            t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetWidth(mm(.6));t.SetDrill(mm(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(*layers);t.SetNet(netobjects[net]);b.Add(t);vias.append((net,x,y))
    run=[path[0]]
    for item in path[1:]:
        if item[2]!=run[-1][2]:
            addtrack(net,[(x*STEP,y*STEP) for x,y,l in run],width,run[0][2]);run=[item];continue
        if len(run)>1:
            a,z=run[-2],run[-1]
            if (z[0]-a[0])*(item[1]-z[1])==(z[1]-a[1])*(item[0]-z[0]):run.pop()
        run.append(item)
    addtrack(net,[(x*STEP,y*STEP) for x,y,l in run],width,run[0][2])

for x,y in [(3,12),(16,12),(24,12),(27,21),(33,24.5),(5,25),(17.5,25),(30,34)]:
    t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetWidth(mm(.6));t.SetDrill(mm(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(*layers);t.SetNet(netobjects['GND']);b.Add(t)
    vias.append(('GND',x,y))

failed=[]
order=['M1','M2','REV','VCC','BATT+','DISCH','DB1','DB2','CLK1','CLK2','RESET_N','RUN','NOT_REV','POR_INV','POR_RC','SW1','SW2']
for net in order:
    if net not in points:continue
    width=1.0 if net in ('M1','M2','BATT+','VCC') else .25
    if net=='GND':width=.3
    remaining=set(points[net]);start=min(remaining);remaining.remove(start);tree={start}
    # 同一穿孔焊盤的兩面已相連。
    for point in list(remaining):
        if point[:2]==start[:2]:tree.add(point);remaining.remove(point)
    while remaining:
        start,goal=min(((a,z) for a in remaining for z in tree),key=lambda az:abs(az[0][0]-az[1][0])+abs(az[0][1]-az[1][1])+(10 if az[0][2]!=az[1][2] else 0))
        blocked,via_mask=masks(net,width)
        path=route(start,goal,blocked,via_mask)
        if path is None:
            failed.append((net,start,goal));remaining.remove(start);print('無路徑',net,start,goal,flush=True);continue
        output(net,path,width);tree.update(path);remaining.remove(start)
        for point in list(remaining):
            if point in tree or point[:2]==start[:2]:tree.add(point);remaining.remove(point)
        print(net,'剩餘',len(remaining),'過孔',len(vias),flush=True)

# 手動 WSON 引出段與自動線段交界也要切角。
nodes={}
for t in b.GetTracks():
    if type(t) is not p.PCB_TRACK:continue
    a,z=t.GetStart(),t.GetEnd()
    for start,end in ((a,z),(z,a)):
        nodes.setdefault((t.GetNetCode(),t.GetLayer(),start.x,start.y),[]).append((t,start,end))
for (net,layer,x,y),items in nodes.items():
    if len(items)!=2:continue
    (t,a,z),(s,c,d)=items
    u=(z.x-a.x,z.y-a.y);w=(d.x-c.x,d.y-c.y)
    lu,lw=math.hypot(*u),math.hypot(*w)
    if not lu*lw or abs(u[0]*w[0]+u[1]*w[1])/(lu*lw)>1e-7:continue
    if any(pad.IsOnLayer(layer) and pad.HitTest(v(p.ToMM(x),p.ToMM(y))) for f in b.GetFootprints() for pad in f.Pads()):continue
    cut=min(mm(.25),lu*.4,lw*.4)
    aa=p.VECTOR2I(round(x+u[0]*cut/lu),round(y+u[1]*cut/lu));zz=p.VECTOR2I(round(x+w[0]*cut/lw),round(y+w[1]*cut/lw))
    (t.SetStart if t.GetStart()==a else t.SetEnd)(aa)
    (s.SetStart if s.GetStart()==c else s.SetEnd)(zz)
    join=p.PCB_TRACK(b);join.SetStart(aa);join.SetEnd(zz);join.SetWidth(min(t.GetWidth(),s.GetWidth()));join.SetLayer(layer);join.SetNetCode(net);b.Add(join)

for layer in layers:
    zone=p.ZONE(b);zone.SetLayer(layer);zone.SetNet(netobjects['GND']);zone.SetLocalClearance(mm(.2));zone.SetPadConnection(p.ZONE_CONNECTION_FULL);zone.SetMinThickness(mm(.2))
    poly=zone.Outline();poly.NewOutline()
    for x,y in [(.35,.35),(39.65,.35),(39.65,39.65),(.35,39.65)]:poly.Append(mm(x),mm(y))
    b.Add(zone)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(ROOT/'mode2-no-firmware.kicad_pcb'),b)
(ROOT/'reports/routing.json').write_text(json.dumps({'failed':failed,'vias':len(vias),'tracks':len(tracks)},indent=2),encoding='utf-8')
print('完成',len(tracks),'段銅線；',len(failed),'條待修復。')
