from pathlib import Path
import nbformat as nbf

root = Path(__file__).resolve().parents[2]
path = root / '時系列_水温と電圧の周期.ipynb'
nb = nbf.read(path, as_version=4)

nb.cells.append(nbf.v4.new_markdown_cell('''## 気圧と水温の周期を同じ44時間で照合する

`DEFI/Air_Append_2026-08-31_10-17-39-444.csv`の気圧と、`DEFI/Data/depth20.csv`・`depth35.csv`・`depth45.csv`・`deoth55.csv`・`depth65.csv`の水温を2026年8月27日12:00–29日08:00の**同じ1分時刻**にそろえる。気圧は`Air_Append`の圧力列のみを使い、異常な`water50m`の圧力は使わない。

長周期は上と同じ**二次トレンドを含む調和回帰**で気圧の8–20時間を探索し、12.42時間固定の振幅も計算する。気圧と各深度の水温について、元系列の相関と、各系列から別々に二次トレンドを除いた**同時刻（遅れ0）の相関**を比べる。図の標準化残差は形を見るためのもので、気圧と水温の振幅を同じ単位にした値ではない。8.3分については1分系列から30分移動平均を引き、[SciPyのコヒーレンス](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.coherence.html)で気圧との一致を試す。短い窓での相関・コヒーレンスには有意確率を付けず、圧力から水温の原因を断定しない。

気圧が地下水位に影響し得ることは[USGSの観測研究](https://www.usgs.gov/publications/aquifer-response-record-low-barometric-pressures-southeastern-united-states)で示されているが、**水温への経路と時間遅れはこの井戸で未測定**である。月の半日潮M₂は[NOAAの潮汐成分表](https://prod.tidesandcurrents.noaa.gov/publications/tidal_datums_and_their_applications.pdf)にある12.42時間を参考にする。'''))

nb.cells.append(nbf.v4.new_code_cell('''# 気圧とDEFI水温を同一時刻に結合し、周期・相関を並べて点検
air_pressure = aux['Air'].loc[start:end, 'pressure'].rename('Air kPa')
one_minute = {z: d.temp.resample('1min').mean().rename(f'{z} m') for z, d in data.items()}
comparison = pd.concat([air_pressure, *one_minute.values()], axis=1).dropna()
assert len(comparison) == 2641 and comparison.index.to_series().diff().dropna().eq(pd.Timedelta('1min')).all()

time_h = np.arange(len(comparison)) / 60
base = np.column_stack([np.ones(len(time_h)), time_h, time_h**2])
residuals = {}
for column in comparison:
    y = comparison[column].to_numpy()
    residuals[column] = y - base @ np.linalg.lstsq(base, y, rcond=None)[0]

air_y = comparison['Air kPa'].to_numpy()
air_errors = np.array([fit_wave(air_y, time_h, p)[0] for p in periods])
air_best = periods[np.argmin(air_errors)]
air_rss12, air_amp12, _ = fit_wave(air_y, time_h, 12.42)
air_improvement12 = 1 - air_rss12 / np.sum(residuals['Air kPa']**2)
air_half_periods = []
for segment in np.array_split(air_y, 2):
    segment_t = np.arange(len(segment)) / 60
    air_half_periods.append(periods[np.argmin([fit_wave(segment, segment_t, p)[0] for p in periods])])
display(pd.DataFrame([['Air', air_best, air_amp12, air_improvement12,
                       *air_half_periods]], columns=['系列', '全期間の最良周期 h',
                       '12.42 h振幅 kPa', '12.42 hでの改善率',
                       '前半の周期 h', '後半の周期 h']).round(3))

air_high = comparison['Air kPa'] - comparison['Air kPa'].rolling(30, center=True, min_periods=1).mean()
relation_rows = []
for z in data:
    column = f'{z} m'
    temp_high = comparison[column] - comparison[column].rolling(30, center=True, min_periods=1).mean()
    freq, coherence = signal.coherence(air_high.to_numpy(), temp_high.to_numpy(),
                                        fs=1/60, nperseg=512, noverlap=256)
    coh_8min = coherence[np.argmin(abs(freq - 1/(8.3*60)))]
    relation_rows.append([z, comparison['Air kPa'].corr(comparison[column]),
                          np.corrcoef(residuals['Air kPa'], residuals[column])[0,1], coh_8min])
air_relation = pd.DataFrame(relation_rows, columns=['深度 m', '元系列の同時刻相関',
    '二次トレンド除去後の同時刻相関', '8.3分の気圧とのコヒーレンス'])
display(air_relation.round(3))

fig, ax = plt.subplots(2, 1, figsize=(11, 7))
for column, label in [('Air kPa', 'Air pressure'), ('20 m', 'Water temp 20 m'),
                      ('65 m', 'Water temp 65 m')]:
    y = comparison[column].to_numpy()
    errs = np.array([fit_wave(y, time_h, p)[0] for p in periods])
    ax[0].plot(periods, 1 - errs / np.sum(residuals[column]**2), label=label)
    scaled = residuals[column] / np.std(residuals[column])
    ax[1].plot(comparison.index, pd.Series(scaled, index=comparison.index).rolling(15, center=True,
                   min_periods=1).mean(), label=label, lw=1)
ax[0].axvline(12.42, color='grey', ls=':', label='M2 12.42 h')
ax[0].set(xlabel='Trial period (h)', ylabel='Reduction vs quadratic drift')
ax[1].set(ylabel='Detrended, standardized (15-min mean)', xlabel='Time')
for a in ax:
    a.grid(alpha=.25); a.legend(fontsize=8)
plt.tight_layout(); plt.show()'''))

nb.cells.append(nbf.v4.new_markdown_cell('''**結果の読み方**：気圧の全期間の最良値は約**13.33時間**で、水温5深度の約**12.50–12.55時間**とは一致しない。気圧の12.42時間固定振幅は約**0.078 kPa**、二次トレンドからの改善率は約**0.365**。気圧を半分ずつにすると最良値は約**14.25時間**と**17.68時間**へ動き、気圧の半日周期を安定した成分とは呼べない。元系列は気圧と水温で約−0.51～−0.53の相関を示すが、各系列の二次トレンドを除くと同時刻相関は約**−0.25～−0.32**に弱まる。したがって、共有する緩い変化が元系列の相関を強めている。8.3分帯の気圧とのコヒーレンスは20 mで約0.50、他の深度では約0.08–0.29と揃わず、共通の短周期擾乱を示す証拠にはならない。

**限界**：遅れ0の相関が弱くても、遅れて伝わる気圧応答は除外できない。気圧と水温の双方に短い観測窓・強い自己相関・気象変化の影響があり、探索した最良周期や相関は因果関係・有意確率を表さない。気圧変化が地下水位や流動を介して水温に効くのか、潮汐や揚水が共通要因なのかを分けるには、正常な水圧／水位、流速、気圧、降雨・揚水履歴を数週間以上同期して測る必要がある。'''))

nbf.validate(nb)
nbf.write(nb, path)
print(path, len(nb.cells))
