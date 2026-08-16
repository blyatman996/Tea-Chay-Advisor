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
