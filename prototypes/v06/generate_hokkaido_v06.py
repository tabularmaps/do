from PIL import Image, ImageDraw, ImageFont
from scipy.optimize import linear_sum_assignment
import math, json

R={
'空知':'夕張 岩見沢 美唄 芦別 赤平 三笠 滝川 砂川 歌志内 深川 南幌 奈井江 上砂川 由仁 長沼 栗山 月形 浦臼 新十津川 妹背牛 秩父別 雨竜 北竜 沼田'.split(),
'石狩':'札幌 江別 千歳 恵庭 北広島 石狩 当別 新篠津'.split(),
'後志':'小樽 島牧 寿都 黒松内 蘭越 ニセコ 真狩 留寿都 喜茂別 京極 倶知安 共和 岩内 泊 神恵内 積丹 古平 仁木 余市 赤井川'.split(),
'胆振':'室蘭 苫小牧 登別 伊達 豊浦 壮瞥 白老 厚真 洞爺湖 安平 むかわ'.split(),
'日高':'日高 平取 新冠 浦河 様似 えりも 新ひだか'.split(),
'渡島':'函館 北斗 松前 福島 知内 木古内 七飯 鹿部 森 八雲 長万部'.split(),
'檜山':'江差 上ノ国 厚沢部 乙部 奥尻 今金 せたな'.split(),
'上川':'旭川 士別 名寄 富良野 鷹栖 東神楽 当麻 比布 愛別 上川 東川 美瑛 上富良野 中富良野 南富良野 占冠 和寒 剣淵 下川 美深 音威子府 中川 幌加内'.split(),
'留萌':'留萌 増毛 小平 苫前 羽幌 初山別 遠別 天塩'.split(),
'宗谷':'稚内 猿払 浜頓別 中頓別 枝幸 豊富 礼文 利尻 利尻富士 幌延'.split(),
'オホーツク':'北見 網走 紋別 美幌 津別 斜里 清里 小清水 訓子府 置戸 佐呂間 遠軽 湧別 滝上 興部 西興部 雄武 大空'.split(),
'十勝':'帯広 音更 士幌 上士幌 鹿追 新得 清水 芽室 中札内 更別 大樹 広尾 幕別 池田 豊頃 本別 足寄 陸別 浦幌'.split(),
'釧路':'釧路 釧路町 厚岸 浜中 標茶 弟子屈 鶴居 白糠'.split(),
'根室':'根室 別海 中標津 標津 羅臼'.split()}
assert sum(map(len,R.values()))==179
reg={m:r for r,ms in R.items() for m in ms}
colors={'宗谷':'#8cc5e3','留萌':'#7db7d8','上川':'#87c99b','オホーツク':'#6cc6c1','空知':'#e6c86a','石狩':'#e99562','後志':'#c9a5d6','胆振':'#e28b78','日高':'#e7a3a8','十勝':'#b6d36f','釧路':'#73b5b2','根室':'#67a7a5','渡島':'#d79b72','檜山':'#b98b75'}
centers={'宗谷':(7,1),'留萌':(3.5,3),'上川':(8,4),'オホーツク':(12,4),'空知':(6,7),'石狩':(4,9),'後志':(1.5,9),'胆振':(5.5,11),'日高':(8,13),'十勝':(11,10),'釧路':(13.5,11),'根室':(15,10),'渡島':(4,14.5),'檜山':(1,13.5)}
anchors=['函館','小樽','旭川','稚内','北見','苫小牧','室蘭','帯広','釧路','根室']
blocks=[('札幌',4,4)]+[(m,2,2) for m in anchors]
over={'札幌':(4,8),'小樽':(2,6.3),'旭川':(8,5),'稚内':(7,0.5),'北見':(11.5,5),'函館':(4,14),'室蘭':(4.5,11.5),'苫小牧':(7,11),'帯広':(10.5,10),'釧路':(13,11),'根室':(15,11),
'江別':(6,8),'岩見沢':(6.5,7),'滝川':(7,6),'深川':(7.5,5.8),'恵庭':(5,10),'千歳':(5.7,10.2),'北広島':(4.8,9.5),'石狩':(3,7.3),'当別':(4.5,7),'新篠津':(5.3,7.3)}
target={}
for r,ms in R.items():
 cx,cy=centers[r]
 for i,m in enumerate(ms): target[m]=(cx+1.15*math.cos(i*2.35),cy+1.15*math.sin(i*2.35))
