#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
「今天喝什么」茶饮推荐 MCP Server（v1.8）
========================================

场景约定
--------
  - 器具：默认 400ml 茶壶 + 1.6L 冷泡壶；可用 set_brewer 修改容量，投茶量自动等比缩放
  - 泡法：壶泡法，只泡一泡，不续水
  - 水质：TDS ≈ 20 纯净水（软水）
  - 温度：软水浸出率高、无离子缓冲、苦涩易显 → 嫩绿茶水温比常规建议再降 2~3℃

参数校准原则
------------
  - 茶水比约 1:60~1:80（6g/400ml 基准），介于功夫泡(1:25)与审评法(1:50)之间
  - 浸泡时间接近审评法（GB/T 23776：红绿茶 4~5min、乌龙 5min），一次浸出到位
  - 碎茶/CTC 减量减时；紧压茶增量、先润茶；代用茶按物性单列

推荐算法（软权重 + 加权随机，绝不硬规则封杀）
--------------------------------------------
  weight = 季节亲和 × 时段亲和 × 节气彩蛋 × 疲劳降权 × 库存轮换加成 × 对数均匀噪声
  再用 softmax 温度 τ 加权无放回抽样；τ 由 randomness 参数控制（0=应季, 1=惊喜）
  例如：夏天熟普权重 0.7 而非 0 → 仍可能被抽中，只是概率低。
