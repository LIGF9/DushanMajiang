# 麻将牌定义文件
"""
定义麻将游戏中使用的牌相关常量和辅助函数
"""

# 麻将牌花色
TILE_SUITS = ['万', '条', '筒']

# 麻将牌数值
TILE_VALUES = ['1', '2', '3', '4', '5', '6', '7', '8', '9']

# 单张麻将牌定义（每种牌各一张）
TILE = [f"{value}{suit}" for suit in TILE_SUITS for value in TILE_VALUES]

# 完整的牌堆（108张，每种牌4张）
TILES = TILE * 4

def get_tile_value(tile: str) -> int:
    """获取麻将牌的数值部分
    
    Args:
        tile: 麻将牌字符串，如 "1万"
    
    Returns:
        int: 牌的数值部分，如 1
    """
    return int(tile[0]) 

def get_tile_suit(tile: str) -> str:
    """获取麻将牌的花色部分
    
    Args:
        tile: 麻将牌字符串，如 "1万"
    
    Returns:
        str: 牌的花色部分，如 "万"
    """
    return tile[1]

def is_tile_valid(tile: str) -> bool:
    """检查麻将牌是否有效
    
    Args:
        tile: 麻将牌字符串
    
    Returns:
        bool: 是否为有效的麻将牌
    """
    return tile in TILE

def create_tile(value: int, suit: str) -> str:
    """创建麻将牌字符串
    
    Args:
        value: 牌的数值部分，如 1
        suit: 牌的花色部分，如 "万"
    
    Returns:
        str: 完整的麻将牌字符串，如 "1万"
    """
    return f"{value}{suit}"

