from source.rule import Rule
from collections import defaultdict
from typing import Dict, List, Tuple
import copy
from source.public import Tag


class MajiangAI0:
    def __init__(self):
        """初始化AI"""
        self.rule = Rule()
        self.has_passport = self.rule.has_passport
        self.check_ting = self.rule.check_ting
        self.check_hu = self.rule.check_hu
        self.chicken_tiles = ["1条"]

    def check_hand(self, hand: List[str]) -> Tuple[int, int, Dict[str, float], Dict[str, List[str]]]:
        """
        统计麻将手牌的面子数量、搭子数量和已组成的面子/搭子
        :param hand: 手牌字符串列表，如['1万','3条','4条','5条','7条','7条','9条','5筒','7筒','9筒','9筒','9筒','3万']
        :return: 元组(面子数量, 搭子数量, 特殊牌型潜力字典, 已组成的面子/搭子字典)
        """
        # 1. 按花色（万/条/筒）分类，统计每个数字的出现次数
        suit_counts = {
            '万': defaultdict(int),
            '条': defaultdict(int),
            '筒': defaultdict(int)
        }
        for card in hand:
            # 拆分数字和花色（如'1万'→数字1，花色'万'）
            num = int(card[:-1])
            suit = card[-1]
            suit_counts[suit][num] += 1
        
        # 2. 计算面子数量（刻子 + 顺子）并记录已组成的面子
        meld_count = 0  # 面子总数
        original_suit_counts = copy.deepcopy(suit_counts)
        composed_melds = {}
        composed_tiles = set()  # 已组成面子的牌
        
        # 2.1 先统计刻子（3张相同），并更新剩余牌数
        for suit, num_counts in suit_counts.items():
            for num in list(num_counts.keys()):  # 遍历副本避免修改字典时出错
                count = num_counts[num]
                if count >= 3:
                    melds = count // 3  # 刻子数量（如6张相同则算2个刻子）
                    meld_count += melds
                    for _ in range(melds):
                        # 记录已组成的刻子
                        tile_name = f"{num}{suit}"
                        if suit not in composed_melds:
                            composed_melds[suit] = []
                        composed_melds[suit].append(("刻子", [tile_name, tile_name, tile_name]))
                        composed_tiles.update([tile_name, tile_name, tile_name])
                    num_counts[num] = count % 3  # 剩余牌数（0/1/2）

        # 2.2 统计顺子（同花色连续3张）
        for suit, num_counts in suit_counts.items():
            # 持续遍历直到无新顺子可组成
            while True:
                # 筛选当前花色有剩余牌的数字，按升序排列
                available_nums = sorted([n for n in num_counts if num_counts[n] > 0])
                found_straight = False  # 标记本轮是否找到顺子
                i = 0
                while i < len(available_nums) - 2:  # 至少需要3个数字才可能组成顺子
                    current = available_nums[i]
                    next1 = current + 1
                    next2 = current + 2
                    # 检查连续3个数字是否都有剩余牌
                    if next1 in num_counts and next2 in num_counts:
                        if num_counts[current] >= 1 and num_counts[next1] >= 1 and num_counts[next2] >= 1:
                            meld_count += 1  # 顺子数量+1
                            # 记录已组成的顺子
                            tile1 = f"{current}{suit}"
                            tile2 = f"{next1}{suit}"
                            tile3 = f"{next2}{suit}"
                            if suit not in composed_melds:
                                composed_melds[suit] = []
                            composed_melds[suit].append(("顺子", [tile1, tile2, tile3]))
                            composed_tiles.update([tile1, tile2, tile3])
                            # 扣除组成顺子的牌数
                            num_counts[current] -= 1
                            num_counts[next1] -= 1
                            num_counts[next2] -= 1
                            found_straight = True
                            break  # 重新遍历（因为牌数已变）
                    i += 1
                if not found_straight:
                    break  # 无新顺子，退出循环

        # 3. 计算搭子数量（对子 + 边张/嵌张）并记录已组成的搭子
        tile_count = 0  # 搭子总数
        composed_tatsus = {}
        
        # 3.1 先统计对子（2张相同），并更新剩余牌数
        for suit, num_counts in suit_counts.items():
            for num in list(num_counts.keys()):
                count = num_counts[num]
                if count >= 2:
                    tatsus = count // 2  # 对子数量（如4张相同则算2个对子）
                    tile_count += tatsus
                    for _ in range(tatsus):
                        # 记录已组成的对子
                        tile_name = f"{num}{suit}"
                        if suit not in composed_tatsus:
                            composed_tatsus[suit] = []
                        composed_tatsus[suit].append(("对子", [tile_name, tile_name]))
                        composed_tiles.update([tile_name, tile_name])
                    num_counts[num] = count % 2  # 剩余牌数（0/1）

        # 3.2 统计边张/嵌张搭子（同花色单张牌组成）
        for suit, num_counts in suit_counts.items():
            # 筛选当前花色剩余的单张牌（次数=1），按升序排列
            single_nums = sorted([n for n in num_counts if num_counts[n] == 1])
            i = 0
            used_nums = set()
            while i < len(single_nums) - 1:
                a = single_nums[i]
                b = single_nums[i+1]
                if a in used_nums or b in used_nums:
                    i += 1
                    continue
                    
                if b == a + 1:
                    # 连张搭子（如1&2、2&3），质量高
                    tile_count += 1.2  # 连张搭子质量更高
                    # 记录已组成的连张搭子
                    tile1 = f"{a}{suit}"
                    tile2 = f"{b}{suit}"
                    if suit not in composed_tatsus:
                        composed_tatsus[suit] = []
                    composed_tatsus[suit].append(("连张搭子", [tile1, tile2]))
                    composed_tiles.update([tile1, tile2])
                    used_nums.add(a)
                    used_nums.add(b)
                    i += 2  # 跳过已用的牌
                elif b == a + 2:
                    # 嵌张搭子（如1&3、2&4），质量一般
                    tile_count += 1.0  # 嵌张搭子质量一般
                    # 记录已组成的嵌张搭子
                    tile1 = f"{a}{suit}"
                    tile2 = f"{b}{suit}"
                    if suit not in composed_tatsus:
                        composed_tatsus[suit] = []
                    composed_tatsus[suit].append(("嵌张搭子", [tile1, tile2]))
                    composed_tiles.update([tile1, tile2])
                    used_nums.add(a)
                    used_nums.add(b)
                    i += 2  # 跳过已用的牌
                else:
                    # 间隔超过2，无法组成搭子
                    i += 1
            # 移除边张搭子的错误识别，避免将所有零散牌都标记为已组成搭子
            # 只保留真正的连张和嵌张搭子

        # 4. 评估特殊牌型潜力
        pattern_potential = {
            '七对子': 0.0,
            '碰碰胡': 0.0,
            '清一色': 0.0,
            '门清': 0.0
        }
        
        # 4.1 七对子潜力评估
        pair_count = 0
        for suit, num_counts in original_suit_counts.items():
            for num, count in num_counts.items():
                if count >= 2:
                    pair_count += 1
        if pair_count >= 4:
            pattern_potential['七对子'] = min(1.0, pair_count / 6.0)
        
        # 4.2 碰碰胡潜力评估
        # 碰碰胡需要4个刻子+1个对子
        triplet_count = 0
        for suit, num_counts in original_suit_counts.items():
            for num, count in num_counts.items():
                if count >= 2:
                    triplet_count += 1
        if triplet_count >= 4:
            pattern_potential['碰碰胡'] = min(1.0, triplet_count / 5.0)
        
        # 4.3 清一色潜力评估
        suit_distribution = {}
        for suit, num_counts in original_suit_counts.items():
            suit_cards = sum(num_counts.values())
            suit_distribution[suit] = suit_cards
        max_suit_cards = max(suit_distribution.values())
        if max_suit_cards >= 7:
            pattern_potential['清一色'] = min(1.0, max_suit_cards / 13.0)
        
        # 4.4 门清潜力评估
        # 假设没有副露就是门清，这里简化处理
        pattern_potential['门清'] = 1.0
        
        # 5. 整理已组成的面子和搭子
        composed = {
            "melds": composed_melds,
            "tatsus": composed_tatsus,
            "composed_tiles": list(composed_tiles)
        }
        
        return (meld_count, tile_count, pattern_potential, composed)

    def get_discard_precedence_list(self,
            hand: Dict[str, List[str]],
            all_discards: List[List[str]],
            all_exposed: List[List[Dict]],
            chicken_tiles: List[str]):
        """
        智能排序：综合"进攻/防守/听牌/鸡牌"策略，返回按"最该打"到"最不该打"排序的牌列表
        参数：
            hand: 自己手牌
            all_discards: 四家弃牌堆，每家一个列表，顺序为[上家, 自己, 下家, 对家]
            all_exposed: 其他三家已副露列表，顺序为[上家, 自己, 下家, 对家]
            chicken_tiles: 鸡牌列表,默认值为["1条"]
        返回：
            (排序后的牌列表, 前3张牌的推荐理由列表)：(List[str], List[str])
        """
        self.chicken_tiles = chicken_tiles
        concealed = hand["concealed"]
        exposed = [exp for sublist in hand["exposed"] for exp in sublist["tiles"][:3]]  # 扁平化副露牌列表
        meld_count, dazi_count, pattern_potential, composed = self.check_hand(concealed+exposed)
        ready0 = meld_count+dazi_count >= 3  # 准备听牌了
        ready1 = ready0 and meld_count >= 3  # 已经听牌了
        all_used = self._get_all_used_tiles(hand, all_discards, all_exposed)
        total_used = len(all_used)
        
        # 获取已组成的面子和搭子
        composed_tiles = set(composed["composed_tiles"])
        composed_melds = composed["melds"]
        composed_tatsus = composed["tatsus"]
        
        # 确定牌局阶段
        if total_used < 70:
            game_stage = "早期"
        elif total_used < 95:
            game_stage = "中期"
        else:
            game_stage = "后期"
        
        # 统计牌的数量
        tile_count = {}
        for tile in concealed:
            tile_count[tile] = tile_count.get(tile, 0) + 1
        
        # 统计花色分布
        suit_counts = {"万": 0, "条": 0, "筒": 0}
        for tile in concealed+exposed:
            for suit in suit_counts:
                if suit in tile:
                    suit_counts[suit] += 1
                    break
        max_suit = max(suit_counts, key=suit_counts.get)
        max_suit_count = suit_counts[max_suit]
        
        # 评估每张牌的危险度和价值
        discard_scores = {}
        
        # 1. 统计暴露的鸡牌情况
        # 只有自己暴露的鸡牌才需要考虑，别人的鸡牌与自己无关
        exposed_chicken_count = 0
        # 只统计自己的暴露鸡牌（hand["exposed"]是自己的副露）
        for exposed in hand["exposed"]:
            for t in exposed["tiles"]:
                if t in self.chicken_tiles:
                    exposed_chicken_count += 1
        
        for tile in set(concealed):
            reason = ""
            tile_num = int(tile[:-1])
            tile_suit = tile[-1]
            current_tile_count = tile_count[tile]
            
            # 检查该牌是否属于已组成的面子/搭子
            is_in_composed = tile in composed_tiles
            
            # 检查是否有做大牌的特殊情况
            is_big_pattern = False
            if pattern_potential['七对子'] > 0.8 or pattern_potential['碰碰胡'] > 0.8 or pattern_potential['清一色'] > 0.8:
                is_big_pattern = True
            
            # 2. 检查打出该牌后是否可以听牌
            can_ting = False
            ting_info = []
            ting_bonus = 0
            ting_reason = ""
            
            # 检查当前总手牌数量
            current_exposed = [tile for group in hand["exposed"] for i,tile in enumerate(group["tiles"]) if i<3]
            current_total = len(concealed + current_exposed)
            
            # 根据麻将规则，当手牌数量为14张时，需要打出一张，此时可以听牌
            if current_total == 14:
                # 模拟打出该牌后的手牌
                temp_concealed = [t for t in concealed if t != tile]
                temp_hand = {
                    "concealed": temp_concealed,
                    "exposed": hand["exposed"]
                }
                
                # 计算打出牌后的总手牌数量
                temp_exposed = [tile for group in temp_hand["exposed"] for i,tile in enumerate(group["tiles"]) if i<3]
                temp_total = len(temp_concealed + temp_exposed)
                
                # 只有当打出牌后手牌数量为13张时，才检查是否听牌
                if temp_total == 13:
                    # 调用check_ting函数检查是否听牌
                    is_ting, ting_tiles = self.check_ting(temp_hand, all_used)
                    if is_ting:
                        can_ting = True
                        ting_info = ting_tiles
                        
                        # 评估听牌质量
                        ting_quality = self._evaluate_ting_quality(ting_tiles)
                        
                        # 计算听牌加成，越后期加成越高
                        if game_stage == "早期":
                            # 早期听牌加成较低，且如果听牌质量不高，可以考虑换听
                            if ting_quality < 50:  # 听牌质量不高（边张/卡张）
                                ting_bonus = -100  # 降低听牌加成
                                ting_reason = "打出后可以听牌，但听牌质量不高，考虑是否换听"
                            else:
                                ting_bonus = -200  # 早期听牌加成
                                ting_reason = "打出后可以听牌，早期优先"
                        elif game_stage == "中期":
                            ting_bonus = -300  # 中期听牌加成中等
                            ting_reason = "打出后可以听牌，中期优先"
                        else:  # 后期
                            ting_bonus = -500  # 后期听牌加成很高
                            ting_reason = "打出后可以听牌，后期优先"
                        
                        # 只有自己暴露的鸡牌才影响听牌优先级
                        if exposed_chicken_count > 0:
                            ting_bonus += exposed_chicken_count * (-50)
                            ting_reason += f"，暴露{exposed_chicken_count}张鸡牌，优先听牌"
            
            # 3. 基本牌型价值评估（决定牌的基本优先级）
            # 注意：我们将牌分为几个优先级级别，级别越高，越不应该被打出
            priority_level = 0
            basic_reason = ""
            
            # 3.1 刻子或暗杠：优先级最高，绝对不拆
            if current_tile_count >= 3:
                priority_level = 5
                basic_reason = "刻子/暗杠价值极高，绝对不拆"
            # 3.2 唯一将牌：优先级很高，绝对不拆
            elif current_tile_count == 2 and sum(1 for t in tile_count if tile_count[t] >= 2) == 1:
                priority_level = 4
                basic_reason = "唯一的对子作为将牌，绝对不拆"
            # 3.3 普通对子：优先级高，尽量不拆
            elif current_tile_count == 2:
                priority_level = 3
                basic_reason = "对子价值高，尽量不拆"
            # 3.4 已组成的面子/搭子：优先级很高，非必须情况不拆
            elif is_in_composed:
                # 已组成的面子/搭子，非必须情况不拆
                priority_level = 6  # 提高优先级，确保只有在特殊情况下才会拆
                basic_reason = "已组成面子/搭子，非必须情况不拆"
            # 3.5 强搭子（连张搭子）：优先级中高，尽量保留
            elif current_tile_count == 1:
                # 检查是否是强搭子的一部分
                prev1 = self._get_tile_by_number(tile, tile_num - 1)
                next1 = self._get_tile_by_number(tile, tile_num + 1)
                has_prev1 = prev1 in concealed
                has_next1 = next1 in concealed
                
                prev2 = self._get_tile_by_number(tile, tile_num - 2)
                next2 = self._get_tile_by_number(tile, tile_num + 2)
                has_prev2 = prev2 in concealed
                has_next2 = next2 in concealed
                
                if has_prev1 or has_next1:
                    # 连张搭子，优先级中高
                    priority_level = 2
                    basic_reason = "连张搭子，质量高，尽量保留"
                elif has_prev2 or has_next2:
                    # 嵌张搭子，优先级中等
                    priority_level = 1
                    basic_reason = "嵌张搭子，质量一般"
                else:
                    # 孤张牌，优先级低，优先打出
                    priority_level = 0
                    basic_reason = "孤张牌，价值低，优先打出"
            
            # 4. 鸡牌特殊处理
            if tile in self.chicken_tiles:
                # 检查是否是冲锋鸡或横鸡
                is_first_discard = self._is_first_chicken_discard(tile, all_discards)
                is_first_global = self._is_first_global_chicken_discard(tile, all_discards)
                
                # 在手牌情况较好时再考虑打出鸡牌
                # 改进：更严格的手牌质量评估
                is_good_hand = meld_count >= 2 and dazi_count >= 2  # 增加搭子数量要求
                
                if is_first_discard and ready0 and len(all_used) < 90:
                    # 避免打冲锋鸡，提高优先级
                    priority_level -= 3  # 增加优先级提升幅度
                    basic_reason = "牌型较好，冲锋鸡收益高，可以打出"
                elif is_first_global and ready1 and len(all_used) < 90:
                    # 避免打横鸡，提高优先级
                    priority_level -= 2  # 增加优先级提升幅度
                    basic_reason = "牌型较好，横鸡收益较高，可以打出"
                elif not is_good_hand:
                    # 手牌情况不好，先留着鸡牌，提高优先级
                    # 手牌不好时，鸡牌优先级极高，确保不被轻易打出
                    priority_level += 4  # 进一步提高鸡牌优先级，从+3改为+4
                    basic_reason = "手牌情况不好，建议保留鸡牌"
                else:
                    # 手牌情况好，可以考虑打鸡牌，降低优先级
                    priority_level -= 1
                    basic_reason = "手牌情况较好，可以打出鸡牌"
            
            # 5. 特殊牌型策略调整
            # 5.1 清一色潜力
            if max_suit_count >= 9:
                if tile_suit == max_suit:
                    # 主花色牌，提高优先级
                    priority_level += 1
                else:
                    # 非主花色牌，降低优先级
                    priority_level -= 1
                    basic_reason = f"有{max_suit}清一色潜力，优先打出其他花色牌"
            
            # 5.2 七对子潜力
            if pattern_potential['七对子'] > 0.7:
                if current_tile_count == 1:
                    # 七对子情况下，单张牌优先级降低
                    priority_level -= 1
                    basic_reason = "七对子潜力大，优先打出单张牌"
            
            # 5.3 碰碰胡潜力
            if pattern_potential['碰碰胡'] > 0.7:
                if current_tile_count == 1:
                    # 碰碰胡情况下，单张牌优先级降低
                    priority_level -= 1
                    basic_reason = "碰碰胡潜力大，优先打出单张牌"
            
            # 6. 牌局阶段调整
            if game_stage == "早期":
                # 早期优先打孤张和幺九牌，但不拆已组成的面子/搭子
                if priority_level == 0 and (tile_num == 1 or tile_num == 9):
                    priority_level -= 1
                    basic_reason = "早期牌局，优先打出幺九孤张"
                elif priority_level == 0:
                    basic_reason = "早期牌局，优先打出孤张牌"
            elif game_stage == "后期":
                # 后期优先考虑防守，但不拆已组成的面子/搭子
                danger_score = self._calculate_danger_score(tile, all_discards, all_exposed, all_used, concealed)
                if danger_score < 10:
                    # 安全牌，降低优先级
                    priority_level -= 1
                    basic_reason += "，后期优先打安全牌"
            
            # 7. 特殊情况处理：只有在听牌或有极强大牌潜力时才可以拆打已组成的面子/搭子
            if is_in_composed:
                # 已组成的面子/搭子，非必须情况不拆
                if can_ting:
                    # 听牌优先级最高，可以拆搭子
                    pass  # 听牌加成已经在后面处理
                elif is_big_pattern and max(pattern_potential.values()) > 0.9:
                    # 极强的大牌潜力（超过0.9），可以考虑拆搭子
                    priority_level = 2
                    basic_reason = f"极强{max(pattern_potential, key=pattern_potential.get)}潜力，考虑拆面子/搭子"
                else:
                    # 非必须情况，不拆已组成的面子/搭子
                    priority_level = 6
                    basic_reason = "已组成面子/搭子，非必须情况不拆"
            
            # 8. 计算最终得分（将优先级转换为分数）
            # 优先级越高，分数越高，越不应该被打出
            # 分数越低，越优先被打出
            final_score = priority_level * 100
            
            # 9. 点炮风险微调（仅在同一优先级内调整）
            if priority_level <= 2:  # 仅对低优先级牌进行点炮风险调整
                danger_score = self._calculate_danger_score(tile, all_discards, all_exposed, all_used, concealed)
                if game_stage == "早期":
                    final_score -= danger_score * 0.2
                elif game_stage == "中期":
                    final_score -= danger_score * 0.5
                else:
                    final_score -= danger_score * 1.0
            
            # 10. 添加听牌加成（直接降低分数，使牌更优先被打出）
            # 听牌优先级最高，无论是否是已组成的面子/搭子
            if can_ting:
                final_score += ting_bonus
                basic_reason = ting_reason
                # 听牌时，直接将优先级设为最低，确保优先打出
                final_score = min(final_score, -1000)
            
            # 11. 确保理由清晰明确
            if reason.endswith("，"):
                reason = reason[:-1]
            if reason == "":
                reason = basic_reason
            
            discard_scores[tile] = (final_score, reason)
        
        # 调试：打印每张牌的得分
        # for tile, (score, reason) in discard_scores.items():
        #     print(f"牌 {tile}: 得分 {score}, 理由 {reason}")
        
        # 按分数排序（分数越低越优先打）
        # 注意：分数越高表示这张牌越不应该被打出
        sorted_discards = sorted(discard_scores.items(), key=lambda x: x[1][0])
        
        # 生成排序后的牌列表
        result = []
        for tile, (score, reason) in sorted_discards:
            result.extend([tile] * tile_count[tile])
        
        # 获取前3张牌的推荐理由
        top_reasons = []
        for i in range(min(3, len(sorted_discards))):
            tile, (score, reason) = sorted_discards[i]
            top_reasons.append(reason)
        
        return result, top_reasons

    def decide_peng(self,
            hand,
            all_discards: List[List[str]],
            all_exposed: List[List[Dict]],
            chicken_tiles: List[str],
            tile: str):
        """
        智能决策是否碰牌
        参数：
            hand: 自己手牌
            all_discards: 四家弃牌堆，每家一个列表，顺序为[上家, 自己, 下家, 对家]
            all_exposed: 其他三家已副露列表，顺序为[上家, 自己, 下家, 对家]
            chicken_tiles: 鸡牌列表,默认值为["1条"]
            tile: 要判断的牌，是否碰这张牌
        返回：
            (是否碰牌, 推荐理由)：(True/False, "推荐理由")
        """
        self.chicken_tiles = chicken_tiles
        all_used_tiles = self._get_all_used_tiles(hand, all_discards, all_exposed)
        concealed = hand["concealed"][:]
        
        # 检查是否是鸡牌
        if tile in self.chicken_tiles:
            # 检查是否是别人打的冲锋鸡或横鸡
            is_first_discard = self._is_first_chicken_discard(tile, all_discards)
            if is_first_discard:
                return False, "鸡牌-别人冲锋鸡，碰后包牌风险极高"
            
            is_first_global = self._is_first_global_chicken_discard(tile, all_discards)
            if is_first_global:
                return False, "鸡牌-别人横鸡，碰后包牌风险高"
        
        # 检查手牌中是否有两张相同牌
        count = concealed.count(tile)
        if count >= 2:
            # 有两张，可以碰
            # 检查碰牌后对听牌的影响
            new_concealed = [t for t in concealed if t != tile][:2]  # 移除两张
            new_hand = {"concealed": new_concealed, "exposed": hand["exposed"] + [{"tiles": [tile, tile, tile], "is_gang": False}]}
            
            is_ting, _ = self.check_ting(new_hand, all_used_tiles)
            if is_ting:
                return True, "碰牌后可以听牌"
            
            # 检查碰牌对整体牌型的影响
            _, _, new_pattern_potential = self.check_hand(new_concealed)
            pattern_score = self._evaluate_pattern_score(new_concealed, new_pattern_potential)
            if pattern_score > 0:
                return True, "碰牌有利于形成好牌型"
        
        return False, "碰牌对当前牌型帮助不大"

    def decide_gang(self,
            hand,
            all_discards: List[List[str]],
            all_exposed: List[List[Dict]],
            chicken_tiles: List[str],
            tile: str):
        """
        智能决策是否杠牌
        参数：
            hand: 自己手牌
            all_discards: 四家弃牌堆，每家一个列表，顺序为[上家, 自己, 下家, 对家]
            all_exposed: 其他三家已副露列表，顺序为[上家, 自己, 下家, 对家]
            chicken_tiles: 鸡牌列表,默认值为["1条"]
            tile: 要判断的牌，是否杠这张牌
        返回：
            (是否杠牌, 推荐理由)：(True/False, "推荐理由")
        """
        self.chicken_tiles = chicken_tiles
        all_used_tiles = self._get_all_used_tiles(hand, all_discards, all_exposed)
        concealed = hand["concealed"][:]
        
        # 检查是否是鸡牌
        if tile in self.chicken_tiles:
            # 检查是否是别人打的冲锋鸡或横鸡
            is_first_discard = self._is_first_chicken_discard(tile, all_discards)
            if is_first_discard:
                return False, "鸡牌-别人冲锋鸡，杠后包牌风险极高"
            
            is_first_global = self._is_first_global_chicken_discard(tile, all_discards)
            if is_first_global:
                return False, "鸡牌-别人横鸡，杠后包牌风险高"
        
        # 检查手牌中是否有三张相同牌（暗杠）或已碰牌（明杠）
        count = concealed.count(tile)
        
        # 检查是否已碰过此牌（明杠）
        for exposed in hand["exposed"]:
            if exposed["tiles"] == [tile, tile, tile] and not exposed["is_gang"]:
                # 可以明杠
                new_hand = copy.deepcopy(hand)
                for i, exp in enumerate(new_hand["exposed"]):
                    if exp["tiles"] == [tile, tile, tile] and not exp["is_gang"]:
                        new_hand["exposed"][i]["is_gang"] = True
                        new_hand["exposed"][i]["tiles"] = [tile, tile, tile, tile]
                        break
                
                is_ting, _ = self.check_ting(new_hand, all_used_tiles)
                if is_ting:
                    return True, "明杠后可以听牌"
                
                # 检查是否已有通行证
                has_pass, _, _ = self.has_passport(new_hand)
                if has_pass:
                    return True, "明杠获得通行证"
        
        # 检查暗杠
        if count >= 4:
            # 有四张，可以暗杠
            new_concealed = [t for t in concealed if t != tile]
            new_hand = {"concealed": new_concealed, "exposed": hand["exposed"] + [{"tiles": [tile, tile, tile, tile], "is_gang": True}]}
            
            is_ting, _ = self.check_ting(new_hand, all_used_tiles)
            if is_ting:
                return True, "暗杠后可以听牌"
            
            # 检查是否已有通行证
            has_pass, _, _ = self.has_passport(new_hand)
            if has_pass:
                return True, "暗杠获得通行证"
        
        return False, "杠牌对当前牌型帮助不大"

    def decide_hu(self,
            hand,
            all_discards: List[List[str]],
            all_exposed: List[List[Dict]],
            chicken_tiles: List[str],
            tile: str):
        """
        智能决策是否胡牌
        参数：
            hand: 自己手牌
            all_discards: 四家弃牌堆，每家一个列表，顺序为[上家, 自己, 下家, 对家]
            all_exposed: 其他三家已副露列表，顺序为[上家, 自己, 下家, 对家]
            chicken_tiles: 鸡牌列表,默认值为["1条"]
            tile: 要判断的牌，是否胡这张牌
        返回：
            (是否胡牌, 推荐理由)：(True/False, "推荐理由")
        """
        
        return True, f"simpleAI 推荐胡牌"

    def _get_all_used_tiles(self, hand, all_discards, all_exposed):
        """获取所有已使用的牌"""
        all_tiles = []
        all_tiles.extend(hand["concealed"])
        for exposed in hand["exposed"]:
            all_tiles.extend(exposed["tiles"])
        
        for discards in all_discards:
            all_tiles.extend(discards)
        
        for exposed_list in all_exposed:
            for exposed in exposed_list:
                all_tiles.extend(exposed["tiles"])
        
        return all_tiles

    def _is_first_chicken_discard(self, tile, all_discards):
        """检查是否是自己的第一张鸡牌（冲锋鸡）"""
        for discard_list in all_discards:
            for disc_tile in discard_list:
                if disc_tile in self.chicken_tiles and disc_tile == tile:
                    return True  # 是第一张鸡牌
        return False

    def _is_first_global_chicken_discard(self, tile, all_discards):
        """检查是否是全场第一张鸡牌（横鸡）"""
        first_chicken = None
        for discard_list in all_discards:
            for disc_tile in discard_list:
                if disc_tile in self.chicken_tiles:
                    if first_chicken is None:
                        first_chicken = disc_tile
                    elif disc_tile == tile:
                        return True  # 是横鸡
        return False

    def _evaluate_single_tile(self, tile, concealed):
        """评估单张牌的价值"""
        # 检查是否能与相邻牌形成顺子或搭子
        score = 0
        tile_num = self._get_tile_number(tile)
        tile_suit = tile[-1]
        
        if tile_num:
            # 检查前后牌是否存在
            prev1 = self._get_tile_by_number(tile, tile_num - 1)
            prev2 = self._get_tile_by_number(tile, tile_num - 2)
            next1 = self._get_tile_by_number(tile, tile_num + 1)
            next2 = self._get_tile_by_number(tile, tile_num + 2)
            
            # 统计相邻牌的数量
            adjacent_count = 0
            for check_tile in concealed:
                if check_tile != tile and check_tile[-1] == tile_suit:
                    check_num = self._get_tile_number(check_tile)
                    if abs(check_num - tile_num) <= 2:
                        adjacent_count += 1
            
            if adjacent_count >= 2:
                # 有多个相邻牌，价值高
                score += 40  # 这是顺子的中间张或有多个搭子可能
                reason = "有多个相邻牌，价值高"
            elif prev1 in concealed and next1 in concealed:
                score += 30  # 这是顺子的中间张
                reason = "顺子中间张，价值高"
            elif prev1 in concealed or next1 in concealed:
                score += 25  # 可以形成连张搭子，质量高
                reason = "连张搭子，质量高"
            elif prev2 in concealed or next2 in concealed:
                score += 15  # 可以形成嵌张搭子，质量一般
                reason = "嵌张搭子，质量一般"
            else:
                score -= 30  # 孤张牌，价值低
                reason = "孤张牌，价值低"

        return score

    def _evaluate_pair_tile(self, tile, concealed, game_stage, ready0):
        """评估两张相同牌的价值"""
        # 两张相同牌，可能形成刻子或对子
        score = 25  # 形成对子的基础分，价值较高
        
        # 检查是否有第三张
        tile_count_in_hand = concealed.count(tile)
        if tile_count_in_hand >= 3:
            score += 30  # 可以碰成刻子或暗杠，价值极高
        
        # 根据牌局阶段调整对子价值
        if game_stage == "早期":
            # 早期对子价值较高，可以考虑碰牌或形成刻子
            score += 10
        elif game_stage == "中期":
            # 中期对子价值取决于是否能形成刻子或作为将牌
            score += 5
        else:  # 后期
            # 后期对子如果能作为将牌，价值极高
            if ready0:
                score += 20  # 接近听牌，将牌价值极高
        
        return score

    def _calculate_danger_score(self, tile, all_discards, all_exposed, all_used, current_hand):
        """计算点炮风险"""
        danger_score = 0
        total_used = len(all_used)
        
        # 1. 检查牌是否被打出过
        tile_seen = False
        tile_recently_seen = False
        for i, discards in enumerate(all_discards):
            if i == 1:  # 跳过自己的弃牌堆
                continue
            if tile in discards:
                tile_seen = True
                # 检查是否最近被打出
                if tile in discards[-3:]:
                    tile_recently_seen = True
                break
        
        if tile_recently_seen:
            danger_score -= 20  # 最近被打出过，较安全
        elif tile_seen:
            danger_score += 5  # 被打出过但不是最近，风险一般
        else:
            # 从未被打出过，根据牌局阶段调整风险
            if total_used < 20:  # 牌局初期
                danger_score += 10  # 初期风险较低
            elif total_used < 50:  # 牌局中期
                danger_score += 20  # 中期风险中等
            else:  # 牌局后期
                danger_score += 40  # 后期风险较高
        
        # 2. 检查其他玩家的副露情况
        has_exposed = any(len(exposed_list) > 0 for exposed_list in all_exposed)
        if has_exposed:
            for exposed_list in all_exposed:
                if not exposed_list:  # 跳过自己的副露
                    continue
                # 检查是否有相同花色的副露
                tile_suit = tile[-1]
                suit_exposed = False
                for exposed in exposed_list:
                    if exposed["tiles"][0][-1] == tile_suit:
                        suit_exposed = True
                        break
                if suit_exposed:
                    # 检查是否可能形成顺子或刻子
                    tile_num = int(tile[:-1])
                    for exposed in exposed_list:
                        if exposed["tiles"][0][-1] == tile_suit:
                            # 检查刻子
                            if len(exposed["tiles"]) == 3 and exposed["tiles"][0] == exposed["tiles"][1] == exposed["tiles"][2]:
                                if exposed["tiles"][0] == tile:
                                    danger_score += 60  # 别人已经有碰牌，再打就点杠
                            # 检查顺子
                            else:
                                # 提取副露中的数字
                                exposed_nums = []
                                for t in exposed["tiles"]:
                                    if t[-1] == tile_suit:
                                        exposed_nums.append(int(t[:-1]))
                                # 检查是否需要当前牌组成顺子
                                if len(exposed_nums) == 2:
                                    min_num = min(exposed_nums)
                                    max_num = max(exposed_nums)
                                    if max_num - min_num == 1:
                                        # 连张副露，如12万，需要3万或0万（不可能）
                                        if tile_num == min_num - 1 or tile_num == max_num + 1:
                                            danger_score += 50  # 可能点炮
                                    elif max_num - min_num == 2:
                                        # 嵌张副露，如13万，需要2万
                                        if tile_num == min_num + 1:
                                            danger_score += 60  # 很可能点炮
        
        # 3. 考虑牌局进程
        if total_used > 90:  # 牌局末期
            danger_score *= 2.0  # 末期风险放大
        elif total_used < 20:  # 牌局初期
            danger_score *= 0.3  # 初期风险大幅降低
        elif total_used < 50:  # 牌局中期
            danger_score *= 0.8  # 中期风险降低
        
        # 4. 考虑牌的类型（如字牌、幺九牌等）
        tile_num = int(tile[:-1])
        if tile_num == 1 or tile_num == 9:  # 幺九牌
            danger_score *= 0.7  # 幺九牌风险稍低
        
        # 5. 考虑手牌中该牌的数量
        current_count = current_hand.count(tile)
        if current_count >= 3:
            danger_score *= 0.5  # 手里有刻子，打出单张风险较低
        elif current_count == 2:
            danger_score *= 1.3  # 手里有对子，打出单张风险更高
        
        return danger_score

    def _evaluate_pattern_score(self, concealed, pattern_potential):
        """评估手牌形成好牌型的潜力"""
        score = 0
        
        # 1. 评估特殊牌型潜力
        for pattern, potential in pattern_potential.items():
            if potential > 0:
                if pattern == '七对子':
                    score += potential * 40  # 七对子得分高
                elif pattern == '碰碰胡':
                    score += potential * 30  # 碰碰胡得分较高
                elif pattern == '清一色':
                    score += potential * 50  # 清一色得分最高
                elif pattern == '门清':
                    score += potential * 20  # 门清得分一般
        
        # 2. 统计牌型分布
        tiles_by_type = {"万": [], "条": [], "筒": []}
        for tile in concealed:
            for tile_type in tiles_by_type:
                if tile_type in tile:
                    tiles_by_type[tile_type].append(tile)
                    break
        
        # 3. 检查是否可能混一色
        max_suit_count = max([len(tiles) for tiles in tiles_by_type.values()])
        if max_suit_count >= 9:
            score += 15  # 有混一色潜力
        
        # 4. 检查对子和刻子潜力
        tile_counts = {}
        for tile in concealed:
            tile_counts[tile] = tile_counts.get(tile, 0) + 1
        
        pair_count = 0
        triplet_count = 0
        quad_count = 0
        for tile, count in tile_counts.items():
            if count == 2:
                pair_count += 1
                score += 10
            elif count == 3:
                triplet_count += 1
                score += 30
            elif count >= 4:
                quad_count += 1
                score += 60
        
        # 5. 检查搭子质量
        # 统计连张搭子和嵌张搭子
        suit_dicts = {}
        for suit, tiles in tiles_by_type.items():
            suit_dict = defaultdict(int)
            for tile in tiles:
                num = int(tile[:-1])
                suit_dict[num] += 1
            suit_dicts[suit] = suit_dict
        
        for suit, num_dict in suit_dicts.items():
            nums = sorted(num_dict.keys())
            consecutive_pairs = 0
            gap_pairs = 0
            
            for i in range(len(nums) - 1):
                if nums[i+1] == nums[i] + 1:
                    consecutive_pairs += 1
                elif nums[i+1] == nums[i] + 2:
                    gap_pairs += 1
            
            # 连张搭子质量更高
            score += consecutive_pairs * 12
            score += gap_pairs * 8
        
        # 6. 检查单张牌数量
        single_count = 0
        for count in tile_counts.values():
            if count == 1:
                single_count += 1
        
        # 单张牌越少，牌型越好
        if single_count <= 2:
            score += 20
        elif single_count <= 4:
            score += 10
        elif single_count >= 6:
            score -= 10
        
        return score

    def _evaluate_ting_quality(self, ting_tiles):
        """
        评估听牌质量
        :param ting_tiles: 听牌列表，每个元素为(胡牌类型, 听的牌, 剩余数量)
        :return: 听牌质量评分，范围0-100，越高越好
        """
        if not ting_tiles:
            return 0
        
        # 评估每个听牌的质量
        quality_score = 0
        for ting_info in ting_tiles:
            # 提取听的牌（元组的第二个元素）
            tile = ting_info[1]
            tile_num = int(tile[:-1])
            
            # 边张和卡张质量较低
            if tile_num == 1 or tile_num == 9:
                # 边张，质量低
                quality_score += 30
            elif tile_num == 2 or tile_num == 8:
                # 接近边张，质量较低
                quality_score += 50
            elif tile_num == 3 or tile_num == 7:
                # 中间张，质量中等
                quality_score += 70
            else:
                # 中心张，质量高
                quality_score += 90
        
        # 计算平均质量
        return quality_score / len(ting_tiles)

    def _is_strong_hand(self, hand):
        """检查自己是否是强牌"""
        # 检查是否有杠牌
        for exposed in hand["exposed"]:
            if exposed["is_gang"]:
                return True
        
        # 检查鸡牌数量
        chicken_count = sum(1 for tile in hand["concealed"] if tile in self.chicken_tiles)
        if chicken_count >= 2:
            return True
        
        return False

    def _get_tile_number(self, tile):
        """获取牌的数字"""
        if tile[0].isdigit():
            return int(tile[0])
        return 0

    def _get_tile_by_number(self, base_tile, num):
        """根据数字和类型获取牌"""
        if 1 <= num <= 9:
            tile_type = ""
            for t in ["万", "条", "筒"]:
                if t in base_tile:
                    tile_type = t
                    break
            if tile_type:
                return f"{num}{tile_type}"
        return ""

