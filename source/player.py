# Player类定义
from source.tile import TILE
from settings import Settings
from source.public import DecisionType,DecisionResult,Tag

class Player:
    
    """玩家基类，用于管理玩家信息"""
    
    def __init__(self, name, is_human=False, position="east"):
        """
        初始化玩家
        
        Args:
            name: 玩家名字
            is_human: 是否是人类玩家
            position: 玩家位置 (east/north/south/west)
            avatar: 玩家头像路径
        """
        
        self.name = name
        self.is_human = is_human
        self.position = position
        self.avatar = None
        self.score = Settings.score  # 玩家积分
        self.player_id = name  # 使用名字作为player_id，方便标识
        self.first_draw = True # 是否是玩家摸的第一张牌,第一次检测到之后切换为False
        self.first_discard = True # 是否是玩家弃的第一张牌,第一次检测到之后切换为False
        self.gender = 'boy'  # 玩家性别，默认为男孩
        self.is_girl = False  # 是否为女孩，默认为False
        self.time_limit = 10  # 玩家决策时间限制，单位秒
        self.ting_info = "暂未叫牌"  # 叫牌信息
        self.hu_type = {}  # 胡牌类型统计
        self.jiaopai = False
        
        # 手牌对象，包含隐藏牌和明牌
        self.hand = {
            'concealed': [],  # 隐藏的手牌（未打出的牌）,只能包含TILE类的实例
            'exposed': []     # 明牌（碰杠的牌）,每个元素是一个字典，包含牌组、来源、是否为杠牌、杠牌类型
        }
        self.discard_tiles = []  # 弃牌堆
        
        # 标签系统，存储游戏行为产生的标签
        # 每个标签对象是一个字典，包含'tag'（标签名称）和'source'（来源）
        self.tags = []
        
        # 统计变量
        self.starting_score = Settings.score  # 起始积分
        self.win_count = 0  # 胡牌局数
        self.OfferingWin_count = 0  # 点炮/热炮等局数，含抢杠胡
        self.gain_ji_count = 0  # 冲鸡分数，包含碰杠鸡/打出鸡
        self.loss_ji_count = 0  # 包鸡分数，包含责任鸡/不叫牌包鸡
        self.previous_score = Settings.score  # 本局结算前的分数
    
    @property
    def name(self):
        name_str = self.__dict__['name']
        if len(name_str) == 2:
            name_str = name_str[0] + "  " + name_str[1]
        return name_str

    @name.setter
    def name(self, value):
        # 将原始值存入__dict__
        self.__dict__['name'] = value

    def add_tile(self, tile, exposed=False, source='east', is_gang=False, gang_type=None):
        """添加一张牌到手牌
        
        Args:
            tile: 要添加的牌
            exposed: 是否为明牌（碰杠的牌）
            source: 明牌来源（east/north/south/west）
            is_gang: 是否为杠牌
            gang_type: 杠牌类型，可选值为'added'（加杠）或'exposed'（明杠）
        """
        if tile not in TILE:
            raise ValueError(f"牌 {tile} 不是有效的牌面")
        if exposed:
            # 找到相同的明牌组，如果存在则添加到该组中，保持格式一致
            added_to_existing_group = False
            for group in self.hand['exposed']:
                # 只合并相同类型的牌组（碰牌组只能合并到碰牌组，杠牌组只能合并到杠牌组）
                if (isinstance(group, dict) and 
                    'tiles' in group and 
                    group.get('is_gang', False) == is_gang and
                    group.get('source') == source and
                    group.get('tiles')):
                    # 检查牌组中第一张牌是否与当前牌相同
                    if group['tiles'][0] == tile:
                        group['tiles'].append(tile)
                        added_to_existing_group = True
                        break
            
            # 如果没有找到相同的牌组，则创建新的牌组
            if not added_to_existing_group:
                # 创建统一格式的牌组字典
                group_dict = {
                    'tiles': [tile],
                    'source': source,
                    'is_gang': is_gang
                }
                # 根据情况添加额外字段
                if is_gang:
                    group_dict['gang_type'] = gang_type
                else:
                    group_dict['action_type'] = 'exposed'
                    
                self.hand['exposed'].append(group_dict)
        else:
            self.hand['concealed'].append(tile)

    def sort_hand(self):
        """整理手牌-排序"""
        # 对隐藏手牌按万条筒顺序从小到大排序
        self.hand['concealed'].sort(key=lambda t: (t[-1], t[0]))
    
    def get_hand(self):
        """获取手牌
        
        Returns:
            dict: 手牌对象，包含隐藏牌和明牌
        """
        return self.hand
    
    def hu_tile(self, tile):
        """胡牌操作
        
        Args:
            tile: 胡的牌
            source_position: 牌的来源位置（如果是吃胡）
        """
        hand = self.hand['concealed']
        if len(hand) in [1,4,7,10,13]:
            self.hand['concealed'].append(tile)
    
    def get_discard_tiles(self):
        """获取玩家的弃牌列表
        
        Returns:
            list: 弃牌列表
        """
        return self.discard_tiles

    def get_concealed_hand(self):
        """获取玩家的隐藏手牌
        
        Returns:
            list: 隐藏手牌列表
        """
        return self.hand['concealed']

    def get_exposed_hand(self):
        """获取玩家的明牌手牌
        
        Returns:
            list: 明牌手牌列表
        """
        return self.hand['exposed']

    #移除手牌并加入弃牌堆：正常弃牌
    def discard_tile(self, tile):
        # 从隐藏手牌中移除该牌
        if tile in self.hand['concealed']:
            self.hand['concealed'].remove(tile)
        # 添加到弃牌堆
        self.discard_tiles.append(tile)

    # 从弃牌堆中移除牌：用于处理放炮，被碰牌，被杠牌
    def remove_discard_tile(self, tile):
        # 从弃牌堆中移除该牌
        if tile in self.discard_tiles:
            self.discard_tiles.remove(tile)

    def peng_tile(self, tile, source="self",ji_tag=None):
        """碰牌操作
        
        Args:
            tile: 要碰的牌
            source_position: 牌的来源位置
        """
        # 从隐藏手牌中移除两张相同的牌
        if self.hand['concealed'].count(tile) >= 2:
            # 移除两张牌（使用循环确保正确移除指定数量的牌）
            for _ in range(2):
                if tile in self.hand['concealed']:
                    self.hand['concealed'].remove(tile)
                else:
                    print(f"警告: 尝试从{self.name}的隐藏手牌中移除不存在的牌 {tile}")
                    break
            
            # 添加到明牌中（包含打出的那张牌）
            self.hand['exposed'].append({
                'tiles': [tile, tile, tile],  # 三张相同的牌
                'source': source,
                'is_gang': False,
                'action_type': 'peng',
                'ji_tag': ji_tag
            })
            return True
        return False
    
    def gang_tile(self, tile, source_name, gang_type='exposed',ji_tag=None):
        """杠牌操作
        
        Args:
            tile: 要杠的牌
            source_name: 牌的来源位置（如果是明杠或加杠）
            gang_type: 杠牌类型 ('exposed' 明杠, 'added' 加杠, 'hidden' 自杠)
        
        Returns:
            bool: 杠牌操作是否成功
        """
        try:
            # 手里3张，杠别人打出的牌
            if gang_type == 'exposed':
                # 明杠：从隐藏手牌中移除三张相同的牌
                if self.hand['concealed'].count(tile) >= 3:
                    # 移除三张牌，使用循环确保正确移除指定数量的牌
                    removed_count = 0
                    for _ in range(3):
                        if tile in self.hand['concealed']:
                            self.hand['concealed'].remove(tile)
                            removed_count += 1
                        else:
                            print(f"警告: 尝试从{self.name}的隐藏手牌中移除不存在的牌 {tile}")
                            break
                    
                    # 只有成功移除了三张牌才添加到明牌中
                    if removed_count == 3:
                        # 添加到明牌中（包含打出的那张牌）
                        self.hand['exposed'].append({
                            'tiles': [tile, tile, tile, tile],  # 四张相同的牌
                            'source': source_name,
                            'is_gang': True,
                            'action_type': 'gang',
                            'gang_type': 'exposed',
                            'ji_tag': ji_tag
                        })
                        return True
            # 手里1张，加杠自己碰过的牌
            elif gang_type == 'add':
                # 加杠：从已经碰的牌中添加一张牌
                for group in self.hand['exposed']:
                    if isinstance(group, dict) and 'tiles' in group and not group.get('is_gang', False):
                        if group['tiles'][0] == tile and len(group['tiles']) == 3:
                            # 从隐藏手牌中移除一张牌
                            if tile in self.hand['concealed']:
                                self.hand['concealed'].remove(tile)
                                # 添加到碰牌组中，使其成为杠牌组
                                group['tiles'].append(tile)
                                group['is_gang'] = True
                                group['action_type'] = 'gang'
                                group['gang_type'] = 'added'
                                group['ji_tag'] = ji_tag
                                if not tile in Settings.chicken_tile:
                                    group['source'] = "self"
                                return True
                            else:
                                print(f"警告: {self.name}的隐藏手牌中没有牌 {tile} 用于补杠")
            #手里4张，自己杠
            elif gang_type == 'self':
                # 自杠：从隐藏手牌中移除四张相同的牌
                if self.hand['concealed'].count(tile) == 4:
                    # 移除四张牌，使用循环确保正确移除指定数量的牌
                    removed_count = 0
                    for _ in range(4):
                        if tile in self.hand['concealed']:
                            self.hand['concealed'].remove(tile)
                            removed_count += 1
                        else:
                            print(f"警告: 尝试从{self.name}的隐藏手牌中移除不存在的牌 {tile}")
                            break
                    
                    # 只有成功移除了四张牌才添加到明牌中
                    if removed_count == 4:
                        # 添加到明牌中
                        self.hand['exposed'].append({
                            'tiles': [tile, tile, tile, tile],  # 四张相同的牌
                            'source': "self",  # 来源是自己
                            'is_gang': True,
                            'action_type': 'gang',
                            'gang_type': 'self',
                            'ji_tag': ji_tag
                        })
                        return True
                    
        except Exception as e:
            print(f"{self.name}杠牌时发生错误: {e}")
        
        return False

    def add_tag(self, tag_name, source="self"):
        """
        为玩家添加标签
        
        Args:
            tag_name: 标签名称
            source: 标签来源（可选）
        """
        tag = {
            'tag': tag_name,
            'source': source
        }
        # 检查标签是否已存在
        if not any(t['tag'] == tag_name for t in self.tags) or tag_name == Tag.YAO_JI:
            self.tags.append(tag)
        return tag
    
    def change_tag_source(self, tag_name, new_source):
        """
        改变玩家标签的来源
        
        Args:
            tag_name: 标签名称
            new_source: 新的标签来源
        """
        for tag in self.tags:
            if tag['tag'] == tag_name:
                tag['source'] = new_source
                break

    def remove_tag(self, tag_name):
        """
        为玩家移除标签
        
        Args:
            tag_name: 标签名称
        """
        tags = self.tags
        for tag in tags:
            if tag['tag'] == tag_name:
                tags.remove(tag)
                break
        self.tags = tags

    def get_tags(self):
        """
        获取玩家的所有标签
        
        Returns:
            list: 标签对象列表
        """
        return self.tags
    
    def has_tag(self, tag_name):
        """
        检查玩家是否有特定标签
        
        Args:
            tag_name: 标签名称
            
        Returns:
            bool: 如果有该标签则返回True，否则返回False
        """
        return any(t['tag'] == tag_name for t in self.tags)

    def print_hand(self):
        """打印玩家当前手牌"""
        print("="*40)
        print(f"[{self.name}] 手牌:",end="  ")
        for tile in self.hand['concealed']:
            print(f"[{tile}]",end="  ")
        if self.hand['exposed']:
            print(f"\n副露牌:")
            for group in self.hand['exposed']:
                print(f"[{' '.join(tile for tile in group['tiles'])}]",end="")
                print(f"({group['source']})")
        # 打印玩家标签
        if self.tags:
            print(f"\n玩家标签:")
            for tag in self.tags:
                print(f"  - {tag['tag'].value}" + (f"({tag['source']})" if tag['source'] != 'self' else ""))
        print()
        print("="*40)

    def print_result(self):
        """打印玩家游戏结果"""
        print("="*60)
        print(f"[{self.name}] 游戏结果:")
        result = self.result
        print("叫  牌:", "✅" if result.get('jiaopai') else "❌")
        print("本  局:", f"{result.get('total_ji', 0):+4}")

        if result.get('hu_ji', {}).get('num', 0):
            print("胡  牌:", f"{result.get('hu_ji', {}).get('num', 0):+4}", 
                  f"( {', '.join(result.get('hu_ji', {}).get('source', ''))} )" if result.get('hu_ji', {}).get('source') else "")
        
        if result.get('ji', {}).get('source', ""):
            print("鸡  牌:", f"{result.get('ji', {}).get('num', 0):+4}",
                f"( {', '.join(result.get('ji', {}).get('source', ''))} )" if result.get('ji', {}).get('source') else "")
        
        if result.get('gang_ji', {}).get('source', ""):
            print("杠  牌:", f"{result.get('gang_ji', {}).get('num', 0):+4}",
                f"( {', '.join(result.get('gang_ji', {}).get('source', ''))} )" if result.get('gang_ji', {}).get('source') else "")

        if result.get('count_with_other_player'):
            print("\n结  算:")
            for item in result['count_with_other_player']:
                print(f"{item['name']}: {item['num']:+4}", 
                      f"( {item['source']}" if item.get('source') else "")
        
        if self.hu_type:
            print("\n胡牌类型:")
            for hu_type, num in self.hu_type.items():
                print(f"  {hu_type.value}: {num:2} 局")

        print("="*60)

    def reset(self):
        """重置玩家数据"""
        self.hand = {'exposed': [], 'concealed': []}
        self.tags = []
        self.discard_tiles = []
        self.reject_hu = False # 拒绝胡牌标志
        self.first_discard = True # 第一次出牌标志
        self.first_draw = True # 第一次摸牌标志
        # 保存当前分数作为下一局的previous_score
        self.previous_score = self.score

    def make_discard_decision(self, cards):
        """AI决定要打出的牌"""

        hand = cards["hand"]
        all_discards = cards["all_discards"]
        all_exposed = cards["all_exposed"]
        chicken_tiles = cards["chicken_tiles"]
        tile = None
        while not tile:
            sorted_tiles, discard_reason = self.simple_ai.get_discard_precedence_list(
                hand, all_discards, all_exposed, chicken_tiles
            )
            if sorted_tiles and sorted_tiles[0] in hand["concealed"]:
                return sorted_tiles[0], discard_reason[0]
            else:
                raise ValueError("AI推荐的牌不在手牌中，请检查！！")
            
        if self.hand and "concealed" in self.hand and self.hand["concealed"]:
            len_concealed = len(self.hand["concealed"])
            tile = self.hand["concealed"][len_concealed-1]
        else:
            tile = None

        # 回退到简单逻辑：打出第一张牌
        return (tile,"AI推荐失败，自动选择最后一张牌") if tile else (None,"没有手牌可推荐，请检查")

    def make_peng_decision(self,tile,cards):
        """AI决定要碰的牌"""
        hand = cards["hand"]
        all_discards = cards["all_discards"]
        all_exposed = cards["all_exposed"]
        chicken_tiles = cards["chicken_tiles"]
        result, reason = self.simple_ai.decide_peng(
            hand, all_discards, all_exposed, chicken_tiles,tile
        )
        return result,reason
    
    def make_gang_decision(self,tile,cards):
        """AI决定要杠的牌"""
        hand = cards["hand"]
        all_discards = cards["all_discards"]
        all_exposed = cards["all_exposed"]
        chicken_tiles = cards["chicken_tiles"]
        result, reason = self.simple_ai.decide_gang(
            hand, all_discards, all_exposed, chicken_tiles,tile
        )
        return result,reason
    
    def make_hu_decision(self,tile,cards):
        """AI决定要胡的牌"""
        hand = cards["hand"]
        all_discards = cards["all_discards"]
        all_exposed = cards["all_exposed"]
        chicken_tiles = cards["chicken_tiles"]
        result, reason = self.simple_ai.decide_hu(
            hand, all_discards, all_exposed, chicken_tiles,tile
        )
        
        return result,reason


