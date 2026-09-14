from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, KeepTogether,
)

ROOT = Path(__file__).resolve().parents[2]
TMP = ROOT / 'tmp/pdfs'
OUT = ROOT / 'output/pdf'
OUT.mkdir(parents=True, exist_ok=True)

FONT = '/Library/Fonts/BIZ-UDGothicR.ttc'
pdfmetrics.registerFont(TTFont('NotoJP', FONT))

NAVY = colors.HexColor('#19384D')
BLUE = colors.HexColor('#166A90')
PALE = colors.HexColor('#EDF5F8')
ORANGE = colors.HexColor('#A65B25')
GREY = colors.HexColor('#53636C')

def style(name, size, leading=None, color=NAVY, space_before=0, space_after=0, align=TA_LEFT):
    return ParagraphStyle(name, fontName='NotoJP', fontSize=size,
        leading=leading or size*1.55, textColor=color, spaceBefore=space_before,
        spaceAfter=space_after, alignment=align, wordWrap='CJK', allowWidows=0,
        allowOrphans=0)

S = {
    'title': style('title', 17, 26, space_after=8),
    'subtitle': style('subtitle', 9, 15, GREY, space_after=12),
    'h': style('h', 12, 18, BLUE, space_before=8, space_after=6),
    'body': style('body', 9.3, 16, space_after=7),
    'small': style('small', 8.6, 14, space_after=5),
    'tiny': style('tiny', 7.4, 11, GREY, space_after=3),
    'caption': style('caption', 8.5, 13, GREY, space_before=3, space_after=8),
    'cell': style('cell', 8.7, 13),
    'cellhead': style('cellhead', 8.7, 13, colors.white),
    'call': style('call', 10.2, 17),
}

def P(txt, key='body'):
    return Paragraph(txt, S[key])

def heading(txt):
    return P(txt, 'h')

def img(name, width):
    path = TMP / name
    iw, ih = ImageReader(str(path)).getSize()
    return Image(str(path), width=width, height=width * ih / iw)

def table(rows, widths, header=True):
    data = [[P(str(v), 'cellhead' if header and ri == 0 else 'cell') for v in row]
            for ri, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign='LEFT')
    styles = [
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),7), ('RIGHTPADDING',(0,0),(-1,-1),7),
        ('TOPPADDING',(0,0),(-1,-1),5), ('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LINEBELOW',(0,-1),(-1,-1),0.5,colors.HexColor('#C7D6DC')),
    ]
    if header:
        styles += [('BACKGROUND',(0,0),(-1,0),NAVY),
                   ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE])]
    t.setStyle(TableStyle(styles))
    return t

def callout(text):
    t = Table([[P(text, 'call')]], colWidths=[515])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),PALE),
        ('BOX',(0,0),(-1,-1),0.7,colors.HexColor('#A8C8D6')),
        ('LEFTPADDING',(0,0),(-1,-1),12), ('RIGHTPADDING',(0,0),(-1,-1),12),
        ('TOPPADDING',(0,0),(-1,-1),10), ('BOTTOMPADDING',(0,0),(-1,-1),10),
    ]))
    return t

def footer(canvas, doc):
    canvas.saveState()
    w, _ = A4
    canvas.setStrokeColor(colors.HexColor('#C7D6DC'))
    canvas.line(40, 35, w-40, 35)
    canvas.setFont('NotoJP', 7.2)
    canvas.setFillColor(GREY)
    canvas.drawString(40, 23, '2026年観測実習 | 2026-09-14 | 出典と解釈の範囲は本文参照')
    canvas.drawRightString(w-40, 23, str(doc.page))
    canvas.restoreState()

def make(path, story):
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=40,
        leftMargin=40, topMargin=42, bottomMargin=47,
        title=path.stem, author='Observation workspace')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)

