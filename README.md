# 🍵 今天喝什么 · tea-planner MCP

> **无由持一碗，寄与爱茶人。** —— 白居易
> 
> **休对故人思故国，且将新火试新茶。诗酒趁年华。** —— 苏轼

事情是这样的：家里茶越来越多，多到每次打开柜子要发呆五分钟，最后拿的还是离手最近的那一盒。茶叶受潮怪自己，选择困难也怪自己，不如让程序背锅。

于是有了这个挂在 Cherry Studio 上的 MCP——「今天喝什么」。内置 107 款茶的壶泡参数（绿茶、乌龙、黑茶、红茶、白茶、黄茶、花茶，还有一堆说不清该归哪类的怪东西），每天替你抛一枚**有理由的硬币**：按季节、时段、最近喝没喝过、库存积灰程度加权抽签。夏天也能抽中熟普，只是概率低；深夜也不会只塞给你代用茶——规则是软的，没有哪款茶被判死刑。

## 有什么工具（11 个）

| 工具 | 你说的话 |
|---|---|
| `recommend` | 今天喝什么？ |
| `coldbrew_recommend` | 今天冷泡什么？ |
| `add_tea` | 我买了龙井、铁观音、正山小种（支持批量） |
| `remove_tea` | 我喝光了碧螺春 |
| `clear_inventory` | 我搬到了外地（一键清空，别继承作者的茶柜） |
| `set_brewer` | 我的茶壶是 300ml / 冷泡壶换成 2L |
| `review` | 太淡了 / 有点苦 / 仓气重 / 洗茶太过 / 闷味 / 泡酸了 / 香味没了 |
| `record` / `undo_record` / `history` | 我喝了XX / 记错了撤回 / 最近喝过啥 |

## 部署（Cherry Studio，两分钟）

需要 Python 3.10+：

```bash
pip install "mcp[cli]"
```

Cherry Studio → 设置 → MCP 服务器 → 导入这段 JSON（把路径换成你的）：

```json
{
  "mcpServers": {
    "tea-planner": {
      "command": "python",
      "args": ["C:\\your\\path\\tea-planner\\tea_planner.py"],
      "env": {}
    }
  }
}
```

打开开关，工具列表出现 11 个工具即成功。Windows 用户注意：`command` 最好写 python.exe 全路径——`WindowsApps` 里那个 0 字节的商店占位符会把你送到微软商店，而不是茶汤。

然后在相应位置部署SKILL.md

## 开箱三步

1. **搬家**：「我搬到了外地」→ 把作者的 107 款茶清空（确认两次才动手，不误伤）
2. **进货**：「我买了龙井、大红袍、老白茶」→ 批量入库，参数自动按类别套好
3. **开喝**：「今天喝什么？」→ 剩下的事程序替你纠结

## 关于泡法（动手前先看这条）

**这不是功夫茶泡法。** 没有盖碗、没有快出汤、没有"一泡香二泡水三泡茶"。作者自用的是 **400ml 大茶壶 + 1.6L 冷泡壶、TDS20 纯净水**，一次注满、泡四五分钟、一次性出汤、茶水分离，路数接近茶叶审评和英式茶壶。所有投茶量、水温、时间都按这个场景校准。

茶具不一样？说一句「我的茶壶是 500ml」，投茶量自动按茶水比缩放，水温时间不动。冷泡同理。

## 复盘：让茶越喝越对味

理论参数只是起点，商家批次、仓储年份都会让茶偏离说明书。喝得不对味就说：

- **太淡 / 太浓 / 涩** → 自动微调投茶、时间、水温
- **仓气重 / 洗茶太过** → 调洗茶档位（生普默认：快洗1次+慢洗1次+散味2分钟；熟普/六堡/边销砖：快洗2次+慢洗1次+散味2分钟+快洗1次）
- **闷味 / 香气散** → 盖盖还是开盖
- **泡酸了 / 香味没了** → 水温降 3℃
- 调过头了说「重置XX」，一键回到理论值

所有数据都写在脚本旁边的 `state.json` 里，备份这一个文件，口味就能跟你搬家。

---

**仅供参考。** 茶是你的茶，嘴是你的嘴，参数是理论的，好喝才算数。程序不会泡茶，它只会抛一枚比较讲道理的硬币。

# 🍵 Man! What Tea Today? · tea-planner MCP

> **With no reason to hold a bowl of tea, I send it to those who love tea.** — Bai Juyi
> 
> **Brood not over the old country with old friends; light a new fire and try the new tea. Poetry and wine, while time is still ours.** — Su Shi

Here's how it started: the tea collection kept growing until opening the cabinet meant five minutes of blank staring, followed by grabbing whichever box was closest. Tea getting damp? My fault. Choice paralysis? Also my fault. So I made the program take the blame.

Thus this MCP living inside Cherry Studio — "What Tea Today?". It ships with brewing parameters for 107 teas (green, oolong, dark, black, white, yellow, jasmine, plus a bunch of oddities that defy categorization). Every day it flips a coin for you — but a coin with reasons: weighted by season, time of day, what you drank recently, and how long each tea has been gathering dust. Ripe pu-erh can still win in summer (just less likely), and late nights won't be limited to herbal tisanes — the rules are soft. No tea gets a death sentence.

## The 11 tools