target.update(over)
occ=[[-1]*16 for _ in range(16)]; placements={}
def valid(x,y,w,h): return 0<=x and 0<=y and x+w<=16 and y+h<=16 and all(occ[Y][X]<0 for Y in range(y,y+h) for X in range(x,x+w))
for i,(m,w,h) in enumerate(blocks):
 opts=[]
 for y in range(17-h):
  for x in range(17-w):
   if valid(x,y,w,h):
    tx,ty=target[m]; opts.append(((x+(w-1)/2-tx)**2+(y+(h-1)/2-ty)**2,x,y))
 _,x,y=min(opts); placements[i]=(x,y,w,h)
 for Y in range(y,y+h):
  for X in range(x,x+w): occ[Y][X]=i
opens=[(x,y) for y in range(16) for x in range(16) if occ[y][x]<0]
# 32 structural spaces. Keep a dense core but recover breathing room at the perimeter and regional seams.
space_targets=[(x,0) for x in range(6)]+[(15,0),(15,1),(0,1),(0,2),(0,3),
 (1,5),(2,5),(3,5),(2,8),(3,8),(4,12),(5,12),(6,12),(7,12),(8,12),(9,12),
 (0,15),(1,15),(2,15),(13,15),(14,15),(15,15),(15,7),(15,8),(14,8),(1,11)]
spaces=[]
for q in space_targets:
 c=min(opens,key=lambda p:(p[0]-q[0])**2+(p[1]-q[1])**2); spaces.append(c); opens.remove(c)
blocked={m for m,_,_ in blocks}; rem=[m for ms in R.values() for m in ms if m not in blocked]
assert len(rem)==len(opens)==168
cost=[[(x-target[m][0])**2+(y-target[m][1])**2 for x,y in opens] for m in rem]
ri,ci=linear_sum_assignment(cost); assign={opens[j]:rem[i] for i,j in zip(ri,ci)}
assert 16+10*4+168+32==256
layout={'grid':[16,16],'classes':{'札幌':[4,4],'regional_anchor':[2,2],'municipality':[1,1]},'regional_anchors':anchors,'structural_spaces':spaces,'blocks':{},'cells':{}}
for i,(x,y,w,h) in placements.items(): layout['blocks'][blocks[i][0]]={'x':x,'y':y,'w':w,'h':h}
for (x,y),m in assign.items(): layout['cells'][m]={'x':x,'y':y}
with open('/mnt/data/hokkaido-v06-layout.json','w',encoding='utf-8') as f: json.dump(layout,f,ensure_ascii=False,indent=2)
fp='/usr/share/fonts/truetype/noto/NotoSansCJK-VF.ttf.ttc'; F=lambda n:ImageFont.truetype(fp,n,index=2)
S=90;M=60;TOP=170; im=Image.new('RGB',(M*2+16*S,TOP+16*S+150),'white'); d=ImageDraw.Draw(im)
d.text((M,25),'tabularmaps 北海道試作 06',font=F(42),fill='#172033'); d.text((M,78),'16×16 全道・三階級基準案',font=F(42),fill='#172033'); d.text((M,132),'札幌4×4、広域拠点10か所2×2、その他168市町村1×1。1×2は未使用。',font=F(20),fill='#64748b')
for i in range(17):
 d.line((M+i*S,TOP,M+i*S,TOP+16*S),fill='#e5eaf0'); d.line((M,TOP+i*S,M+16*S,TOP+i*S),fill='#e5eaf0')
for (x,y),m in assign.items():
 x0=M+x*S+3;y0=TOP+y*S+3;x1=x0+S-6;y1=y0+S-6;d.rounded_rectangle((x0,y0,x1,y1),5,fill=colors[reg[m]],outline='white',width=2); lab=m if len(m)<5 else m[:3]; bb=d.textbbox((0,0),lab,font=F(15));d.text(((x0+x1-(bb[2]-bb[0]))/2,(y0+y1-(bb[3]-bb[1]))/2),lab,font=F(15),fill='#172033')
for i,(x,y,w,h) in placements.items():
 m=blocks[i][0];x0=M+x*S+3;y0=TOP+y*S+3;x1=M+(x+w)*S-3;y1=TOP+(y+h)*S-3;fill='#d95f59' if m=='札幌' else '#e27d60';d.rounded_rectangle((x0,y0,x1,y1),8,fill=fill,outline='#334155',width=4);bb=d.textbbox((0,0),m,font=F(23));d.text(((x0+x1-(bb[2]-bb[0]))/2,(y0+y1-(bb[3]-bb[1]))/2),m,font=F(23),fill='#172033')
for x,y in spaces:
 x0=M+x*S+3;y0=TOP+y*S+3;d.rounded_rectangle((x0,y0,x0+S-6,y0+S-6),5,fill='#f7fafc',outline='#dfe6ec',width=2)
d.text((M,TOP+16*S+25),'セル収支: 16 + 40 + 168 + 32 = 256。構造余白は無名。将来の限定的な1×2昇格余力を含む。',font=F(19),fill='#52606d')
im.save('/mnt/data/tabularmaps_hokkaido_prototype_06_three_tiers.png')
print('generated')