class MajiangAI1:
    def __init__(self):
        """初始化AI"""
        self.rule = Rule()
        self.has_passport = self.rule.has_passport
        self.check_ting = self.rule.check_ting
        self.check_hu = self.rule.check_hu
        self.chicken_tiles = ["1条"]

    def check_hand(self, hand: List[str]) -> Tuple[int, int, Dict[str, float], Dict[str, List[str]]]:
        """
        统计麻将手牌的面子数量、搭子数量和已组成的面子/搭子
        :param hand: 手牌字符串列表，如['1万','3条','4条','5条','7条','7条','9条','5筒','7筒','9筒','9筒','9筒','3万']
        :return: 元组(面子数量, 搭子数量, 特殊牌型潜力字典, 已组成的面子/搭子字典)
        """
        # 1. 按花色（万/条/筒）分类，统计每个数字的出现次数
        suit_counts = {
            '万': defaultdict(int),
            '条': defaultdict(int),
            '筒': defaultdict(int)
        }
        for card in hand:
            # 拆分数字和花色（如'1万'→数字1，花色'万'）
            num = int(card[:-1])
            suit = card[-1]
            suit_counts[suit][num] += 1
        
        # 2. 计算面子数量（刻子 + 顺子）并记录已组成的面子
        meld_count = 0  # 面子总数
        original_suit_counts = copy.deepcopy(suit_counts)
        composed_melds = {}
        composed_tiles = set()  # 已组成面子的牌
        
        # 2.1 先统计刻子（3张相同），并更新剩余牌数
        for suit, num_counts in suit_counts.items():
            for num in list(num_counts.keys()):  # 遍历副本避免修改字典时出错
                count = num_counts[num]
                if count >= 3:
                    melds = count // 3  # 刻子数量（如6张相同则算2个刻子）
                    meld_count += melds
                    for _ in range(melds):
                        # 记录已组成的刻子
                        tile_name = f"{num}{suit}"
                        if suit not in composed_melds:
                            composed_melds[suit] = []
                        composed_melds[suit].append(("刻子", [tile_name, tile_name, tile_name]))
                        composed_tiles.update([tile_name, tile_name, tile_name])
                    num_counts[num] = count % 3  # 剩余牌数（0/1/2）

        # 2.2 统计顺子（同花色连续3张）
        for suit, num_counts in suit_counts.items():
            # 持续遍历直到无新顺子可组成
            while True:
                # 筛选当前花色有剩余牌的数字，按升序排列
                available_nums = sorted([n for n in num_counts if num_counts[n] > 0])
                found_straight = False  # 标记本轮是否找到顺子
                i = 0
                while i < len(available_nums) - 2:  # 至少需要3个数字才可能组成顺子
                    current = available_nums[i]
                    next1 = current + 1
                    next2 = current + 2
                    # 检查连续3个数字是否都有剩余牌
                    if next1 in num_counts and next2 in num_counts:
                        if num_counts[current] >= 1 and num_counts[next1] >= 1 and num_counts[next2] >= 1:
                            meld_count += 1  # 顺子数量+1
                            # 记录已组成的顺子
                            tile1 = f"{current}{suit}"
                            tile2 = f"{next1}{suit}"
                            tile3 = f"{next2}{suit}"
                            if suit not in composed_melds:
                                composed_melds[suit] = []
                            composed_melds[suit].append(("顺子", [tile1, tile2, tile3]))
                            composed_tiles.update([tile1, tile2, tile3])
                            # 扣除组成顺子的牌数
                            num_counts[current] -= 1
                            num_counts[next1] -= 1
                            num_counts[next2] -= 1
                            found_straight = True
                            break  # 重新遍历（因为牌数已变）
                    i += 1
                if not found_straight:
                    break  # 无新顺子，退出循环

        # 3. 计算搭子数量（对子 + 边张/嵌张）并记录已组成的搭子
        tile_count = 0  # 搭子总数
        composed_tatsus = {}
        
        # 3.1 先统计对子（2张相同），并更新剩余牌数
        for suit, num_counts in suit_counts.items():
            for num in list(num_counts.keys()):
                count = num_counts[num]
                if count >= 2:
                    tatsus = count // 2  # 对子数量（如4张相同则算2个对子）
                    tile_count += tatsus
                    for _ in range(tatsus):
                        # 记录已组成的对子
                        tile_name = f"{num}{suit}"
                        if suit not in composed_tatsus:
                            composed_tatsus[suit] = []
                        composed_tatsus[suit].append(("对子", [tile_name, tile_name]))
                        composed_tiles.update([tile_name, tile_name])
                    num_counts[num] = count % 2  # 剩余牌数（0/1）

        # 3.2 统计边张/嵌张搭子（同花色单张牌组成）
        for suit, num_counts in suit_counts.items():
            # 筛选当前花色剩余的单张牌（次数=1），按升序排列
            single_nums = sorted([n for n in num_counts if num_counts[n] == 1])
            i = 0
            used_nums = set()
            while i < len(single_nums) - 1:
                a = single_nums[i]
                b = single_nums[i+1]
                if a in used_nums or b in used_nums:
                    i += 1
                    continue
                    
                if b == a + 1:
                    # 连张搭子（如1&2、2&3），质量高
                    tile_count += 1.2  # 连张搭子质量更高
                    # 记录已组成的连张搭子
                    tile1 = f"{a}{suit}"
                    tile2 = f"{b}{suit}"
                    if suit not in composed_tatsus:
                        composed_tatsus[suit] = []
                    composed_tatsus[suit].append(("连张搭子", [tile1, tile2]))
                    composed_tiles.update([tile1, tile2])
                    used_nums.add(a)
                    used_nums.add(b)
                    i += 2  # 跳过已用的牌
                elif b == a + 2:
                    # 嵌张搭子（如1&3、2&4），质量一般
                    tile_count += 1.0  # 嵌张搭子质量一般
                    # 记录已组成的嵌张搭子
                    tile1 = f"{a}{suit}"
                    tile2 = f"{b}{suit}"
                    if suit not in composed_tatsus:
                        composed_tatsus[suit] = []
                    composed_tatsus[suit].append(("嵌张搭子", [tile1, tile2]))
                    composed_tiles.update([tile1, tile2])
                    used_nums.add(a)
                    used_nums.add(b)
                    i += 2  # 跳过已用的牌
                else:
                    # 间隔超过2，无法组成搭子
                    i += 1
            # 移除边张搭子的错误识别，避免将所有零散牌都标记为已组成搭子
            # 只保留真正的连张和嵌张搭子

        # 4. 评估特殊牌型潜力
        pattern_potential = {
            '七对子': 0.0,
            '碰碰胡': 0.0,
            '清一色': 0.0,
            '门清': 0.0
        }
        
        # 4.1 七对子潜力评估
        pair_count = 0
        for suit, num_counts in original_suit_counts.items():
            for num, count in num_counts.items():
                if count >= 2:
                    pair_count += 1
        if pair_count >= 4:
            pattern_potential['七对子'] = min(1.0, pair_count / 6.0)
        
        # 4.2 碰碰胡潜力评估
        # 碰碰胡需要4个刻子+1个对子
        triplet_count = 0
        for suit, num_counts in original_suit_counts.items():
            for num, count in num_counts.items():
                if count >= 2:
                    triplet_count += 1
        if triplet_count >= 4:
            pattern_potential['碰碰胡'] = min(1.0, triplet_count / 5.0)
        
        # 4.3 清一色潜力评估
        suit_distribution = {}
        for suit, num_counts in original_suit_counts.items():
            suit_cards = sum(num_counts.values())
            suit_distribution[suit] = suit_cards
        max_suit_cards = max(suit_distribution.values())
        if max_suit_cards >= 7:
            pattern_potential['清一色'] = min(1.0, max_suit_cards / 13.0)
        
        # 4.4 门清潜力评估
        # 假设没有副露就是门清，这里简化处理
        pattern_potential['门清'] = 1.0
        
        # 5. 整理已组成的面子和搭子
        composed = {
            "melds": composed_melds,
            "tatsus": composed_tatsus,
            "composed_tiles": list(composed_tiles)
        }
        
        return (meld_count, tile_count, pattern_potential, composed)

    def get_discard_precedence_list(self,
            hand: Dict[str, List[str]],
            all_discards: List[List[str]],
            all_exposed: List[List[Dict]],
            chicken_tiles: List[str]):
        """
        智能排序：综合"进攻/防守/听牌/鸡牌"策略，返回按"最该打"到"最不该打"排序的牌列表
        参数：
            hand: 自己手牌
            all_discards: 四家弃牌堆，每家一个列表，顺序为[上家, 自己, 下家, 对家]
            all_exposed: 其他三家已副露列表，顺序为[上家, 自己, 下家, 对家]
            chicken_tiles: 鸡牌列表,默认值为["1条"]
        返回：
            (排序后的牌列表, 前3张牌的推荐理由列表)：(List[str], List[str])
        """
        self.chicken_tiles = chicken_tiles
        concealed = hand["concealed"]
        exposed = [exp for sublist in hand["exposed"] for exp in sublist["tiles"][:3]]  # 扁平化副露牌列表
        meld_count, dazi_count, pattern_potential, composed = self.check_hand(concealed+exposed)
        ready0 = meld_count+dazi_count >= 3  # 准备听牌了
        ready1 = ready0 and meld_count >= 3  # 已经听牌了
        all_used = self._get_all_used_tiles(hand, all_discards, all_exposed)
        total_used = len(all_used)
        
        # 获取已组成的面子和搭子
        composed_tiles = set(composed["composed_tiles"])
        composed_melds = composed["melds"]
        composed_tatsus = composed["tatsus"]
        
        # 确定牌局阶段
        if total_used < 70:
            game_stage = "早期"
        elif total_used < 95:
            game_stage = "中期"
        else:
            game_stage = "后期"
        
        # 统计牌的数量
        tile_count = {}
        for tile in concealed:
            tile_count[tile] = tile_count.get(tile, 0) + 1
        
        # 统计花色分布
        suit_counts = {"万": 0, "条": 0, "筒": 0}
        for tile in concealed+exposed:
            for suit in suit_counts:
                if suit in tile:
                    suit_counts[suit] += 1
                    break
        max_suit = max(suit_counts, key=suit_counts.get)
        max_suit_count = suit_counts[max_suit]
        
        # 评估每张牌的危险度和价值
        discard_scores = {}
        
        # 1. 统计暴露的鸡牌情况
        # 只有自己暴露的鸡牌才需要考虑，别人的鸡牌与自己无关
        exposed_chicken_count = 0
        # 只统计自己的暴露鸡牌（hand["exposed"]是自己的副露）
        for exposed in hand["exposed"]:
            for t in exposed["tiles"]:
                if t in self.chicken_tiles:
                    exposed_chicken_count += 1
        
        for tile in set(concealed):
            reason = ""
            tile_num = int(tile[:-1])
            tile_suit = tile[-1]
            current_tile_count = tile_count[tile]
            
            # 检查该牌是否属于已组成的面子/搭子
            is_in_composed = tile in composed_tiles
            
            # 检查是否有做大牌的特殊情况
            is_big_pattern = False
            if pattern_potential['七对子'] > 0.8 or pattern_potential['碰碰胡'] > 0.8 or pattern_potential['清一色'] > 0.8:
                is_big_pattern = True
            
            # 2. 检查打出该牌后是否可以听牌
            can_ting = False
            ting_info = []
            ting_bonus = 0
            ting_reason = ""
            
            # 检查当前总手牌数量
            current_exposed = [tile for group in hand["exposed"] for i,tile in enumerate(group["tiles"]) if i<3]
            current_total = len(concealed + current_exposed)
            
            # 根据麻将规则，当手牌数量为14张时，需要打出一张，此时可以听牌
            if current_total == 14:
                # 模拟打出该牌后的手牌
                temp_concealed = [t for t in concealed if t != tile]
                temp_hand = {
                    "concealed": temp_concealed,
                    "exposed": hand["exposed"]
                }
                
                # 计算打出牌后的总手牌数量
                temp_exposed = [tile for group in temp_hand["exposed"] for i,tile in enumerate(group["tiles"]) if i<3]
                temp_total = len(temp_concealed + temp_exposed)
                
                # 只有当打出牌后手牌数量为13张时，才检查是否听牌
                if temp_total == 13:
                    # 调用check_ting函数检查是否听牌
                    is_ting, ting_tiles = self.check_ting(temp_hand, all_used)
                    if is_ting:
                        can_ting = True
                        ting_info = ting_tiles
                        
                        # 评估听牌质量
                        ting_quality = self._evaluate_ting_quality(ting_tiles)
                        
                        # 计算听牌加成，越后期加成越高
                        if game_stage == "早期":
                            # 早期听牌加成较低，且如果听牌质量不高，可以考虑换听
                            if ting_quality < 50:  # 听牌质量不高（边张/卡张）
                                ting_bonus = -100  # 降低听牌加成
                                ting_reason = "打出后可以听牌，但听牌质量不高，考虑是否换听"
                            else:
                                ting_bonus = -200  # 早期听牌加成
                                ting_reason = "打出后可以听牌，早期优先"
                        elif game_stage == "中期":
                            ting_bonus = -300  # 中期听牌加成中等
                            ting_reason = "打出后可以听牌，中期优先"
                        else:  # 后期
                            ting_bonus = -500  # 后期听牌加成很高
                            ting_reason = "打出后可以听牌，后期优先"
                        
                        # 只有自己暴露的鸡牌才影响听牌优先级
                        if exposed_chicken_count > 0:
                            ting_bonus += exposed_chicken_count * (-50)
                            ting_reason += f"，暴露{exposed_chicken_count}张鸡牌，优先听牌"
            
            # 3. 基本牌型价值评估（决定牌的基本优先级）
            # 注意：我们将牌分为几个优先级级别，级别越高，越不应该被打出
            priority_level = 0
            basic_reason = ""
            
            # 3.1 刻子或暗杠：优先级最高，绝对不拆
            if current_tile_count >= 3:
                priority_level = 5
                basic_reason = "刻子/暗杠价值极高，绝对不拆"
            # 3.2 唯一将牌：优先级很高，绝对不拆
            elif current_tile_count == 2 and sum(1 for t in tile_count if tile_count[t] >= 2) == 1:
                priority_level = 4
                basic_reason = "唯一的对子作为将牌，绝对不拆"
            # 3.3 普通对子：优先级高，尽量不拆
            elif current_tile_count == 2:
                priority_level = 3
                basic_reason = "对子价值高，尽量不拆"
            # 3.4 已组成的面子/搭子：优先级很高，非必须情况不拆
            elif is_in_composed:
                # 已组成的面子/搭子，非必须情况不拆
                priority_level = 6  # 提高优先级，确保只有在特殊情况下才会拆
                basic_reason = "已组成面子/搭子，非必须情况不拆"
            # 3.5 强搭子（连张搭子）：优先级中高，尽量保留
            elif current_tile_count == 1:
                # 检查是否是强搭子的一部分
                prev1 = self._get_tile_by_number(tile, tile_num - 1)
                next1 = self._get_tile_by_number(tile, tile_num + 1)
                has_prev1 = prev1 in concealed
                has_next1 = next1 in concealed
                
                prev2 = self._get_tile_by_number(tile, tile_num - 2)
                next2 = self._get_tile_by_number(tile, tile_num + 2)
                has_prev2 = prev2 in concealed
                has_next2 = next2 in concealed
                
                if has_prev1 or has_next1:
                    # 连张搭子，优先级中高
                    priority_level = 2
                    basic_reason = "连张搭子，质量高，尽量保留"
                elif has_prev2 or has_next2:
                    # 嵌张搭子，优先级中等
                    priority_level = 1
                    basic_reason = "嵌张搭子，质量一般"
                else:
                    # 孤张牌，优先级低，优先打出
                    priority_level = 0
                    basic_reason = "孤张牌，价值低，优先打出"
            
            # 4. 鸡牌特殊处理
            if tile in self.chicken_tiles:
                # 检查是否是冲锋鸡或横鸡
                is_first_discard = self._is_first_chicken_discard(tile, all_discards)
                is_first_global = self._is_first_global_chicken_discard(tile, all_discards)
                
                # 在手牌情况较好时再考虑打出鸡牌
                # 改进：更严格的手牌质量评估
                is_good_hand = meld_count >= 2 and dazi_count >= 2  # 增加搭子数量要求
                
                if is_first_discard and ready0 and len(all_used) < 90:
                    # 避免打冲锋鸡，提高优先级
                    priority_level -= 3  # 增加优先级提升幅度
                    basic_reason = "牌型较好，冲锋鸡收益高，可以打出"
                elif is_first_global and ready1 and len(all_used) < 90:
                    # 避免打横鸡，提高优先级
                    priority_level -= 2  # 增加优先级提升幅度
                    basic_reason = "牌型较好，横鸡收益较高，可以打出"
                elif not is_good_hand:
                    # 手牌情况不好，先留着鸡牌，提高优先级
                    # 手牌不好时，鸡牌优先级极高，确保不被轻易打出
                    priority_level += 4  # 进一步提高鸡牌优先级，从+3改为+4
                    basic_reason = "手牌情况不好，建议保留鸡牌"
                else:
                    # 手牌情况好，可以考虑打鸡牌，降低优先级
                    priority_level -= 1
                    basic_reason = "手牌情况较好，可以打出鸡牌"
            
            # 5. 特殊牌型策略调整
            # 5.1 清一色潜力
            if max_suit_count >= 9:
                if tile_suit == max_suit:
                    # 主花色牌，提高优先级
                    priority_level += 1
                else:
                    # 非主花色牌，降低优先级
                    priority_level -= 1
                    basic_reason = f"有{max_suit}清一色潜力，优先打出其他花色牌"
            
            # 5.2 七对子潜力
            if pattern_potential['七对子'] > 0.7:
                if current_tile_count == 1:
                    # 七对子情况下，单张牌优先级降低
                    priority_level -= 1
                    basic_reason = "七对子潜力大，优先打出单张牌"
            
            # 5.3 碰碰胡潜力
            if pattern_potential['碰碰胡'] > 0.7:
                if current_tile_count == 1:
                    # 碰碰胡情况下，单张牌优先级降低
                    priority_level -= 1
                    basic_reason = "碰碰胡潜力大，优先打出单张牌"
            
            # 6. 牌局阶段调整
            if game_stage == "早期":
                # 早期优先打孤张和幺九牌，但不拆已组成的面子/搭子
                if priority_level == 0 and (tile_num == 1 or tile_num == 9):
                    priority_level -= 1
                    basic_reason = "早期牌局，优先打出幺九孤张"
                elif priority_level == 0:
                    basic_reason = "早期牌局，优先打出孤张牌"
            elif game_stage == "后期":
                # 后期优先考虑防守，但不拆已组成的面子/搭子
                danger_score = self._calculate_danger_score(tile, all_discards, all_exposed, all_used, concealed)
                if danger_score < 10:
                    # 安全牌，降低优先级
                    priority_level -= 1
                    basic_reason += "，后期优先打安全牌"
            
            # 7. 特殊情况处理：只有在听牌或有极强大牌潜力时才可以拆打已组成的面子/搭子
            if is_in_composed:
                # 已组成的面子/搭子，非必须情况不拆
                if can_ting:
                    # 听牌优先级最高，可以拆搭子
                    pass  # 听牌加成已经在后面处理
                elif is_big_pattern and max(pattern_potential.values()) > 0.9:
                    # 极强的大牌潜力（超过0.9），可以考虑拆搭子
                    priority_level = 2
                    basic_reason = f"极强{max(pattern_potential, key=pattern_potential.get)}潜力，考虑拆面子/搭子"
                else:
                    # 非必须情况，不拆已组成的面子/搭子
                    priority_level = 6
                    basic_reason = "已组成面子/搭子，非必须情况不拆"
            
            # 8. 计算最终得分（将优先级转换为分数）
            # 优先级越高，分数越高，越不应该被打出
            # 分数越低，越优先被打出
            final_score = priority_level * 100
            
            # 9. 点炮风险微调（仅在同一优先级内调整）
            if priority_level <= 2:  # 仅对低优先级牌进行点炮风险调整
                danger_score = self._calculate_danger_score(tile, all_discards, all_exposed, all_used, concealed)
                if game_stage == "早期":
                    final_score -= danger_score * 0.2
                elif game_stage == "中期":
                    final_score -= danger_score * 0.5
                else:
                    final_score -= danger_score * 1.0
            
            # 10. 添加听牌加成（直接降低分数，使牌更优先被打出）
            # 听牌优先级最高，无论是否是已组成的面子/搭子
            if can_ting:
                final_score += ting_bonus
                basic_reason = ting_reason
                # 听牌时，直接将优先级设为最低，确保优先打出
                final_score = min(final_score, -1000)
            
            # 11. 确保理由清晰明确
            if reason.endswith("，"):
                reason = reason[:-1]
            if reason == "":
                reason = basic_reason
            
            discard_scores[tile] = (final_score, reason)
        
        # 调试：打印每张牌的得分
        # for tile, (score, reason) in discard_scores.items():
        #     print(f"牌 {tile}: 得分 {score}, 理由 {reason}")
        
        # 按分数排序（分数越低越优先打）
        # 注意：分数越高表示这张牌越不应该被打出
        sorted_discards = sorted(discard_scores.items(), key=lambda x: x[1][0])
        
        # 生成排序后的牌列表
        result = []
        for tile, (score, reason) in sorted_discards:
            result.extend([tile] * tile_count[tile])
        
        # 获取前3张牌的推荐理由
        top_reasons = []
        for i in range(min(3, len(sorted_discards))):
            tile, (score, reason) = sorted_discards[i]
            top_reasons.append(reason)
        
        return result, top_reasons

    def decide_peng(self,
            hand,
            all_discards: List[List[str]],
            all_exposed: List[List[Dict]],
            chicken_tiles: List[str],
            tile: str):
        """
        智能决策是否碰牌
        参数：
            hand: 自己手牌
            all_discards: 四家弃牌堆，每家一个列表，顺序为[上家, 自己, 下家, 对家]
            all_exposed: 其他三家已副露列表，顺序为[上家, 自己, 下家, 对家]
            chicken_tiles: 鸡牌列表,默认值为["1条"]
            tile: 要判断的牌，是否碰这张牌
        返回：
            (是否碰牌, 推荐理由)：(True/False, "推荐理由")
        """
        return True, "simpleAI 推荐碰牌"

    def decide_gang(self,
            hand,
            all_discards: List[List[str]],
            all_exposed: List[List[Dict]],
            chicken_tiles: List[str],
            tile: str):
        """
        智能决策是否杠牌
        参数：
            hand: 自己手牌
            all_discards: 四家弃牌堆，每家一个列表，顺序为[上家, 自己, 下家, 对家]
            all_exposed: 其他三家已副露列表，顺序为[上家, 自己, 下家, 对家]
            chicken_tiles: 鸡牌列表,默认值为["1条"]
            tile: 要判断的牌，是否杠这张牌
        返回：
            (是否杠牌, 推荐理由)：(True/False, "推荐理由")
        """
        
        return True, "simpleAI 推荐杠牌"

    def decide_hu(self,
            hand,
            all_discards: List[List[str]],
            all_exposed: List[List[Dict]],
            chicken_tiles: List[str],
            tile: str):
        """
        智能决策是否胡牌
        参数：
            hand: 自己手牌
            all_discards: 四家弃牌堆，每家一个列表，顺序为[上家, 自己, 下家, 对家]
            all_exposed: 其他三家已副露列表，顺序为[上家, 自己, 下家, 对家]
            chicken_tiles: 鸡牌列表,默认值为["1条"]
            tile: 要判断的牌，是否胡这张牌
        返回：
            (是否胡牌, 推荐理由)：(True/False, "推荐理由")
        """
        
        return True, f"simpleAI 推荐胡牌"

    def _get_all_used_tiles(self, hand, all_discards, all_exposed):
        """获取所有已使用的牌"""
        all_tiles = []
        all_tiles.extend(hand["concealed"])
        for exposed in hand["exposed"]:
            all_tiles.extend(exposed["tiles"])
        
        for discards in all_discards:
            all_tiles.extend(discards)
        
        for exposed_list in all_exposed:
            for exposed in exposed_list:
                all_tiles.extend(exposed["tiles"])
        
        return all_tiles

    def _is_first_chicken_discard(self, tile, all_discards):
        """检查是否是自己的第一张鸡牌（冲锋鸡）"""
        for discard_list in all_discards:
            for disc_tile in discard_list:
                if disc_tile in self.chicken_tiles and disc_tile == tile:
                    return True  # 是第一张鸡牌
        return False

    def _is_first_global_chicken_discard(self, tile, all_discards):
        """检查是否是全场第一张鸡牌（横鸡）"""
        first_chicken = None
        for discard_list in all_discards:
            for disc_tile in discard_list:
                if disc_tile in self.chicken_tiles:
                    if first_chicken is None:
                        first_chicken = disc_tile
                    elif disc_tile == tile:
                        return True  # 是横鸡
        return False

    def _evaluate_single_tile(self, tile, concealed):
        """评估单张牌的价值"""
        # 检查是否能与相邻牌形成顺子或搭子
        score = 0
        tile_num = self._get_tile_number(tile)
        tile_suit = tile[-1]
        
        if tile_num:
            # 检查前后牌是否存在
            prev1 = self._get_tile_by_number(tile, tile_num - 1)
            prev2 = self._get_tile_by_number(tile, tile_num - 2)
            next1 = self._get_tile_by_number(tile, tile_num + 1)
            next2 = self._get_tile_by_number(tile, tile_num + 2)
            
            # 统计相邻牌的数量
            adjacent_count = 0
            for check_tile in concealed:
                if check_tile != tile and check_tile[-1] == tile_suit:
                    check_num = self._get_tile_number(check_tile)
                    if abs(check_num - tile_num) <= 2:
                        adjacent_count += 1
            
            if adjacent_count >= 2:
                # 有多个相邻牌，价值高
                score += 40  # 这是顺子的中间张或有多个搭子可能
                reason = "有多个相邻牌，价值高"
            elif prev1 in concealed and next1 in concealed:
                score += 30  # 这是顺子的中间张
                reason = "顺子中间张，价值高"
            elif prev1 in concealed or next1 in concealed:
                score += 25  # 可以形成连张搭子，质量高
                reason = "连张搭子，质量高"
            elif prev2 in concealed or next2 in concealed:
                score += 15  # 可以形成嵌张搭子，质量一般
                reason = "嵌张搭子，质量一般"
            else:
                score -= 30  # 孤张牌，价值低
                reason = "孤张牌，价值低"

        return score

    def _evaluate_pair_tile(self, tile, concealed, game_stage, ready0):
        """评估两张相同牌的价值"""
        # 两张相同牌，可能形成刻子或对子
        score = 25  # 形成对子的基础分，价值较高
        
        # 检查是否有第三张
        tile_count_in_hand = concealed.count(tile)
        if tile_count_in_hand >= 3:
            score += 30  # 可以碰成刻子或暗杠，价值极高
        
        # 根据牌局阶段调整对子价值
        if game_stage == "早期":
            # 早期对子价值较高，可以考虑碰牌或形成刻子
            score += 10
        elif game_stage == "中期":
            # 中期对子价值取决于是否能形成刻子或作为将牌
            score += 5
        else:  # 后期
            # 后期对子如果能作为将牌，价值极高
            if ready0:
                score += 20  # 接近听牌，将牌价值极高
        
        return score

    def _calculate_danger_score(self, tile, all_discards, all_exposed, all_used, current_hand):
        """计算点炮风险"""
        danger_score = 0
        total_used = len(all_used)
        
        # 1. 检查牌是否被打出过
        tile_seen = False
        tile_recently_seen = False
        for i, discards in enumerate(all_discards):
            if i == 1:  # 跳过自己的弃牌堆
                continue
            if tile in discards:
                tile_seen = True
                # 检查是否最近被打出
                if tile in discards[-3:]:
                    tile_recently_seen = True
                break
        
        if tile_recently_seen:
            danger_score -= 20  # 最近被打出过，较安全
        elif tile_seen:
            danger_score += 5  # 被打出过但不是最近，风险一般
        else:
            # 从未被打出过，根据牌局阶段调整风险
            if total_used < 20:  # 牌局初期
                danger_score += 10  # 初期风险较低
            elif total_used < 50:  # 牌局中期
                danger_score += 20  # 中期风险中等
            else:  # 牌局后期
                danger_score += 40  # 后期风险较高
        
        # 2. 检查其他玩家的副露情况
        has_exposed = any(len(exposed_list) > 0 for exposed_list in all_exposed)
        if has_exposed:
            for exposed_list in all_exposed:
                if not exposed_list:  # 跳过自己的副露
                    continue
                # 检查是否有相同花色的副露
                tile_suit = tile[-1]
                suit_exposed = False
                for exposed in exposed_list:
                    if exposed["tiles"][0][-1] == tile_suit:
                        suit_exposed = True
                        break
                if suit_exposed:
                    # 检查是否可能形成顺子或刻子
                    tile_num = int(tile[:-1])
                    for exposed in exposed_list:
                        if exposed["tiles"][0][-1] == tile_suit:
                            # 检查刻子
                            if len(exposed["tiles"]) == 3 and exposed["tiles"][0] == exposed["tiles"][1] == exposed["tiles"][2]:
                                if exposed["tiles"][0] == tile:
                                    danger_score += 60  # 别人已经有碰牌，再打就点杠
                            # 检查顺子
                            else:
                                # 提取副露中的数字
                                exposed_nums = []
                                for t in exposed["tiles"]:
                                    if t[-1] == tile_suit:
                                        exposed_nums.append(int(t[:-1]))
                                # 检查是否需要当前牌组成顺子
                                if len(exposed_nums) == 2:
                                    min_num = min(exposed_nums)
                                    max_num = max(exposed_nums)
                                    if max_num - min_num == 1:
                                        # 连张副露，如12万，需要3万或0万（不可能）
                                        if tile_num == min_num - 1 or tile_num == max_num + 1:
                                            danger_score += 50  # 可能点炮
                                    elif max_num - min_num == 2:
                                        # 嵌张副露，如13万，需要2万
                                        if tile_num == min_num + 1:
                                            danger_score += 60  # 很可能点炮
        
        # 3. 考虑牌局进程
        if total_used > 90:  # 牌局末期
            danger_score *= 2.0  # 末期风险放大
        elif total_used < 20:  # 牌局初期
            danger_score *= 0.3  # 初期风险大幅降低
        elif total_used < 50:  # 牌局中期
            danger_score *= 0.8  # 中期风险降低
        
        # 4. 考虑牌的类型（如字牌、幺九牌等）
        tile_num = int(tile[:-1])
        if tile_num == 1 or tile_num == 9:  # 幺九牌
            danger_score *= 0.7  # 幺九牌风险稍低
        
        # 5. 考虑手牌中该牌的数量
        current_count = current_hand.count(tile)
        if current_count >= 3:
            danger_score *= 0.5  # 手里有刻子，打出单张风险较低
        elif current_count == 2:
            danger_score *= 1.3  # 手里有对子，打出单张风险更高
        
        return danger_score

    def _evaluate_pattern_score(self, concealed, pattern_potential):
        """评估手牌形成好牌型的潜力"""
        score = 0
        
        # 1. 评估特殊牌型潜力
        for pattern, potential in pattern_potential.items():
            if potential > 0:
                if pattern == '七对子':
                    score += potential * 40  # 七对子得分高
                elif pattern == '碰碰胡':
                    score += potential * 30  # 碰碰胡得分较高
                elif pattern == '清一色':
                    score += potential * 50  # 清一色得分最高
                elif pattern == '门清':
                    score += potential * 20  # 门清得分一般
        
        # 2. 统计牌型分布
        tiles_by_type = {"万": [], "条": [], "筒": []}
        for tile in concealed:
            for tile_type in tiles_by_type:
                if tile_type in tile:
                    tiles_by_type[tile_type].append(tile)
                    break
        
        # 3. 检查是否可能混一色
        max_suit_count = max([len(tiles) for tiles in tiles_by_type.values()])
        if max_suit_count >= 9:
            score += 15  # 有混一色潜力
        
        # 4. 检查对子和刻子潜力
        tile_counts = {}
        for tile in concealed:
            tile_counts[tile] = tile_counts.get(tile, 0) + 1
        
        pair_count = 0
        triplet_count = 0
        quad_count = 0
        for tile, count in tile_counts.items():
            if count == 2:
                pair_count += 1
                score += 10
            elif count == 3:
                triplet_count += 1
                score += 30
            elif count >= 4:
                quad_count += 1
                score += 60
        
        # 5. 检查搭子质量
        # 统计连张搭子和嵌张搭子
        suit_dicts = {}
        for suit, tiles in tiles_by_type.items():
            suit_dict = defaultdict(int)
            for tile in tiles:
                num = int(tile[:-1])
                suit_dict[num] += 1
            suit_dicts[suit] = suit_dict
        
        for suit, num_dict in suit_dicts.items():
            nums = sorted(num_dict.keys())
            consecutive_pairs = 0
            gap_pairs = 0
            
            for i in range(len(nums) - 1):
                if nums[i+1] == nums[i] + 1:
                    consecutive_pairs += 1
                elif nums[i+1] == nums[i] + 2:
                    gap_pairs += 1
            
            # 连张搭子质量更高
            score += consecutive_pairs * 12
            score += gap_pairs * 8
        
        # 6. 检查单张牌数量
        single_count = 0
        for count in tile_counts.values():
            if count == 1:
                single_count += 1
        
        # 单张牌越少，牌型越好
        if single_count <= 2:
            score += 20
        elif single_count <= 4:
            score += 10
        elif single_count >= 6:
            score -= 10
        
        return score

    def _evaluate_ting_quality(self, ting_tiles):
        """
        评估听牌质量
        :param ting_tiles: 听牌列表，每个元素为(胡牌类型, 听的牌, 剩余数量)
        :return: 听牌质量评分，范围0-100，越高越好
        """
        if not ting_tiles:
            return 0
        
        # 评估每个听牌的质量
        quality_score = 0
        for ting_info in ting_tiles:
            # 提取听的牌（元组的第二个元素）
            tile = ting_info[1]
            tile_num = int(tile[:-1])
            
            # 边张和卡张质量较低
            if tile_num == 1 or tile_num == 9:
                # 边张，质量低
                quality_score += 30
            elif tile_num == 2 or tile_num == 8:
                # 接近边张，质量较低
                quality_score += 50
            elif tile_num == 3 or tile_num == 7:
                # 中间张，质量中等
                quality_score += 70
            else:
                # 中心张，质量高
                quality_score += 90
        
        # 计算平均质量
        return quality_score / len(ting_tiles)

    def _is_strong_hand(self, hand):
        """检查自己是否是强牌"""
        # 检查是否有杠牌
        for exposed in hand["exposed"]:
            if exposed["is_gang"]:
                return True
        
        # 检查鸡牌数量
        chicken_count = sum(1 for tile in hand["concealed"] if tile in self.chicken_tiles)
        if chicken_count >= 2:
            return True
        
        return False

    def _get_tile_number(self, tile):
        """获取牌的数字"""
        if tile[0].isdigit():
            return int(tile[0])
        return 0

    def _get_tile_by_number(self, base_tile, num):
        """根据数字和类型获取牌"""
        if 1 <= num <= 9:
            tile_type = ""
            for t in ["万", "条", "筒"]:
                if t in base_tile:
                    tile_type = t
                    break
            if tile_type:
                return f"{num}{tile_type}"
        return ""
