class HumanPlayer(Player):
    """人类玩家类，继承自Player类"""
    
    def __init__(self, name, position="east",model=None):
        """
        初始化人类玩家
        
        Args:
            name: 玩家名称
            position: 玩家位置，默认east
            avatar: 玩家头像路径
        """
        super().__init__(name, is_human=True, position=position)
        self.selected_tile_list = []
        self.recommend_tile = None
        self.recommend_reason = None
        self.recommend_option = None

    def get_recommend_tile_index(self):
        """获取推荐牌索引"""
        concealed = self.hand['concealed']
        rt = self.recommend_tile
        if concealed[-1]==rt:
            return len(concealed)-1
        return concealed.index(rt) if rt in concealed else -1

    def get_tile_indexes(self,tile):
        """获取手牌中指定牌的索引列表"""
        concealed = self.hand['concealed']
        result = []
        for i,t in enumerate(concealed):
            if t == tile:
                result.append(i)
        return result
        
    def make_decision(self,decision_list,cards,tile,remain_tiles,ting_info):
        """AI根据当前牌进行弃牌决策
        
        Args:
            cards: 可选弃牌列表
            remain_tiles: 剩余牌数
            ting_info: 叫牌信息
        """
        if DecisionType.DISCARD in decision_list and cards:
            tile = None
            option = DecisionType.DISCARD
            tile,reason = self.make_discard_decision(cards)
            return option,tile,reason
        if DecisionType.HU in decision_list:
            option = DecisionType.HU
            result,reason = self.make_hu_decision(tile,cards)
            # print("人类玩家",self.name,"胡牌决策")
            # print(reason)
            if result:
                return option,result,reason
        if DecisionType.GANG in decision_list:
            option = DecisionType.GANG
            result,reason = self.make_gang_decision(tile,cards)
            # print("人类玩家",self.name,"杠牌决策")
            # print(reason)
            if result:
                return option,result,reason
        if DecisionType.PENG in decision_list: 
            option = DecisionType.PENG
            result,reason = self.make_peng_decision(tile,cards)
            # print("人类玩家",self.name,"碰牌决策")
            # print(reason)
            if result:
                return option,result,reason
        return decision_list[0],None,"AI推荐失败，自动选择第一个决策"

