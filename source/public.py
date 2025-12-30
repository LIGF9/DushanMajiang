from dataclasses import dataclass
from enum import Enum, auto
from typing import List


# 胡牌类型枚举
class Tag(Enum):

    # 胡牌方式: 自己摸牌胡
    ZI_MO = "自  摸"
    GANG_SAHNG_KAI_HUA = "杠上开花"
    MIAO_SHOU_HUI_CHUN = "妙手回春"

    # 胡牌方式: 吃胡
    ZHUO_PAO = "捉  炮"
    ZHUO_RE_PAO = "捉热炮"
    QIANG_GANG_HU = "抢杠胡"
    HAI_DI_LAO_YUE = "海底捞月"

    # 胡牌类型
    TIAN_HU = "天  胡"
    BAO_JIAO = "报  叫"
    LONG_QI_DUI = "龙七对"
    QING_YI_SE = "清一色"
    DAN_DIAO = "独  钓"
    XIAO_QI_DUI = "小七对"
    DA_DUI_ZI = "大对子"
    PING_HU = "平  胡"

    # 鸡牌类型
    CHONG_FENG_JI = "冲锋鸡"
    HENG_JI = "横  鸡"
    YAO_JI = "幺  鸡"

    # 其他标签
    JI_QUAN_SHAO = "鸡牌全烧"
    FANG_RE_PAO = "放热炮"
    FANG_PAO = "放  炮"
    ONE_TILE_DOUBLE_BOOM = "一炮双响"
    ONE_TILE_TRIBLE_BOOM = "一炮三响"
    ZE_REN_JI = "责任鸡"
    MI_JIAO_PAI = "米叫牌"
    ZAO_BAO_JI = "遭包鸡"
    GANG = "杠"

# 游戏状态枚举
class GameState(Enum):
    GAME_START = auto()  # 开始游戏
    GAME_OVER = auto()  # 游戏结束
    DRAW_TILE_PHASE = auto()  # 玩家摸牌阶段
    DISCARD_TILE_PHASE = auto()  # 玩家出牌阶段
    GANG_PHASE = auto()  # 玩家杠牌阶段
    DRAW_AFTER_GANG_PHASE = auto()  # 杠牌者摸牌阶段
    REPAO_PHASE = auto()  # 杠牌者热炮牌阶段
    WAIT_PHASE = auto()  # 等待其他玩家操作阶段

# 决策类型枚举（支持扩展吃、胡等）
class DecisionType(Enum):
    PENG = "碰"
    GANG = "杠"
    HU = "胡"
    DISCARD = "出牌"
    CANCEL = "取消"
    default = "默认"

# 决策请求（GameManager → UIManager 传递的信息）
@dataclass
class DecisionRequest:
    decision_list: List[DecisionType]  # 决策类型列表
    player_index: int = -1  # 要检查的玩家索引
    tile: str = ""  # 决策相关数据（如选中的牌）
    callback: callable = None  # 决策完成后的回调函数

# 决策结果（UIManager → GameManager 传递的信息）
@dataclass
class DecisionResult:
    decision_type: DecisionType  # 决策类型
    result: bool = False # 决策结果,False表示拒绝任何行动,True表示执行decision_type
    tile: str = ""  # 决策相关数据（如选中的牌）
    reason: str = ""  # 决策原因

from pathlib import Path

import os, sys

def get_resource_path(relative_path: str) -> str:
    """返回资源的绝对路径，兼容 PyInstaller 单文件运行时。"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    rel = relative_path.replace('/', os.path.sep).lstrip(os.path.sep)
    return os.path.join(base_path, rel)

def get_jpg_names(dir_path):
    """
    从 dir_path 读取所有 .jpg 文件名（去掉后缀），输出并返回列表
    """
    full_path = get_resource_path(dir_path)
    p = Path(full_path)
    if not p.exists() or not p.is_dir():
        names = []
    else:
        names = [f.stem for f in p.iterdir() if f.is_file() and f.suffix.lower() == '.jpg']

    return names