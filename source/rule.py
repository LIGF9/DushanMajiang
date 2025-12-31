from typing import List,Tuple
from source.tile import TILE
from settings import Settings
from source.public import Tag
import copy
from typing import Dict

class Rule:
    def __init__(self):
        self.settings = Settings()
 
    def can_peng(self, hand, tile: str):
        """
        检查玩家是否可以碰牌
        碰牌：隐藏手牌中有2张相同的牌
        hand: 玩家手牌，包含"concealed"（隐藏手牌）和"exposed"（明牌）
            ***如果是自己摸的牌，需要是未插入到"concealed"中的状态
        tile: 要检查的牌
        """
        return hand["concealed"].count(tile) >= 2

    def can_self_gang(self, hand, tile: str):
        """
        检查玩家是否可以杠牌
        自杠：隐藏手牌中有3张相同的牌,又新摸到相同的牌
        hand: 玩家手牌，包含"concealed"（隐藏手牌）和"exposed"（明牌）
        tile: 要检查的牌
        """        
        return hand["concealed"].count(tile) == 4

    def can_add_gang(self, hand, tile: str):
        """
        检查玩家是否可以杠牌
        加杠：明牌中有一组3张相同的牌（碰过的牌），且新摸到一张相同的牌
        hand: 玩家手牌，包含"concealed"（隐藏手牌）和"exposed"（明牌）
        tile: 要检查的牌
        """

        # 加杠：明牌中有一组3张相同的牌（碰过的牌），且新摸到一张相同的牌
        for group in hand["exposed"]:
            if (group["tiles"].count(tile) == 3 
                and tile in hand["concealed"]):
                return True

        return False

    def can_gang_others(self, hand, tile: str):
        """
        检查玩家是否可以杠牌
        其他玩家杠牌：隐藏手牌中有3张相同的牌，要检查的牌来自其他玩家打的牌
        hand: 玩家手牌，包含"concealed"（隐藏手牌）和"exposed"（明牌）
        tile: 要检查的牌
        """

        return hand["concealed"].count(tile) == 3

    def has_gang(self,hand) -> bool:
        """检查玩家是否有杠"""
        return any(len(group["tiles"]) == 4 for group in hand["exposed"])

    def has_passport(self,hand,tags:List[Tag]=[]) -> Tuple[bool, str]:
        """
        检查玩家是否有通行证：
        1. 报叫
        2. 有杠牌
        3. 听牌且听的牌型不是小平胡（若手牌可胡大牌也可胡小平胡，则胡小平胡时不能获得通行证）
        返回：(bool, reason, win_tiles)
            bool: 是否有通行证
            reason: 获得原因，如"有杠牌"/"听非平胡"/""
        """

        def handle_ting_info(ting_tiles):
            if ting_tiles:
                # 按听牌类型分组
                ting_by_type = {}
                for win_type, tile, remaining in ting_tiles:
                    # 排除平胡
                    win_type = [t.value for t in win_type if t!=Tag.PING_HU]
                    if not win_type:
                        break

                    win_type_str = ''.join(win_type)
                    if win_type_str not in ting_by_type:
                        ting_by_type[win_type_str] = f"[{tile}]剩{remaining}张"
                    else:
                        ting_by_type[win_type_str] += f"，[{tile}]剩{remaining}张"
                
                # 格式化每种听牌类型的信息
                ting_info = []
                for win_type, tiles_info in ting_by_type.items():
                    ting_info.append(f"{win_type}({tiles_info})")

                return "，".join(ting_info)


        # 1.报叫
        if any(t['tag'] == Tag.BAO_JIAO for t in tags):
            return True, "报叫"

        # 2. 有杠牌，细化杠类型
        gang_reasons = []
        for group in hand["exposed"]:
            if len(group["tiles"]) == 4:
                tile = group["tiles"][0]
                gang_reasons.append(f"杠{tile}")
        if gang_reasons:
            return True, "，".join(gang_reasons)

        # 3. 听牌且听的牌型不是小平胡，细化胡牌类型
        is_ting, ting_info = self.check_ting(hand, [])
        if is_ting:
            ting_str = handle_ting_info(ting_info)
            if ting_str:
                return True, ting_str

        return False, ""

    def check_hu(self, hand, tile: str) -> Tuple[bool, List[Tag]]:
        """
        检查玩家是否胡牌，支持以下胡牌牌型：
        1. 大对子：1 对将牌 + 4 个刻子（至少一个非暴露刻子）
        2. 单钓将：1 对将牌 + 4 个暴露刻子
        3. 小七对：7 个对子
        4. 龙七对：5 个对子 + 自摸暗杠
        5. 常规胡牌：1 对将牌 + m 个顺子 + n 个刻子（m + n = 4，m 不为 0）
        6. 清一色：所有牌属于同一种花色
        返回：胡牌类型字符串或False
        """

        # 检查清一色
        def is_pure_suit(concealed: List[str],exposed: List[str],tile: str) -> bool:
            tiles = concealed.copy() + exposed.copy()
            tiles.append(tile)
            suit = tiles[0][-1]  # 获取第一张牌的花色
            return all(tile[-1] == suit for tile in tiles)

        # 检查大对子
        def is_big_pairs(concealed: List[str],exposed: List[str],tile: str) -> bool:
            
            #单钓将
            if len(set(exposed)) == 4 or len(concealed) == 1:
                return False

            tiles = concealed.copy() + exposed.copy()
            tiles.append(tile)
            pairs = [tile for tile in set(tiles) if tiles.count(tile) == 2]
            if len(pairs) != 1:
                return False
            test_concealed = tiles.copy()
            test_concealed.remove(pairs[0])
            test_concealed.remove(pairs[0])
            return all(test_concealed.count(tile) == 3 for tile in set(test_concealed))

        #单钓：1 对将牌 + 4 个暴露刻子
        def is_single_tile(concealed: List[str],exposed: List[str],tile: str) -> bool:
            
            if len(set(exposed)) != 4 or len(concealed) != 1:
                return False
            if concealed[0] == tile:
                return True
            return False

        # 检查小七对
        def is_seven_pairs(concealed: List[str],exposed: List[str],tile: str) -> bool:
            tiles = concealed.copy() + exposed.copy()
            if exposed:
                return False
            tiles.append(tile)
            tile_counts = {tile: tiles.count(tile) for tile in set(tiles)}
            # 统计对子的数量
            pairs = sum(count // 2 for count in tile_counts.values())
            # 把出现四张的牌提出来组成列表
            four_tiles = [t for t, c in tile_counts.items() if c == 4]
            return pairs == 7 and tile not in four_tiles

        # 检查龙七对
        def is_dragon_seven_pairs(concealed: List[str],exposed: List[str],tile: str) -> bool:
            concealed = concealed.copy()
            exposed = exposed.copy()
            if exposed:
                return False
            tiles = concealed.copy() + exposed.copy()
            tiles.append(tile)
            tile_counts = {tile: tiles.count(tile) for tile in set(tiles)}
            # 统计对子的数量
            pairs = sum(count // 2 for count in tile_counts.values())
            # 把出现四张的牌提出来组成列表
            four_tiles = [t for t, c in tile_counts.items() if c == 4]
            return pairs == 7 and tile in four_tiles

        # 检查常规胡牌
        def is_normal_win(concealed: List[str],exposed: List[str],tile: str) -> bool:
            """
            判断是否普通胡牌（4个面子 + 1个对子）
            前提：
            - concealed: 隐藏手牌已排序（同花色从小到大）
            - exposed: 明牌已排序（同花色从小到大）
            """
            tiles = concealed.copy()
            exposed = exposed.copy()
            tiles.append(tile)
            # print(f"is_normal_win:牌型为{tiles}，明牌为{exposed}")
            # 1. 计算已副露的面子数
            exposed_count = len(exposed) // 3
            if exposed_count > 4:
                return False
            needed = 4 - exposed_count  # 手牌需组成的面子数
            if len(tiles) != needed * 3 + 2:
                return False

            from collections import Counter
            cnt = Counter(tiles)
            # 2. 枚举将牌（对子）
            for p in cnt:
                if cnt[p] < 2:
                    continue

                # 移除将牌
                concealed = cnt.copy()
                concealed[p] -= 2
                if concealed[p] == 0:
                    del concealed[p]

                n = needed  # 需要组成 n 个面子

                # 3. 贪心：先处理刻子（修复：使用 list(concealed.keys()) 避免迭代时修改）
                for t in list(concealed.keys()):  # ← 修复：转为列表，避免运行时修改问题
                    while concealed[t] >= 3:
                        n -= 1
                        concealed[t] -= 3
                        if concealed[t] == 0:
                            del concealed[t]
                        if n <= 0:
                            break  # 提前退出

                if n <= 0:
                    return True

                # 4. 处理顺子（只对万/条/筒）
                # 按排序处理（已假设手牌有序，但 key 要排序）
                for t in sorted(concealed.keys()):
                    if n <= 0:
                        break
                    if len(t) != 2 or not t[0].isdigit() or t[1] not in '万条筒':
                        continue
                    num = int(t[0])
                    suit = t[1]
                    if num > 7:
                        continue
                    a, b = f"{num+1}{suit}", f"{num+2}{suit}"
                    while t in concealed and a in concealed and b in concealed and concealed[t] > 0 and concealed[a] > 0 and concealed[b] > 0:
                        n -= 1
                        if n < 0:
                            break
                        concealed[t] -= 1
                        concealed[a] -= 1
                        concealed[b] -= 1
                        for x in [t, a, b]:
                            if concealed[x] == 0:
                                del concealed[x]

                if n == 0:
                    return True

            return False

        # 手牌和副露牌(杠牌只取前3张)
        # 过滤隐藏手牌中的非字符串元素或无效字符串
        concealed = [tile for tile in copy.deepcopy(hand["concealed"]) if isinstance(tile, str) and tile.strip()]
        # 过滤副露牌中的非字典元素
        exposed = [tile for group in hand["exposed"] if isinstance(group, dict) for i,tile in enumerate(group["tiles"]) if i<3]

        # 计算总手牌数量
        concealed_tiles = len(concealed + exposed)

        # 仅允许13张牌进行胡牌检查
        if concealed_tiles != 13:
            print(f"check_hu:手牌为{concealed_tiles}张，数量错误。")
            print(f"check_hu:\n隐藏手牌为{hand['concealed']}\n副露牌为{hand['exposed']}\n需要检查的牌为{tile}")
            raise ValueError(f"check_hu:手牌为{concealed_tiles}张，数量错误。")
        
        # 检查所有胡牌牌型
        win_type = []
        if is_big_pairs(concealed,exposed,tile):
            win_type.append(Tag.DA_DUI_ZI)
        if is_single_tile(concealed,exposed,tile):
            win_type.append(Tag.DAN_DIAO)
        if is_seven_pairs(concealed,exposed,tile):
            win_type.append(Tag.XIAO_QI_DUI)   
        if is_dragon_seven_pairs(concealed,exposed,tile):
            win_type.append(Tag.LONG_QI_DUI)
        if not win_type and is_normal_win(concealed,exposed,tile):
            win_type.append(Tag.PING_HU)
        if win_type and is_pure_suit(concealed,exposed,tile):
            if Tag.PING_HU in win_type:
                win_type.remove(Tag.PING_HU)
            win_type.append(Tag.QING_YI_SE)
        return (False, []) if not win_type else (True, win_type)

    def check_ting(self, hand: Dict[str, List[str]], all_used_tiles: List[str]) -> Tuple[bool, List[Tuple[str, str, int]]]:
        """
        检查玩家是否听牌，并返回听牌信息
        参数:
            hand: 玩家手牌，包含"concealed"（隐藏牌）和"exposed"（副露牌）
            all_used_tiles: 所有已用牌（弃牌+副露）
        返回值:
            tuple: (是否听牌, 听的牌及其剩余数量)
        """
        # 首先检查hand参数的格式
        if not isinstance(hand, dict) or "concealed" not in hand or "exposed" not in hand:
            print(f"check_ting:手牌格式错误，hand={hand}")
            return False, []
            
        concealed = hand["concealed"]
        exposed = hand["exposed"]
        
        # 检查手牌数量
        # 创建用于检查的手牌副本，避免修改原始数据
        # 过滤隐藏手牌中的非字符串元素或无效字符串
        test_concealed = [tile for tile in concealed.copy() if isinstance(tile, str) and tile.strip()]
        # 过滤副露牌中的非字典元素
        _exposed = [tile for group in hand["exposed"] if isinstance(group, dict) for i,tile in enumerate(group["tiles"]) if i<3]
        # 计算总手牌数量
        hand_tiles = len(test_concealed + _exposed)
        
        # 检查手牌数量
        if hand_tiles not in [13, 10, 7, 4, 1]:
            if len(concealed) != 0:
                print(f"check_ting:手牌为{hand_tiles}张，数量错误.")
                print(f"check_ting:隐藏手牌为{hand['concealed']}，副露牌为{hand['exposed']}")
                raise ValueError(f"check_ting:手牌为{hand_tiles}张，数量错误.")
        
        # 检查听牌
        ting_tiles = []
        for tile in TILE:
            if not tile:
                print(f"check_ting:牌 {tile} 不是有效的牌面")
                raise ValueError(f"牌 {tile} 不是有效的牌面")
            test_hand = {}
            import copy
            # 使用调整后的test_concealed副本，而不是原始concealed
            test_hand = {
                "concealed": copy.deepcopy(test_concealed),
                "exposed": [group for group in copy.deepcopy(hand["exposed"]) if isinstance(group, dict)]  # 过滤非字典元素
            }
            is_win, win_type = self.check_hu(test_hand, tile)
            if is_win:
                # 计算剩余牌数
                remaining = 4 - all_used_tiles.count(tile)
                ting_tiles.append((win_type, tile, remaining))
            
        return len(ting_tiles) > 0, ting_tiles

    def test_has_passport(self):
        """测试是否有通行证"""
        print("================================通行证测试开始=================================")
        rule = Rule()
        # 1. 有杠牌
        hand = {"concealed": ["3万", "4万", "5万", "4万", "4万", "7筒", "7筒"],
                "exposed": [{
                    "tiles": ["1万", "1万", "1万","一万"],
                    "is_gang": False
                },{
                    "tiles": ["2万", "2万", "2万", "2万"],
                    "is_gang": True
                }]}
        print("有杠牌："+str(rule.has_passport(hand)))
        # 2. 听牌且听的牌型不是小平胡
        hand = {"concealed": ["3万", "4万", "5万", "4万", "4万", "7万", "7万"],
                "exposed": [{
                    "tiles": ["1万", "1万", "1万"],
                    "is_gang": False
                },{
                    "tiles": ["2万", "2万", "2万"],
                    "is_gang": False
                }]}
        print("大牌通行证："+str(rule.has_passport(hand)))
        print("================================通行证测试结束=================================")

    def test_hu(self):
        """测试是否可以胡牌"""
        print("================================胡牌测试开始=================================")
        rule = Rule()
        # 单钓将
        hand = {"concealed": ["2万"],
                "exposed": [
                {
                    "tiles": ["3万", "3万", "3万",],
                    "is_gang": False
                },{
                    "tiles": ["5条", "5条", "5条"],
                    "is_gang": False
                },{
                    "tiles": ["3筒","3筒","3筒"],
                    "is_gang": False
                },{
                    "tiles": ["4筒", "4筒", "4筒"],
                    "is_gang": False
                },]}
        print("常规胡牌3叫卡张(5条))："+str(rule.check_hu(hand, "5条")))
        print("常规胡牌3叫卡张(2万)："+str(rule.check_hu(hand, "2万")))



        # # 清一色
        # hand = {"concealed": ["3万", "4万", "5万", "5万", "6万", "7万","6万", "7万", "8万", "8万", "8万", "9万","9万","9万"],
        #         "exposed": []}
        # print("清一色："+str(rule.check_hu(hand, "9万")))
        # # 大对子
        # hand = {"concealed": ["3万", "3万", "3万", "4万", "4万", "7筒", "7筒"],
        #         "exposed": [{
        #             "tiles": ["1万", "1万", "1万"],
        #             "is_gang": False
        #         },{
        #             "tiles": ["2万", "2万", "2万", "2万"],
        #             "is_gang": False
        #         }]}
        # print("大对子："+str(rule.check_hu(hand, "7筒")))
        # # 小对子
        # hand = {"concealed": ["3筒", "4万", "4万", "5万", "5万", "6万","6万", "7万", "7万", "8万", "8万", "9万","9万"],
        #         "exposed": []}
        # print("小七对："+str(rule.check_hu(hand, "3筒")))
        # hand = {"concealed": ["3筒", "3筒", "3筒", "3筒", "5万", "6万","6万", "7万", "7万", "8万", "8万", "9万","9万"],
        #         "exposed": []}
        # print("小七对："+str(rule.check_hu(hand, "5万")))
        # # 龙七对
        # hand = {"concealed": ["3筒", "3筒", "3筒", "5万", "5万", "6万","6万", "7万", "7万", "8万", "8万", "9万","9万"],
        #         "exposed": []}
        # print("龙七对："+str(rule.check_hu(hand, "3筒")))
        # 常规胡牌
        # # 牌型1:叫对楚
        # hand = {"concealed": ["3万", "4万", "5万", "4万", "4万", "7筒", "7筒"],
        #         "exposed": [{
        #             "tiles": ["1万", "1万", "1万"],
        #             "is_gang": False
        #         },{
        #             "tiles": ["2万", "2万", "2万", "2万"],
        #             "is_gang": False
        #         }]}
        # print("常规胡牌1叫对楚(4万)："+str(rule.check_hu(hand, "4万")))
        # print("常规胡牌1叫对楚(7筒)："+str(rule.check_hu(hand, "7筒")))
        # # 牌型2叫边张
        # hand = {"concealed": ["3万", "4万", "5万", "4万", "4万", "8筒", "7筒"],
        #         "exposed": [{
        #             "tiles": ["1万", "1万", "1万"],
        #             "is_gang": False
        #         },{
        #             "tiles": ["2万", "2万", "2万", "2万"],
        #             "is_gang": False
        #         }]}
        # print("常规胡牌2叫边张(9筒)："+str(rule.check_hu(hand, "9筒")))
        # # 牌型3叫卡张
        # hand = {"concealed": ["1万", "1万", "1万", "3万", "4万", "5万", "4万", "4万", "5筒", "7筒"],
        #         "exposed": [{
        #             "tiles": ["2万", "2万", "2万", "2万"],
        #             "is_gang": False
        #         }]}
        # print("常规胡牌3叫卡张(6筒)："+str(rule.check_hu(hand, "6筒")))
        # # 牌型4叫两头
        # hand = {"concealed": ["1万", "1万", "1万", "3万", "4万", "5万", "4万", "4万", "5筒", "6筒"],
        #         "exposed": [{
        #             "tiles": ["2万", "2万", "2万", "2万"],
        #             "is_gang": False
        #         }]}
        # print("常规胡牌4叫两头(7筒)："+str(rule.check_hu(hand, "7筒")))
        # print("常规胡牌4叫两头(4筒)："+str(rule.check_hu(hand, "4筒")))
        # # 牌型5叫147
        # hand = {"concealed": ["1万", "1万", "2万", "3万", "4万", "5万", "6万", "4筒", "5筒", "6筒"],
        #         "exposed": [{
        #             "tiles": ["2万", "2万", "2万", "2万"],
        #             "is_gang": False
        #         }]}
        # print("常规胡牌5叫147(1万)："+str(rule.check_hu(hand, "1万")))
        # print("常规胡牌5叫147(4万)："+str(rule.check_hu(hand, "4万")))
        # print("常规胡牌5叫147(7万)："+str(rule.check_hu(hand, "7万")))
        # # 牌型6叫258
        # hand = {"concealed": ["1万", "1万", "3万", "4万", "5万", "6万", "7万", "4筒", "5筒", "6筒"],
        #         "exposed": [{
        #             "tiles": ["2条", "2条", "2条", "2条"],
        #             "is_gang": False
        #         }]}
        # print("常规胡牌6叫258(2万)："+str(rule.check_hu(hand, "2万")))
        # print("常规胡牌6叫258(5万)："+str(rule.check_hu(hand, "5万")))
        # print("常规胡牌6叫258(8万)："+str(rule.check_hu(hand, "8万")))
        # # 牌型6叫369
        # hand = {"concealed": ["1万", "1万", "4万", "5万", "6万", "7万", "8万", "4筒", "5筒", "6筒"],
        #         "exposed": [{
        #             "tiles": ["2条", "2条", "2条", "2条"],
        #             "is_gang": False
        #         }]}
        # print("常规胡牌6叫369(3万)："+str(rule.check_hu(hand, "3万")))
        # print("常规胡牌6叫369(6万)："+str(rule.check_hu(hand, "6万")))
        # print("常规胡牌6叫369(9万)："+str(rule.check_hu(hand, "9万")))
        print("================================胡牌测试结束=================================")

    def test_ting(self):
        """测试是否可以听牌,听牌类型和数量"""
        print("================================听牌测试开始=================================")
        rule = Rule()
        all_used_tiles = ['9筒', '8条', '6条', '1万', '5万', '4万', '8条', '5筒', '5筒', '7万']
        # 清一色
        hand = {"concealed": ["3万", "4万", "5万", "5万", "6万", "6万","7万", "7万", "8万", "8万", "8万", "9万","9万"],
                "exposed": []}
        print("清一色："+str(rule.check_ting(hand, all_used_tiles)))
        # 大对子
        hand = {"concealed": ["3万", "3万", "3万", "4万", "4万", "7筒", "7筒"],
                "exposed": [{
                    "tiles": ["1万", "1万", "1万"],
                    "is_gang": False
                },{
                    "tiles": ["2万", "2万", "2万", "2万"],
                    "is_gang": True
                }]}
        print("大对子："+str(rule.check_ting(hand, all_used_tiles)))
        # 小对子
        hand = {"concealed": ["3筒", "4万", "4万", "5万", "5万", "6万","6万", "7万", "7万", "8万", "8万", "9万","9万"],
                "exposed": []}
        print("小七对："+str(rule.check_ting(hand, all_used_tiles)))
        hand = {"concealed": ["3筒", "3筒", "3筒", "3筒", "5万", "6万","6万", "7万", "7万", "8万", "8万", "9万","9万"],
                "exposed": []}
        print("小七对："+str(rule.check_ting(hand, all_used_tiles)))
        # 龙七对
        hand = {"concealed": ["3筒", "3筒", "3筒", "5万", "5万", "6万","6万", "7万", "7万", "8万", "8万", "9万","9万"],
                "exposed": []}
        print("龙七对："+str(rule.check_ting(hand, all_used_tiles)))
        # 常规听牌
        # 牌型1:叫对楚
        hand = {"concealed": ["3万", "4万", "5万", "4万", "4万", "7筒", "7筒"],
                "exposed": [{
                    "tiles": ["1万", "1万", "1万"],
                    "is_gang": False
                },{
                    "tiles": ["2万", "2万", "2万", "2万"],
                    "is_gang": False
                }]}
        print("常规听牌1叫对楚(4万)："+str(rule.check_ting(hand, all_used_tiles)))
        print("常规听牌1叫对楚(7筒)："+str(rule.check_ting(hand, all_used_tiles)))
        # 牌型2叫边张
        hand = {"concealed": ["3万", "4万", "5万", "4万", "4万", "8筒", "7筒"],
                "exposed": [{
                    "tiles": ["1万", "1万", "1万"],
                    "is_gang": False
                },{
                    "tiles": ["2万", "2万", "2万", "2万"],
                    "is_gang": False
                }]}
        print("常规听牌2叫边张(9筒)："+str(rule.check_ting(hand, all_used_tiles)))
        # 牌型3叫卡张
        hand = {"concealed": ["1万", "1万", "1万", "3万", "4万", "5万", "4万", "4万", "5筒", "7筒"],
                "exposed": [{
                    "tiles": ["2万", "2万", "2万", "2万"],
                    "is_gang": False
                }]}
        print("常规听牌3叫卡张(6筒)："+str(rule.check_ting(hand, all_used_tiles)))
        # 牌型4叫两头(47筒)
        hand = {"concealed": ["1万", "1万", "1万", "3万", "4万", "5万", "4万", "4万", "5筒", "6筒"],
                "exposed": [{
                    "tiles": ["2万", "2万", "2万", "2万"],
                    "is_gang": False
                }]}
        print("常规听牌4叫两头(47筒)："+str(rule.check_ting(hand, all_used_tiles)))
        # 牌型5叫147
        hand = {"concealed": ["1万", "1万", "2万", "3万", "4万", "5万", "6万", "4筒", "5筒", "6筒"],
                "exposed": [{
                    "tiles": ["2万", "2万", "2万", "2万"],
                    "is_gang": False
                }]}
        print("常规听牌5叫147："+str(rule.check_ting(hand, all_used_tiles)))
        # 牌型6叫258
        hand = {"concealed": ["1万", "1万", "3万", "4万", "5万", "6万", "7万", "4筒", "5筒", "6筒"],
                "exposed": [{
                    "tiles": ["2条", "2条", "2条", "2条"],
                    "is_gang": False
                }]}
        print("常规听牌6叫258："+str(rule.check_ting(hand, all_used_tiles)))
        # 牌型6叫369
        hand = {"concealed": ["1万", "1万", "4万", "5万", "6万", "7万", "8万", "4筒", "5筒", "6筒"],
                "exposed": [{
                    "tiles": ["2条", "2条", "2条", "2条"],
                    "is_gang": False
                }]}
        print("常规听牌6叫369："+str(rule.check_ting(hand, all_used_tiles)))
        print("================================听牌测试结束============================")

    def get_chicken_tiles(self) -> list:
        """获取幺鸡牌
        
        Returns:
            list: 包含所有幺鸡牌的列表
        """
        return Settings.chicken_tile

    def check_chicken_tile(self, tile: str) -> bool:
        """检查牌是否为幺鸡牌
        
        Args:
            tile (str): 待检查的牌
        
        Returns:
            bool: 如果牌为幺鸡牌则返回True，否则返回False
        """
        return tile in self.get_chicken_tiles()

if __name__ == "__main__":
    rule=Rule()
    rule.test_hu()
    # rule.test_ting()
    # rule.test_has_passport()