| Tool | What you say |
|---|---|
| `recommend` | What should I drink today? |
| `coldbrew_recommend` | What should I cold-brew today? |
| `add_tea` | I bought Longjing, Tieguanyin, Lapsang Souchong (batch supported) |
| `remove_tea` | I finished the Biluochun |
| `clear_inventory` | I moved to another city (one-click wipe — don't inherit the author's tea cabinet) |
| `set_brewer` | My teapot is 300ml / my cold-brew pitcher is now 2L |
| `review` | Too weak / too bitter / warehouse musty / over-rinsed / stewed / turned sour / aroma gone |
| `record` / `undo_record` / `history` | I drank X / undo that / what have I been drinking |

## Deploy (Cherry Studio, two minutes)

Requires Python 3.10+:

```bash
pip install "mcp[cli]"
```

Cherry Studio → Settings → MCP Servers → Import this JSON (swap in your own path):

```json
{
  "mcpServers": {
    "tea-planner": {
      "command": "python",
      "args": ["C:\\your\\path\\tea-planner\\tea_planner.py"],
      "env": {}
    }
  }
}
```

Flip the switch, and once 11 tools show up you're done. Windows users: write the full path to python.exe — the 0-byte store stub in `WindowsApps` will send you to the Microsoft Store, not to tea.

Prefer not to install Python? Drop `SKILL.md` into Cherry Studio's Skills folder for a prompt-only fallback (no persistence, but works out of the box).

## Three steps after install

1. **Move in**: say "I moved to another city" — wipes the author's 107 teas (double confirmation, no accidents)
2. **Stock up**: "I bought Longjing, Dahongpao, aged white tea" — batch import, parameters auto-assigned by category
3. **Drink**: "What should I drink today?" — let the program do the agonizing

## About the brewing method (read before you pour)

**This is not gongfu style.** No gaiwan, no flash infusions, no "first steep aroma, second steep water, third steep flavor". The author brews with a **400ml teapot + 1.6L cold-brew pitcher and TDS-20 purified water**: fill once, steep four to five minutes, pour it all out at once, separate leaf from liquor — closer to tea evaluation cupping and the English teapot. Every dose, temperature, and time is calibrated for that setup.

Different gear? Say "my teapot is 500ml" and the leaf dose scales with the water ratio automatically — temperature and time stay put. Same for cold brew.

## Review: teaching the tea to suit you

Theoretical parameters are just a starting point. Vendors' batches, warehouse years, and storage will all push a tea off its spec sheet. If it tastes wrong, say so:

- **Too weak / too strong / astringent** → auto-tunes dose, time, temperature
- **Warehouse musty / over-rinsed** → adjusts the rinse routine (sheng pu-erh default: 1 quick rinse + 1 slow rinse + 2 min airing; shou pu-erh / liubao / border brick: 2 quick + 1 slow + 2 min airing + 1 quick)
- **Stewed / aroma fading** → lid on or lid off
- **Turned sour / aroma gone** → temperature down 3°C
- Overshot? Say "reset XX" and it's back to the theory

Everything lives in `state.json` next to the script. Back up that one file and your taste moves house with you.

---

**For reference only.** Your tea is your tea, your mouth is your mouth, the parameters are theoretical, and only the taste counts. The program can't brew — it just flips a fairly sensible coin.

# 🍵 嗚呼、諸君ヨ！我々ハ今日ハ何ヲ飮ムカ！ · tea-planner MCP

> **由無ク一碗ヲ持シ、茶ヲ愛スル人ニ寄ス。** —— 白居易
>
> **故人ニ對シテ故國ヲ思フ事休メヨ、且ク新火ヲ將テ新茶ヲ試ミヨ。詩酒ハ年華ニ趁ヘ。** —— 蘇軾

事ノ始マリハ斯ウダ。御茶ノ在庫ガ增エ續ケ、戸棚ヲ開ケル度ニ5分間ボンヤリ立チ盡クシ、結局一番手近ナ箱ヲ掴ム樣ニナッタ。茶葉ガ濕氣ルノハ私ノ所爲。選擇困難モ私ノ所爲。其レ故ニ計畫ニ責任ヲ負ハセタ。

斯ウシテCherry Studio上デ動クMCP「今日ハドノ御茶ニスル？」ガ生マレタ。107種類ノ茶ノ急須抽出條件（綠茶、烏龍茶、黑茶、紅茶、白茶、黃茶、花茶、其ノ他分類不能ナ變ハリ種）ヲ内藏シ、每日**理由ノ有ル硬貨**ヲ投ゲテ呉レル。季節、時間帶、月月火水木金金、最近飮ンダ如何カ、在庫ノ埃被リ度合イデ重ミ付ケ抽選ス。夏デモ熟普洱ガ當タル事ハ有ル。唯ダ確率ガ低イダケ。深夜ニ代用茶許リヲ押シ付ケル事モ爲ナイ——規則ハ柔ラカク、死刑判決ヲ受ケル御茶ハ無イ。

## 道具一覽（11箇）

| 道具 | 貴方ノ言葉 |
|---|---|
| `recommend` | 今日ハ何ヲ飮ム？ |
| `coldbrew_recommend` | 今日ハ何ヲ水出シスル？ |
| `add_tea` | 龍井茶、鐵觀音、正山小種ヲ買ッタ（一括登録對應） |
| `remove_tea` | 碧螺春ヲ飮ミ切ッタ |
| `clear_inventory` | 引ッ越シタ（一回操作デ全消去——作者ノ茶櫃ヲ引キ繼ガナイ） |
| `set_brewer` | 急須ハ300ml / 水出シ容器ヲ2Lニ變ヘタ |
| `review` | 薄スギル / 苦イ / 倉庫臭 / 洗茶シスギ / 蒸レ味 / 酸ッパクナッタ / 香リガ飛ンダ |
| `record` / `undo_record` / `history` | 〇〇ヲ飮ンダ / 記錄ヲ撤回 / 最近何ヲ飮ンダ？ |