summary = [
    P('温度観測グラフ｜結論を簡潔にまとめた資料', 'title'),
    P('河口湖・函嶺洞門 / 2026年の孔内温度と函嶺洞門の44時間時系列', 'subtitle'),
    callout('河口湖は中間の深度で下ほど冷たくなるため勾配が負、函嶺洞門は下ほど温かくなるため正。井戸内の水温を比べた値であり、地下の熱の流れる向きを直接測った値ではない。'),
    Spacer(1, 8),
    img('profile_cell3_1.png', 490),
    P('図1：黒線が2026年。河口湖は二つのほぼ等温帯の間で冷え、函嶺洞門は58–59 mで傾きが緩む。', 'caption'),
    img('series_summary_temperature.png', 490),
    P('図2：函嶺洞門の44時間の水温変化（各深度の平均との差）。20–55 mは似た波形、65 mは小振幅。', 'caption'),
    table([
        ['グラフ', '読み取れること', '考えられる説明と限界'],
        ['河口湖の深度', '60.85–88.85 mは−0.0319 °C/m。上下にほぼ等温の区間。', '温度の異なる地下水の流動・混合が候補。流入元は未特定。'],
        ['函嶺洞門の深度', '20.07–58.07 mは+0.375 °C/m。下側は+0.095 °C/m。', '深部の熱・温水が候補。58–59 mで条件が変化するが、地層境界とは未確定。'],
        ['半日程度の変動', '水温5深度で約12.5 h。65 mの振幅は上の深度の約0.34倍。', '気圧の最良値は約13.33 hで一致せず、同時刻の対応も弱い。潮汐起源は未確定。'],
        ['数分の変動', '3分に共通ピークなし。8分前後は広い山で深度間の一致が弱い。', '有効な共通周期とは判定できず、流れや計器の擾乱は候補にとどまる。'],
    ], [94, 198, 223]),
    Spacer(1, 5),
    P('注意：河口湖2025年の換算値は比較から除外。函嶺洞門の補助水圧は非物理的で水位に換算できない。出典と検証課題は詳細資料に記載。', 'tiny'),
]
make(OUT / '観測グラフ_結論の要約.pdf', summary)