"""

from __future__ import annotations

import json
import math
import random
import re
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    from mcp.server import MCPServer            # mcp 2.x：FastMCP 已更名 MCPServer
    FastMCPCompat = MCPServer
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP as FastMCPCompat   # mcp 1.x
    except ImportError:
        from fastmcp import FastMCP as FastMCPCompat              # 独立 fastmcp 包

BASE = Path(__file__).resolve().parent
STATE_FILE = BASE / "state.json"

mcp = FastMCPCompat("tea-planner")  # 兼容 mcp 2.x / 1.x / 独立 fastmcp

# ----------------------------------------------------------------------------
# 亲和模板
# ----------------------------------------------------------------------------
SEA = {  # 季节亲和（春/夏/秋/冬，按节气划分）。所有值 > 0，只调概率、不封杀。
    "green":       dict(春=1.25, 夏=1.15, 秋=0.75, 冬=0.60),
    "green_flav":  dict(春=1.10, 夏=1.15, 秋=0.85, 冬=0.70),
    "flower":      dict(春=1.15, 夏=1.10, 秋=0.90, 冬=0.80),
    "white_new":   dict(春=1.00, 夏=1.20, 秋=0.90, 冬=0.90),
    "white_old":   dict(春=0.95, 夏=1.10, 秋=1.00, 冬=1.10),
    "yellow":      dict(春=1.15, 夏=0.95, 秋=1.00, 冬=0.85),
    "oolong_qing": dict(春=1.00, 夏=0.95, 秋=1.25, 冬=0.85),
    "oolong_nong": dict(春=0.90, 夏=0.80, 秋=1.20, 冬=1.25),
    "black":       dict(春=0.90, 夏=0.75, 秋=1.15, 冬=1.25),
    "black_ctc":   dict(春=0.85, 夏=0.70, 秋=1.15, 冬=1.30),
    "dark_ripe":   dict(春=0.85, 夏=0.70, 秋=1.10, 冬=1.30),
    "dark_raw":    dict(春=0.95, 夏=1.00, 秋=1.05, 冬=1.05),
    "dark_rawold": dict(春=0.90, 夏=0.85, 秋=1.10, 冬=1.25),
    "herbal_cool": dict(春=0.90, 夏=1.35, 秋=1.00, 冬=0.70),
    "herbal_warm": dict(春=0.85, 夏=0.70, 秋=1.15, 冬=1.40),
    "herbal_neu":  dict(春=1.00, 夏=1.05, 秋=1.05, 冬=1.00),
    "matcha":      dict(春=1.15, 夏=1.20, 秋=0.90, 冬=0.80),
}

TOD = {  # 时段亲和：早晨/上午/午后/下午/傍晚/夜晚/深夜。夜晚不封杀咖啡因，只降权。
    "green_hi":    dict(morning=0.80, late_morning=1.25, noon=1.10, afternoon=1.05, evening=0.60, night=0.25, deep_night=0.10),
    "flower":      dict(morning=0.85, late_morning=1.20, noon=1.05, afternoon=1.00, evening=0.70, night=0.30, deep_night=0.15),
    "white":       dict(morning=1.00, late_morning=1.10, noon=1.10, afternoon=1.05, evening=1.00, night=0.80, deep_night=0.40),
    "white_old":   dict(morning=1.00, late_morning=1.05, noon=1.10, afternoon=1.05, evening=1.05, night=0.95, deep_night=0.50),
    "yellow":      dict(morning=0.90, late_morning=1.15, noon=1.10, afternoon=1.00, evening=0.75, night=0.40, deep_night=0.15),
    "oolong_qing": dict(morning=0.85, late_morning=1.10, noon=1.15, afternoon=1.10, evening=0.70, night=0.35, deep_night=0.15),
    "oolong_nong": dict(morning=0.80, late_morning=1.05, noon=1.20, afternoon=1.15, evening=0.85, night=0.50, deep_night=0.20),
    "black":       dict(morning=1.15, late_morning=1.15, noon=1.05, afternoon=1.05, evening=0.75, night=0.35, deep_night=0.12),
    "black_ctc":   dict(morning=1.25, late_morning=1.10, noon=1.00, afternoon=0.95, evening=0.70, night=0.30, deep_night=0.10),
    "dark_ripe":   dict(morning=1.00, late_morning=1.00, noon=1.25, afternoon=1.10, evening=1.00, night=0.85, deep_night=0.35),
    "dark_raw":    dict(morning=0.80, late_morning=1.10, noon=1.20, afternoon=1.15, evening=0.70, night=0.30, deep_night=0.10),
    "herbal":      dict(morning=1.00, late_morning=1.00, noon=1.05, afternoon=1.00, evening=1.10, night=1.20, deep_night=0.90),
    "matcha":      dict(morning=1.10, late_morning=1.30, noon=1.00, afternoon=0.90, evening=0.50, night=0.15, deep_night=0.05),
    "cocoa":       dict(morning=1.00, late_morning=0.90, noon=0.90, afternoon=1.10, evening=1.25, night=1.00, deep_night=0.50),
}

SLOT_CN = {
    "morning": "早晨 5-9", "late_morning": "上午 9-12", "noon": "午后 12-15",
    "afternoon": "下午 15-18", "evening": "傍晚 18-21",
    "night": "夜晚 21-24", "deep_night": "深夜 0-5",
}

# ----------------------------------------------------------------------------
# 库存数据：107 款
# 字段: id, 名称, 类别, 说明, 投茶g, 水温℃, 浸泡min, 润茶秒, 咖啡因, 茶性,
#       季节模板, 时段模板, 备注
# 咖啡因: 高/中/低/无    茶性: 寒/凉/平/温（用于节气彩蛋与 mood 加权）
# ----------------------------------------------------------------------------
def _tea(i, name, cat, note, g, t, m, rinse, caff, thermo, sea, tod, tip=""):
    return dict(id=i, name=name, cat=cat, note=note, g=g, t=t, m=m, rinse=rinse,
                caff=caff, thermo=thermo, sea=SEA[sea], tod=TOD[tod], tip=tip)

TEAS = [
    # ---- 绿茶（21）----
    _tea("lv_aimin",    "爱民特尖",        "绿茶", "明前 一芽二叶", 6, 83, 4.0, 0, "高", "凉", "green", "green_hi"),
    _tea("lv_biluochun","碧螺春",          "绿茶", "明前 一芽二叶", 6, 82, 4.0, 0, "高", "凉", "green", "green_hi"),
    _tea("lv_huangshan","黄山毛峰",        "绿茶", "明前 一芽二叶", 6, 83, 4.0, 0, "高", "凉", "green", "green_hi"),
    _tea("lv_mogan",    "莫干黄芽",        "绿茶", "雨前 一芽二叶", 6, 85, 4.0, 0, "高", "凉", "green", "green_hi", "绿茶工艺，勿按黄茶泡"),
    _tea("lv_songluo",  "松萝茶",          "绿茶", "雨前",         6, 85, 4.0, 0, "高", "凉", "green", "green_hi"),
    _tea("lv_laoshan",  "崂山绿茶",        "绿茶", "雨前一芽二三叶", 6, 88, 4.5, 0, "高", "凉", "green", "green_hi", "北方茶叶片厚，可到90℃"),
    _tea("lv_qiangu",   "钱谷山绿茶",      "绿茶", "雨前一芽二三叶", 6, 85, 4.0, 0, "高", "凉", "green", "green_hi"),
    _tea("lv_guzhu",    "顾渚紫笋",        "绿茶", "茶饼",         7, 85, 5.0, 20, "高", "凉", "green", "green_hi", "紧压饼，先撬散、润茶20秒"),
    _tea("lv_jinyun",   "缙云毛峰",        "绿茶", "早春 一芽一二叶初展", 6, 82, 3.5, 0, "高", "凉", "green", "green_hi"),
    _tea("lv_yongchuan","永川秀芽",        "绿茶", "明前 一芽一叶初展", 6, 80, 3.5, 0, "高", "凉", "green", "green_hi", "特嫩，水温宁低勿高"),
    _tea("lv_enshi",    "恩施玉露",        "绿茶", "蒸青 明前一芽二叶", 6, 78, 3.5, 0, "高", "凉", "green", "green_hi", "蒸青味浓易苦"),
    _tea("lv_dadugang", "大渡岗岗绿",      "绿茶", "滇绿",         6, 85, 4.0, 0, "高", "凉", "green", "green_hi"),
    _tea("lv_qinggui",  "广宁清桂茶",      "绿茶", "雨前",         6, 85, 4.0, 0, "高", "凉", "green", "green_hi"),
    _tea("lv_yuenan",   "越南太原高山绿茶","绿茶", "明前",         6, 83, 4.0, 0, "高", "凉", "green", "green_hi"),
    _tea("lv_xiongying","湛江雄鸥蒸青",    "绿茶", "蒸青 春茶",    6, 78, 3.5, 0, "高", "凉", "green", "green_hi"),
    _tea("lv_kaoqing",  "刘家坡老树烤青",  "绿茶", "烤青 春茶",    6, 88, 4.0, 0, "高", "凉", "green", "green_hi", "烤青带火香"),
    _tea("lv_zhengmei", "刘家坡蒸酶玉绿",  "绿茶", "蒸青 春茶",    6, 78, 3.5, 0, "高", "凉", "green", "green_hi"),
    _tea("lv_itoen",    "伊藤园农家浓味蒸青", "绿茶", "蒸青 碎茶", 5, 75, 2.5, 0, "高", "凉", "green", "green_hi", "碎茶析出极快，宁短勿长"),
    _tea("lv_huangjinya","广德黄金芽",     "绿茶", "明前 一芽二叶", 6, 82, 4.0, 0, "高", "凉", "green", "green_hi"),
    _tea("lv_xiangao",  "西南大学高香绿茶","绿茶", "春茶",         6, 83, 4.0, 0, "高", "凉", "green", "green_hi"),
    _tea("lv_xichun",   "西农春绿",        "绿茶", "春茶",         6, 83, 4.0, 0, "高", "凉", "green", "green_hi"),
    # ---- 调味绿茶（8）----
    _tea("fl_baolan",   "宝兰飞马香兰绿茶","调味绿茶", "斑斓叶窨制", 6, 85, 4.0, 0, "高", "凉", "green_flav", "green_hi"),
    _tea("fl_xiangcaolan","绿海岛香草兰茶","调味绿茶", "香草兰果荚窨制", 6, 85, 4.0, 0, "高", "凉", "green_flav", "green_hi"),
    _tea("fl_mixiang",  "绿海岛米香茶",    "调味绿茶", "糯米香叶窨制", 6, 85, 4.0, 0, "高", "凉", "green_flav", "green_hi"),
    _tea("fl_nuomi",    "云南糯米香茶",    "调味绿茶", "糯米香叶窨制", 6, 85, 4.0, 0, "高", "凉", "green_flav", "green_hi"),
    _tea("fl_banlan",   "海南斑斓绿茶",    "调味绿茶", "斑斓叶窨制 带碎叶", 6, 85, 4.0, 0, "高", "凉", "green_flav", "green_hi", "带碎叶，出汤时过滤"),
    _tea("fl_ban_vn",   "越南BAN斑斓绿茶","调味绿茶", "斑斓味",      6, 85, 4.0, 0, "高", "凉", "green_flav", "green_hi"),
    _tea("fl_bohe",     "宝锡兰摩洛哥薄荷绿茶", "调味绿茶", "碎茶", 5, 85, 3.0, 0, "高", "凉", "green_flav", "green_hi", "碎茶"),
    _tea("fl_lianhua",  "莲花峰茶丸",      "调味绿茶", "25味药茶",   6, 100, 6.0, 0, "中", "平", "green_flav", "herbal", "药茶丸沸水久浸；茶渣可再煮水"),
    # ---- 花茶（8）----
    _tea("hu_xinong_q", "西农茉莉花茶·清香", "花茶", "重瓣茉莉 烘青春茶", 6, 87, 4.0, 0, "中", "平", "flower", "flower"),
    _tea("hu_xinong_n", "西农茉莉花茶·浓香", "花茶", "茉莉+白玉兰 烘青春茶", 6, 88, 4.0, 0, "中", "平", "flower", "flower"),
    _tea("hu_maojian",  "西农毛尖茉莉",    "花茶", "重瓣茉莉 一芽一二叶", 6, 85, 4.0, 0, "中", "平", "flower", "flower"),
    _tea("hu_houwang",  "中茶猴王金猴王",  "花茶", "浓香 重瓣茉莉", 6, 88, 4.0, 0, "中", "平", "flower", "flower"),
    _tea("hu_gaosui",   "京华茉莉高碎",    "花茶", "七窨 重瓣茉莉", 5, 85, 3.0, 0, "中", "平", "flower", "flower", "高碎，析出快"),
    _tea("hu_18hao",    "京华茉莉18号",    "花茶", "七窨 重瓣茉莉", 6, 88, 4.0, 0, "中", "平", "flower", "flower"),
    _tea("hu_zhulan",   "歙县珠兰玉螺",    "花茶", "珠兰花茶 雨后", 6, 85, 4.0, 0, "中", "平", "flower", "flower"),
    _tea("hu_jinhua",   "金花特级茉莉",    "花茶", "三窨 横县茉莉", 6, 88, 4.0, 0, "中", "平", "flower", "flower"),
    # ---- 白茶（3）----
    _tea("ba_longzhu",  "福鼎白牡丹龙珠",  "白茶", "7年陈 高山",   6, 100, 5.0, 20, "低", "温", "white_old", "white_old", "紧压龙珠约2颗，润茶20秒"),
    _tea("ba_laoshu",   "蝴蝶老树白牡丹",  "白茶", "老树",         6, 95, 4.5, 0, "中", "平", "white_old", "white"),
    _tea("ba_shoumei",  "宁德寿眉",        "白茶", "一芽多叶",     6, 100, 5.0, 0, "中", "平", "white_old", "white"),
    # ---- 黄茶（4）----
    _tea("ya_huoshan",  "霍山黄芽",        "黄茶", "雨前",         6, 85, 4.0, 0, "中", "平", "yellow", "yellow"),
    _tea("ya_mengding", "蒙顶黄芽",        "黄茶", "初春头采 一芽二叶", 6, 83, 4.0, 0, "中", "平", "yellow", "yellow"),
    _tea("ya_yueyang",  "远山岳阳黄小茶",  "黄茶", "黄小茶",       6, 85, 4.0, 0, "中", "平", "yellow", "yellow"),
    _tea("ya_qilu",     "齐鲁干烘黄大茶",  "黄茶", "炭焙 春夏茶",  6, 98, 5.0, 0, "中", "温", "yellow", "yellow", "炭焙高火香，沸水冲"),
    # ---- 乌龙茶（21）----
    _tea("wu_sezhong",  "漳州色种",        "乌龙茶", "闽南乌龙",    7, 100, 5.0, 0, "高", "平", "oolong_nong", "oolong_nong"),
    _tea("wu_liuxiang", "漳州流香",        "乌龙茶", "闽南乌龙",    7, 100, 5.0, 0, "高", "平", "oolong_nong", "oolong_nong"),
    _tea("wu_hongmudan","漳州红牡丹",      "乌龙茶", "闽南乌龙",    7, 100, 5.0, 0, "高", "平", "oolong_nong", "oolong_nong"),
    _tea("wu_yizhichun","漳州一枝春",      "乌龙茶", "闽南乌龙",    7, 100, 5.0, 0, "高", "平", "oolong_nong", "oolong_nong"),
    _tea("wu_baiyaqilan","漳州白芽奇兰",   "乌龙茶", "闽南乌龙",    7, 100, 5.0, 0, "高", "平", "oolong_nong", "oolong_nong"),
    _tea("wu_huangdan", "漳州黄旦",        "乌龙茶", "闽南乌龙",    7, 100, 5.0, 0, "高", "平", "oolong_nong", "oolong_nong"),
    _tea("wu_tieguanyin","漳州铁观音",     "乌龙茶", "霞漳牌 浓香", 7, 100, 5.0, 0, "高", "平", "oolong_nong", "oolong_nong"),
    _tea("wu_longzhu",  "漳州龙珠茶",      "乌龙茶", "浓香 紧压珠", 7, 100, 5.0, 15, "高", "平", "oolong_nong", "oolong_nong", "紧压龙珠，润茶15秒"),
    _tea("wu_shuixian", "漳州三印水仙",    "乌龙茶", "闽南乌龙",    7, 100, 5.0, 0, "高", "平", "oolong_nong", "oolong_nong"),
    _tea("wu_dahongpao","武夷星大红袍",    "乌龙茶", "浓香 春茶",   7, 100, 5.0, 0, "高", "温", "oolong_nong", "oolong_nong"),
    _tea("wu_laocong",  "武夷星老枞水仙",  "乌龙茶", "浓香 春茶",   7, 100, 5.0, 0, "高", "温", "oolong_nong", "oolong_nong"),
    _tea("wu_rougui",   "武夷星肉桂",      "乌龙茶", "浓香 春茶",   7, 100, 5.0, 0, "高", "温", "oolong_nong", "oolong_nong"),
    _tea("wu_fengshan", "凤山铁观音",      "乌龙茶", "清香 秋茶",   6, 95, 4.0, 0, "高", "平", "oolong_qing", "oolong_qing"),
    _tea("wu_at207",    "海堤AT207色种",   "乌龙茶", "浓香 闽南正溪", 7, 100, 5.0, 0, "高", "平", "oolong_nong", "oolong_nong"),
    _tea("wu_qingyuan", "清源茶饼",        "乌龙茶", "紧压饼",      7, 100, 5.0, 20, "高", "平", "oolong_nong", "oolong_nong", "紧压饼，先撬散润茶"),
    _tea("wu_daping",   "大坪高山土山茶",  "乌龙茶", "浓香 春茶",   7, 100, 5.0, 0, "高", "平", "oolong_nong", "oolong_nong"),
    _tea("wu_qidan",    "海堤奇丹大红袍",  "乌龙茶", "浓香",        7, 100, 5.0, 0, "高", "温", "oolong_nong", "oolong_nong"),
    _tea("wu_milan",    "凤凰单丛蜜兰香",  "乌龙茶", "GT303",       7, 100, 4.5, 0, "高", "平", "oolong_nong", "oolong_nong", "高香单丛，4.5分钟封顶防苦涩"),
    _tea("wu_yashi",    "凤凰单丛鸭屎香",  "乌龙茶", "GT304",       7, 100, 4.5, 0, "高", "平", "oolong_nong", "oolong_nong", "高香单丛，4.5分钟封顶防苦涩"),
    _tea("wu_meizhan",  "安溪梅占",        "乌龙茶", "闽南乌龙",    7, 100, 5.0, 0, "高", "平", "oolong_nong", "oolong_nong"),
    _tea("wu_jianghua", "海堤凤凰单丛姜花香", "乌龙茶", "单丛",     7, 100, 4.5, 0, "高", "平", "oolong_nong", "oolong_nong", "高香单丛，4.5分钟封顶防苦涩"),
    # ---- 红茶（12）----
    _tea("ho_xiangao",  "西南大学高香红茶","红茶", "春茶 一芽二三叶", 6, 93, 4.5, 0, "高", "温", "black", "black"),
    _tea("ho_laoshan",  "崂山红茶",        "红茶", "春茶 一芽二叶", 6, 93, 4.5, 0, "高", "温", "black", "black"),
    _tea("ho_zhengshan","正山小种",        "红茶", "传统松烟",     6, 95, 4.5, 0, "高", "温", "black", "black"),
    _tea("ho_darjeeling","大吉岭GOLDENTIPS","红茶", "SFTGFOP1",    6, 92, 4.0, 0, "高", "温", "black", "black", "嫩芽级，95℃以上易涩"),
    _tea("ho_fengning", "凤宁58滇红",      "红茶", "一芽二三叶",   6, 95, 4.5, 0, "高", "温", "black", "black"),
    _tea("ho_keemun",   "天之红祁红",      "红茶", "春茶嫩芽",     6, 93, 4.5, 0, "高", "温", "black", "black"),
    _tea("ho_tanyang",  "坦洋工夫1915",    "红茶", "富春农垦",     6, 95, 4.5, 0, "高", "温", "black", "black"),
    _tea("ho_yorkshire","约克夏经典",      "红茶", "英式拼配",     6, 100, 4.0, 0, "高", "温", "black", "black", "英式习惯沸水4分钟，可加奶"),
    _tea("ho_duoshi",   "朵诗Filiz",       "红茶", "土耳其 CTC",   5, 98, 3.5, 0, "高", "温", "black_ctc", "black_ctc", "CTC碎茶析出快"),
    _tea("ho_yinghong", "英红九号碎红茶",  "红茶", "鸿雁牌 碎茶",  5, 93, 3.5, 0, "高", "温", "black_ctc", "black_ctc", "碎茶"),
    _tea("ho_lipton",   "立顿黄牌",        "红茶", "CTC",          5, 98, 3.5, 0, "高", "温", "black_ctc", "black_ctc", "CTC，可加奶加糖"),
    _tea("ho_mizhuan",  "川字米砖茶",      "红茶", "紧压红茶砖",   7, 100, 5.0, 20, "高", "温", "black", "black", "紧压砖，先撬散润茶"),
    # ---- 调味红茶（6）----
    _tea("ft_lizhi",    "金帆荔枝红茶",    "调味红茶", "带碎荔枝肉", 6, 95, 4.0, 0, "高", "温", "black", "black"),
    _tea("ft_lizhi_sui","金帆荔枝味碎茶",  "调味红茶", "碎茶",      5, 95, 3.5, 0, "高", "温", "black_ctc", "black_ctc", "碎茶"),
    _tea("ft_ningmeng", "韵粤清英德柠檬红茶", "调味红茶", "柠檬叶窨制", 6, 93, 4.0, 0, "高", "温", "black", "black"),
    _tea("ft_meigui",   "叶尔羌玫瑰红茶",  "调味红茶", "重瓣红玫瑰窨制", 6, 95, 4.0, 0, "高", "温", "black", "black"),
    _tea("ft_dilmah",   "迪尔玛伯爵",      "调味红茶", "CTC",        5, 98, 3.5, 0, "高", "温", "black_ctc", "black_ctc", "CTC"),
    _tea("ft_xinjiang", "叶尔羌调味香茶",  "调味红茶", "8味香料调制", 6, 100, 5.0, 0, "中", "温", "black", "black", "沸水激香，可久浸"),
    # ---- 黑茶（12）----
    _tea("he_fuzhuan",  "湘益茯砖",        "黑茶", "紧压砖",       8, 100, 6.0, 30, "低", "温", "dark_ripe", "dark_ripe", "紧压砖，撬散润茶30秒"),
    _tea("he_qingzhuan","川字青砖",        "黑茶", "紧压砖",       8, 100, 6.0, 30, "中", "温", "dark_ripe", "dark_ripe", "紧压砖，撬散润茶30秒"),
    _tea("he_heizhuan", "白沙溪黑砖",      "黑茶", "紧压砖",       8, 100, 6.0, 30, "中", "温", "dark_ripe", "dark_ripe", "紧压砖，撬散润茶30秒"),
    _tea("he_liubao",   "宝兰四兰六堡",    "黑茶", "9年陈",        7, 100, 5.0, 20, "中", "温", "dark_ripe", "dark_ripe", "润茶20秒"),
    _tea("he_zangcha",  "雅安藏茶",        "黑茶", "茶砖",         8, 100, 6.0, 30, "低", "温", "dark_ripe", "dark_ripe", "紧压砖，撬散润茶30秒"),
    _tea("he_shancheng","山城沱生普",      "黑茶", "普洱生茶",     7, 100, 5.0, 15, "高", "凉", "dark_raw", "dark_raw", "润茶15秒"),
    _tea("he_xiatuo15", "下关特沱生普",    "黑茶", "15年陈",       7, 100, 5.0, 15, "高", "平", "dark_rawold", "dark_raw", "老生普，润茶15秒"),
    _tea("he_mini_sheng","下关迷你小沱生普","黑茶", "14年陈",      7, 100, 5.0, 15, "高", "平", "dark_rawold", "dark_raw", "迷你沱约3颗，润茶15秒"),
    _tea("he_mini_shou","下关迷你小沱熟普","黑茶", "12年陈",       7, 100, 5.0, 15, "低", "温", "dark_ripe", "dark_ripe", "迷你沱约3颗，润茶15秒"),
    _tea("he_xiaofa",   "下关销法沱熟普",  "黑茶", "4年陈",        7, 100, 5.0, 15, "低", "温", "dark_ripe", "dark_ripe", "润茶15秒"),
    _tea("he_chagao",   "五指毛桃六堡茶膏","黑茶", "茶膏",         2, 100, 0.0, 0, "低", "温", "dark_ripe", "herbal", "茶膏：沸水直接搅拌溶解即饮，无需壶泡计时"),
    _tea("he_7541",     "7541七子饼生普",  "黑茶", "普洱生茶",     7, 100, 5.0, 15, "高", "凉", "dark_raw", "dark_raw", "撬散润茶15秒"),
    # ---- 代用茶/饮品（12）----
    _tea("da_damai",    "炒大麦茶",        "代用茶", "焙炒大麦",    10, 100, 6.0, 0, "无", "凉", "herbal_cool", "herbal", "麦茶要量大才出味，可久浸"),
    _tea("da_kuqiao",   "黑苦荞茶",        "代用茶", "苦荞",        8, 100, 5.0, 0, "无", "凉", "herbal_cool", "herbal"),
    _tea("da_luohanguo","罗汉果",          "代用茶", "干罗汉果",    5, 100, 8.0, 0, "无", "凉", "herbal_cool", "herbal", "约1/3个掰碎，久浸出甜"),
    _tea("da_pangdahai","胖大海",          "代用茶", "干果",        3, 100, 8.0, 0, "无", "凉", "herbal_cool", "herbal", "2-3颗，泡发体积大"),
    _tea("da_tianyeju", "甜叶菊",          "代用茶", "干叶",        1, 100, 5.0, 0, "无", "平", "herbal_neu", "herbal", "2-3片即可，极甜勿多"),
    _tea("da_jinyinhua","金银花",          "代用茶", "干花",        4, 90, 5.0, 0, "无", "寒", "herbal_cool", "herbal"),
    _tea("da_ningmeng", "干柠檬片",        "代用茶", "冻干柠檬",    3, 80, 5.0, 0, "无", "凉", "herbal_cool", "herbal", "2-3片，高温发苦勿用沸水"),
    _tea("da_xuanmi",   "玄米茶",          "代用茶", "糙米+绿茶",   8, 90, 4.0, 0, "中", "平", "herbal_neu", "herbal", "含绿茶，90℃免发苦"),
    _tea("da_shiya",    "广西石崖茶",      "代用茶", "石崖茶",      5, 100, 5.0, 0, "无", "平", "herbal_neu", "herbal"),
    _tea("da_qianluo",  "崂山野生茶",      "代用茶", "芊罗茶 明前头采", 6, 85, 4.0, 0, "高", "凉", "green", "green_hi", "本质是野生绿茶，按嫩绿茶泡"),
    _tea("da_mocha",    "抹茶粉",          "代用茶", "碾茶粉",      2, 78, 0.0, 0, "高", "凉", "matcha", "matcha", "点茶法：2g粉+60ml温水茶筅刷开再注水，非壶泡"),
    _tea("da_cocoa",    "可可粉",          "代用茶", "可可",        20, 0, 0.0, 0, "低", "温", "herbal_warm", "cocoa", "15-20g+200ml热牛奶(约60℃)搅匀，非壶泡"),
]

# ----------------------------------------------------------------------------
# 动态库存：内置 107 款 + 自购茶（state.json 持久化）
#   state.json 结构: {history:[...], custom_teas:[...], removed_ids:[...]}
# ----------------------------------------------------------------------------
CAT_DEFAULTS = {  # 「我买了XX」时按类别自动套用的壶泡默认参数（400ml 一泡）
    "绿茶":    dict(g=6, t=83, m=4.0, rinse=0,  caff="高", thermo="凉", sea="green",       tod="green_hi"),
    "调味绿茶": dict(g=6, t=85, m=4.0, rinse=0,  caff="高", thermo="凉", sea="green_flav",  tod="green_hi"),
    "花茶":    dict(g=6, t=88, m=4.0, rinse=0,  caff="中", thermo="平", sea="flower",      tod="flower"),
    "白茶":    dict(g=6, t=95, m=4.5, rinse=0,  caff="中", thermo="平", sea="white_old",   tod="white"),
    "黄茶":    dict(g=6, t=85, m=4.0, rinse=0,  caff="中", thermo="平", sea="yellow",      tod="yellow"),
    "乌龙茶":  dict(g=7, t=100, m=5.0, rinse=0, caff="高", thermo="平", sea="oolong_nong", tod="oolong_nong"),
    "红茶":    dict(g=6, t=95, m=4.5, rinse=0,  caff="高", thermo="温", sea="black",       tod="black"),
    "调味红茶": dict(g=6, t=95, m=4.0, rinse=0,  caff="高", thermo="温", sea="black",       tod="black"),
    "黑茶":    dict(g=7, t=100, m=5.0, rinse=15, caff="中", thermo="温", sea="dark_ripe",   tod="dark_ripe"),
    "代用茶":  dict(g=5, t=100, m=5.0, rinse=0,  caff="无", thermo="平", sea="herbal_neu",  tod="herbal"),
}
_UNKNOWN_DEFAULT = dict(g=6, t=90, m=4.0, rinse=0, caff="中", thermo="平", sea="herbal_neu", tod="herbal")

# ----------------------------------------------------------------------------
# 冷泡参数（1.6L 冷泡壶 · 冷藏层约4℃ · 过夜冷泡法）
# 原理：4℃低温下咖啡碱/茶多酚浸出极慢，氨基酸等鲜甜物质优先溶出
#       → 投茶量比热泡大（1:100~1:120）、时长以小时计
# ----------------------------------------------------------------------------
COLD_DEFAULTS = {  # 类别 → (投茶量g/1.6L, 冷藏小时数)
    "绿茶":    (15, 5.0),
    "调味绿茶": (16, 5.0),
    "花茶":    (14, 5.0),
    "白茶":    (16, 5.0),
    "黄茶":    (15, 5.5),
    "乌龙茶":  (16, 7.0),
    "红茶":    (15, 7.0),
    "调味红茶": (15, 7.0),
    "黑茶":    (16, 9.0),
    "代用茶":  (18, 8.0),
    "未分类":  (15, 6.0),
}

COLD_SUIT = {  # 类别冷泡适配度（只降权不封杀；特例在 _COLD_EXCLUDE 硬排除）
    "绿茶": 0.95, "调味绿茶": 0.90, "花茶": 0.85, "白茶": 0.90, "黄茶": 0.80,
    "乌龙茶": 0.75, "红茶": 0.65, "调味红茶": 0.70, "黑茶": 0.55, "代用茶": 0.80, "未分类": 0.70,
}

_COLD_EXCLUDE = ("抹茶", "可可", "茶膏", "茶丸")  # 不适合冷泡壶：抹茶需点茶、可可需热奶、茶膏/药茶丸需沸水


def _cold_params(tea: dict) -> tuple:
    """按类别+特征计算冷泡参数 (投茶g/1.6L, 冷藏小时)。碎茶减量、蒸青减时、紧压加时；复盘调校覆盖。"""
    g, h = COLD_DEFAULTS.get(tea["cat"], COLD_DEFAULTS["未分类"])
    blob = tea["note"] + tea["name"]
    if any(k in blob for k in ("碎", "CTC", "高碎")):
        g -= 2
    if "蒸青" in blob:
        g -= 1
        h = max(3.0, h - 1.0)
    if tea["rinse"]:
        h += 1.0  # 紧压茶低温下更难浸出
    ov = _load_state().get("overrides", {}).get(tea["id"], {}).get("cold", {})  # 复盘覆盖
    if ov.get("g"):
        g = ov["g"]
    if ov.get("h"):
        h = ov["h"]
    return g, h


def _cold_season_factor(d: date) -> float:
    """冷泡的季节软权重：夏天高、冬天低但不封杀。"""
    md = (d.month, d.day)
    if (5, 6) <= md < (9, 8):      # 立夏~白露
        return 1.50
    if (3, 6) <= md < (5, 6) or (9, 8) <= md < (10, 23):  # 春末/初秋
        return 1.00
    return 0.50

# ----------------------------------------------------------------------------
# 复盘调校：个性化参数覆盖（实际口感反馈 → 微调热泡/冷泡参数，持久化到 state.json）
#   state.json.overrides: {茶id: {"hot": {g,t,m,rinse,note}, "cold": {g,h,note}}}
# 理论参数只是起点：商家优劣、陈化、储存变质都会让实际口感偏离，复盘修正。
# ----------------------------------------------------------------------------
_FB_WEAK = ("淡", "不够味", "没味道", "水味", "寡淡", "没什么味", "无味", "太轻", "没味")
_FB_STRONG = ("浓", "苦", "酽", "过浓")
_FB_ASTRINGENT = ("涩", "麻", "发苦发涩")
_FB_GOOD = ("正好", "完美", "好喝", "合适", "不错", "满意", "平衡", "ok", "OK", "Ok")
_FB_RESET = ("重置", "恢复默认", "撤销调校", "回默认", "取消调校")
_FB_WAREHOUSE = ("仓气", "仓味", "陈味", "堆味", "霉味", "渥堆", "土味", "杂味")   # 仓储味反馈 → 加强洗茶/散味
_FB_OVERWASH = ("洗茶太过", "洗过头", "洗太狠", "香味洗掉", "洗掉香", "香洗掉")    # 洗过头反馈 → 减弱洗茶/散味
_FB_STUFFY = ("闷味", "闷熟", "闷坏", "发闷", "水闷")                              # 闷味反馈 → 改开盖泡
_FB_FLAT_AROMA = ("香气散", "跑香", "香味散", "存不住香")                          # 香气散失反馈 → 改盖盖泡
_FB_SOUR = ("泡酸", "发酸", "酸味", "太酸", "酸了")                               # 红茶泡酸（高温出酸）→ 降温
_FB_AROMA_LOST = ("香味没了", "没香气", "香气没了", "不香", "香气消失", "香味消失", "没什么香气")  # 高温毁香 → 降温

_HOT_LIMITS = dict(g=(3.0, 12.0), t=(70, 100), m=(1.5, 8.0))   # 热泡参数边界
_COLD_LIMITS = dict(g=(8.0, 25.0), h=(3.0, 12.0))             # 冷泡参数边界


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _has_any(text: str, keys: tuple) -> bool:
    return any(k in text for k in keys)


def _effective(tea: dict) -> dict:
    """返回应用热泡调校后的参数副本（不改内置数据，可整体回滚）。"""
    st = _load_state()
    ov = st.get("overrides", {}).get(tea["id"], {}).get("hot", {})
    if not ov:
        return tea
    t2 = dict(tea)
    for k in ("g", "t", "m", "rinse"):
        if k in ov:
            t2[k] = ov[k]
    return t2


def _has_override(tea_id: str) -> bool:
    st = _load_state()
    return bool(st.get("overrides", {}).get(tea_id))


def _adjust_hot(cur_g, cur_t, cur_m, fb: str, no_heat: bool = False):
    """按反馈调整热泡参数，返回 (g, t, m, 动作日志)。no_heat=True 时"淡"不加温（酸/香反馈优先降温）。"""
    lo_g, hi_g = _HOT_LIMITS["g"]
    lo_t, hi_t = _HOT_LIMITS["t"]
    lo_m, hi_m = _HOT_LIMITS["m"]
    g, t, m = cur_g, cur_t, cur_m
    log = []
    if _has_any(fb, _FB_WEAK):
        if g < hi_g:
            step = max(0.5, round(g * 0.15 * 2) / 2)
            g = _clamp(round((g + step) * 2) / 2, lo_g, hi_g)
            log.append(f"投茶 +{step:g}g")
        else:
            log.append("投茶已达上限12g")
        if m < hi_m:
            m = _clamp(round((m + 0.5) * 2) / 2, lo_m, hi_m)
            log.append("浸泡 +0.5min")
        else:
            log.append("浸泡已达上限8min")
        if no_heat:
            log.append("酸/香反馈存在，水温保持不加")
        elif t < hi_t:
            t = _clamp(t + 2, lo_t, hi_t)
            log.append("水温 +2℃")
        else:
            log.append("水温已达上限100℃")
    elif _has_any(fb, _FB_ASTRINGENT):
        if t > lo_t:
            t = _clamp(t - 3, lo_t, hi_t)
            log.append("水温 -3℃")
        if m > lo_m:
            m = _clamp(round((m - 0.5) * 2) / 2, lo_m, hi_m)
            log.append("浸泡 -0.5min")
    elif _has_any(fb, _FB_STRONG):
        if g > lo_g:
            step = max(0.5, round(g * 0.15 * 2) / 2)
            g = _clamp(round((g - step) * 2) / 2, lo_g, hi_g)
            log.append(f"投茶 -{step:g}g")
        if m > lo_m:
            m = _clamp(round((m - 0.5) * 2) / 2, lo_m, hi_m)
            log.append("浸泡 -0.5min")
        if t > lo_t:
            t = _clamp(t - 2, lo_t, hi_t)
            log.append("水温 -2℃")
    return g, t, m, log


def _adjust_cold(cur_g, cur_h, fb: str):
    """按反馈调整冷泡参数，返回 (g, h, 动作日志)。"""
    lo_g, hi_g = _COLD_LIMITS["g"]
    lo_h, hi_h = _COLD_LIMITS["h"]
    g, h = cur_g, cur_h
    log = []
    if _has_any(fb, _FB_WEAK):
        if g < hi_g:
            g = _clamp(g + 2, lo_g, hi_g)
            log.append("投茶 +2g")
        else:
            log.append("投茶已达上限25g")
        if h < hi_h:
            h = _clamp(h + 1, lo_h, hi_h)
            log.append("冷藏 +1h")
        else:
            log.append("冷藏已达上限12h")
    elif _has_any(fb, _FB_ASTRINGENT):
        if h > lo_h:
            h = _clamp(h - 1, lo_h, hi_h)
            log.append("冷藏 -1h")
        if g > lo_g:
            g = _clamp(g - 1, lo_g, hi_g)
            log.append("投茶 -1g")
    elif _has_any(fb, _FB_STRONG):
        if g > lo_g:
            g = _clamp(g - 2, lo_g, hi_g)
            log.append("投茶 -2g")
        if h > lo_h:
            h = _clamp(h - 1, lo_h, hi_h)
            log.append("冷藏 -1h")
    return g, h, log


# ----------------------------------------------------------------------------
# 洗茶/散味档位（仓气调校）：0~6 档，对应黑茶预处理强度
#   快洗 = 沸水快速冲淋即出（润茶）；慢洗 = 茶叶浸沸水5秒后倒出；
#   散味 = 出汤弃后镊子拨散茶叶、静置散味，再正式冲泡
# 默认：生普 L2（快1慢1散2）；熟普/六堡/边销砖 L4（快2慢1散2快1）
# 复盘：「仓气重」→ 档位+1；「洗茶太过」→ 档位-1
# ----------------------------------------------------------------------------
PREWASH_PLANS = {
    0: "",
    1: "快洗1次（沸水快速冲淋即出）",
    2: "快洗1次 → 慢洗1次（浸沸水5秒） → 出汤弃 → 镊子拨散散味2分钟",       # 生普默认
    3: "快洗2次 → 慢洗1次 → 出汤弃 → 拨散散味2分钟",
    4: "快洗2次 → 慢洗1次 → 出汤弃 → 拨散散味2分钟 → 再快洗1次",            # 熟普/六堡/边销砖默认
    5: "快洗3次 → 慢洗1次 → 出汤弃 → 拨散散味3分钟 → 再快洗1次",
    6: "快洗3次 → 慢洗2次 → 出汤弃 → 拨散散味3分钟 → 再快洗2次",
}
_PREWASH_MIN, _PREWASH_MAX = 0, 6


def _default_prewash(tea: dict) -> int:
    """默认洗茶档位：生普L2、熟普/六堡/边销砖L4、紧压类L1、非壶泡品/其他L0。"""
    if not tea.get("m"):
        return 0  # 茶膏/抹茶/可可等非壶泡品不洗茶
    blob = tea["name"] + tea["note"]
    if tea["cat"] == "黑茶":
        if any(k in blob for k in ("生普", "生茶")):
            return 2   # 生普：快洗1+慢洗1+散味2
        return 4       # 熟普/六堡/边销砖：快洗2+慢洗1+散味2+快洗1
    if any(k in blob for k in ("龙珠", "茶饼", "茶砖", "小沱")):
        return 1
    if "黄大茶" in tea["name"] or "炭焙" in tea["note"] or "干烘" in tea["note"]:
        return 1   # 重炭焙表面有浮尘，快洗1次去浮尘（非仓味）
    return 0


def _prewash_of(tea: dict) -> int:
    """当前生效的洗茶档位 = 复盘覆盖 or 默认。"""
    st = _load_state()
    ov = st.get("overrides", {}).get(tea["id"], {}).get("hot", {}).get("prewash")
    if ov is not None:
        return int(ov)
    return _default_prewash(tea)


# ----------------------------------------------------------------------------
# 盖盖/开盖（壶泡存香 vs 散气）：bool，热泡参数之一，复盘可调
# 默认规则：
#   花茶/调味绿茶/乌龙/红茶/调味红茶/白茶/代用茶 → 盖盖（存香保温）
#   绿茶/黄茶(嫩)/黑茶 → 开盖（防闷味/散仓气）
#   特例：崂山红茶（发酵偏轻、有机酸多）→ 开盖挥发；芊罗茶按绿茶 → 开盖
# 复盘：「闷味重」→ 改开盖；「香气散/不香」→ 改盖盖
# ----------------------------------------------------------------------------
def _default_lid(tea: dict) -> bool:
    """默认是否盖盖。非壶泡品返回 True（不显示，无意义）。"""
    name, cat = tea["name"], tea["cat"]
    if not tea.get("m"):
        return True
    if "崂山红茶" in name or "芊罗" in name:
        return False   # 崂山红茶：有机酸多，开盖挥发；芊罗茶：绿茶工艺，开盖防闷
    if cat in ("绿茶", "黑茶"):
        return False   # 嫩绿茶防闷味；黑茶散仓气
    if cat == "黄茶":
        return "炭焙" in tea["note"] or "干烘" in tea["note"]  # 黄大茶盖盖，嫩黄茶开盖
    return True        # 花茶/调味绿茶/乌龙/红茶/调味红茶/白茶/代用茶：盖盖存香


def _lid_of(tea: dict) -> bool:
    """当前是否盖盖 = 复盘覆盖 or 默认。"""
    st = _load_state()
    ov = st.get("overrides", {}).get(tea["id"], {}).get("hot", {}).get("lid")
    if ov is not None:
        return bool(ov)
    return _default_lid(tea)


def _norm_category(s: str) -> str:
    """类别归一化：支持「普洱」→黑茶、「茉莉」→花茶 等常见叫法；认不出返回空串。"""
    s = s.strip()
    if not s:
        return ""
    cats = ("调味绿茶", "调味红茶", "乌龙茶", "代用茶", "绿茶", "红茶", "花茶", "白茶", "黄茶", "黑茶")
    if s in cats:                      # 精确匹配优先（防止「绿茶」被「调味绿茶」吞掉）
        return s
    if "安吉白" in s:                  # 特例：安吉白茶按工艺归绿茶
        return "绿茶"
    if any(k in s for k in ("普洱", "生普", "熟普", "六堡", "茯砖", "青砖", "黑砖", "藏茶", "沱茶", "砖茶", "老茶头")):
        return "黑茶"
    if any(k in s for k in ("茉莉", "桂花", "玫瑰", "珠兰", "窨制")):
        return "花茶"
    if any(k in s for k in ("龙井", "碧螺", "毛峰", "毛尖", "云雾", "蒸青", "炒青", "烘青", "雀舌", "猴魁", "瓜片", "旗枪", "滇绿")):
        return "绿茶"
    if any(k in s for k in ("大红袍", "肉桂", "水仙", "铁观音", "单丛", "岩茶", "奇兰", "冻顶", "乌龙")):
        return "乌龙茶"
    if any(k in s for k in ("伯爵", "锡兰", "大吉岭", "祁红", "滇红", "金骏眉", "正山", "阿萨姆", "CTC", "工夫")):
        return "红茶"
    if any(k in s for k in ("大麦", "苦荞", "罗汉果", "胖大海", "菊花", "柠檬", "薄荷", "玄米", "路易")):
        return "代用茶"
    for cat in cats:                   # 最后正向包含（「XX白茶」→白茶）
        if cat in s:
            return cat
    return ""


def _all_teas() -> list:
    """组装当前有效库存 = 内置茶（剔除已喝光的）+ 自购茶。"""
    st = _load_state()
    removed = set(st.get("removed_ids", []))
    builtin = [t for t in TEAS if t["id"] not in removed]
    customs = [c for c in st.get("custom_teas", []) if c.get("id") not in removed]
    return builtin + customs

# ----------------------------------------------------------------------------
# 场景计算
# ----------------------------------------------------------------------------
def _season(d: date) -> str:
    md = (d.month, d.day)
    if (2, 4) <= md < (5, 6):
        return "春"
    if (5, 6) <= md < (8, 8):
        return "夏"
    if (8, 8) <= md < (11, 7):
        return "秋"
    return "冬"


def _slot(hour: int) -> str:
    if 5 <= hour < 9:   return "morning"
    if 9 <= hour < 12:  return "late_morning"
    if 12 <= hour < 15: return "noon"
    if 15 <= hour < 18: return "afternoon"
    if 18 <= hour < 21: return "evening"
    if 21 <= hour < 24: return "night"
    return "deep_night"


def _festival(tea: dict, d: date) -> float:
    """节气彩蛋：只小幅加权，不改变大局。"""
    b = 1.0
    if abs((d - date(d.year, 4, 4)).days) <= 7 and ("明前" in tea["note"] or "早春" in tea["note"] or "初展" in tea["note"]):
        b *= 1.15  # 清明前后，明前茶应景
    if abs((d - date(d.year, 7, 22)).days) <= 10 and tea["cat"] == "代用茶":
        b *= 1.15  # 大暑前后，清凉代用茶
    if d >= date(d.year, 11, 7) and tea["thermo"] == "温":
        b *= 1.10  # 立冬后，温性茶
    return b


def _mood(tea: dict, mood: str) -> float:
    m = mood.strip()
    if not m:
        return 1.0
    b = 1.0
    if any(k in m for k in ("香", "馥郁", "浓香")):
        if tea["cat"] in ("乌龙茶", "花茶", "红茶"):
            b *= 1.30
    if any(k in m for k in ("清淡", "清爽", "鲜")):
        if tea["cat"] in ("绿茶", "白茶", "黄茶"):
            b *= 1.30
    if any(k in m for k in ("暖", "暖胃", "温")):
        if tea["thermo"] in ("温", "平") or tea["cat"] == "红茶":
            b *= 1.30
    if any(k in m for k in ("甜", "回甘")):
        if tea["cat"] in ("调味红茶", "红茶", "代用茶"):
            b *= 1.25
    if any(k in m for k in ("提神", "醒", "困")):
        if tea["caff"] == "高":
            b *= 1.30
    if any(k in m for k in ("安神", "睡觉", "低咖啡因", "不失眠")):
        if tea["caff"] in ("低", "无"):
            b *= 1.40
    return b


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"history": []}


_DEFAULT_POT_ML = 400    # 茶壶默认容量（投茶量存储基准）
_DEFAULT_COLD_ML = 1600  # 冷泡壶默认容量（投茶量存储基准）


def _brew_config() -> dict:
    """壶具配置：{pot_ml: 茶壶容量, cold_ml: 冷泡壶容量}，默认 400ml / 1.6L。"""
    st = _load_state()
    cfg = st.get("brewer", {})
    pot = int(cfg.get("pot_ml", _DEFAULT_POT_ML)) or _DEFAULT_POT_ML
    cold = int(cfg.get("cold_ml", _DEFAULT_COLD_ML)) or _DEFAULT_COLD_ML
    return {"pot_ml": max(100, min(pot, 3000)), "cold_ml": max(500, min(cold, 6000))}


def _g_for_pot(base_g: float) -> float:
    """热泡投茶量按茶壶容量等比缩放（0.5g 步长）。存储值始终是 400ml 基准。"""
    pot = _brew_config()["pot_ml"]
    return round(base_g * pot / _DEFAULT_POT_ML * 2) / 2


def _g_for_cold(base_g: float) -> float:
    """冷泡投茶量按冷泡壶容量等比缩放（0.5g 步长）。存储值始终是 1.6L 基准。"""
    cold = _brew_config()["cold_ml"]
    return round(base_g * cold / _DEFAULT_COLD_ML * 2) / 2


def _save_state(s: dict) -> None:
    STATE_FILE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


def _fatigue(hist: list, tea_id: str, today: date) -> float:
    """近期喝过 → 降权（软性，不封杀）。"""
    for h in reversed(hist):
        if h.get("id") == tea_id:
            try:
                days = (today - date.fromisoformat(h["ts"][:10])).days
            except Exception:
                continue
            if days <= 3:
                return 0.20
            if days <= 7:
                return 0.50
            if days <= 14:
                return 0.75
            if days <= 30:
                return 0.90
            return 1.0
    return 1.0


def _rotation(hist: list, tea_id: str, today: date) -> float:
    """库存轮换：很久没喝（或从没喝过）→ 小幅加成，拯救角落茶。"""
    last = None
    for h in reversed(hist):
        if h.get("id") == tea_id:
            last = h["ts"][:10]
            break
    if last is None:
        return 1.05
    try:
        days = (today - date.fromisoformat(last)).days
    except Exception:
        return 1.0
    return 1.15 if days > 30 else 1.0


def _pick(pairs: list, count: int) -> list:
    """加权无放回抽样。pairs: [(weight, tea), ...]"""
    items = list(pairs)
    out = []
    for _ in range(count):
        if not items:
            break
        total = sum(w for w, _ in items)
        if total <= 0:
            break
        r = random.random() * total
        acc = 0.0
        for idx, (w, it) in enumerate(items):
            acc += w
            if acc >= r:
                out.append(it)
                items.pop(idx)
                break
    return out


# ----------------------------------------------------------------------------
# MCP 工具
# ----------------------------------------------------------------------------
@mcp.tool()
def recommend(datetime_str: str = "", randomness: float = 0.6, count: int = 1, mood: str = "") -> str:
    """推荐今天（或指定日期时间）喝什么茶，输出 400ml 壶泡一泡的完整参数。

    参数:
      datetime_str: 可选，ISO 格式 '2026-02-14T20:30'；缺省用系统当前时间
      randomness:   0~1 随机程度。0=非常应季规律，1=非常随机惊喜。默认 0.6
      count:        返回几款（主推+备选），默认 1，最多 5
      mood:         可选偏好词，如 '想喝香的' / '清淡' / '暖胃' / '提神' / '安神'
    """
    now = datetime.now()
    if datetime_str.strip():
        try:
            now = datetime.fromisoformat(datetime_str.strip())
        except ValueError:
            now = datetime.now()
    d, h = now.date(), now.hour
    season, slot = _season(d), _slot(h)
    count = max(1, min(count, 5))
    randomness = max(0.0, min(randomness, 1.0))

    hist = _load_state().get("history", [])
    allt = _all_teas()
    if not allt:
        return "🍂 库存是空的。说「我买了XX」入库后就能推荐啦。"
    scored = []
    for tea in allt:
        w = tea["sea"].get(season, 1.0)
        w *= tea["tod"].get(slot, 1.0)
        w *= _festival(tea, d)
        w *= _mood(tea, mood)
        w *= _fatigue(hist, tea["id"], d)
        w *= _rotation(hist, tea["id"], d)
        w *= math.exp(random.uniform(-0.50, 0.50))  # 对数均匀噪声 0.61~1.65
        scored.append((w, tea))

    # softmax 温度：randomness 越大越随机（权重差异被抹平）
    tau = 0.20 + randomness * 2.00
    warmed = [(w ** (1.0 / tau), t) for w, t in scored]
    picked = _pick(warmed, count)

    pot = _brew_config()["pot_ml"]
    lines = [
        f"🫖 今天喝什么 ｜ {d.month}月{d.day}日 周{'一二三四五六日'[d.weekday()]} "
        f"｜ {SLOT_CN[slot]} ｜ {season}季 ｜ TDS20纯水 ｜ {pot}ml壶泡·仅一泡",
    ]
    if mood:
        lines.append(f"🎯 偏好加权：{mood}")
    medal = ["🥇 主推", "🥈 备选1", "🥉 备选2", "4️⃣ 备选3", "5️⃣ 备选4"]
    for rank, tea in enumerate(picked):
        w_before = next(w for w, t in scored if t is tea)
        eff = _effective(tea)
        mark = " ★已调校" if _has_override(tea["id"]) else ""
        rinse = f"{eff['rinse']}秒润茶" if eff["rinse"] else "无需润茶"
        lines.append("")
        lid = _lid_of(tea)
        lid_cn = "盖盖" if lid else "开盖"
        lines.append(f"{medal[rank]}：{tea['name']}（{tea['cat']}·{tea['note']}）{mark}")
        if eff["g"] and eff["m"]:
            g_disp = _g_for_pot(eff["g"])
            lines.append(
                f"   投茶 {g_disp:g}g ｜ 水温 {eff['t']}℃ ｜ 浸泡 {eff['m']:.1f}分钟 ｜ {rinse} ｜ {lid_cn}泡 ｜ 茶水比约 1:{pot/g_disp:.0f}"
            )
        if eff["m"]:
            pw = _prewash_of(tea)
            if pw > 0:
                op = f"   操作：温壶 → 投茶 → {PREWASH_PLANS[pw]} → 注满{pot}ml → {lid_cn} → 计时 → 到点一次性出汤（茶水分离）"
            else:
                op = ("   操作：温壶 → 投茶" + (" → 注水润茶后倒掉" if eff["rinse"] else "") +
                      f" → 注满{pot}ml → {lid_cn} → 计时 → 到点一次性出汤（茶水分离）")
            lines.append(op)
        reason_parts = [
            f"季节亲和×{tea['sea'].get(season, 1.0):.2f}",
            f"时段亲和×{tea['tod'].get(slot, 1.0):.2f}",
            f"综合权重{w_before:.3f}",
        ]
        lines.append("   理由：" + " ｜ ".join(reason_parts))
        if tea["tip"]:
            lines.append(f"   💡 {tea['tip']}")
    lines.append("")
    lines.append("喝完后对我说「我喝了{茶名}」（或让我调用 record 记录），接下来几天它会自动降权，换别的茶翻牌。")
    return "\n".join(lines)


@mcp.tool()
def record(name: str) -> str:
    """记录「我刚喝了XX」，用于疲劳降权与库存轮换。茶名可模糊匹配。"""
    key = name.strip()
    hits = [t for t in _all_teas() if key in t["name"] or t["name"] in key]
    if not hits:
        return f"库存里没找到「{name}」。说「看看库存」列出全部茶品。"
    tea = hits[0]
    st = _load_state()
    st.setdefault("history", []).append({
        "id": tea["id"], "name": tea["name"],
        "ts": datetime.now().isoformat(timespec="seconds"),
    })
    _save_state(st)
    n = len(st["history"])
    return f"✅ 已记录：{tea['name']}（{tea['cat']}）。历史共 {n} 条。近3天内它被再次推荐的概率会降到原来的20%左右。"


@mcp.tool()
def undo_record() -> str:
    """撤销最近一条喝茶记录（记错了可悔）。"""
    st = _load_state()
    hist = st.get("history", [])
    if not hist:
        return "还没有任何记录。"
    last = hist.pop()
    _save_state(st)
    return f"↩️ 已撤销：{last.get('name', '?')}（{last.get('ts', '')[:16]}）"


@mcp.tool()
def inventory(category: str = "") -> str:
    """列出库存茶品及壶泡参数。category 可选：绿茶/调味绿茶/花茶/白茶/黄茶/乌龙茶/红茶/调味红茶/黑茶/代用茶。"""
    if category:
        category = _norm_category(category) or category
    items = [t for t in _all_teas() if not category or t["cat"] == category]
    if not items and not category:
        return "🍂 库存是空的。说「我买了XX」入库。"
    if category and not items:
        return f"没有类别「{category}」。可选：绿茶、调味绿茶、花茶、白茶、黄茶、乌龙茶、红茶、调味红茶、黑茶、代用茶"
    pot = _brew_config()["pot_ml"]
    lines = [f"🍵 库存 {len(items)} 款" + (f"（{category}）" if category else "") + f" ｜ 按{pot}ml壶折算投茶量"]
    for t in items:
        eff = _effective(t)
        mark = " ★" if _has_override(t["id"]) else ""
        g_disp = _g_for_pot(eff["g"]) if eff["m"] else eff["g"]
        brew = f"{g_disp:g}g/{eff['t']}℃/{eff['m']:.1f}min" if eff["m"] else eff["tip"] or "直接冲调"
        pw = _prewash_of(t)
        if pw > 0:
            rinse = f" 洗L{pw}"
        elif eff["rinse"]:
            rinse = f" 润{eff['rinse']}s"
        else:
            rinse = ""
        lid = _lid_of(t)
        lines.append(f"- {t['name']}{mark}｜{t['note']}｜{brew}{rinse}｜{'盖' if lid else '开'}")
    return "\n".join(lines)


@mcp.tool()
def history(limit: int = 10) -> str:
    """查看最近喝茶记录。"""
    hist = _load_state().get("history", [])
    if not hist:
        return "还没有喝茶记录。"
    lines = [f"📖 最近 {min(limit, len(hist))} 条记录："]
    for h in hist[-limit:]:
        lines.append(f"- {h.get('ts', '')[:16]}  {h.get('name', '?')}")
    return "\n".join(lines)


def _add_single(key: str, category: str = "", note: str = "", g: float = 0.0, temp: int = 0, minutes: float = 0.0, rinse: int = -1) -> str:
    """单款入库（供 add_tea 单款/批量调用）。"""
    st = _load_state()

    # 1) 与"已喝光"的内置茶**全名相同** → 视为重新买回，恢复库存（简称不会误恢复）
    removed = st.get("removed_ids", [])
    for t in TEAS:
        if t["id"] in removed and t["name"] == key:
            removed.remove(t["id"])
            _save_state(st)
            return (f"♻️ 「{t['name']}」重新买回（原参数恢复）：\n"
                    f"   {t['g']}g ｜ {t['t']}℃ ｜ {t['m']:.1f}分钟 ｜ {'润茶%d秒' % t['rinse'] if t['rinse'] else '无需润茶'}")
    if "removed_ids" not in st:
        st["removed_ids"] = removed

    # 2) 已存在同名 → 拒绝重复
    for t in _all_teas():
        if t["name"] == key:
            return f"⚠️ 库存已有「{key}」（{t['cat']}）。若是另一款同名茶请改名（如「铁观音·新」）。"

    # 3) 组装新茶条目
    cat = _norm_category(category) if category else _norm_category(key)  # 类别没说时从茶名推断
    base = CAT_DEFAULTS.get(cat, _UNKNOWN_DEFAULT)
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    tea_id = "custom_" + ts
    n = 1
    while any(c.get("id") == tea_id for c in st.get("custom_teas", [])):
        n += 1
        tea_id = f"custom_{ts}_{n}"
    tea = dict(
        id=tea_id, name=key, cat=cat or "未分类", note=note.strip() or "自购",
        g=float(g) if g > 0 else base["g"],
        t=int(temp) if temp > 0 else base["t"],
        m=float(minutes) if minutes > 0 else base["m"],
        rinse=int(rinse) if rinse >= 0 else base["rinse"],
        caff=base["caff"], thermo=base["thermo"],
        sea=SEA[base["sea"]], tod=TOD[base["tod"]],
        tip=("未指定类别，参数为通用默认，可让我调整" if not cat else ""),
    )
    st.setdefault("custom_teas", []).append(tea)
    _save_state(st)
    return (f"✅ 已入库：{tea['name']}（{tea['cat']}｜{tea['note']}）｜ {tea['g']}g/{tea['t']}℃/{tea['m']:.1f}min"
            f"{('｜润茶%d秒' % tea['rinse']) if tea['rinse'] else ''}｜库存现共 {len(_all_teas())} 款")


@mcp.tool()
def add_tea(name: str, category: str = "", note: str = "", g: float = 0.0, temp: int = 0, minutes: float = 0.0, rinse: int = -1) -> str:
    """「我买了XX」：新茶入库。支持批量：「我买了龙井、铁观音、正山小种」一次入库多款。
    与内置茶全名相同的会恢复原参数（搬家清空后可用）；新茶自动按类别套默认壶泡参数。
    参数:
      name:     茶名（必填）。多个茶名可用顿号/逗号/分号/换行分隔
      category: 可选类别（可模糊，「普洱」会归到黑茶）；批量导入时用于无法从茶名推断的茶
      note:     可选备注，如「明前」「2024年」「朋友送的」
      g/temp/minutes/rinse: 可选自定义壶泡参数（400ml一泡）。0 或 -1 表示用类别默认；批量模式不支持显式参数
    """
    key = name.strip()
    if not key:
        return "茶名不能为空，例如「我买了龙井茶」。"
    parts = [p.strip() for p in re.split(r"[、,，;；\n]+", key) if p.strip()]
    if len(parts) > 1:
        if g > 0 or temp > 0 or minutes > 0 or rinse >= 0:
            return "批量导入不支持显式 g/temp/minutes/rinse 参数；请逐款导入或仅提供茶名。"
        msgs = [_add_single(p, category, note) for p in parts]
        return f"🛒 批量入库 {len(parts)} 款：\n" + "\n".join(msgs)
    return _add_single(key, category, note, g, temp, minutes, rinse)


@mcp.tool()
def remove_tea(name: str) -> str:
    """「我喝光了XX」：把茶移出库存。内置茶标记为喝光（可说「我买了XX」恢复）；自购茶直接删除。茶名模糊匹配。"""
    key = name.strip()
    if not key:
        return "茶名不能为空。"
    hits = [t for t in _all_teas() if key in t["name"] or t["name"] in key]
    if not hits:
        return f"库存里没找到「{name}」。说「看看库存」核对名称。"
    if len(hits) > 1:
        exact = [t for t in hits if t["name"] == key]
        if not exact:
            return f"「{key}」匹配到多款：{'、'.join(t['name'] for t in hits[:8])}。请说清楚是哪一款。"
        hits = exact
    tea = hits[0]
    st = _load_state()
    if tea["id"].startswith("custom_"):
        st["custom_teas"] = [c for c in st.get("custom_teas", []) if c["id"] != tea["id"]]
        action = "自购茶，已删除"
    else:
        removed = st.setdefault("removed_ids", [])
        if tea["id"] in removed:
            return f"「{tea['name']}」之前已标记喝光。"
        removed.append(tea["id"])
        action = "内置茶，已标记喝光"
    _save_state(st)
    total = len(_all_teas())
    return (f"🍂 已移除：{tea['name']}（{tea['cat']}）。{action}，库存还剩 {total} 款。\n"
            f"   误操作说「我买了{tea['name']}」即可恢复。")


@mcp.tool()
def clear_inventory(confirm: bool = False) -> str:
    """「我搬到了外地」：清空全部库存（内置107款全部标记移除、自购茶删除）与喝茶历史、复盘调校。
    清空后可用「我买了XX、YY、ZZ」批量导入新茶单；与内置茶全名相同的会自动恢复原参数。

    参数:
      confirm: 必须为 True 才真正执行（防误触）。首次调用返回预览。
    """
    st = _load_state()
    if not confirm:
        return (f"⚠️ 「我搬到了外地」将清空：内置 {len(TEAS)} 款 + 自购 {len(st.get('custom_teas', []))} 款 + "
                f"历史 {len(st.get('history', []))} 条 + 复盘调校 {len(st.get('overrides', {}))} 款。\n"
                f"确认请说「确认清空」/「搬走了」，或让我调用 clear_inventory(confirm=True)。")
    st["removed_ids"] = [t["id"] for t in TEAS]
    st["custom_teas"] = []
    st["history"] = []
    st["overrides"] = {}
    _save_state(st)
    return (f"🧳 已清空全部库存与记录。\n"
            f"   现在说「我买了龙井、铁观音、正山小种」批量导入你的茶单即可（内置同名茶自动恢复原参数）。")


@mcp.tool()
def set_brewer(pot_ml: int = -1, cold_ml: int = -1, reset: bool = False) -> str:
    """修改壶具容量：「我的茶壶是500ml」/「冷泡壶换成2L」。投茶量按茶水比自动等比缩放，水温/时间不变。
    默认 400ml 茶壶 + 1.6L 冷泡壶；存储的投茶量始终是 400ml/1.6L 基准值，仅显示时折算。

    参数:
      pot_ml:   茶壶容量 ml（100~3000），>=0 才生效
      cold_ml:  冷泡壶容量 ml（500~6000），>=0 才生效
      reset:    True 恢复默认 400ml / 1.6L
    """
    st = _load_state()
    cfg = st.setdefault("brewer", {})
    if reset:
        cfg.clear()
        _save_state(st)
        return "↩️ 已恢复默认壶具：400ml 茶壶 + 1.6L 冷泡壶。"
    if pot_ml >= 0:
        cfg["pot_ml"] = max(100, min(int(pot_ml), 3000))
    if cold_ml >= 0:
        cfg["cold_ml"] = max(500, min(int(cold_ml), 6000))
    _save_state(st)
    c = _brew_config()
    pot, cold = c["pot_ml"], c["cold_ml"]
    return (f"🫖 壶具已更新：茶壶 {pot}ml（投茶量按 {pot/400:.2f}× 缩放）｜ "
            f"冷泡壶 {cold/1000:g}L（投茶量按 {cold/1600:.2f}× 缩放）。\n"
            f"   水温与浸泡/冷藏时间不随容量变化；说「重置壶具」恢复默认。")


@mcp.tool()
def coldbrew_recommend(datetime_str: str = "", randomness: float = 0.6, count: int = 1) -> str:
    """「今天冷泡什么」：为 1.6L 冷泡壶推荐冷泡茶（冷藏层约4℃）。
    输出投茶量、冷藏时长、预计可饮时间。抹茶/可可/茶膏/药茶丸不适合冷泡壶，自动排除。

    参数:
      datetime_str: 可选，ISO 格式 '2026-08-16T21:30'；缺省用系统当前时间（用于计算"几点能喝"）
      randomness:   0~1 随机程度，默认 0.6
      count:        返回几款（主推+备选），默认 1，最多 5
    """
    now = datetime.now()
    if datetime_str.strip():
        try:
            now = datetime.fromisoformat(datetime_str.strip())
        except ValueError:
            now = datetime.now()
    d, h = now.date(), now.hour
    season = _season(d)
    count = max(1, min(count, 5))
    randomness = max(0.0, min(randomness, 1.0))

    hist = _load_state().get("history", [])
    allt = _all_teas()
    if not allt:
        return "🍂 库存是空的。说「我买了XX」入库后就能推荐啦。"

    cands = [t for t in allt if not any(k in t["name"] for k in _COLD_EXCLUDE)]
    if not cands:
        return "库存里没有适合冷泡的茶。"

    season_f = _cold_season_factor(d)
    scored = []
    for tea in cands:
        w = COLD_SUIT.get(tea["cat"], 0.70)
        w *= season_f
        w *= _fatigue(hist, tea["id"], d)
        w *= _rotation(hist, tea["id"], d)
        w *= math.exp(random.uniform(-0.50, 0.50))
        scored.append((w, tea))

    tau = 0.20 + randomness * 2.00
    warmed = [(w ** (1.0 / tau), t) for w, t in scored]
    picked = _pick(warmed, count)

    cold = _brew_config()["cold_ml"]
    lines = [
        f"🧊 今天冷泡什么 ｜ {d.month}月{d.day}日 周{'一二三四五六日'[d.weekday()]} "
        f"｜ {season}季 ｜ {cold/1000:g}L冷泡壶 ｜ 冷藏层约4℃",
    ]
    medal = ["🥇 主推", "🥈 备选1", "🥉 备选2", "4️⃣ 备选3", "5️⃣ 备选4"]
    for rank, tea in enumerate(picked):
        g, hours = _cold_params(tea)
        g_disp = _g_for_cold(g)
        w_before = next(w for w, t in scored if t is tea)
        done_dt = now + timedelta(hours=hours)
        cmark = " ★已调校" if _has_override(tea["id"]) else ""
        lines.append("")
        lines.append(f"{medal[rank]}：{tea['name']}（{tea['cat']}·{tea['note']}）{cmark}")
        lines.append(f"   投茶 {g_disp:g}g ｜ 冷水 {cold/1000:g}L ｜ 冷藏 {hours:.0f}-{hours + 1:.0f} 小时 ｜ 无需润茶")
        lines.append(
            "   操作：茶叶装茶包袋 → 入壶注满直饮水 → 盖好放冷藏层（约4℃，勿冷冻）"
            " → 到点取出茶袋（茶水分离）→ 24小时内喝完"
        )
        lines.append(f"   时间线：现在 {now.strftime('%H:%M')} 做 → {done_dt.strftime('%H:%M')} 前后取出茶袋即饮")
        reason_parts = [
            f"冷泡适配×{COLD_SUIT.get(tea['cat'], 0.70):.2f}",
            f"季节因子×{season_f:.2f}",
            f"综合权重{w_before:.3f}",
        ]
        lines.append("   理由：" + " ｜ ".join(reason_parts))
        if tea["tip"]:
            tip = re.sub(r"[，,]?润茶\d*秒", "", tea["tip"])  # 冷泡不润茶，过滤热泡提示
            if tip:
                lines.append(f"   💡 {tip}")
    lines.append("")
    lines.append("冷泡喝完后说「我喝了{茶名}」同样计入疲劳降权。")
    return "\n".join(lines)


@mcp.tool()
def review(name: str, feedback: str = "", mode: str = "hot", reset: bool = False,
           g: float = -1.0, temp: int = -1, minutes: float = -1.0, hours: float = -1.0,
           prewash: int = -1, lid: int = -1, note: str = "") -> str:
    """「复盘」：记录喝感评价，并自动微调该款茶的热泡/冷泡参数（持久化到 state.json）。
    理论参数只是起点——商家优劣、陈化、储存变质都会让实际口感偏离，复盘让参数贴合你的真实杯子。

    参数:
      name:     茶名（必填，模糊匹配库存）
      feedback: 喝感反馈词。'太淡'/'不够味'→加量延时加温；'太浓'/'苦'→减量延时降温；'涩'→降温减时；
                '仓气重'/'仓味'/'堆味'/'霉味'→洗茶档位+1；'洗茶太过'/'香味洗掉'→洗茶档位-1；
                '闷味'/'闷熟'→改开盖泡；'香气散'/'跑香'→改盖盖泡；
                '泡酸'/'发酸'→降温（红茶高温出酸）；'香味没了'/'没香气'→降温（高温毁香）；
                '正好'/'好喝'→记录不调；含'重置'→清除调校。多维可组合（如'仓气重还淡'、'香味没了还淡'）。
      mode:     hot=热泡壶泡（默认）；cold=冷泡
      reset:    True 直接清除该茶该场景的调校（等价 feedback 含'重置'）
      g/temp/minutes: 直接指定热泡目标参数（投茶g/水温℃/浸泡min，>=0 才生效，优先于自动调整）
      hours:    直接指定冷泡冷藏小时数（>=0 生效）
      prewash:  直接指定洗茶档位 0~6（0=不洗，2=生普默认，4=熟普/六堡/砖茶默认；>=0 生效）
      lid:      直接指定盖盖/开盖：1=盖盖（存香保温），0=开盖（散气防闷）；>=0 生效
      note:     可选备注，如 '商家这批偏淡' / '放久了仓气重'
    """
    key = name.strip()
    if not key:
        return "茶名不能为空，例如「复盘：正山小种太淡了」。"
    hits = [t for t in _all_teas() if key in t["name"] or t["name"] in key]
    if not hits:
        return f"库存里没找到「{name}」。说「看看库存」核对名称。"
    if len(hits) > 1:
        exact = [t for t in hits if t["name"] == key]
        if not exact:
            return f"「{key}」匹配到多款：{'、'.join(t['name'] for t in hits[:8])}。请说清楚是哪一款。"
        hits = exact
    tea = hits[0]

    mode = "cold" if mode.strip().lower() in ("cold", "冷泡", "冷") else "hot"
    mode_cn = "冷泡" if mode == "cold" else "热泡"
    fb = (feedback or "").strip()

    st = _load_state()
    ov_all = st.setdefault("overrides", {})
    ov_tea = ov_all.setdefault(tea["id"], {})

    # ---- 重置 -------
    if reset or _has_any(fb, _FB_RESET):
        ov_tea.pop(mode, None)
        if not ov_tea:
            ov_all.pop(tea["id"], None)
        _save_state(st)
        if mode == "hot":
            return f"↩️ 已清除「{tea['name']}」的热泡调校，恢复理论参数：{_g_for_pot(tea['g']):g}g ｜ {tea['t']}℃ ｜ {tea['m']:.1f}分钟。"
        cg, ch = _cold_params(tea)
        return f"↩️ 已清除「{tea['name']}」的冷泡调校，恢复理论参数：{_g_for_cold(cg):g}g ｜ 冷藏 {ch:.0f}h。"

    # ---- 显式目标参数 -------
    if g >= 0 or temp >= 0 or minutes >= 0 or hours >= 0 or prewash >= 0 or lid >= 0:
        new_ov = {}
        if g >= 0:
            base_g = float(g) * _DEFAULT_POT_ML / _brew_config()["pot_ml"]
            new_ov["g"] = _clamp(base_g, *_HOT_LIMITS["g"])
        if temp >= 0:
            new_ov["t"] = _clamp(int(temp), *_HOT_LIMITS["t"])
        if minutes >= 0:
            new_ov["m"] = _clamp(float(minutes), *_HOT_LIMITS["m"])
        if hours >= 0:
            new_ov["h"] = _clamp(float(hours), *_COLD_LIMITS["h"])
        if prewash >= 0:
            new_ov["prewash"] = _clamp(int(prewash), _PREWASH_MIN, _PREWASH_MAX)
        if lid >= 0:
            new_ov["lid"] = bool(lid)
        if note.strip():
            new_ov["note"] = note.strip()
        ov_tea[mode] = new_ov
        _save_state(st)
        if mode == "cold":
            cg2, ch2 = _cold_params(tea)
            detail = f"   手动指定：投茶 {_g_for_cold(cg2):g}g ｜ 冷藏 {ch2:.0f}小时"
        else:
            eff = _effective(tea)
            detail = f"   手动指定：投茶 {_g_for_pot(eff['g']):g}g ｜ 水温 {eff['t']}℃ ｜ 浸泡 {eff['m']:.1f}分钟"
            pw2 = _prewash_of(tea)
            if pw2:
                detail += f" ｜ 洗茶L{pw2}：{PREWASH_PLANS[pw2]}"
            detail += f" ｜ {'盖盖' if _lid_of(tea) else '开盖'}泡"
        return (f"📝 复盘已记录：{tea['name']}（{tea['cat']}·{mode_cn}）\n"
                f"{detail}\n"
                f"   下次推荐将使用新参数（★已调校）。")

    # ---- 反馈自动调整 -------
    if mode == "hot":
        eff = _effective(tea)
        old_g, old_t, old_m = eff["g"], eff["t"], eff["m"]
        if fb and _has_any(fb, _FB_GOOD):
            _save_state(st)
            return (f"📝 复盘已记录：{tea['name']}（{tea['cat']}·热泡）\n"
                    f"   反馈：{fb} → 参数保持 {_g_for_pot(old_g):g}g ｜ {old_t}℃ ｜ {old_m:.1f}分钟不变。")
        if not fb:
            pw0 = _prewash_of(tea)
            pw_info = f" ｜ 洗茶L{pw0}（{PREWASH_PLANS[pw0]}）" if pw0 else ""
            lid_info = f" ｜ {'盖盖' if _lid_of(tea) else '开盖'}泡"
            return (f"请给点反馈，如「{tea['name']}太淡」/「{tea['name']}有点苦」/「{tea['name']}仓气重」/「{tea['name']}闷味」/「{tea['name']}正好」。"
                    f"当前参数：{_g_for_pot(old_g):g}g ｜ {old_t}℃ ｜ {old_m:.1f}分钟{pw_info}{lid_info}。")

        # 1) 洗茶档位（仓气维度，独立于浓淡）
        pw_old = _prewash_of(tea)
        pw_new = pw_old
        pw_log = []
        if _has_any(fb, _FB_WAREHOUSE):
            if pw_old < _PREWASH_MAX:
                pw_new = pw_old + 1
                pw_log.append(f"洗茶/散味加强：L{pw_old}→L{pw_new}")
            else:
                pw_log.append(f"洗茶档位已达上限L{_PREWASH_MAX}")
        elif _has_any(fb, _FB_OVERWASH):
            if pw_old > _PREWASH_MIN:
                pw_new = pw_old - 1
                pw_log.append(f"洗茶/散味减弱：L{pw_old}→L{pw_new}")
            else:
                pw_log.append("已是不洗茶L0")

        # 2) 浓淡/苦涩维度（酸/香反馈存在时"淡"不加温，避免降温与加温打架）
        aroma_issue = _has_any(fb, _FB_SOUR) or _has_any(fb, _FB_AROMA_LOST)
        ng, nt, nm, log = _adjust_hot(old_g, old_t, old_m, fb, no_heat=aroma_issue)
        if aroma_issue:
            lo_t2, _hi_t2 = _HOT_LIMITS["t"]
            nt2 = _clamp(nt - 3, lo_t2, _hi_t2)
            if nt2 < nt:
                log.append("水温额外-3℃（高温导致发酸/香气流失）")
            else:
                log.append("水温已至下限70℃，无法再降")
            nt = nt2
        new_ov = dict(ov_tea.get("hot", {}))
        new_ov.update({"g": ng, "t": nt, "m": nm})
        if pw_new != pw_old:
            new_ov["prewash"] = pw_new

        # 3) 盖盖维度（闷味/香气，独立调整）
        lid_old = _lid_of(tea)
        lid_new = lid_old
        lid_log = []
        if _has_any(fb, _FB_STUFFY):
            if lid_old:
                lid_new = False
                lid_log.append("改为开盖泡（散闷味/挥发）")
            else:
                lid_log.append("已为开盖泡，无需调整")
        elif _has_any(fb, _FB_FLAT_AROMA):
            if not lid_old:
                lid_new = True
                lid_log.append("改为盖盖泡（存香）")
            else:
                lid_log.append("已为盖盖泡，无需调整")
        if lid_new != lid_old:
            new_ov["lid"] = lid_new
        if note.strip():
            new_ov["note"] = note.strip()
        ov_tea["hot"] = new_ov
        _save_state(st)
        changed = [f"投茶 {_g_for_pot(old_g):g}g→{_g_for_pot(ng):g}g", f"水温 {old_t}℃→{nt}℃", f"浸泡 {old_m:.1f}min→{nm:.1f}min"]
        if pw_new != pw_old:
            old_plan = f"L{pw_old}（{PREWASH_PLANS[pw_old]}）" if pw_old else "不洗茶"
            new_plan = f"L{pw_new}（{PREWASH_PLANS[pw_new]}）" if pw_new else "不洗茶"
            changed.append(f"洗茶 {old_plan} → {new_plan}")
        if lid_new != lid_old:
            changed.append(f"{'盖盖' if lid_old else '开盖'} → {'盖盖' if lid_new else '开盖'}")
        all_log = pw_log + log + lid_log
        return (f"📝 复盘已记录：{tea['name']}（{tea['cat']}·热泡）\n"
                f"   反馈：{fb or '（未填写）'}\n"
                f"   调整：{' ｜ '.join(changed)}\n"
                f"   动作：{'、'.join(all_log) if all_log else '无变化'}\n"
                f"   下次推荐将使用新参数（★已调校）；不满意说「还是淡/还是苦/仓气还是重」继续微调，「重置{tea['name']}」恢复默认。")

    # cold
    if _has_any(fb, _FB_WAREHOUSE) or _has_any(fb, _FB_OVERWASH):
        return (f"🧊 冷泡场景一般不洗茶。「{tea['name']}」若仓气重，建议：冷泡前先用沸水快洗1次（即出）再装袋冷藏；"
                f"或改热泡后复盘说「仓气重」，我会调整洗茶档位。")
    if _has_any(fb, _FB_SOUR) or _has_any(fb, _FB_AROMA_LOST):
        return (f"🧊 冷泡固定 4℃ 冷藏，一般不会高温发酸/毁香。若冷泡仍发酸，建议缩短冷藏时长或改热泡，"
                f"热泡复盘说「泡酸了」/「香味没了」我会自动降温。")
    cg, ch = _cold_params(tea)
    if fb and _has_any(fb, _FB_GOOD):
        _save_state(st)
        return (f"📝 复盘已记录：{tea['name']}（{tea['cat']}·冷泡）\n"
                f"   反馈：{fb} → 参数保持 {_g_for_cold(cg):g}g ｜ 冷藏 {ch:.0f}h 不变。")
    if not fb:
        return (f"请给点反馈，如「冷泡的{tea['name']}太淡」/「{tea['name']}冷泡有点苦」。"
                f"当前参数：{_g_for_cold(cg):g}g ｜ 冷藏 {ch:.0f}h。")
    ng2, nh2, log2 = _adjust_cold(cg, ch, fb)
    new_ov = dict(ov_tea.get("cold", {}))
    new_ov.update({"g": ng2, "h": nh2})
    if note.strip():
        new_ov["note"] = note.strip()
    ov_tea["cold"] = new_ov
    _save_state(st)
    return (f"📝 复盘已记录：{tea['name']}（{tea['cat']}·冷泡）\n"
            f"   反馈：{fb or '（未填写）'}\n"
            f"   调整：投茶 {_g_for_cold(cg):g}g→{_g_for_cold(ng2):g}g ｜ 冷藏 {ch:.0f}h→{nh2:.0f}h\n"
            f"   动作：{'、'.join(log2) if log2 else '无变化'}\n"
            f"   下次冷泡推荐将使用新参数；「重置{tea['name']}」恢复默认。")


if __name__ == "__main__":
    mcp.run(transport="stdio")