## 配備（Cherry Studio、2分）

Python 3.10以上ガ必要：

```bash
pip install "mcp[cli]"
```

Cherry Studio → 設定 → MCPサーバー → 此ノJSONヲ取込（經路ハ自分ノ環境ニ置キ換ヘ）：

```json
{
  "mcpServers": {
    "tea-planner": {
      "command": "python",
      "args": ["C:\\your\\path\\tea-planner\\tea_planner.py"],
      "env": {}
    }
  }
}
```

開閉器ヲ入レニシ、道具一覽ニ11箇ノ道具ガ表示サレレバ成功。Windowsユーザーヘノ注意：`command` ニハ python.exe ノ完全經路ヲ書ク事。`WindowsApps` 内ノ0バイトノストア用スタブハ、御茶デハナク Microsoft Store ヘ連レテ行ッテ仕舞ウ。

Pythonヲ入レタクナイ場合ハ、`SKILL.md` ヲ Cherry Studio ノ Skills フォルダニ入レルト、指示文ノミノ代替手段ガ使ヘル（永續化ハサレナイガ、直グ使ヘル）。

## 導入後3手順

1. **引ッ越ス**：「引ッ越シタ」ト言ウ → 作者ノ107種類ノ御茶ヲ消去（誤操作防止ノ爲2回確認）
2. **仕入レル**：「龍井茶、大紅袍、熟成白茶ヲ買ッタ」 → 一括登録、條件ハ分類別ニ自動設定
3. **飮ム**：「今日ハ何ヲ飮ム？」 → 後ハ計畫ガ惱ンデ呉レル

## 淹レ方ニ就イテ（注グ前ニ讀ム事）

**コレハ工夫茶式デハ有リマセン。** 蓋碗モ、高速抽出モ、「一煎目ハ香リ、二煎目ハ水、三煎目ハ茶」モ有リマセン。作者ガ普段使ッテヰルノハ **400mlノ大急須 + 1.6Lノ水出シ容器、TDS20ノ純水**。一度ニ滿タシ、4〜5分蒸ラシ、一氣ニ注ギ出シテ茶葉ト茶湯ヲ分離スル——茶ノ官能審査ヤ鬼畜米英式茶壺ニ近イ遣リ方デス。總テノ茶葉量、湯温、時間ハ此ノ構成ニ合ハセテ調整サレテヰマス。

道具ガ違ウ？「急須ハ500ml」ト言ヘバ、茶葉量ガ茶水比ニ應ジテ自動デ調整サレ、湯温ト時間ハ變ハラナイ。水出シモ同様。

## 評價：御茶ヲ貴方好ミニ育テル

理論上ノ條件ハ出發點ニ過ギマセン。販賣元ノロット、倉庫デノ年数、保存狀態ニ因ッテ、御茶ハ仕様書カラ外レテ行キマス。味ガ合ハナイト感ジタラ、然ウ言ッテ下サイ：

- **薄スギル / 濃スギル / 澁イ** → 茶葉量・時間・湯温ヲ自動微調整
- **倉庫臭ガ强イ / 洗茶シスギ** → 洗茶手順ヲ調整（生普洱初期設定：高速洗イ1回＋低速洗イ1回＋2分空氣ニ當テル。熟普洱／六堡茶／邊境磚茶：高速洗イ2回＋低速洗イ1回＋2分空氣ニ當テル＋高速洗イ1回）
- **蒸レ味 / 香リガ飛ブ** → 蓋ヲスルカ開ケルカ
- **酸ッパクナッタ / 香リガ消ヘタ** → 湯温ヲ3℃下ゲル
- 調整シスギタラ「〇〇ヲ初期化」ト言ヘバ、一回操作デ理論値ニ戻ル

總テノ情報ハスクリプトノ隣ニ有ル `state.json` ニ保存サレマス。此ノファイル一ツヲ控ヘトシテ保存スレバ、貴方ノ味ノ好ミモ一緒ニ引ッ越セマス。

---

**御參考マデニ。** 御茶ハ貴方ノ御茶、口ハ貴方ノ口、條件ハ理論値、而シテ美味シサコソガ正義。計畫ハ御茶ヲ淹レラレマセン。唯ダ、ソコソコ理屈ノ有ル硬貨ヲ投ゲルダケデス。

# 🍵 キョウ サ、ドノ ティー ニ スル？ · tea-planner MCP

> ワケ モ ナク ティー ヲ イッパイ イレテ、ティー ガ スキ ナ ヒト ニ プレゼント。—— ハク キョイ
>
> フルイ トモダチ ト フルサト ノ コト ナンカ シンク スル ノ ヤメテ、アタラシイ ヒ デ アタラシイ ティー ヲ トライ シヨウ。ポエトリー ト ワイン ハ、タイム ガ ヤング ナ ウチ ニ エンジョイ シロ。—— ソ ショク

コト ノ ハジマリ ハ コウ。ティーコレクション ガ ドンドン グロー シテ、キャビネット オープン スル タビ ニ 5ミニッツ ボーッ ト スタンド シテ、ケッキョク イチバン テジカ ナ ボックス グラブ スル ヨウ ニ ナッタ。ティーリーフ ガ ダンプ ニ ナル ノ ハ マイ フォールト。チョイスパラライシス モ マイ フォールト。ダカラ プログラム ニ レスポンシビリティ オシッツケタ。