class AIPlayer(Player):
    """AI玩家类，继承自Player类"""
    
    def __init__(self, name, position):
        """
        初始化AI玩家
        
        Args:
            name: 玩家名称
            position: 玩家位置
            avatar: 玩家头像路径
        """
        super().__init__(name, is_human=False, position=position)

    def make_decision(self,decision_list,tile,cards):
        """AI根据决策列表和当前牌进行决策
        
        Args:
            decision_list: 决策类型列表
            tile: 当前牌
        """
        decision = None
        result = True
        tile = None
        if DecisionType.DISCARD in decision_list:
            decision = DecisionType.DISCARD
            tile,_ = self.make_discard_decision(cards)
            return DecisionResult(decision,result,tile)
        if DecisionType.HU in decision_list:
            decision = DecisionType.HU
            # result,reason = self.make_hu_decision(tile,cards)
            return DecisionResult(decision,result,tile,"规则限定必须胡牌")
        if DecisionType.GANG in decision_list:
            decision = DecisionType.GANG
            result,reason = self.make_gang_decision(tile,cards)
            if result:
                return DecisionResult(decision,result,tile,reason)
        if DecisionType.PENG in decision_list:
            decision = DecisionType.PENG
            result,reason = self.make_peng_decision(tile,cards)
            if result:
                return DecisionResult(decision,result,tile,reason)
        return DecisionResult(DecisionType.CANCEL,True,None)





