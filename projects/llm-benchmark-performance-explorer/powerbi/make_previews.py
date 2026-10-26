"""Render static Power BI-style report previews from the benchmark CSV."""
import csv
from collections import Counter, defaultdict
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "benchmark_scores.csv"
OUT = Path(__file__).resolve().parent / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1600, 900
NAVY = "#142A43"; NAVY2 = "#203A59"; TEAL = "#00A6A6"; BLUE = "#3B82F6"
INK = "#172B4D"; MUTED = "#6B7A90"; BG = "#F3F6FA"; CARD = "#FFFFFF"
GRID = "#E3EAF2"; GOLD = "#E6A23C"; PALE = "#E9F5F5"
FONT = r"C:\Windows\Fonts\segoeui.ttf"
BOLD = r"C:\Windows\Fonts\segoeuib.ttf"

def font(size, bold=False):
    path = BOLD if bold else FONT
    try: return ImageFont.truetype(path, size)
    except OSError: return ImageFont.load_default()

def read_rows():
    with DATA.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["score_num"] = float(r["score"])
        r["pct_num"] = float(r["score_pct"])
        r["date_year"] = int(r["release_date"][:4])
    return rows

def base_page(title, subtitle, page_num):
    im=Image.new("RGB", (W,H), BG); d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,74), fill=NAVY)
    d.text((28,17),"MODEL PERFORMANCE",font=font(16,True),fill="#C9D6E6")
    d.text((330,16),title,font=font(24,True),fill="#FFFFFF")
    d.text((331,47),subtitle,font=font(12),fill="#C9D6E6")
    # Left navigation rail.
    d.rectangle((0,74,68,H),fill="#192E48")
    for i,(label,active) in enumerate([("OVERVIEW",page_num==1),("COVERAGE",page_num==2)]):
        y=130+i*88
        if active: d.rounded_rectangle((8,y-10,60,y+49),radius=10,fill="#2C4968")
        d.rounded_rectangle((23,y,45,y+21),radius=5,outline=TEAL if active else "#A9B7C9",width=2)
        d.text((9,y+30),label,font=font(8,True),fill="#FFFFFF" if active else "#A9B7C9")
    # Footer provenance note.
    d.text((92,869),"Source: supplied benchmark_scores.csv  |  Static report preview generated from the supplied data",font=font(11),fill=MUTED)
    d.text((1515,869),f"{page_num} / 2",font=font(11,True),fill=MUTED)
    return im,d

def card(d, box, label, value, note=None, accent=TEAL):
    x0,y0,x1,y1=box
    d.rounded_rectangle(box,radius=12,fill=CARD,outline=GRID,width=1)
    d.rounded_rectangle((x0,y0,x0+5,y1),radius=3,fill=accent)
    d.text((x0+20,y0+13),label.upper(),font=font(11,True),fill=MUTED)
    d.text((x0+20,y0+36),value,font=font(28,True),fill=INK)
    if note: d.text((x0+20,y1-25),note,font=font(10),fill=MUTED)

def panel(d,box,title,subtitle=None):
    x0,y0,x1,y1=box
    d.rounded_rectangle(box,radius=12,fill=CARD,outline=GRID,width=1)
    d.text((x0+18,y0+15),title,font=font(16,True),fill=INK)
    if subtitle: d.text((x0+18,y0+40),subtitle,font=font(10),fill=MUTED)
    return (x0+18,y0+67,x1-18,y1-18)