コウシテ Cherry Studio ノ ウエ デ ラン スル MCP「キョウ ワ ドノ ティー？」ガ ボーン シタ。107タイプ ノ ティー ノ ポットブリュー パラメータ（グリーンティー、ウーロンティー、ダークティー、ブラックティー、ホワイトティー、イエローティー、フラワーティー、ソノタ クラシファイ フノウ ナ ウィアード ナ ヤツ）ヲ ビルトイン シテ、エブリデイ リーズナブル ナ コイン ヲ トス シテ クレル。シーズン、タイムオブデイ、レセントリー ドリンク シタカ、インベントリー ノ ダスト レベル デ ウェイテッド ロット スル。サマー デモ ライププーアル ガ ヒット スル コト アル。タダ プロバビリティ ガ ロー ナ ダケ。レイトナイト ニ ハーバルティー バッカリ プッシュ スル コト モ シナイ——ルール ワ ソフト デ、デス センテンス ヲ イイワタサレル ティー ハ ナイ。

## ツールリスト（11コ）

| ツール | アナタ ノ コトバ |
|---|---|
| `recommend` | キョウ ワ ナニ ドリンク スル？ |
| `coldbrew_recommend` | キョウ ワ ナニ コールドブリュー スル？ |
| `add_tea` | ロンジン、テツカンノン、ラプサンスーチョン ゲット シタ（バッチ サポート ツキ） |
| `remove_tea` | ビールオチュン フィニッシュ シタ |
| `clear_inventory` | ムーブ シタ（ワンクリック ワイプ——オーサー ノ ティーキャビネット ヲ インヘリット シナイ） |
| `set_brewer` | マイ ティーポット ハ 300ml / コールドブリューポット ヲ 2L ニ チェンジ シタ |
| `review` | ウィークスギル / ビター / ウェアハウスムスティ / リンス シスギ / スチュード / サワー ニ ナッタ / アロマ ガ ゴーン |
| `record` / `undo_record` / `history` | 〇〇 ドリンク シタ / レコード アンドゥ / レセントリー ナニ ドリンク シタ？ |

## デプロイ（Cherry Studio、2ミニッツ）

Python 3.10+ ガ イル：

```bash
pip install "mcp[cli]"
```

Cherry Studio → セッティング → MCPサーバー → コノ JSON ヲ インポート（パス ワ ユア ノ ニ リプレイス）：

```json
{
  "mcpServers": {
    "tea-planner": {
      "command": "python",
      "args": ["C:\\your\\path\\tea-planner\\tea_planner.py"],
      "env": {}
    }
  }
}
```

スイッチ オン ニ シテ、ツールリスト ニ 11コ アピア シタラ サクセス。Windows ノ ヒト ヘ ノ アテンション：`command` ニ ワ python.exe ノ フルパス ヲ ライト スル コト。`WindowsApps` ノ ナカ ノ ゼロバイト ノ ストアスタブ ワ、ティー ジャ ナクテ Microsoft Store ニ テイク シチャウ。

Python インストール シタクナイ ヒト ワ、`SKILL.md` ヲ Cherry Studio ノ Skills フォルダ ニ パット スレバ、プロンプトオンリー ノ フォールバック ガ ユーズ デキル（パーシステンス ハ ナイ ケド、アウトオブボックス デ ユーズ デキル）。

## インストール ノ アト 3ステップ

1. **ムーブイン**：「ムーブ シタ」ト イエバ → オーサー ノ 107タイプ ノ ティー ゼンブ ワイプ（ミステイク フセグ タメ ニ 2カイ コンファーム）
2. **ストック**：「ロンジン、ダーホンパオ、エイジドホワイトティー ゲット シタ」 → バッチ インポート、パラメータ ワ カテゴリー ベツ ニ オート セット
3. **ドリンク**：「キョウ ワ ナニ ドリンク スル？」 → アト ワ プログラム ガ ワリー シテ クレル

## ブリューイング ニ ツイテ（ポア スル マエ ニ リード シテ）

**コレ ワ ゴンフースタイル ジャ ナイ。** ガイワン モ、フラッシュインフュージョン モ、「ファースト インフュージョン ワ アロマ、セカンド ワ ウォーター、サード ワ フレーバー」モ ナイ。オーサー ガ ユーズ シテル ノ ワ **400ml ノ ビッグ ティーポット + 1.6L ノ コールドブリューポット、TDS20 ノ ピュアウォーター**。ワンタイム デ フィル シテ、4〜5ミニッツ スティープ シテ、ワンゴー デ ポアアウト シテ ティーリーフ ト リカー ヲ セパレート スル——ティー キュッピング ヤ ブリティッシュ ティーポット ニ クロース ナ アプローチ。スベテ ノ リーフリョウ、テンペラチャー、タイム ワ コノ セットアップ ニ キャリブレーション サレテル。

ギア ガ ディファレント？「マイ ティーポット ハ 500ml」ト イエバ、リーフリョウ ガ ティーウォーターレシオ ニ オウジテ オート デ スケール サレル。テンペラチャー ト タイム ワ チェンジ シナイ。コールドブリュー モ セイム。

## レビュー：ティー ヲ ユア テイスト ニ グロー サセル

セオリー ノ パラメータ ワ タダ ノ スタートポイント。ベンダー ノ ロット、ウェアハウス イヤー、ストレージ コンディション ニ ヨッテ、ティー ワ スペックシート カラ デビエート シテ イク。テイスト ガ ヘン ダト フィール シタラ、ソノママ セイ シテ イイ：