detail = [
    P('温度観測グラフ｜詳細な考察', 'title'),
    P('測定結果・仮説・未確定事項を分けて読む / 2026年9月14日', 'subtitle'),
    P('対象は「温度プロファイル_勾配と熱流量.ipynb」と「時系列_水温と電圧の周期.ipynb」の保存済み図・表。2026年の深度は河口湖に+0.85 m、函嶺洞門に+0.07 mを加算した値で示す。河口湖の空気中32 mと比較範囲外の33 mは除いた。過去年の深度基準は完全には統一されていない。', 'small'),
    heading('1　孔内温度プロファイルが示す形'),
    img('profile_cell3_1.png', 515),
    P('図1：水温 (横軸) と深度 (縦軸)。2026年は黒線。背景の帯は注目区間であり、帯水層や地層境界を同定したものではない。', 'caption'),
    table([
        ['地点・区間（補正後）', '2026年の観測値', '過去観測との比較'],
        ['河口湖 40.85–54.85 m', '平均10.614 °C、幅0.031 °C', '浅側の緩勾配が複数年に見られる。'],
        ['河口湖 60.85–88.85 m', '平均勾配−0.0319 °C/m', '2013・14・18・19・24年も約−0.0300～−0.0329 °C/m。'],
        ['河口湖 92.85–120.85 m', '平均9.764 °C、幅0.022 °C', '深部のほぼ等温形は複数年で再現。'],
        ['函嶺洞門 20.07–58.07 m / 59.07–70.07 m', '+0.375 / +0.095 °C/m', '約60 mの折れ目は2015・22・23・25年にもある。'],
    ], [180, 151, 184]),
    P('函嶺洞門の58.07–59.07 mは38.563→38.607 °C。59.07–70.07 mも38.607→39.645 °Cへ上がり続ける。「深部の温度一定層」という表現はこの図には合わない。', 'small'),
    PageBreak(),

    P('2　地質・地下水をどう結びつけるか', 'title'),
    heading('河口湖：低勾配と地下水流動'),
    P('南岸の地域研究では、富士山由来の溶岩と火山砂礫の互層が透水性の高い層をつくり、古富士泥流堆積物の表面に地下谷が推定される [1]。したがって、二つのほぼ等温区間を水の移動や孔内混合が温度を均した結果とみることは合理的な仮説である。USGSも低勾配を孔内流動を調べる手掛かりに挙げる [4]。', 'body'),
    P('具体的な流入元の候補は二つある。①湖水が南岸から溶岩・火山砂礫へ浸透し、湖の南側の地下谷に沿って流れる経路。②富士山北麓の降水が火山噴出物に浸透し、南岸周辺の帯水部を涵養する経路である。[1]は南岸の浅井戸で湖水の寄与を示す地点と、富士山周辺の降水を主な涵養源とみる地点が混在すると報告する。この井戸の上側10.61 °Cと下側9.76 °Cがそれぞれどちらかは、水温だけでは決められない。', 'body'),
    P('湖底湧水の直接採水では、同位体比から主に御坂山地側の地下水が湖底へ出ると示唆された [2]。その水が湖を経て南岸へ再浸透する可能性は概念的にあるが、ホテルレジーナ脇の40–120 mへ直接流入した証拠ではない。二つのほぼ等温区間が別々の帯水層か、開放された同じ井戸内の混合区間かも未確定である。', 'body'),
    table([
        ['河口湖の経路仮説', '見分けるための同井データ'],
        ['湖水 → 南岸の火山砂礫・溶岩 → 井戸', '深度別の水素・酸素同位体に湖水の蒸発履歴が残るか。湖水・周辺井戸と同時比較。'],
        ['富士山側の降水 → 火山噴出物 → 井戸', '天水線との関係、溶存成分・バナジウム、水頭差と流速の比較。'],
    ], [223, 292]),
    heading('函嶺洞門：折れ目と温度上昇'),
    P('2026年の区間平均勾配は約58–59 mを挟んで+0.375から+0.095 °C/mへ約4分の1になった。地域の経路候補は、箱根火山に降った雨雪が地下へ入り、湯本の早川凝灰角礫岩などの割れ目を通る間に温められた水と、早川・須雲川の谷沿いの比較的浅い地下水との混合である [5, 8]。温泉地学研究所の温度検層研究は湯本地域で局所的な熱水流入を報告する [8]。ただし、この井戸の約58–59 mにどちらの水が入り、どちら向きに流れるかは不明である。', 'body'),
    P('提示された久野観測井の「69.5 m以深は湯ヶ島層群」という古い区分は、後年の温泉地学研究所の再検討で誤りとされ、同井の300 m全体を早川凝灰角礫岩相当とみる [6]。しかも久野と函嶺洞門は別の井戸である。したがって、函嶺洞門の58 mの折れ目に「湯ヶ島層群との境界」という地層名を付ける根拠にはならない。', 'body'),
    heading('二地点の対比'),
    P('深度を下向き正とすると、熱伝導だけが卓越する地温は通常下ほど高くなる。河口湖の60–89 mで逆に冷える形は、温度の異なる地下水や孔内流動が水温を強く変えている仮説と整合する。一方、函嶺洞門は20–70 mで温度が大きく上がり、湯本地域の熱水活動の背景と整合する [5, 8]。ただし両図は井戸内の水温であり、熱流の向きそのものではない。この井戸の熱が直接マグマ由来か、河口湖の熱収支を低温地下水が「支配」するかは定量化できない。', 'body'),
    PageBreak(),

    P('3　函嶺洞門の44時間時系列', 'title'),
    P('DEFIの20・35・45・55・65 mを2026年8月27日12:00～29日08:00の共通44時間で比較。各深度15,841点、10秒間隔、温度欠損は0点。図2の上段は深度ごとに平均との差を引き、下段は電圧を示す。', 'small'),
    img('series_cell3_1.png', 515),
    P('図2：20–55 mには似た半日程度の水温変化があり、65 mは振幅が小さい。下段の電圧は0.01 V刻みの段階値で、水温に似た波形を示さない。', 'caption'),
    table([
        ['名目深度', '全期間の最良周期', '12.42 h固定の水温振幅', '前半 / 後半の最良周期'],
        ['20 m', '12.500 h', '0.100 °C', '13.400 / 12.125 h'],
        ['35 m', '12.550 h', '0.110 °C', '13.775 / 12.200 h'],
        ['45 m', '12.500 h', '0.105 °C', '13.025 / 12.300 h'],
        ['55 m', '12.525 h', '0.109 °C', '13.875 / 12.200 h'],
        ['65 m', '12.525 h', '0.036 °C', '14.000 / 12.350 h'],
    ], [85, 110, 155, 165]),
    P('二次トレンドと正弦波を同時に最小二乗回帰し、8–20 hを探索した結果である。全期間の最良値が約12.5 hに集まる一方、前後半では周期が動く。44時間は約3.5周期しかなく、月の半日潮M2（12.42 h）と太陽半日潮S2（12.00 h）を分離できない [7]。潮汐・潮汐応答は候補であり、起源は未確認。', 'body'),
    PageBreak(),

    P('4　周期探索と短周期の検出限界', 'title'),
    img('series_cell5_1.png', 400),
    P('図3：候補周期ごとに二次トレンドのみとの残差平方和の改善率を比較。ピークの近さは、周期の物理的起源の証明や統計的有意確率を意味しない。', 'caption'),
    P('65 mの12.42 h固定振幅0.036 °Cは、20–55 mの中央値0.107 °Cの0.34倍。名目65 mはプロファイルの折れ目より下側に位置する。同じ深度基準なら65.07 mに当たるが、ロガーの設置基準は未照合である。地下水の流入・混合、割れ目や岩相の変化と整合し得る一方、校正差や固定状態でも振幅は変わり得る。', 'body'),
    img('series_cell10_1.png', 400),
    P('図4：30分移動平均を除いた水温の2–10分帯Welchスペクトル。3分に共通する鋭いピークはない。8分前後の広い山は深度間のコヒーレンスが低い。', 'caption'),
    P('固定3分の回帰振幅は0.0001–0.0004 °Cで水温CSVの0.001 °C刻みより小さい。10秒サンプリングは3分を表現できるが、観測された信号として採用する根拠にはならない。8.3分で20 mと他深度のコヒーレンスは約0.06–0.16。電圧の12.42 h振幅は最大0.00113 Vで、0.01 Vの表示刻みに満たず、電圧周期とも判定しない。', 'body'),
    heading('数分帯に見える擾乱の候補'),
    table([
        ['候補', 'このデータとの関係 / 判別方法'],
        ['井戸内の対流・流入水の混合', '温度差の大きい湯本の井戸では局所的な揺らぎはあり得る [9]。水温と同時に流速・水圧を高頻度で測る。'],
        ['近隣の揚水・設備・センサーの揺れ', '深度ごとの不一致と両立するが運転記録がない。揚水ログ・固定状態・複数計器を照合する。'],
        ['量子化・ノイズ・解析窓の効果', '3分振幅は記録刻み以下。8分の広い山は窓長を変えて再現性を確かめる。'],
    ], [165, 350]),
    P('どれも現時点では候補であり、「8分の地下水周期」や「3分の潮汐」とは結論しない。', 'small'),
    PageBreak(),

    P('5　気圧と水温の周期は対応するか', 'title'),
    P('Air_Appendの気圧とDEFI水温を同じ1分時刻にそろえ、各系列の二次トレンドを除いて比較した。図5上は8–20 hの調和回帰、下は残差を標準化して15分平均した形。標準化は単位と振幅を揃えない。', 'small'),
    img('series_air_comparison.png', 510),
    P('図5：気圧の最良周期は水温より長い。残差波形も同時刻に常に重ならない。', 'caption'),
    table([
        ['系列', '全期間の最良周期', '12.42 h固定振幅', '前半 / 後半'],
        ['気圧', '13.325 h', '0.078 kPa', '14.25 / 17.675 h'],
        ['水温20 m', '12.500 h', '0.100 °C', '13.40 / 12.13 h'],
        ['水温65 m', '12.525 h', '0.036 °C', '14.00 / 12.35 h'],
    ], [82, 126, 150, 157]),
    P('気圧と水温の元系列の同時刻相関は−0.51～−0.53だが、二次トレンドを各系列から取り除くと−0.25～−0.32へ弱まる。つまり、共通する緩い変化が元系列の相関を強めている。気圧の半日帯の最良値も前後半で大きく動き、安定した12.42 hの気圧成分とは判定できない。', 'body'),
    P('8.3分で気圧とのコヒーレンスは20 mで0.50、残る4深度で0.08～0.29とそろわない。気圧が水位を変え、遅れて流れや水温に作用する可能性はある [10] が、遅れ0の相関だけではそれを除外も立証もできない。異常なwater50m水圧の代わりに正常な水位・水圧を同期観測する必要がある。', 'body'),
    PageBreak(),

    P('6　補助ログと次の検証', 'title'),
    img('series_cell15_1.png', 500),
    P('図6：気圧、水圧、補助水温。水圧は負の非物理値に飛んでおり、水位換算には使えない。', 'caption'),
    P('Air_Appendの共通窓の気圧は99.436–99.982 kPa。water50mの温度は38.934–39.211 °CでDEFI 65 mの1分平均と相関0.872だが、ファイル名だけでは実設置深度が分からない。water50mの圧力は約−376.67 kPa、Depth欄も約−3845 cmで非物理的。正常な同時水位を欠くため、半日水温変動と潮汐・地下水位の位相関係は検証できない。', 'body'),
    table([
        ['判別したいこと', '追加で必要な測定'],
        ['等温区間の起源・流入経路', '井戸の柱状図とスクリーン、深度別水質・安定同位体、流速・流向、反復温度検層。'],
        ['58–59 mの折れ目と65 mの減衰', '同井のコア・物理検層、50–75 mの密な温度・流速・電気伝導度、ロガー校正と設置深度。'],
        ['半日変動の起源', '数週間以上の同時水温・正常な水位・気圧、降雨・揚水記録、時刻同期。'],
    ], [170, 345]),
    heading('参照資料'),
    P('[1] 山本ほか (2017)「河口湖南岸の浅層地下水」 <link href="https://www.mfri.pref.yamanashi.jp/mfr/pdf/no11/2017-p1-p9.pdf" color="#166A90">富士山研究 11, 1–9</link>。 [2] 山本ほか (2020)「河口湖の湖底湧水」 <link href="https://doi.org/10.5026/jgeography.129.665" color="#166A90">地学雑誌 129, 665–676</link>。 [3] 林 (2020)「富士山北部の地下水流動」 <link href="https://doi.org/10.5026/jgeography.129.677" color="#166A90">地学雑誌 129, 677–695</link>。', 'tiny'),
    P('[4] <link href="https://www.usgs.gov/media/images/geophysical-logs-temperature-logs" color="#166A90">USGS Temperature logs</link>。 [5] <link href="https://www.onken.odawara.kanagawa.jp/hotspring/onsen_kouza/20200519-01.html" color="#166A90">神奈川県温泉地学研究所「箱根温泉」</link>。 [6] <link href="https://www.onken.odawara.kanagawa.jp/files/PDF/tayori/SP_50thAnn/50thAnn_05.pdf" color="#166A90">同研究所 50年誌, p.89</link>。 [7] <link href="https://prod.tidesandcurrents.noaa.gov/publications/tidal_datums_and_their_applications.pdf" color="#166A90">NOAA 潮汐成分資料</link>。', 'tiny'),
    P('[8] <link href="https://www.onken.odawara.kanagawa.jp/files/PDF/houkoku/48/houkoku48_p17-24.pdf" color="#166A90">温泉地学研究所「箱根火山の地温勾配」</link>。 [9] <link href="https://www.usgs.gov/publications/simple-method-detecting-anomalous-fluid-motions-boreholes-continuous-temperature-logs" color="#166A90">USGS 孔内流体運動と温度ログ</link>。 [10] <link href="https://www.usgs.gov/publications/aquifer-response-record-low-barometric-pressures-southeastern-united-states" color="#166A90">USGS 気圧と地下水位の応答</link>。', 'tiny'),
]
make(OUT / '観測グラフ_詳細な考察.pdf', detail)
print(OUT / '観測グラフ_結論の要約.pdf')
print(OUT / '観測グラフ_詳細な考察.pdf')