def overview(rows):
    bench="MMLU"
    selected=[r for r in rows if r["benchmark"]==bench]
    selected.sort(key=lambda r:(-r["pct_num"],r["model_name"]))
    top=selected[:10]
    all_models=len({r["model_id"] for r in rows})
    all_orgs=len({r["organization"] for r in rows})
    leader=selected[0]
    median=sorted(r["pct_num"] for r in selected)[len(selected)//2]
    im,d=base_page("LLM Benchmark Performance","Benchmark-specific comparison | Selected benchmark: MMLU | Score shown as supplied percentage",1)
    # Filter chips.
    d.text((96,91),"FILTERS",font=font(10,True),fill=MUTED)
    for x,w,label,value in [(150,225,"BENCHMARK","MMLU  v"),(389,210,"CAPABILITY","knowledge  v"),(613,220,"ORGANISATION","All  v"),(847,220,"RELEASE YEAR","All  v")]:
        d.rounded_rectangle((x,86,x+w,133),radius=8,fill=CARD,outline=GRID,width=1)
        d.text((x+12,92),label,font=font(9,True),fill=MUTED); d.text((x+12,108),value,font=font(12,True),fill=INK)
    # KPI cards.
    y0,y1=150,252; gap=14; x0=96; cw=350
    card(d,(x0,y0,x0+cw,y1),"Models reported",f"{len(selected)}","100% of models in this benchmark")
    card(d,(x0+cw+gap,y0,x0+2*cw+gap,y1),"Top score",f"{leader['pct_num']:.1f}%",leader["model_name"],BLUE)
    card(d,(x0+2*(cw+gap),y0,x0+3*cw+2*gap,y1),"Median score",f"{median:.1f}%","Within MMLU only",GOLD)
    card(d,(x0+3*(cw+gap),y0,x0+4*cw+3*gap,y1),"Models in dataset",f"{all_models}",f"Across {all_orgs} organisations",NAVY2)
    # Top score bars.
    bx0,by0,bx1,by1=panel(d,(96,270,920,630),"Top 10 models","MMLU score percentage  |  sorted within selected benchmark")
    left=bx0+150; right=bx1-20; topy=by0+8; rowh=25; plotw=right-left
    for tick in (0,20,40,60,80,100):
        xx=left+plotw*tick/100; d.line((xx,topy-4,xx,by1-4),fill=GRID,width=1); d.text((xx-8,by1+1),str(tick),font=font(9),fill=MUTED)
    for i,r in enumerate(reversed(top)):
        yy=topy+i*rowh
        d.text((bx0,yy+2),r["model_name"][:22],font=font(10),fill=INK)
        width=plotw*r["pct_num"]/100
        color=TEAL if r["model_id"]==leader["model_id"] else BLUE
        d.rounded_rectangle((left,yy+1,left+width,yy+17),radius=4,fill=color)
        d.text((left+width+7,yy),f"{r['pct_num']:.1f}",font=font(9,True),fill=INK)
    # Distribution histogram.
    hx0,hy0,hx1,hy1=panel(d,(940,270,1504,630),"Score distribution","Model count by MMLU score band")
    values=[r["pct_num"] for r in selected]; buckets=Counter(min(9,int(v//10)) for v in values)
    chart_left=hx0+35; chart_right=hx1-8; chart_top=hy0+24; chart_bottom=hy1-33
    max_count=max(buckets.values()); ch=chart_bottom-chart_top; cw2=(chart_right-chart_left)/10
    for tick in (0,max_count//2,max_count):
        yy=chart_bottom-ch*tick/max_count if max_count else chart_bottom
        d.line((chart_left,yy,chart_right,yy),fill=GRID,width=1)
        d.text((chart_left-25,yy-6),str(tick),font=font(9),fill=MUTED)
    for i in range(10):
        x=chart_left+i*cw2+4; h=ch*buckets.get(i,0)/max_count if max_count else 0
        d.rounded_rectangle((x,chart_bottom-h,x+cw2-8,chart_bottom),radius=4,fill=TEAL if i>=8 else BLUE)
        d.text((x+2,chart_bottom+7),f"{i*10}-{i*10+10}",font=font(8),fill=MUTED)
    # Release cohort trend.
    tx0,ty0,tx1,ty1=panel(d,(96,646,920,840),"Score by release year","Average MMLU percentage by model release year")
    years=defaultdict(list)
    for r in selected: years[r["date_year"]].append(r["pct_num"])
    trend=sorted((year,sum(vals)/len(vals)) for year,vals in years.items())
    tl,tt,tr,tb=tx0+32,ty0+12,tx1-10,ty1-28
    if trend:
        ymin=max(0,min(v for _,v in trend)-5); ymax=min(100,max(v for _,v in trend)+5); span=max(1,ymax-ymin)
        points=[]
        for year,val in trend:
            xx=tl+(year-trend[0][0])/max(1,trend[-1][0]-trend[0][0])*(tr-tl)
            yy=tb-(val-ymin)/span*(tb-tt)
            points.append((xx,yy,year,val))
        for yy in (tt,tb): d.line((tl,yy,tr,yy),fill=GRID,width=1)
        for a,b in zip(points,points[1:]): d.line((a[0],a[1],b[0],b[1]),fill=TEAL,width=3)
        for x,y,year,val in points:
            d.ellipse((x-5,y-5,x+5,y+5),fill=TEAL,outline=CARD,width=2)
            d.text((x-12,tb+7),str(year),font=font(9),fill=MUTED)
    # Compact detail table.
    dx0,dy0,dx1,dy1=panel(d,(940,646,1504,840),"Leaderboard","Top results in selected benchmark")
    cols=[dx0,dx0+42,dx0+300,dx0+425]
    d.text((cols[0],dy0),"#",font=font(9,True),fill=MUTED); d.text((cols[1],dy0),"MODEL",font=font(9,True),fill=MUTED); d.text((cols[2],dy0),"ORGANISATION",font=font(9,True),fill=MUTED); d.text((cols[3],dy0),"SCORE",font=font(9,True),fill=MUTED)
    d.line((dx0,dy0+18,dx1,dy0+18),fill=GRID,width=1)
    for i,r in enumerate(selected[:5]):
        yy=dy0+24+i*23
        d.text((cols[0],yy),str(i+1),font=font(10),fill=MUTED)
        d.text((cols[1],yy),r["model_name"][:27],font=font(10),fill=INK)
        d.text((cols[2],yy),r["organization"][:16],font=font(10),fill=INK)
        d.text((cols[3],yy),f"{r['pct_num']:.1f}%",font=font(10,True),fill=INK)
    d.text((96,850),"Interpretation: compare only within the selected benchmark; scores from different benchmarks are not interchangeable.",font=font(10,True),fill="#3B556F")
    im.save(OUT/"overview.png",optimize=True)

def coverage(rows):
    im,d=base_page("Benchmark Coverage","Availability and organisation coverage | Coverage is not the same as performance",2)
    d.text((96,91),"VIEW",font=font(10,True),fill=MUTED)
    d.rounded_rectangle((150,86,362,133),radius=8,fill=CARD,outline=GRID,width=1)
    d.text((162,92),"METRIC",font=font(9,True),fill=MUTED); d.text((162,108),"Models reported  v",font=font(12,True),fill=INK)
    d.rounded_rectangle((375,86,615,133),radius=8,fill=CARD,outline=GRID,width=1)
    d.text((387,92),"CAPABILITY",font=font(9,True),fill=MUTED); d.text((387,108),"All  v",font=font(12,True),fill=INK)
    model_total=len({r["model_id"] for r in rows}); bench_counts=Counter(r["benchmark"] for r in rows)
    model_sets=defaultdict(set); org_models=defaultdict(set); org_bench=defaultdict(lambda:defaultdict(set))
    for r in rows:
        model_sets[r["benchmark"]].add(r["model_id"])
        org_models[r["organization"]].add(r["model_id"])
        org_bench[r["organization"]][r["benchmark"]].add(r["model_id"])
    full=sum(len({r["benchmark"] for r in rows if r["model_id"]==mid})==15 for mid in {r["model_id"] for r in rows})
    min_cov=min(bench_counts.values())/model_total*100
    card(d,(96,150,434,251),"Model-benchmark records",f"{len(rows):,}",f"{len(rows)/(model_total*15)*100:.1f}% of possible combinations")
    card(d,(448,150,786,251),"Complete benchmark profiles",str(full),f"Models with results on all 15 benchmarks",BLUE)
    card(d,(800,150,1138,251),"Lowest benchmark coverage",f"{min_cov:.1f}%","52 of 113 models reported",GOLD)
    card(d,(1152,150,1490,251),"Total models",str(model_total),"Across the supplied dataset",NAVY2)
    # Coverage bars sorted by count.
    x0,y0,x1,y1=panel(d,(96,270,770,840),"Reported models by benchmark","Distinct model IDs with a score record")
    sorted_b=sorted(bench_counts.items(),key=lambda x:(x[1],x[0]))
    l=x0+180; r=x1-36; y=y0+5; rowh=30; pw=r-l
    for tick in (0,25,50,75,100,125):
        xx=l+pw*tick/125; d.line((xx,y-3,xx,y+15*rowh),fill=GRID,width=1); d.text((xx-10,y+15*rowh+2),str(tick),font=font(9),fill=MUTED)
    for i,(name,count) in enumerate(sorted_b):
        yy=y+i*rowh
        d.text((x0,yy+2),name[:27],font=font(10),fill=INK)
        width=pw*count/125
        d.rounded_rectangle((l,yy,l+width,yy+17),radius=4,fill=GOLD if count<=53 else TEAL if count==model_total else BLUE)
        d.text((l+width+6,yy+1),str(count),font=font(9,True),fill=INK)
    # Coverage matrix for most represented organizations and common benchmarks.
    mx0,my0,mx1,my1=panel(d,(790,270,1504,840),"Benchmark availability by organisation","Cell value = share of that organisation's models with a score")
    org_order=[o for o,_ in Counter({o:len(ms) for o,ms in org_models.items()}).most_common(9)]
    common=[b for b,_ in sorted(bench_counts.items(),key=lambda item:(item[1],item[0]))[:8]]
    left=mx0+139; top=my0+72; cellw=47; cellh=37
    for j,b in enumerate(common):
        label_map={"AIME 2024":"AIME","MMMU":"MMMU","SWE-Bench Verified":"SWE-B","LiveCodeBench":"LiveCode","MMLU-Pro":"MMLU-P","Chatbot Arena ELO":"Arena ELO","GPQA Diamond":"GPQA","BBH":"BBH"}
        label=label_map.get(b,b[:10])
        if len(label)>11: label=label[:10]+"…"
        d.text((left+j*cellw,top-28),label,font=font(7,True),fill=MUTED)
    for i,org in enumerate(org_order):
        yy=top+i*cellh
        d.text((mx0,yy+9),org[:19],font=font(9),fill=INK)
        total=len(org_models[org])
        for j,b in enumerate(common):
            pct=(len(org_bench[org][b])/total*100) if total else 0
            x=left+j*cellw
            color=PALE if pct>=85 else "#DCE8F5" if pct>=60 else "#F9E8C9" if pct>=40 else "#F5DADA"
            d.rounded_rectangle((x,yy,x+cellw-4,yy+cellh-4),radius=5,fill=color)
            d.text((x+4,yy+8),f"{pct:.0f}%",font=font(9,True),fill=INK)
    # Legend and note.
    ly=top+len(org_order)*cellh+12
    d.text((mx0,ly),"Coverage",font=font(9,True),fill=MUTED)
    for i,(lab,col) in enumerate([("High","#BFE8E2"),("Medium","#DCE8F5"),("Low","#F9E8C9"),("Sparse","#F5DADA")]):
        xx=mx0+77+i*126
        d.rounded_rectangle((xx,ly,xx+17,ly+15),radius=3,fill=col)
        d.text((xx+23,ly+1),lab,font=font(9),fill=MUTED)
    d.text((96,850),"Coverage differences can affect ranking stability; newer benchmarks have fewer reported models in this dataset.",font=font(10,True),fill="#3B556F")
    im.save(OUT/"coverage.png",optimize=True)

if __name__ == "__main__":
    rows=read_rows()
    overview(rows)
    coverage(rows)
    print(f"Rendered two report preview images from {len(rows)} score records into {OUT}")