- **ウィークスギル / ストロングスギル / アストリンジェント** → リーフリョウ・タイム・テンペラチャー ヲ オート ファインチューン
- **ウェアハウスムスティ / リンス シスギ** → リンス ルーチン ヲ アジャスト（ナマ プーアル デフォルト：クイック リンス 1カイ + スロー リンス 1カイ + 2ミニッツ エアリング。ライプ プーアル / リュウバオ / ボーダーブリック：クイック 2カイ + スロー 1カイ + 2ミニッツ エアリング + クイック 1カイ）
- **スチュード / アロマ フェーディング** → リッド オン カ リッド オフ カ
- **サワー ニ ナッタ / アロマ ゴーン** → テンペラチャー ヲ 3℃ ダウン
- オーバーチューン シタラ「〇〇 リセット」テ イエバ、ワンクリック デ セオリー ニ バック

データ ワ ゼンブ スクリプト ノ トナリ ノ `state.json` ニ セーブ サレテル。コノ ファイル ダケ バックアップ スレバ、ユア テイスト プリファレンス モ イッショ ニ ムーブ デキル。

---

**マジ、サンコウ ニ シテ ネ。** ティー ワ ユア ティー、マウス ワ ユア マウス、パラメータ ワ セオリー、オイシサ コソ ガ ジャスティス。プログラム ワ ティー ヲ ブリュー デキナイ。タダ ソコソコ リーズナブル ナ コイン ヲ トス シテル ダケダヨ。

# 🍵 오늘은 뭘 마실까 · tea-planner MCP

> **이유(理由) 없이 한 사발을 들어, 차(茶)를 사랑하는 이에게 부치노라.** — 백거이(白居易)
>
> **고인(故人)과 고국(故國) 생각은 그만두고, 새 불로 새 차(茶)를 시험(試驗)하라. 시(詩)와 술, 청춘(靑春)이 바로 지금이다.** — 소식(蘇軾)

사정(事情)은 이렇습니다: 집에 차(茶)가 점점(漸漸) 많아져서, 찬장(饌欌)을 열 때마다 5분(五分鐘) 동안 멍하니 있다가, 결국(結局) 손(手)에 가장 가까운 한 통(桶)을 집게 됩니다. 차(茶)가 습기(濕氣)를 먹는 건 제 탓, 선택(選擇) 장애(障礙)도 제 탓이니, 프로그램(program)이 뒤집어쓰게 만든 겁니다.

그래서 Cherry Studio 위에 얹은 이 MCP(엠시피) — “오늘은 뭘 마실까”. 107가지 차(茶)의 호포(壺泡) 매개변수(媒介變數)를 내장(內藏)하고 있습니다 (녹차(綠茶), 우롱차(烏龍茶), 흑차(黑茶), 홍차(紅茶), 백차(白茶), 황차(黃茶), 화차(花茶), 그리고 어디에 넣어야 할지 애매한 괴상한 것들까지). 매일(每日) 여러분 대신 **이유(理由) 있는 동전(銅錢)** 을 던져줍니다: 계절(季節), 시간대(時間帶), 최근(最近)에 마셨는지 여부(與否), 재고(在庫)가 먼지를 뒤집어쓴 정도(程度)를 가중(加重)해 추첨(抽籤)합니다. 여름에도 숙보(熟普)가 뽑힐 수 있지만, 확률(確率)이 낮을 뿐입니다. 늦은 밤에도 대용차(代用茶)만 떠안기지 않습니다. 규칙(規則)은 부드럽고, 어떤 차(茶)도 사형(死刑) 선고(宣告)를 받지 않습니다.

## 도구(道具) 11개

| 도구(道具) | 이렇게 말하세요 |
|---|---|
| `recommend` | 오늘 뭐 마실까요? |
| `coldbrew_recommend` | 오늘 냉포(冷泡) 뭐 할까요? |
| `add_tea` | 용정(龍井), 철관음(鐵觀音), 정산소종(正山小種) 샀어요 (일괄(一括) 지원(支援)) |
| `remove_tea` | 벽라춘(碧螺春) 다 마셨어요 |
| `clear_inventory` | 외지(外地)로 이사(移徙)했어요 (한 번에 비우기 — 작가(作家)의 차(茶) 찬장(饌欌)을 물려받지 마세요) |
| `set_brewer` | 제 다관(茶罐)은 300ml예요 / 냉포(冷泡) 주전자를 2L로 바꿨어요 |
| `review` | 너무 연해요 / 좀 써요 / 창고(倉庫) 냄새가 나요 / 세차(洗茶)가 과해요 / 민미(悶味)가 나요 / 시어졌어요 / 향(香)이 없어졌어요 |
| `record` / `undo_record` / `history` | XX 마셨어요 / 잘못 기록(記錄)했으니 되돌리기 / 최근(最近)에 뭐 마셨죠 |

## 배포(部署) (Cherry Studio, 2분(分))

Python 3.10+ 필요(必要):

```bash
pip install "mcp[cli]"
```

Cherry Studio → 설정(設定) → MCP 서버(server) → 이 JSON(제이슨) 가져오기 (경로(經路)를 본인 것으로 바꾸세요):

```json
{
  "mcpServers": {
    "tea-planner": {
      "command": "python",
      "args": ["C:\\your\\path\\tea-planner\\tea_planner.py"],
      "env": {}
    }
  }
}
```

스위치를 켜고 도구(道具) 목록(目錄)에 11개 도구(道具)가 나타나면 성공(成功)입니다. Windows 사용자(使用者)는 주의(注意): `command`에 python.exe 전체 경로(全體 經路)를 쓰는 것이 좋습니다 — `WindowsApps` 안의 0바이트 스토어 자리표시자(placeholder)는 당신을 마이크로소프트 스토어로 보내지, 차(茶)로 보내지 않습니다.

그런 다음 해당(該當) 위치(位置)에 SKILL.md를 배포(部署)하세요.

## 개봉(開封) 3단계(三段階)

1. **이사(移徙)**: “외지(外地)로 이사(移徙)했어요” → 작가(作家)의 107가지 차(茶)를 비웁니다 (두 번 확인(確認) 후 실행(實行), 실수(失手) 방지(防止))
2. **입고(入庫)**: “용정(龍井), 대홍포(大紅袍), 노백차(老白茶) 샀어요” → 일괄(一括) 입고(入庫), 매개변수(媒介變數)는 자동(自動)으로 분류(分類)에 따라 설정(設定)됩니다
3. **시음(試飮)**: “오늘 뭐 마실까요?” → 나머지는 프로그램(program)이 대신(代身) 고민(苦悶)합니다

## 포법(泡法)에 관해 (따르기 전에 먼저 읽으세요)

**이것은 공푸차(工夫茶) 포법(泡法)이 아닙니다.** 개완(蓋碗)도 없고, 빠른 출탕(出湯)도 없고, “첫 우리 향(香), 둘째 물, 셋째 차(茶)”도 없습니다. 저자(著者)가 쓰는 것은 **400ml 대형(大型) 다관(茶罐) + 1.6L 냉포(冷泡) 주전자, TDS20 정제수(淨製水)** 입니다. 한 번 가득 붓고, 4~5분(分) 우리고, 한 번에 전부 출탕(出湯)하고, 차(茶)와 물을 분리(分離)합니다. 차(茶) 심사(審査)나 영국식(英國式) 티포트(teapot)에 가깝습니다. 모든 투차량(投茶量), 수온(水溫), 시간(時間)은 이 시나리오(scenario)에 맞춰 보정(補正)되어 있습니다.

차 도구(道具)가 다르면? "내 다관(茶罐)은 500ml예요"라고 말하면 투차량(投茶量)이 자동(自動)으로 차수(茶水) 비율(比率)에 따라 조정(調整)됩니다. 수온(水溫)과 시간(時間)은 그대로입니다. 냉포(冷泡)도 동일(同一)합니다.

## 복기(復碁): 차(茶)를 마실수록 입맛에 맞게

이론적(理論的) 매개변수(媒介變數)는 출발점(出發點)일 뿐입니다. 상인(商人) 배치(batch), 창고(倉庫) 연도(年度), 저장(貯藏) 상태(狀態)에 따라 차(茶)가 설명서(說明書)에서 벗어납니다. 맛이 이상하면 말하세요:

- **너무 연함 / 너무 진함 / 떫음** → 투차량(投茶量), 시간(時間), 수온(水溫) 자동(自動) 미세 조정(微細 調整)
- **창고(倉庫) 냄새 / 세차(洗茶) 과다(過多)** → 세차(洗茶) 단계(段階) 조정(調整) (생푸(生普) 기본(基本): 빠른 세차 1회(一回) + 느린 세차 1회(一回) + 2분(分) 산미(散味); 숙푸(熟普)/육보(六堡)/변소전(邊銷磚): 빠른 2회(二回) + 느린 1회(一回) + 2분(分) 산미(散味) + 빠른 1회(一回))
- **민미(悶味) / 향(香)이 흩어짐** → 뚜껑을 덮거나 엶
- **시어짐 / 향(香)이 사라짐** → 수온(水溫) 3℃ 하락(下落)
- 과하게 조정(調整)했으면 "XX 리셋"이라고 말하세요 — 이론값(理論값)으로 복귀(復歸)

모든 데이터(資料)는 스크립트 옆 `state.json`에 저장(貯藏)됩니다. 이 파일(文件) 하나만 백업(backup)하면 입맛이 이사(移徙)해도 따라갑니다.

---

**참고(參考)만 하세요.** 차(茶)는 당신의 차(茶), 입은 당신의 입, 매개변수(媒介變數)는 이론적(理論的)이고, 맛있어야 진짜입니다. 프로그램(program)은 차(茶)를 우리지 못합니다. 그저 제법 사리(事理) 있는 동전(銅錢) 하나를 던질 뿐입니다.

# 🍵 Hôm nay uống gì · tea-planner MCP

> **无由持一碗，寄与爱茶人。** (Không cớ gì mà nâng chén trà（茶）, xin gửi tặng người yêu trà（茶）.) —— Bạch Cư Dị（白居易）
>
> **休对故人思故国，且将新火试新茶。诗酒趁年华。** (Đừng đối diện cố nhân（故人） mà nhớ cố quốc（故國）, hãy nhóm lửa mới pha thử trà（茶） mới. Thơ（詩） và rượu, kịp lúc tuổi xuân（春）.) —— Tô Thức（蘇軾）

Chuyện là thế này: trà trong nhà ngày càng nhiều, nhiều đến mức mỗi lần mở tủ là ngẩn người năm phút, cuối cùng vẫn lấy hộp gần tay nhất. Trà bị ẩm thì trách mình, khó chọn cũng trách mình, chi bằng để chương trình（章程） gánh tội.

Thế là có MCP này treo trên Cherry Studio —— 「Hôm nay uống gì」. Tích hợp（集合） sẵn tham số（參數） pha trà（茶） cho 107 loại trà（trà xanh（綠茶）, ô long（烏龍）, hắc trà（黑茶）, hồng trà（紅茶）, bạch trà（白茶）, hoàng trà（黃茶）, hoa trà（花茶）, cùng một đống thứ kỳ quái khó phân loại（分類）), mỗi ngày thay bạn tung một **đồng xu có lý do（理由）**: theo mùa, thời điểm（時點） trong ngày, gần đây có uống hay không, mức độ bám bụi tồn kho（存庫） mà gia quyền（加權） rút thăm. Mùa hè vẫn có thể trúng Phổ Nhĩ thục（普洱熟）, chỉ là xác suất（確率） thấp; đêm khuya cũng không nhét cho bạn toàn trà thay thế（茶代替） —— quy tắc（規則） mềm, không có loại trà nào bị kết án tử hình（死刑）.

## Có những công cụ（工具） gì (11 cái)

| Công cụ（工具） | Bạn nói gì |
|---|---|
| `recommend` | Hôm nay uống gì? |
| `coldbrew_recommend` | Hôm nay pha lạnh gì? |
| `add_tea` | Tôi mua Long Tỉnh（龍井）, Thiết Quan Âm（鐵觀音）, Chính Sơn Tiểu Chủng（正山小種） (hỗ trợ（互助） nhập hàng loạt（行率）) |
| `remove_tea` | Tôi uống hết Bích La Xuân（碧螺春） rồi |
| `clear_inventory` | Tôi chuyển nhà đến nơi khác (một nút xóa sạch, đừng kế thừa（繼承） tủ trà của tác giả（作者）) |
| `set_brewer` | Ấm trà của tôi là 300ml / bình pha lạnh đổi thành 2L |
| `review` | Quá nhạt / hơi đắng / mùi kho nặng / rửa trà quá tay / mùi hầm / bị chua / mất hương（香） |
| `record` / `undo_record` / `history` | Tôi uống XX / Ghi nhầm thì thu hồi（收回） / Gần đây đã uống gì |

## Triển khai（展開） (Cherry Studio, hai phút)

Cần Python 3.10+:

```bash
pip install "mcp[cli]"
```

Cherry Studio → Cài đặt → MCP Servers → Nhập đoạn JSON này (đổi đường dẫn（路引） thành của bạn):

```json
{
  "mcpServers": {
    "tea-planner": {
      "command": "python",
      "args": ["C:\\your\\path\\tea-planner\\tea_planner.py"],
      "env": {}
    }
  }
}
```

Bật công tắc（工則）, danh sách（名冊） công cụ（工具） xuất hiện（出現） 11 công cụ（工具） là thành công（成功）. Người dùng Windows lưu ý（留意）: `command` tốt nhất nên ghi đường dẫn（路引） đầy đủ của python.exe —— cái stub 0 byte trong `WindowsApps` sẽ đưa bạn đến Microsoft Store, chứ không phải chén trà（茶）.

Không muốn cài Python? Thả `SKILL.md` vào thư mục（書目） Skills của Cherry Studio để dùng bản fallback chỉ chạy prompt (không lưu trạng thái（狀態）, nhưng dùng được ngay).

## Ba bước sau khi cài

1. **Chuyển nhà**: 「Tôi chuyển nhà đến nơi khác」→ xóa sạch 107 loại trà của tác giả（作者） (xác nhận（確認） hai lần mới thực hiện（實現）, không xóa nhầm)
2. **Nhập hàng（入行）**: 「Tôi mua Long Tỉnh（龍井）, Đại Hồng Bào（大紅袍）, lão bạch trà（老白茶）」→ nhập kho（入庫） hàng loạt, tham số（參數） tự động（自動） phân loại（分類） theo chủng loại（種類）
3. **Uống trà（茶）**: 「Hôm nay uống gì?」→ việc còn lại để chương trình（章程） thay bạn đau đầu

## Về cách pha (đọc trước khi rót)

**Đây không phải cách pha trà công phu（功夫茶）.** Không có gaiwan（蓋碗）, không có rót nhanh, không có “nhất phao hương, nhị phao thủy, tam phao trà（一泡香二泡水三泡茶）”. Tác giả（作者） tự dùng **ấm trà lớn 400ml + bình pha lạnh 1.6L, nước tinh khiết（純潔） TDS20**, một lần rót đầy, pha bốn năm phút, rót ra một lần, tách trà（茶） khỏi nước, lối pha gần với đánh giá cảm quan trà（茶葉審評） và ấm trà kiểu Anh. Mọi lượng trà, nhiệt độ（溫度）, thời gian（時間） đều được hiệu chỉnh（校正） theo bối cảnh（背景） này.

Dụng cụ trà（茶具） khác ư? Nói một câu「Ấm trà của tôi là 500ml」, lượng trà tự động（自動） co giãn theo tỷ lệ（比例） trà-nước, nhiệt độ（溫度） và thời gian（時間） giữ nguyên. Pha lạnh cũng tương tự（相似）.

## Phục bàn（復盤）: để trà càng uống càng hợp khẩu vị（口味）

Tham số（參數） lý thuyết（理論） chỉ là điểm xuất phát（出發點）; lô hàng của người bán, năm tồn kho（存庫） đều khiến trà lệch khỏi sách hướng dẫn（向引）. Uống thấy không hợp khẩu vị（口味） thì nói:

- **Quá nhạt / quá đậm / chát** → tự động（自動） vi chỉnh（微整） lượng trà, thời gian（時間）, nhiệt độ（溫度）
- **Mùi kho nặng / rửa trà quá tay** → điều chỉnh（調整） cấp độ rửa trà (Phổ Nhĩ sinh（普洱生） mặc định（默定）: rửa nhanh 1 lần + rửa chậm 1 lần + tản mùi（散味） 2 phút; Phổ Nhĩ thục（普洱熟）/ Lục Bảo（六堡）/ biên tiêu chuyên（邊銷磚）: rửa nhanh 2 lần + rửa chậm 1 lần + tản mùi（散味） 2 phút + rửa nhanh 1 lần)
- **Mùi hầm / hương thơm tản** → đậy nắp hay mở nắp
- **Bị chua / mất hương（香）** → nhiệt độ（溫度） nước giảm 3℃
- Chỉnh quá tay thì nói「reset XX」, một nút quay về giá trị（價值） lý thuyết（理論）.

Mọi dữ liệu（資料） đều ghi trong `state.json` cạnh script, sao lưu（備份） một file này, khẩu vị（口味） có thể theo bạn chuyển nhà.

---

**Chỉ để tham khảo（參考）.** Trà là trà của bạn, miệng là miệng của bạn, tham số（參數） là lý thuyết（理論）, uống ngon mới tính. Chương trình（章程） không biết pha trà, nó chỉ tung một đồng xu khá biết lý lẽ（理例）.


# 🍵 今日何茶飲 · tea-planner MCP

> 無由持一碗，寄與愛茶人。——白居易
>
> 休對故人思故國，且將新火試新茶。詩酒趁年華。——蘇軾

惟家中之茶日增，乃至啟櫝茫然，凝立半晌，終取去手最近者。茶受潮，咎在己；擇之難，咎亦在己；不如委其過於程序。遂有此掛於 Cherry Studio 之 MCP，名曰「今日飲何茶」。內置百有七品茶之壺泡參數（綠茶、青茶、黑茶、紅茶、白茶、黃茶、花茶，又有難歸何類之異品若干），每日代君擲一有據之錢：以季節、時辰、邇日飲否、庫藏積塵之久暫，權其輕重而抽籤。盛夏亦或得熟普，特其機微；深夜亦不惟以代用茶相塞——法度柔軟，無一茶遭棄。

## 器用十一

| 器 | 君之所言 |
|---|---|
| `recommend` | 今日飲何茶？ |
| `coldbrew_recommend` | 今日冷泡何茶？ |
| `add_tea` | 吾購龍井、鐵觀音、正山小種（可並列） |
| `remove_tea` | 吾飲盡碧螺春 |
| `clear_inventory` | 吾遷居異地（一鍵清空，毋承余之茶櫝） |
| `set_brewer` | 吾壺三百毫升 / 冷泡壺易二升 |
| `review` | 太淡 / 微苦 / 倉氣重 / 洗茶過甚 / 悶味 / 泡酸 / 香氣盡 |
| `record` / `undo_record` / `history` | 吾飲某茶 / 誤記撤回 / 近飲何茶 |

## 部署法（Cherry Studio，頃刻可成）

須 Python 3.10 以上：

```bash
pip install "mcp[cli]"
```

Cherry Studio → 設置 → MCP 服務器 → 導入此 JSON（路徑易以君之實徑）：

```json
{
  "mcpServers": {
    "tea-planner": {
      "command": "python",
      "args": ["C:\\your\\path\\tea-planner\\tea_planner.py"],
      "env": {}
    }
  }
}
```

啟其開關，工具列表現十一器即成功。Windows 用者慎之：`command` 宜書 python.exe 全徑——`WindowsApps` 中零字節之商店佔位符，將導君至微軟商店，而非茶湯。

復於相應處部署 `SKILL.md`。不願裝設 Python 者，亦可置 `SKILL.md` 於 Cherry Studio 之 Skills 目錄，徒以提示詞權充（無持久之功，然開箱即用）。

## 初用三步

1. **遷居**：「吾遷居異地」→ 清空余之一百七品茶（兩度確認乃行，不誤傷）
2. **進貨**：「吾購龍井、大紅袍、老白茶」→ 成批入庫，參數依類自定
3. **開飲**：「今日飲何茶？」→ 餘事付程序躊躇

## 論泡法（操壺前先觀此）

**此非工夫茶法也。** 無蓋碗，無疾出湯，無「一泡香二泡水三泡茶」之說。余自用 **四百毫升大壺、一升六冷泡壺、TDS 二十純水**，一注而滿，瀹四五分鐘，一傾而盡，茶水分離，其路數近茶葉審評與英式茶壺。投茶之量、水溫、時長，悉按此境校定。

茶具有異？但言「吾壺五百毫升」，投茶量即按茶水比增損，水溫與時長不改。冷泡亦然。

## 復盤：使茶愈飲愈合口

紙上參數，徒為起點。商戶批次、倉儲年份，皆足使茶背離譜籍。飲之不合，便直言：

- **太淡 / 太濃 / 澀** → 自動微調投茶、時長、水溫
- **倉氣重 / 洗茶過甚** → 調洗茶之檔（生普默認：快洗一次+慢洗一次+散味二分鐘；熟普/六堡/邊銷磚：快洗二次+慢洗一次+散味二分鐘+快洗一次）
- **悶味 / 香氣散** → 加蓋抑或開蓋
- **泡酸 / 香氣盡** → 水溫降三度
- 調之過甚，言「重置某茶」，一鍵復歸紙上之值

諸數據咸存於腳本旁之 `state.json` 中；但備份此一文件，口味便可隨君遷徙。

---

**僅供參酌。** 茶乃君之茶，口乃君之口，參數乃紙上之談，甘旨方為準。程序不能瀹茗，惟擲一枚稍近情理之錢耳。
