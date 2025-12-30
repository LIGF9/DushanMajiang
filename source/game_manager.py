
import random,os,copy,time
from random import randint
from source.player import HumanPlayer,AIPlayer,Player
from source.rule import Rule
from majiangAI import MajiangAI0,MajiangAI1
from source.tile import TILES
from source.public import Tag, GameState,DecisionType,DecisionResult,DecisionRequest, get_resource_path
from typing import List

class GameManager:
    def __init__(self, settings):
        """
        初始化游戏管理器
        
        Args:
            settings: 设置对象，包含游戏配置信息
        """
        self.settings = settings
        self.players = []  #所有玩家
        self.majiang_tiles = []  # 牌堆
        self.winner = []
        self.banker = None  # 庄家
        self.rule = Rule() # 初始化规则检查器
        self.game_state = GameState.GAME_START# 使用枚举管理游戏状态
        self.is_game_over = False  # 是否游戏结束
        self.sound_callback = None  # 声音播放回调函数
        self.discard_tile = ""  # 当前弃牌
        self.ting_info = "暂未叫牌"  # 叫牌信息
        self.hu_type = {
            Tag.PING_HU: 0,#平胡
            Tag.DA_DUI_ZI: 0,#大对子
            Tag.QING_YI_SE: 0,#清一色
            Tag.DAN_DIAO: 0,#独钓
            Tag.XIAO_QI_DUI: 0,#小七对
        }  # 胡牌类型
        self.fanji_tile = ""  # 翻鸡牌
        self.fanji_tiles = []  # 翻鸡牌
        
        # 游戏统计信息
        self.total_games = 0  # 总局数
        self.draw_games = 0  # 流局数
        self.win_games = 0  # 胡牌局数
        
        # 决策碰/杠/胡/弃牌相关状态
        self.decision_result:DecisionResult = None  # 决策结果
        self.decision_request:DecisionRequest = None  # 决策请求

        # 玩家相关状态
        self.turn_start_time = 0  # 玩家回合开始时间
        
        # 记录上次的人类玩家名字，用于判断是否需要重新初始化玩家数据
        self.last_human_player_name = None

        # 游戏状态更新函数映射
        self.update = {
            GameState.GAME_START: self.game_start,
            GameState.WAIT_PHASE: self.wait_phase,
            GameState.DRAW_TILE_PHASE: self.draw_tile_phase,
            GameState.DISCARD_TILE_PHASE: self.discard_tile_phase,
            GameState.GANG_PHASE: self.gang_phase,
            GameState.DRAW_AFTER_GANG_PHASE: self.draw_after_gang_phase,
            GameState.REPAO_PHASE: self.repao_phase,
            GameState.GAME_OVER: self.game_over
        }

    def initialize_manager(self):
        """初始化游戏管理器、玩家列表"""
        # 检查当前人类玩家名字是否与上次相同，如果相同则不需要重新初始化
        if self.players:  # 如果已有玩家，检查人类玩家名字是否相同
            # 获取当前人类玩家
            current_human = next((p for p in self.players if p.is_human), None)
            if current_human and current_human.name == self.settings.human:  # 如果人类玩家名字未变，跳过初始化
                return
        
        # 新建玩家列表
        # 1. 创建人类玩家（东家）
        avatar_dir = get_resource_path('resource/avatar')
        
        # 检查是否已有玩家，如果有则保留人类玩家的分数
        existing_human_score = None
        if self.players:
            existing_human = next((p for p in self.players if p.is_human), None)
            if existing_human:
                existing_human_score = existing_human.score
        
        human_player = HumanPlayer(name=self.settings.human, position=self.settings.position_order[0])
        human_player.time_limit = self.settings.human_time_limit

        # 设置人类玩家性别
        human_player.gender = 'girl' if self.settings.human in self.settings.players_girl else 'boy'
        human_player.is_girl = True if human_player.gender == 'girl' else False
        human_player.avatar = os.path.join(avatar_dir,human_player.gender, f"{self.settings.human}.jpg")        
        
        # 如果有现有分数，使用现有分数初始化新的人类玩家
        if existing_human_score is not None:
            human_player.score = existing_human_score
            human_player.previous_score = existing_human_score
            human_player.starting_score = existing_human_score
        
        name_length = len(self.settings.human)

        # 2. 创建3个AI玩家
        ai_players = []
        available_positions = self.settings.position_order[1:]  # 排除东家
        
        # 确定人类玩家的性别
        human_name = self.settings.human
        human_is_girl = human_name in self.settings.players_girl
        
        # 过滤掉人类玩家名称，确保AI名称不重复
        available_boys = [name for name in self.settings.players_boy if name != human_name and len(name)==name_length]
        available_girls = [name for name in self.settings.players_girl if name != human_name and len(name)==name_length]
        
        # 选择AI玩家，确保男2女2配置
        # 总共有4个玩家，人类+3个AI，所以如果人类是男孩，AI需要1男2女；如果人类是女孩，AI需要2男1女
        if human_is_girl:
            # 人类是女孩，AI需要2男1女
            selected_boys = random.sample(available_boys, 2)  # 选择2个男孩
            selected_girls = random.sample(available_girls, 1)  # 选择1个女孩
        else:
            # 默认AI配置为1男2女
            selected_boys = random.sample(available_boys, 1)
            selected_girls = random.sample(available_girls, 2)
        
        # 组合AI玩家名单并随机打乱
        selected_ai_names = selected_boys + selected_girls
        random.shuffle(selected_ai_names)
        
        # 创建AI玩家/设置AI版本
        human_ai_version = int(self.settings.human_ai_version)
        ai_list = [MajiangAI0(),MajiangAI1()]
        human_player.simple_ai = ai_list[human_ai_version]
        human_player.ai_version = f"玩家{human_ai_version}"
        opponent_ai_version_list = self.settings.opponent_ai_version_list
        
        # 保留现有AI玩家的分数（如果有）
        existing_ai_scores = {}
        if self.players:
            for p in self.players:
                if not p.is_human:
                    existing_ai_scores[p.name] = p.score
        
        for i in range(3):
            ai_player = AIPlayer(name=selected_ai_names[i], position=available_positions[i])
            ai_player.time_limit = self.settings.ai_time_limit
            index = int(opponent_ai_version_list[i])
            ai_player.simple_ai = ai_list[index]
            ai_player.ai_version = f"AI-{index}"
            
            # 设置AI玩家性别
            if selected_ai_names[i] in self.settings.players_boy:
                ai_player.gender = 'boy'
                ai_player.is_girl = False
            else:
                ai_player.gender = 'girl'
                ai_player.is_girl = True
            
            ai_player.avatar = os.path.join(avatar_dir, ai_player.gender, f"{selected_ai_names[i]}.jpg")
            
            # 如果有现有分数，使用现有分数初始化新的AI玩家
            if selected_ai_names[i] in existing_ai_scores:
                ai_player.score = existing_ai_scores[selected_ai_names[i]]
                ai_player.previous_score = existing_ai_scores[selected_ai_names[i]]
                ai_player.starting_score = existing_ai_scores[selected_ai_names[i]]
            
            ai_players.append(ai_player)

        self.players = [human_player] + ai_players
        position_order = self.settings.position_order # 按东南西北顺序重新排列玩家
        self.players.sort(key=lambda p: position_order.index(p.position))
        
        # 保存当前人类玩家名字，用于下次判断
        self.last_human_player_name = self.settings.human

    def initialize_test_data(self):
        """初始化测试数据"""
        self.banker = self.players[0]
        self_name = self.players[0].name
        opposite_name = self.players[2].name
        after_name = self.players[1].name
        before_name = self.players[3].name
        for i, player in enumerate(self.players):
            if i == 0:  # 自家
                player.hand['concealed'] = ['4万','4万','4万','6万','6万', '7万', '8万', '9万','9万','9万', '1条', '2条', '3条']
                player.hand['exposed'] = []
                player.discard_tiles = []
                player.tags = []

            elif i == 1:  # 下家
                player.hand['concealed'] = ['4万','4万','4万','5万','6万', '7万', '8万', '9万','9万','9万', '1条', '1条', '1条']
                player.hand['exposed'] = []
                player.discard_tiles = []
                player.tags = []
            elif i == 2:  # 对家
                player.hand['concealed'] = ['4万','4万','4万','6万','6万', '7万', '8万', '9万','9万','9万', '3条', '3条', '3条']
                player.hand['exposed'] = []
                player.discard_tiles = []
                player.tags = []
            elif i == 3:  # 上家
                player.hand['concealed'] = ['4万','4万','4万','6万','6万', '7万', '8万', '9万','9万','9万', '2条', '2条', '3条']
                player.hand['exposed'] = []
                player.discard_tiles = []
                player.tags = []

        self.majiang_tiles.insert(0, '4万')
        
        # 整理所有玩家的手牌
        for player in self.players:
            player.sort_hand()

    def initialize_game(self, test_mode=False):
        """初始化游戏:牌堆\庄家、重置玩家数据"""

        # 初始化牌堆
        self.majiang_tiles = TILES.copy()
        random.shuffle(self.majiang_tiles)

        self.current_player_index = -1  # 当前玩家索引
        self.last_player_index = -1  # 上一个玩家索引
        self.draw_tile = None  # 当前打出的牌
        self.discard_tile = None  # 当前弃牌的牌
        self.gang_tile = None  # 当前杠牌的牌
        self.hot_tile = None  # 当前热炮牌

        # 选择庄家：上局赢家或随机选择
        self.banker = self.players[random.randint(0, len(self.players) - 1)] if not self.winner else self.winner[0]
        self.banker = self.banker if self.banker in self.players else self.players[random.randint(0, len(self.players) - 1)]
        banker_index = self.players.index(self.banker)
        ordered_players = self.players[banker_index:] + self.players[:banker_index]
        self.current_player_index = self.players.index(self.banker) # 把庄家设置为当前玩家
        print(f"庄家: {self.banker.name}")
        print(f"轮次顺序: {' -> '.join([p.name for p in ordered_players])}")

        self.winner: List[Player] = []  #初始化赢家
        self.winner_check_indexes = []  # 检查胡牌玩家索引列表,处理多玩家胡牌场景检查
        self.reject_hu = False  # 是否拒绝胡牌,处理弃牌触发可胡但是玩家拒绝胡牌的场景
        #鸡牌标记
        self.HENGJI_ROUND = False  # 是否是鸡牌轮
        self.hengji_start_player_index = -1  # 鸡牌轮开始玩家索引
        self.hengji_player_indexes = []  # 鸡牌轮玩家索引列表
        
        # 重置所有玩家数据后，发13张牌
        for player in self.players:
            player.reset()
            # 发13张牌
            for _ in range(13):
                if self.majiang_tiles:
                    tile = self.majiang_tiles.pop(0)
                    player.add_tile(tile)
            player.sort_hand()

        # 测试模式开启时，初始化测试数据：麻将牌、玩家手牌（覆盖上述发牌逻辑）、弃牌区、庄家等（根据测试目的定制）
        if test_mode:
            self.initialize_test_data()
        

        # 更新游戏状态为游戏开始
        self.is_game_over = False
        self.game_state = GameState.GAME_START
        print("游戏开始！\n")

    def is_game_state(self, state: GameState):
        """检查当前游戏状态是否匹配
        
        Args:
            state (GameState): 要检查的游戏状态
            
        Returns:
            bool: 如果当前状态匹配则返回True，否则返回False
        """
        return self.game_state == state

    def is_current_player_human(self):
        """检查当前玩家是否为人类玩家
        
        Returns:
            bool: 如果当前玩家为人类玩家则返回True，否则返回False
        """
        return self.players[self.current_player_index].is_human

    def turn_switch_to_human(self):
        """检查是否为人类玩家回合切换
        
        Returns:
            bool: 如果为人类玩家回合切换则返回True，否则返回False
        """

        players = self.players
        last_player = players[self.last_player_index]
        current_player = self.get_current_player()

        return (not last_player.is_human) and current_player.is_human

    def turn_switch_from_human(self):
        """检查是否为人类玩家回合切换
        
        Returns:
            bool: 如果为人类玩家回合切换则返回True，否则返回False
        """

        players = self.players
        last_player = players[self.last_player_index]
        current_player = self.get_current_player()

        return last_player.is_human and (not current_player.is_human)

    def change_game_state(self, state: GameState):
        """改变游戏状态
        
        Args:
            state (GameState): 要设置的游戏状态
        """
        self.LAST_STATE = self.game_state
        self.game_state = state

    def _draw_tile(self):
        """玩家摸牌
        Returns:
            str: 摸到的牌，如果牌墙为空则返回None
        """
        if not self.majiang_tiles:
            return None
        # 从牌堆顶部摸一张牌
        return self.majiang_tiles.pop(0)

    def get_current_player(self):
        """获取当前玩家
        
        Returns:
            Player: 当前玩家对象
        """
        return self.players[self.current_player_index]

    def get_current_player_index(self):
        """获取当前玩家索引
        
        Returns:
            int: 当前玩家的索引
        """
        return self.current_player_index

    def get_players(self):
        """获取所有玩家
        
        Returns:
            list: 包含所有玩家对象的列表
        """
        return self.players

    def get_human_player(self):
        """获取人类玩家"""
        for player in self.players:
            if player.is_human:
                return player
        return None

    def get_remaining_tiles_count(self):
        """获取剩余牌数
        
        Returns:
            int: 剩余牌数
        """
        return len(self.majiang_tiles)

    def check_and_display_ting(self, player):
        """
        检查并显示玩家是否听牌
        
        Args:
            player: 要检查的玩家
        """
        # 收集所有已使用的牌（所有玩家的弃牌）
        all_used_tiles = []
        for p in self.players:
            if p == player:
                all_used_tiles.extend(p.hand['concealed'])
            all_used_tiles.extend([g for g in p.hand['exposed']])
            all_used_tiles.extend(p.discard_tiles)
        
        # 使用Rule检查听牌
        is_ting, ting_tiles = self.rule.check_ting(player.hand,all_used_tiles)
        
        if is_ting and ting_tiles:
            # 按听牌类型分组
            ting_by_type = {}
            for win_type, tile, remaining in ting_tiles:
                win_type_str = ''.join([t.value for t in win_type])
                if win_type_str not in ting_by_type:
                    ting_by_type[win_type_str] = f"{tile}剩{remaining}张"
                else:
                    ting_by_type[win_type_str] += f"，{tile}剩{remaining}张"
            
            # 格式化每种听牌类型的信息
            ting_info = []
            for win_type, tiles_info in ting_by_type.items():
                ting_info.append(f"{win_type}({tiles_info})")

            return "，".join(ting_info)

    def check_other_players_can_hu(self,current_player,tile,default_passport=None):
        """检查其他玩家是否可以胡牌
        Args:
            tile (str): 要检查的牌
        Returns:
            bool: 如果其他玩家可以胡牌则返回True，否则返回False
            list: 如果其他玩家可以胡牌则返回胡牌玩家索引列表，否则返回空列表
        """
        # 检查其他玩家是否可以胡牌
        winner = []
        players = self.players
        human_toast_shown = False  # 标记是否已经显示过人类玩家的toast提示
        for player in players:
            if player == current_player:
                continue
            can_hu,_ = self.rule.check_hu(player.hand,tile)
            if player != current_player and can_hu:
                pass_port,win_str,tiles = self.rule.has_passport(player.hand,player.tags)
                if pass_port and (tile in tiles or '杠' in win_str):
                    winner.append(self.players.index(player))
                elif default_passport:  #热炮/抢杠胡等默认通行证
                    winner.append(self.players.index(player))
                else:
                    print(f"❌ [{player.name}] 没有通行证，不能吃胡 [{tile}]({current_player.name})")
                    # 如果是人类玩家，显示toast提示，只显示一次
                    if player.is_human and not human_toast_shown:
                        self.toast_callback(f"{player.name} 没有通行证，不能吃胡 [{tile}]")
                        human_toast_shown = True  # 标记已经显示过toast提示

        return (False,[]) if not winner else (True,winner)

    def check_other_players_can_gang(self,current_player,tile):
        """检查其他玩家是否可以杠牌
        
        Args:
            tile (str): 要检查的牌
            
        Returns:
            bool: 如果其他玩家可以杠牌则返回True，否则返回False
        """
        for player in self.players:
            if player != current_player and self.rule.can_gang_others(player.hand,tile) and len(self.majiang_tiles)>0:
                if self.had_player_BAOJIAO(player):
                    print(f"❌{player.name}已经报叫，不可以杠牌。")
                    return False,-1
                else:
                    return True,self.players.index(player)
        return False,-1

    def check_other_players_can_peng(self,current_player,tile):
        """检查其他玩家是否可以碰牌
        
        Args:
            tile (str): 要检查的牌
            
        Returns:
            bool: 如果其他玩家可以碰牌则返回True，否则返回False
        """
        for player in self.players:
            if player != current_player and self.rule.can_peng(player.hand,tile):
                if self.had_player_BAOJIAO(player):
                    print(f"❌{player.name}已经报叫，不可以碰牌。")
                    return False,-1
                else:
                    return True,self.players.index(player)
        return False,-1

    def reset_current_card(self):
        """重置当前玩家的牌"""
        self.discard_tile = None
        self.gang_tile = None
        self.hot_tile = None
        self.recommend_option = None
        self.recommend_tile = None
        self.recommend_reason = None

    def change_current_player(self,index):
        """改变当前玩家
        
        Args:
            index (int): 要设置的当前玩家索引
        """
        self.reset_current_card()
        self.last_player_index = self.current_player_index
        self.current_player_index = index
        current_player = self.players[index]
        if current_player.is_human:
            current_player.time_limit = self.settings.human_time_limit
        else:
            current_player.time_limit = self.settings.ai_time_limit
        self.turn_start_time = time.time()
        return current_player

    def change_to_next_player(self):
        """改变当前玩家为下家"""
        self.change_current_player((self.current_player_index + 1) % 4)

    def get_cards_for_ai(self,player_index):
        """获取玩家当前可用的牌
        
        Args:         
            current_player_index (int): 当前玩家索引
        Returns:
            hand: 自己手牌
            all_discards: 四家出牌堆，每家一个列表，顺序为[上家, 自己, 下家, 对家]
            all_exposed: 其他三家已副露列表，顺序为[上家, 自己, 下家, 对家]
            chicken_tiles: 鸡牌列表 
        """
        players = self.players
        index = player_index
        all_exposed = [players[(index + i-1) % 4].get_exposed_hand() for i in range(4)]

        cards = {
            "hand": players[index].hand,
            "all_discards": [players[(index + i-1) % 4].get_discard_tiles() for i in range(4)],
            "all_exposed": all_exposed,
            "chicken_tiles": self.rule.get_chicken_tiles()
        }
        return cards

    def get_cards_for_ai0(self,player_index):
        """获取玩家当前可用的牌，需要对exposed做扁平化处理
        
        Args:
            current_player_index (int): 当前玩家索引
        Returns:
            hand: 自己手牌
            all_discards: 四家出牌堆，每家一个列表，顺序为[上家, 自己, 下家, 对家]
            all_exposed: 其他三家已副露列表，顺序为[上家, 自己, 下家, 对家]
            chicken_tiles: 鸡牌列表 
        """
        players = self.players
        index = player_index
        hand = players[index].hand
        hand["exposed"] = [tile for group in hand["exposed"] if group["tiles"] for tile in group["tiles"]]
        all_exposed = []
        all_discards = []
        for i in range(4):
            all_exposed.extend([tile for group in players[(index + i-1) % 4].get_exposed_hand() if group["tiles"] for tile in group["tiles"]])
            all_discards.extend(players[(index + i-1) % 4].get_discard_tiles())
        
        cards = {
            "hand": hand,
            "all_discards": all_discards,
            "all_exposed": all_exposed,
            "chicken_tiles": self.rule.get_chicken_tiles()
        }
        return cards
    
    def had_player_BAOJIAO(self,player):
        """检查是否有玩家报叫
        
        Args:
            player (Player): 要检查的玩家
            
        Returns:
            bool: 如果有玩家报叫则返回True，否则返回False
        """
        return player.has_tag(Tag.BAO_JIAO)

    def check_chicken_tile(self,tile):
        """检查是否是鸡牌
        
        Args:
            tile (str): 要检查的牌
            
        Returns:
            bool: 如果是鸡牌则返回True，否则返回False
        """
        return tile in self.rule.get_chicken_tiles()

    def check_chicken_tile_type(self,tile,first_discard):
        """检查鸡牌类型
        
        Args:
            tile (str): 要检查的牌
            
        Returns:
            str: 冲锋鸡/横鸡/幺鸡
        """
        if not self.check_chicken_tile(tile):
            return None
        if first_discard:
            return Tag.CHONG_FENG_JI
        elif self.HENGJI_ROUND:
            return Tag.HENG_JI
        else:
            return Tag.YAO_JI

    def print_discard_tile(self,discard_tile):
        current_player = self.players[self.current_player_index]

        # 检查鸡牌类型
        # 如果是当前玩家的第一次出牌，且不是鸡牌，且不是横鸡牌，且不是幺鸡牌，且不是冲锋鸡牌，
        # 当前玩家==横鸡牌的开始玩家，也就是横鸡玩家再次出牌，即结束横鸡轮次
        if self.HENGJI_ROUND:
            if self.current_player_index == self.hengji_start_player_index:
                print(f"[{current_player.name}] 再次出牌，结束 [横鸡轮次]")
                self.HENGJI_ROUND = False
            elif self.current_player_index in self.hengji_player_indexes:
                print(f"[{current_player.name}] 再次出牌，结束 [横鸡轮次]")
                self.HENGJI_ROUND = False

        hot_flag = self.hot_tile and (self.hot_tile == discard_tile)
        action = "热炮" if hot_flag else "打出"
        safe_flag = "✅ （热炮安全）" if hot_flag else ""
        reason = current_player.recommend_reason if current_player.is_human else ""
        reason = reason if current_player.is_human and reason else ""

        #如果是鸡牌，判定幺鸡、横鸡、冲锋鸡
        if self.check_chicken_tile(discard_tile):
            # 不是该玩家第一次出牌，且不是横鸡轮次，且横鸡轮次未开启过（即self.hengji_player_indexes为空），则当前玩家为横鸡牌的开始玩家，开始横鸡轮次
            if not current_player.first_discard and not self.HENGJI_ROUND and not self.hengji_player_indexes:
                self.hengji_player_indexes.append(self.current_player_index)
                self.HENGJI_ROUND = True
                print(f"[{current_player.name}] 首出横鸡，开启 [横鸡轮次]")
            elif self.HENGJI_ROUND and self.current_player_index not in self.hengji_player_indexes:
                self.hengji_player_indexes.append(self.current_player_index)
            JI_tag = self.check_chicken_tile_type(discard_tile,current_player.first_discard)
            tag = current_player.add_tag(JI_tag)
            source_info = f"({tag['source']})" if tag['source'] != "self" else ""
            print(f"[{current_player.name}] {action} [{discard_tile}] {safe_flag} {reason}") 
            print(f"[{current_player.name}] 获得 🏷️  [{JI_tag.value}🐔]{source_info}")
        else:
            print(f"[{current_player.name}] {action} [{discard_tile}] {safe_flag} {reason}")

        # 检查玩家是否听牌
        has_passport, win_types, win_tiles = self.rule.has_passport(current_player.hand,current_player.tags)
        ting_info = self.check_and_display_ting(current_player)
        if ting_info:
            print(f"[{current_player.name}] ✅ 听  牌: {ting_info}")
            current_player.ting_info = ting_info
            if has_passport:
                print(f"[{current_player.name}] ✅ 通行证: {win_types}{' 可以胡：' if win_tiles else ''}{', '.join(win_tiles)}\n")
            else:
                print(f"[{current_player.name}] ❌ 通行证\n")
        else:
            print()

        #弃牌阶段退出前检查听牌、排序手牌，并失效玩家的第一次出牌
        current_player.sort_hand()
        if current_player.is_human:
            current_player.recommend_reason = ""

    def execute_gang(self,is_self_draw,tile):
        
        current_player_index = self.current_player_index
        current_player = self.players[current_player_index]
        can_add_gang = self.rule.can_add_gang(current_player.hand,tile)

        gang_type = "exposed"
        gang_type_str = "明杠"
        if is_self_draw:
            if can_add_gang:
                gang_type = "add"
                gang_type_str = "加杠"
            else:
                gang_type = "self"
                gang_type_str = "自杠"

        #执行杠操作
        last_player = self.players[self.last_player_index]
        source = "self" if is_self_draw else last_player.name
        source_to_show = f"({source}) " if source != "self" else ""               
        tag = Tag.YAO_JI
        
        can_hu,hu_index = self.check_other_players_can_hu(current_player,tile,default_passport="抢杠检查")
        if can_hu and not self.reject_hu:
            hu_player = ",".join([self.players[i].name for i in hu_index])
            print(f"[{hu_player}] 可胡 [{tile}]，但 [{gang_type_str}] 不可抢杠❌")
            self.toast_callback(f"{current_player.name} 自杠，不可抢杠胡 [{tile}]")
        
        if gang_type == "exposed" and self.check_chicken_tile(tile):
            if last_player.has_tag(Tag.CHONG_FENG_JI):
                tag = Tag.CHONG_FENG_JI
            elif last_player.has_tag(Tag.HENG_JI):
                tag = Tag.HENG_JI
            last_player.add_tag(Tag.ZE_REN_JI,current_player.name)
            last_player.change_tag_source(tag,current_player.name)
            # current_player.add_tag(tag,source)  ##20251211,碰鸡不加鸡标签，已经在gang_tile时group中添加tag信息
            # print(f"[{current_player.name}] 获得 🏷️  [{tag.value}🐔]{source_to_show}")
            print(f"[{current_player.name}] {gang_type_str} [{tile}] {source_to_show}🀄")
            print(f"[{last_player.name}] 获得 🏷️  [{Tag.ZE_REN_JI.value}🐔]({current_player.name})")            
        else:
            print(f"[{current_player.name}] {gang_type_str} [{tile}] {source_to_show}🀄")

        current_player.gang_tile(tile,source,gang_type,tag)
        self.change_game_state(GameState.DRAW_AFTER_GANG_PHASE)
        self.draw_tile = None
        
        # 播放杠牌音效
        if self.sound_callback:
            self.sound_callback('action', player=current_player, action_type='gang')

    # 处理决策请求
    def make_decision_request(self,player_index:int,decision_list:list,tile=None)->bool:
        """决定是否胡牌/碰牌/杠牌
        
        Args:
            player_index (int): 要检查的玩家索引
            decision_list (list): 决策类型列表
            tile (str): 要决策操作的牌
            
        Returns:
            bool: 如果决定请求完成则返回True，否则返回False
        """
        self.decision_player_index = player_index
        # 如果已经有决策结果，直接返回该结果
        if self.decision_result.result:
            dc_type = self.decision_result.decision_type
            if dc_type in decision_list or dc_type == DecisionType.CANCEL:
                self.reset_decision_request()
                return self.decision_result.result

        # 否则直接发起决策请求
        else:
            self.decision_request = DecisionRequest(decision_list,player_index,tile)
        
        self.LAST_STATE = self.game_state
        self.change_game_state(GameState.WAIT_PHASE)
        return False

    def have_decision_request(self):
        """检查是否有决策请求
        
        Args:
            decision_type (DecisionType): 要检查的决策类型
        
        Returns:
            bool: 如果有决策请求则返回True，否则返回False
        """
        return self.decision_request.decision_list != [DecisionType.default]

    def reset_decision_request(self):
        """重置决策请求
        """
        self.decision_request = DecisionRequest([DecisionType.default])

    # 处理决策结果
    def get_decision_result(self):
        """获取决策结果
            重置决策请求和结果
        Returns:
            DecisionResult: 当前决策结果
        """
        result = self.decision_result 
        self.reset_decision_request()
        self.reset_decision_result()
        return result

    def have_decision_result(self):
        """检查是否有决策结果
        
        Returns:
            bool: 如果有决策结果则返回True，否则返回False
        """
        return self.decision_result.result

    def reset_decision_result(self):
        """重置决策结果
        """
        self.decision_result = DecisionResult(DecisionType.default,False,None,None)

    def get_decision_list(self,can_hu=False,can_gang=False,can_peng=False)->list:
        """获取决策列表
        
        Args:
            can_hu (bool): 是否可以胡牌
            can_gang (bool): 是否可以杠牌
            can_peng (bool): 是否可以碰牌
        
        Returns:
            list: 决策列表
        """
        decision_list = []
        if can_hu:
            decision_list.append(DecisionType.HU)
        if can_gang:
            decision_list.append(DecisionType.GANG)
        if can_peng:
            decision_list.append(DecisionType.PENG)
        return decision_list

    # 处理胡牌
    def handle_hu(self,hu_index,hu_tile,tile_source_index,hu_type)->bool:
        """处理胡牌
        
        Args:
            hu_index (list): 胡牌玩家索引列表
            hu_tile (str): 胡牌的牌
            tile_source_index (int): 胡牌的牌来源索引
            hu_type (Tag): 胡牌类型
            
        Returns:
            bool: 如果胡牌成功则返回True，否则返回False
        """

        players = self.get_players()
        other_player = players[tile_source_index]

        # 处理自摸胡牌
        # 检查是否是玩家的第一次摸牌,如果是则天胡,否则自摸,如果是最后一张牌自摸，触发妙手回春
        if hu_type == Tag.ZI_MO:
            hu_player = players[hu_index[0]]
            
            # 非第一张牌：自摸，（最后一张牌就是妙手回春）
            if not hu_player.first_draw:
                # 自摸
                if self.get_remaining_tiles_count() != 0:
                    hu_player.add_tag(Tag.ZI_MO)
                    print(f"[{hu_player.name}] 自摸！🎉 ")
                    
                # 妙手回春
                else:
                    hu_player.add_tag(Tag.MIAO_SHOU_HUI_CHUN)
                    print(f"[{hu_player.name}] 妙手回春！🎉🎉🎉 ")

            # 第一张牌自摸就是天胡
            else:
                hu_player.add_tag(Tag.TIAN_HU)
                print(f"[{hu_player.name}] 天胡！🎉🎉🎉 ")

            hand = hu_player.hand.copy()
            hand['concealed'] = hand['concealed'][:-1]
            _,win_type = self.rule.check_hu(hand,hu_tile)
            for wt in win_type:
                hu_player.add_tag(wt)

            hu_player.hu_tile(hu_tile)
            self.winner.append(hu_player)

        #处理点炮胡牌
        elif hu_type == Tag.ZHUO_PAO:
            is_the_last_discard = self.get_remaining_tiles_count() == 0  
            # 点炮者的牌从弃牌中移除 20251212,移除的话牌桌上的指示器会指示空处，且不易看出哪张牌点炮
            # other_player.remove_discard_tile(hu_tile)
            # 处理多个赢家
            print(f"[{other_player.name}] 打出 [{hu_tile}] 放炮！🔥")
            for index in hu_index:
                hu_player:Player = players[index]                    
                _,passs_port,_ = self.rule.has_passport(hu_player.hand,hu_player.tags)
                if is_the_last_discard:
                    hu_player.add_tag(Tag.HAI_DI_LAO_YUE)
                    print(f"🎉🎉🎉{hu_player.name} 海底捞月！🎉🎉🎉")
                    passs_port = passs_port + " 海底捞月"

                if self.check_chicken_tile(hu_tile):
                    other_player.add_tag(Tag.ZE_REN_JI,source=other_player.name)
                
                _,win_type = self.rule.check_hu(hu_player.hand,hu_tile)
                for wt in win_type:
                    hu_player.add_tag(wt,source=other_player.name)

                print(f"[{hu_player.name}] 捉炮！🎉 (通行证：{passs_port})")
                hu_player.add_tag(Tag.ZHUO_PAO,source=other_player.name)
                hu_player.hu_tile(hu_tile)
                other_player.add_tag(Tag.FANG_PAO,source=hu_player.name)
                self.winner.append(hu_player)

        # 处理抢杠胡牌
        elif hu_type == Tag.QIANG_GANG_HU:
            other_player:Player = self.players[tile_source_index]
            other_player.discard_tile(hu_tile)
            other_player.remove_discard_tile(hu_tile)
            print(f"[{other_player.name}] 打出 [{hu_tile}] 被抢杠全烧！🔥 ")
            # 处理赢牌玩家
            for index in hu_index:    
                hu_player = self.players[index]

                _,win_type = self.rule.check_hu(hu_player.hand,hu_tile)
                for wt in win_type:
                    hu_player.add_tag(wt,source=other_player.name)

                hu_player.hu_tile(hu_tile)
                print(f"[{hu_player.name}] 抢杠！🎉 ")
                hu_player.add_tag(Tag.QIANG_GANG_HU,source=other_player.name) # 记录抢杠胡玩家标签
                self.winner.append(hu_player)
                other_player.add_tag(Tag.JI_QUAN_SHAO,source=hu_player.name)  # 记录被抢杠玩家为鸡牌全烧
                            
        # 处理杠上开花胡牌
        elif hu_type == Tag.GANG_SAHNG_KAI_HUA:
            
            hu_player = self.get_players()[hu_index[0]]

            _,win_type = self.rule.check_hu(hu_player.hand,hu_tile)
            for wt in win_type:
                hu_player.add_tag(wt)

            hu_player.add_tag(Tag.GANG_SAHNG_KAI_HUA) # 记录杠上开花玩家标签
            hu_player.hu_tile(hu_tile)
            print(f"[{hu_player.name}] 杠上开花！🎉🎉🎉")
            self.winner.append(hu_player)
        
        # 处理热炮胡牌
        elif hu_type == Tag.ZHUO_RE_PAO:
            other_player = self.players[tile_source_index]# 播放热炮胡音效
            # 热炮牌其实还未打出，这里要将点炮者的牌从手牌中移除
            other_player.discard_tile(hu_tile)
            # 处理赢牌玩家
            print(f"[{other_player.name}] 打出 [{hu_tile}] 被热炮全烧！🔥 ")
            for index in hu_index:
                hu_player = self.players[index]

                _,win_type = self.rule.check_hu(hu_player.hand,hu_tile)
                for wt in win_type:
                    hu_player.add_tag(wt,source=other_player.name)

                hu_player.add_tag(Tag.ZHUO_RE_PAO,source=other_player.name) # 记录热炮胡玩家标签
                print(f"[{hu_player.name}] 捉热炮！🎉 ")
                hu_player.hu_tile(hu_tile)
                self.winner.append(hu_player)
                other_player.add_tag(Tag.JI_QUAN_SHAO,source=hu_player.name)  # 记录放热炮玩家为鸡牌全烧
                
        hu_num = len(self.winner)
        # 检查是否一炮双响
        if hu_num==2:
            source = f"{self.winner[0].name}、{self.winner[1].name}"
            other_player.add_tag(Tag.ONE_TILE_DOUBLE_BOOM,source=source)  # 记录放炮玩家一炮双响
            print(f"{other_player.name} 打出的 [{hu_tile}] [{Tag.ONE_TILE_DOUBLE_BOOM.value}]")

        # 检查是否一炮三响
        elif hu_num==3:
            source = f"{self.winner[0].name}、{self.winner[1].name}、{self.winner[2].name}"
            other_player.add_tag(Tag.ONE_TILE_TRIBLE_BOOM,source=source)  # 记录放炮玩家一炮三响
            print(f"{other_player.name} 打出的 [{hu_tile}] [{Tag.ONE_TILE_TRIBLE_BOOM.value}]")

        # 没人胡牌
        if hu_num==0:
            return False

        # 结束游戏
        self.change_game_state(GameState.GAME_OVER)
        return True

    def make_hu_decision(self,hu_index,tile,other_player_index,hu_type)->bool:
        """处理多玩家胡牌场景,根据玩家决策处理胡牌
        
        Args:
            hu_index (list): 胡牌玩家索引列表
            tile (Tile): 胡牌的牌
            current_player_index (int): 当前玩家索引
            hu_type (Tag): 胡牌类型
        
        Returns:
            bool: 是否完成处理多玩家胡牌决策
        """
        players = self.get_players()
        for index in hu_index:
            if index in self.winner_check_indexes:
                continue
            if not self.make_decision_request(index,[DecisionType.HU],tile):
                return False
            if self.get_decision_result().result:
                self.winner.append(players[index])
                self.reset_decision_result()
            self.winner_check_indexes.append(index)
            if len(self.winner_check_indexes) == len(hu_index):
                hu_index = [players.index(player) for player in self.winner]
                self.winner_check_indexes = []
                self.winner = []
                if self.handle_hu(hu_index,tile,other_player_index,hu_type):
                    return True
        return False

    def print_game_result(self):
        """打印游戏结果"""
        # 所有玩家手牌信息
        players = self.get_players()
        for p in players:            
            p.print_hand()
            p.print_result()

        # 输出游戏详情到命令行
        print("\n" + "="*60)
        print("游戏详情")
        print("="*60)
        
        # 计算流局率
        total_games = self.total_games if hasattr(self, 'total_games') else 1
        draw_games = self.draw_games if hasattr(self, 'draw_games') else 0
        draw_rate = (draw_games / total_games * 100) if total_games > 0 else 0
        
        print(f"总局数: {total_games}   流局数: {draw_games}   流局率: {draw_rate:.1f}%")
        
        # 按分数排序玩家
        sorted_players = sorted(players, key=lambda p: p.score, reverse=True)
        
        print("\n排行榜:")
        for player in sorted_players:
            # 计算本局获得的分数
            current_round_score = player.result.get('total_ji', 0) if hasattr(player, 'result') else 0
            # 显示积分计算式
            print(f"{player.name}(AI-{player.ai_version}): {player.score:>4} = {player.previous_score:>4} {current_round_score:<+3}")
            print(f"  胡牌:   {player.win_count}局/{player.win_rate:.2f}%   冲鸡: {player.gain_ji_count}分/{player.gain_ji_rate:.2f}%")
            print(f"  献胡:   {player.OfferingWin_count}局/{player.OfferingWin_rate:.2f}%   丢鸡: {player.loss_ji_count}分/{player.loss_ji_rate:.2f}%\n")

        # 输出胡牌类型统计
        print("\n胡牌类型统计:")
        for tag, count in self.hu_type.items():
            print(f"  {tag.value}: {count}局")

        print("="*60)

    def check_concealed_ji(self,player:Player)->tuple:
        """检查玩家弃牌的鸡牌数量
        
        Args:
            player (Player): 玩家对象
        
        Returns:
            int: 弃牌的鸡牌数量
        """
        reason = []
        concealed_ji = sum([1 for t in player.get_concealed_hand() if self.check_chicken_tile(t)])
        jin_ji = 2 if self.fanji_tile in ['9条','2条'] else 1
        if concealed_ji:
            reason.append(f"[手牌幺鸡]+{concealed_ji*jin_ji}")

        return concealed_ji,reason

    def check_hu_ji(self,player:Player,other_player:Player=None)->tuple:
        """检查玩家胡牌的鸡牌数量
        
        Args:
            player (Player): 玩家对象
        
        Returns:
            tuple: (胡牌的鸡牌数量, 胡牌鸡牌来源)
        """
        majiang_scores = self.settings.majiang_scores
        self_hu = majiang_scores['self_hu']
        qiuren_hu = majiang_scores['qiuren_hu']
        hu_type = majiang_scores['hu_type']
        hu_ji = 0
        reason = []
        tags = player.get_tags()

        self_hu_tag = [t for t in tags if t['tag'] in self_hu.keys()]
        qiuren_hu_tag = [t for t in tags if t['tag'] in qiuren_hu.keys()]
        hu_type_tag = [t for t in tags if t['tag'] in hu_type.keys()]

        hu_self_num = sum([self_hu[t['tag']] for t in tags if t['tag'] in self_hu.keys()])
        hu_qiuren_num = sum([qiuren_hu[t['tag']] for t in tags if t['tag'] in qiuren_hu.keys()])
        hu_type_num = sum([hu_type[t['tag']] for t in tags if t['tag'] in hu_type.keys()])
        hu_ji += hu_self_num + hu_qiuren_num + hu_type_num

        #检查自摸胡牌标签和求人胡牌标签是否同时存在
        if self_hu_tag and qiuren_hu_tag:
            print(f"⚠️ [{player.name}] 同时存在自摸胡牌标签和求人胡牌标签")
            raise ValueError("同时存在自摸胡牌标签和求人胡牌标签")
        
        #传入了other_player，检查player与other_player的相对胡牌标签
        if other_player and hu_type_tag:
            
            if self_hu_tag:
                reason.append(f"[{hu_type_tag[0]['tag'].value}][{self_hu_tag[0]['tag'].value}]+{hu_ji}")
            elif qiuren_hu_tag:
                if hu_type_tag[0]['source'] == other_player.name:
                    reason.append(f"[{hu_type_tag[0]['tag'].value}][{qiuren_hu_tag[0]['tag'].value}]+{hu_ji}")
                else:
                    hu_ji = 0
        
        #没有传入other_player，检查player的胡牌标签
        elif hu_type_tag:

            if self_hu_tag:
                reason.append(f"[{hu_type_tag[0]['tag'].value}][{self_hu_tag[0]['tag'].value}]+{hu_ji}")
            elif qiuren_hu_tag:
                reason.append(f"[{hu_type_tag[0]['tag'].value}][{qiuren_hu_tag[0]['tag'].value}]({qiuren_hu_tag[0]['source']})+{hu_ji}")
            
        return hu_ji,reason

    def check_gang_ji(self,player:Player,other_player:Player=None)->tuple:
        """检查玩家杠牌的鸡牌数量
            Args:
                player (Player): 玩家对象
            Returns:
                    tuple: (杠牌的鸡牌数量, 杠牌鸡牌来源)
        """
        
        majiang_scores = self.settings.majiang_scores
        gang_score = majiang_scores['other_tag'][Tag.GANG]
        gang_ji = 0
        reason = []
        if other_player:
            for g in player.get_exposed_hand():
                # 鸡牌的分数已经在check_exposed_ji中计算
                if self.check_chicken_tile(g["tiles"][0]):
                    gang_ji += 0            
                # 计算其他玩家杠牌的鸡牌数量
                elif g["is_gang"] and (g['source'] == other_player.name or g['source'] == "self"):
                    gang_ji += gang_score
                    reason.append(f"[杠{g['tiles'][0]}]+{gang_score}")
        else:
            for g in player.get_exposed_hand():
                # 鸡牌的分数已经在check_exposed_ji中计算
                if self.check_chicken_tile(g["tiles"][0]):
                    gang_ji += 0            
                # 计算其他玩家杠牌的鸡牌数量
                elif g["is_gang"]:
                    gang_ji += gang_score
                    reason.append(f"[杠{g['tiles'][0]}]({g['source'] if g['source'] != 'self' else '自杠'})+{gang_score}")

        return gang_ji,reason

    def check_exposed_ji(self,player:Player,other_player:Player=None)->tuple:
        """检查玩家暴露的鸡牌数量
        
        Args:
            player (Player): 玩家对象
        
        Returns:
            tuple: (暴露的鸡牌数量, 暴露鸡牌来源)
        """        
        majiang_scores = self.settings.majiang_scores
        ji_type = majiang_scores['ji_type']        
        jin_ji = 2 if self.fanji_tile in ['9条','2条'] else 1
        exposed_ji = 0
        reason = []
        # 传入了other_player，检查player与other_player的相对暴露牌鸡数
        if other_player:
            for g in player.get_exposed_hand():
                if self.check_chicken_tile(g["tiles"][0]):
                    ji_num = ji_type[g['ji_tag']]
                    if g["is_gang"] and g['source'] == other_player.name:
                        exposed_ji = 3 + (3 + ji_num)*jin_ji
                        reason.append(f"杠[{g['ji_tag'].value}]+{exposed_ji}")
                    elif g["is_gang"]:
                        exposed_ji = 3 + 4*jin_ji
                        reason.append(f"杠[幺  鸡]+{exposed_ji}")
                    elif g['source'] == other_player.name:
                        exposed_ji = (2 + ji_num)*jin_ji
                        reason.append(f"碰[{g['ji_tag'].value}]+{exposed_ji}")
                    else:
                        exposed_ji = 3*jin_ji
                        reason.append(f"碰[幺  鸡]+{exposed_ji}")
            
        # 没有传入other_player，检查player的暴露牌鸡数,仅用在计算包鸡的个数
        else:
            for g in player.get_exposed_hand():
                if self.check_chicken_tile(g["tiles"][0]):
                    ji_num = ji_type[g['ji_tag']]
                    if g["is_gang"]:
                        exposed_ji = 3 + (3 + ji_num)*jin_ji
                        reason.append(f"杠[{g['ji_tag'].value}]({g['source']})+{exposed_ji}")
                    else:
                        exposed_ji = (2 + ji_num)*jin_ji
                        reason.append(f"碰[{g['ji_tag'].value}]({g['source']})+{exposed_ji}")

        # 检查玩家的打出的鸡牌得分
        concealed_ji = 0
        Tags = [Tag.CHONG_FENG_JI,Tag.HENG_JI,Tag.YAO_JI]
        majiang_scores = self.settings.majiang_scores
        ji_type = majiang_scores['ji_type']
        for tag in player.tags:
            if tag['tag'] in Tags and tag['source'] == "self":
                concealed_ji += ji_type[tag['tag']]*jin_ji
                reason.append(f"[{tag['tag'].value}]+{ji_type[tag['tag']]}")
        
        if jin_ji==2:
            reason = reason.append("(金鸡)")

        return exposed_ji+concealed_ji,reason

    def check_fanji_ji(self,player:Player)->tuple:
        """检查玩家翻鸡牌的鸡牌数量
            Args:
                player (Player): 玩家对象
            Returns:
                    tuple: (翻鸡牌的鸡牌数量, 翻鸡牌鸡牌来源)
        """
        fanji_ji = 0
        reason = []
        hand = [tile for group in player.hand['exposed'] for tile in group['tiles']] + player.hand['concealed']
        for tile in self.fanji_tiles:
            fanji_ji += hand.count(tile)
            if hand.count(tile) > 0:
                reason.append(f"翻鸡[{tile}]+{hand.count(tile)}")
        return fanji_ji,reason

    def count_ji_between_players(self,player:Player,other_player:Player=None)->tuple:
        """
        计算player与other_player之间的鸡牌数量，包括胡鸡、杠鸡、暴露鸡和弃牌鸡
        当other_player为None时，计算player的总鸡牌数量
        返回总鸡牌数量和来源说明
        """
        hu_ji,hu_ji_reason = self.check_hu_ji(player,other_player)
        gang_ji,gang_ji_reason = self.check_gang_ji(player,other_player)
        exposed_ji,exposed_ji_reason = self.check_exposed_ji(player,other_player)
        concealed_ji,concealed_ji_reason = self.check_concealed_ji(player)
        fanji_ji,fanji_ji_reason = self.check_fanji_ji(player)

        if player.has_tag(Tag.JI_QUAN_SHAO): #鸡全烧，杠牌都不算鸡
            if other_player:
                exposed_ji = 0
                exposed_ji_reason = []
                return (0,0,0),([],[],[f"[{Tag.JI_QUAN_SHAO.value}]"])
            ji = exposed_ji+concealed_ji
            ji_reason = concealed_ji_reason+exposed_ji_reason+[f"[{Tag.JI_QUAN_SHAO.value}]-{ji}"]
            gang_ji_reason += [f"[{Tag.JI_QUAN_SHAO.value}]-{gang_ji}"]
            reason = (hu_ji_reason,gang_ji_reason,ji_reason)
            return (0,0,0),reason

        jiaopai,_ =  (True,"") if player in self.winner else self.rule.check_ting(player.hand,[])
        if not jiaopai: #如果没有叫牌，只计算包鸡
            if exposed_ji:  #如果有暴露牌或打出牌，算包鸡
                player.add_tag(Tag.ZAO_BAO_JI)
                return (0,0,-exposed_ji),([],[],[f"[包  鸡]{-exposed_ji}"])
            else: #如果没有暴露牌或打出牌，不算包鸡
                return (0,0,0),([],[],[])
        else: #叫牌了
            if not self.winner: #叫牌但是流局(没有赢家)
                return (0,0,0),([],[],[])
            else: #叫牌了，没有流局
                total_ji = (hu_ji,gang_ji,concealed_ji+exposed_ji+fanji_ji)
                reason = (hu_ji_reason,gang_ji_reason,concealed_ji_reason+exposed_ji_reason+fanji_ji_reason)
                return total_ji,reason
        
    def count_ji_diff_between_players(self,player:Player,other_player:Player)->tuple:
        """计算玩家和其他玩家之间的鸡牌数量
        
        Args:
            player (Player): 玩家对象
            other_player (Player): 其他玩家对象
        
        Returns:
            int: 玩家和其他玩家之间的鸡牌数量
        """

        # 计算玩家鸡牌数量
        total_ji,reason = self.count_ji_between_players(player,other_player)
        total_ji = sum(total_ji)
        reason = [i for item in reason for i in item]
        reason = ('我: ' if reason else '') + ','.join(reason)
        
        # 计算其他玩家的鸡牌数量
        other_total_ji,other_reason = self.count_ji_between_players(other_player,player)
        other_total_ji = sum(other_total_ji)
        other_reason = [item.translate(str.maketrans({"+": "-", "-": "+"})) for relist in other_reason for item in relist]
        other_reason = ('Ta: ' if other_reason else '') + ','.join(other_reason)
        
        #计算差值
        ji_diff = total_ji - other_total_ji
        toatal_reason = reason + (',' if other_reason and reason else '') + other_reason

        return ji_diff,toatal_reason

    def get_fanji_tiles(self,tile):
        """获取翻鸡牌"""
        from source.tile import get_tile_value,get_tile_suit,create_tile
        num = get_tile_value(tile)
        suit = get_tile_suit(tile)
        if self.settings.shangxia_ji:
            # 上下鸡，取同花色+1/-1的牌
            return [create_tile((num - 2) % 9 + 1,suit),create_tile(num % 9 + 1,suit)]
        else:
            # 下鸡，取同花色数字+1的牌
            return [create_tile(num % 9 + 1,suit)]

    def count_all(self):
        
        players = self.get_players()
        winner = self.winner
        if winner and self.majiang_tiles and self.settings.fan_ji:
            self.fanji_tile = self.majiang_tiles.pop(0)
            fanji_type = "上下鸡" if self.settings.shangxia_ji else "下鸡"
            self.fanji_tiles = self.get_fanji_tiles(self.fanji_tile)
            jin_ji = True if self.fanji_tile in ['2条','9条'] else False
            print(f"翻鸡({fanji_type}): {' '.join([f'[{tile}]' for tile in self.fanji_tiles])} {'(🐔金鸡🐔)' if jin_ji else ''}")
        
        for player in players:
            #查叫
            jiaopai,_ =  (True,"") if player in winner else self.rule.check_ting(player.hand,[])

            #计算各类型鸡分
            ji,reason = self.count_ji_between_players(player)
            hu_ji,gang_ji,ji = ji
            hu_ji_reason,gang_ji_reason,ji_reason = reason

            result = {
                "jiaopai":jiaopai,
                "total_ji":0,
                "hu_ji":{
                    "num":hu_ji,
                    "source":hu_ji_reason,
                },
                "ji":{
                    "num":ji,
                    "source":ji_reason,
                },
                "gang_ji":{
                    "num":gang_ji,
                    "source":gang_ji_reason,
                },
                "count_with_other_player":[]             
            }
            for p in players:
                if p == player:
                    continue
                ji_diff,ji_reason = self.count_ji_diff_between_players(player,p)
                result["count_with_other_player"].append({
                    "name":p.name,
                    "num":ji_diff,
                    "source":ji_reason,
                })
                result["total_ji"] += ji_diff
            
            player.result = result

    ##### 更新游戏状态入口函数 #####
    def update_game_state(self):
        self.update[self.game_state]()

    # 游戏开始，转摸牌阶段
    def game_start(self):
        self.reset_decision_request()
        self.reset_decision_result()
        self.change_current_player(self.get_current_player_index())
        self.change_game_state(GameState.DRAW_TILE_PHASE)

    # 检查游戏是否结束,流局/输出赢家信息
    def game_over(self):

        #查叫牌
        players:List[Player] = self.get_players()
        winner:List[Player] = self.winner

        # 更新游戏统计信息
        self.total_games += 1
        if winner:
            self.win_games += 1
        else:
            self.draw_games += 1

        # 游戏结束，输出赢家信息
        if winner:
            majiang_score = self.settings.majiang_scores
            winner_str_list = []
            # 播放胡牌音效/输出简单胡牌信息
            for p in winner:
                for tag in p.tags:
                    if tag['tag'] in majiang_score["self_hu"].keys():
                        self.sound_callback('action', player=p, action_type='zi_mo')
                    if tag['tag'] in majiang_score["qiuren_hu"].keys():
                        self.sound_callback('action', player=p, action_type='hu')                     
                    # 统计胡牌类型
                    if tag['tag'] in majiang_score["hu_type"].keys():
                        p.hu_type.setdefault(tag['tag'], 0)
                        p.hu_type[tag['tag']] += 1
                        self.hu_type.setdefault(tag['tag'], 0)
                        self.hu_type[tag['tag']] += 1
                _,winner_str = self.check_hu_ji(p)
                winner_str_list.append(f"{p.name}  ( {', '.join(winner_str)} )")
            print(f"\n游戏结束，🏆 赢家： {'  ，  '.join(winner_str_list)}")
        
        #流局，输出流局信息
        else:
            print(f"牌墙剩余数量: {len(self.majiang_tiles)}")
            self.change_current_player(self.last_player_index)
            print("游戏结束，流局.....")
            
            # 播放流局结束音效
            if self.sound_callback:
                self.sound_callback('game_end', is_draw=True)
        
        # 计算各玩家的鸡牌数量和差值，增加玩家result字段
        self.count_all()

        # 更新所有玩家的实际分数/统计信息
        for player in players:
            # 记录上一局的分数
            player.previous_score = player.score
            # 将本局积分加到玩家的实际分数中
            player.score += player.result.get('total_ji', 0)

            # 更新赢家统计数据: 赢局数
            if player in winner:
                player.win_count += 1

            # 更新点炮玩家的统计数据:放炮/放热炮/被抢杠
            if player.has_tag(Tag.FANG_PAO) or player.has_tag(Tag.JI_QUAN_SHAO):
                player.OfferingWin_count += 1

            jiaopai = player.result.get('jiaopai', False)
            ji = player.result.get('ji', {}).get('num', 0)
            # 更新冲锋鸡和包鸡统计
            if not jiaopai:
                player.loss_ji_count += -ji
            else:
                player.gain_ji_count += ji

            # 计算流局率
            total_games = self.total_games if hasattr(self, 'total_games') else 1
            # 计算胡牌率和点炮率，冲锋鸡率和包鸡率
            total_ji = player.gain_ji_count + player.loss_ji_count
            total_ji = total_ji if total_ji > 0 else 1
            player.win_rate = (player.win_count / total_games * 100)
            player.OfferingWin_rate = (player.OfferingWin_count / total_games * 100)
            player.gain_ji_rate = (player.gain_ji_count / total_ji * 100)
            player.loss_ji_rate = (player.loss_ji_count / total_ji * 100)

        # 控制台打印游戏结果
        # self.print_game_result()

        self.is_game_over = True
        return

    # 等待其他玩家操作阶段,如果已经有玩家决策结果,推进游戏状态
    def wait_phase(self):

        if self.have_decision_result():
            self.reset_decision_request()
            self.change_game_state(self.LAST_STATE)
            self.turn_start_time = time.time()
            return
        
        index = self.decision_player_index
        decision_player: Player = self.get_players()[index]
        decision_request = self.decision_request
        decision_list = decision_request.decision_list
        time_limit = decision_player.time_limit
        time_pass = time.time()-self.turn_start_time
        time_out = time_pass>time_limit
        time_half_out = time_pass>(time_limit/2)

        # 非人类玩家，超时执行,重置玩家计时
        if (not decision_player.is_human) and time_out:
            tile = self.decision_request.tile
            cards = self.get_cards_for_ai(index)
            self.decision_result = decision_player.make_decision(decision_list,tile,cards)
            self.turn_start_time = time.time()

        # 人类玩家，超时执行推荐决策，重置玩家计时
        elif time_out:
            if DecisionType.DISCARD in decision_list:
                option = DecisionType.DISCARD
                tile = decision_player.recommend_tile
                reason = decision_player.recommend_reason
                self.decision_result = DecisionResult(option,True,tile,reason)
            else:
                option = decision_player.recommend_option
                reason = decision_player.recommend_reason
                result = True if option!=DecisionType.default else False
                self.decision_result = DecisionResult(option,result,None,reason)
            self.turn_start_time = time.time()
            return
        
        # 人类玩家，发起决策请求
        elif decision_player.is_human and time_half_out:
            tile = self.decision_request.tile
            cards = self.get_cards_for_ai(index)
            ting_info = self.ting_info
            remain_tiles_count = self.get_remaining_tiles_count()
            option,tile,reason = decision_player.make_decision(decision_list,cards,tile,remain_tiles_count,ting_info)
            decision_player.recommend_option = option
            decision_player.recommend_tile = tile
            decision_player.recommend_reason = f'(AI推荐:[{tile}]，{reason})'
            if tile:
                self.toast_callback(f"AI推荐:[{tile}]，{reason}")
            else:
                self.toast_callback(f"AI:{reason}")

            return

    # 1.摸牌阶段：天胡/自摸/妙手回春，结束游戏，否则检查是否杠牌，再则出牌
    def draw_tile_phase(self):

        current_player_index = self.get_current_player_index()
        current_player = self.get_players()[current_player_index]

        # 有玩家决策请求，直接使用当前牌
        if self.draw_tile:
            tile = self.draw_tile
        
        # 没有玩家决策请求，正常摸牌
        else:
            tile = self._draw_tile()
            self.draw_tile = tile
            if tile is None: 
                self.change_game_state(GameState.GAME_OVER)
                return
            print(f"[{current_player.name}] 摸进 [{tile}]")
            current_player.add_tile(tile)
            self.discard_tile = None
            
            # 播放摸牌音效
            if self.sound_callback:
                self.sound_callback('draw')
        
        # 检查是否自摸胡牌或可以自杠(牌墙是否至少有一张牌)
        hand = copy.deepcopy(current_player.hand)
        can_gang = (self.rule.can_add_gang(hand,tile) or self.rule.can_self_gang(hand,tile)) and len(self.majiang_tiles)>0
        hand["concealed"] = hand["concealed"][:-1]
        can_hu,_ = self.rule.check_hu(hand,tile)
        decision_list = self.get_decision_list(can_hu,can_gang,False)
        
        # 检查玩家决定
        if any([can_hu,can_gang]) and self.make_decision_request(current_player_index,decision_list,tile):
            
            decision_result = self.get_decision_result()
            self.draw_tile = None

            # 检查玩家是否决定胡牌
            if decision_result.decision_type == DecisionType.HU:
                self.handle_hu([current_player_index],tile,current_player_index,Tag.ZI_MO)
                return
        
            #检查玩家是否决定杠牌
            elif decision_result.decision_type == DecisionType.GANG:
                self.gang_tile = tile
                self.change_game_state(GameState.GANG_PHASE)
                return
            
            # 检查玩家是否决定碰牌
            elif decision_result.decision_type == DecisionType.CANCEL:
                self.change_game_state(GameState.DISCARD_TILE_PHASE)
                self.draw_tile = None
                return
        
        # 不胡不杠或不在等待决策，转玩家出牌阶段
        if not any(decision_list) or not self.have_decision_request():
            self.change_game_state(GameState.DISCARD_TILE_PHASE)
            self.draw_tile = None
        
        # 失效玩家的第一次摸牌
        if current_player.first_draw:
            current_player.first_draw = False

    # 2.出牌阶段，处理鸡牌检查/吃胡检查/杠牌判断跳转/碰牌判断跳转/直接出牌/海底捞月
    def discard_tile_phase(self):

        current_player_index = self.get_current_player_index()
        current_player = self.players[current_player_index]

        def deal_discard_tile(discard_tile):
            current_player.discard_tile(discard_tile)
            self.discard_tile = discard_tile
            self.print_discard_tile(discard_tile)
            current_player.first_discard = False
            
            # 播放弃牌音效
            if self.sound_callback:
                self.sound_callback('discard')
                # 播放读牌音效
                self.sound_callback('card', player=current_player, card_name=discard_tile)
        
        if self.discard_tile:
            discard_tile = self.discard_tile
            if self.hot_tile and self.hot_tile == discard_tile:
                if discard_tile not in current_player.hand["concealed"]:
                    # print("DISCARD_TILE: 弃牌选择错误1 ")
                    self.reset_decision_request()
                    self.reset_decision_result()
                    return
                deal_discard_tile(discard_tile)
                self.hot_tile = None
        elif not self.make_decision_request(current_player_index,[DecisionType.DISCARD]):
            return
        elif self.have_decision_result():
            discard_tile = self.get_decision_result().tile
            if discard_tile not in current_player.hand["concealed"]:
                # print("DISCARD_TILE: 弃牌选择错误2 ")
                self.reset_decision_request()
                self.reset_decision_result()
                return
            deal_discard_tile(discard_tile)
            self.reject_hu = False
            
        # 检查其他玩家是否可以胡牌/碰牌/杠牌
        pass_port = not self.majiang_tiles   #海底捞月通行证
        can_hu,hu_index = self.check_other_players_can_hu(current_player,discard_tile,pass_port)
        can_gang,gang_index = self.check_other_players_can_gang(current_player,discard_tile)
        can_peng,peng_index = self.check_other_players_can_peng(current_player,discard_tile)

        # 优先处理玩家可以胡牌的场景,吃胡/海底捞月
        if can_hu and not self.reject_hu:
            index = hu_index
            tag = Tag.ZHUO_PAO
            # 是否完成处理多玩家胡牌决策
            if not self.make_hu_decision(hu_index,discard_tile,current_player_index,tag):
                return
            else:
                if not self.winner:
                    self.reject_hu = True
                return
        
        # 没有可以胡牌的玩家/拒绝胡，检查是否可以杠牌/碰牌
        else:
            if can_gang:
                index = gang_index
            elif can_peng:
                index = peng_index
        
        decision_list = self.get_decision_list(False,can_gang,can_peng)

        # 发起决策请求/执行玩家决策
        if any([can_gang,can_peng]) and self.make_decision_request(index,decision_list,discard_tile):
            
            decision_result = self.get_decision_result()
            self.discard_tile = None

            #决定杠牌
            if decision_result.decision_type == DecisionType.GANG:
                self.change_game_state(GameState.GANG_PHASE)
                self.change_current_player(index)
                current_player.remove_discard_tile(discard_tile)
                self.gang_tile = discard_tile
                self.discard_tile = None
                return
            
            # 决定碰牌
            elif decision_result.decision_type == DecisionType.PENG:
                peng_player = self.players[peng_index]
                current_player.remove_discard_tile(discard_tile)
                source = current_player.name
                tag = None

                if self.check_chicken_tile(discard_tile):                 
                    tag = Tag.YAO_JI
                    if current_player.has_tag(Tag.CHONG_FENG_JI):
                        tag = Tag.CHONG_FENG_JI
                    elif current_player.has_tag(Tag.HENG_JI):
                        tag = Tag.HENG_JI
                    current_player.add_tag(Tag.ZE_REN_JI,peng_player.name)
                    current_player.change_tag_source(tag,peng_player.name)
                    # peng_player.add_tag(tag,source)  #20251211,碰鸡不加鸡标签，已经在peng_tile时group中添加tag信息
                    # print(f"[{peng_player.name}] 获得 🏷️  [{tag.value}🐔]({source})")
                    print(f"[{peng_player.name}] 碰了 [{tag.value}🐔] ({source})" )
                    print(f"[{current_player.name}] 获得 🏷️  [{Tag.ZE_REN_JI.value}]({peng_player.name})")
                else:
                    print(f"[{peng_player.name}] 碰了 [{discard_tile}]({source})")
                
                # 播放碰牌音效
                if self.sound_callback:
                    self.sound_callback('action', player=peng_player, action_type='peng')

                current_player = self.change_current_player(index)  
                current_player.peng_tile(discard_tile,source,tag)
                self.discard_tile = None
                current_player.first_discard = False
                self.change_game_state(GameState.DISCARD_TILE_PHASE)
                return
            
            # 点击取消，当前玩家完成出牌,转1
            elif decision_result.decision_type == DecisionType.CANCEL:
                self.change_to_next_player()
                self.discard_tile = None
                self.reject_hu = False # 恢复拒绝胡牌标志
                self.change_game_state(GameState.DRAW_TILE_PHASE)
                self.draw_tile = None
                return

        # 其他玩家都不可以胡/碰/杠/非等待决策，当前玩家完成出牌,转1
        if (not any(decision_list)) or not self.have_decision_request():
            self.change_to_next_player()
            self.discard_tile = None
            self.reject_hu = False # 恢复拒绝胡牌标志
            self.change_game_state(GameState.DRAW_TILE_PHASE)
            self.draw_tile = None

    # 3.杠牌阶段：检查抢杠胡/杠牌/补牌/杠上开花，热炮跳转
    def gang_phase(self):
        current_player_index = self.get_current_player_index()
        current_player = self.get_current_player()

        tile = None
        if self.gang_tile:
            tile = self.gang_tile
            self.draw_tile = None
        else:
            print("没有可以杠的牌")
            raise ValueError("没有可以杠的牌")

        hand = copy.deepcopy(current_player.hand)

        # 检查是否是自己摸上的牌
        is_self_draw = None
        can_add_gang = self.majiang_tiles and self.rule.can_add_gang(hand,tile)
        can_self_gang = self.majiang_tiles and self.rule.can_self_gang(hand,tile)
        can_gang_others = self.majiang_tiles and self.rule.can_gang_others(hand,tile)
        if can_self_gang or can_add_gang:
            is_self_draw = True
        elif can_gang_others:
            is_self_draw = False

        #自己暗杠/杠别人的牌，直接执行杠牌
        if can_self_gang or (not is_self_draw):
            self.execute_gang(is_self_draw,tile)

        #自己加杠,检查是否有其他玩家可以抢杠胡牌
        elif is_self_draw and can_add_gang and not self.reject_hu:
            tag = Tag.QIANG_GANG_HU
            can_qianggang_hu,hu_index = self.check_other_players_can_hu(current_player,tile,default_passport=tag)

            # 发起决策请求/执行玩家决策
            if can_qianggang_hu and self.make_hu_decision(hu_index,tile,current_player_index,tag):
                # 是否完成处理多玩家胡牌决策
                if not self.make_hu_decision(hu_index,tile,current_player_index,tag):
                    return
                else:
                    if not self.winner:
                        self.reject_hu = True
                    # return  #这里不能return，因为可胡牌玩家拒绝胡牌，需要继续执行杠牌
            
            # 没有抢杠胡/拒绝胡牌，执行杠牌
            if not can_qianggang_hu or self.reject_hu:
                self.execute_gang(is_self_draw,tile)

    # 4.杠牌者摸牌阶段：检查是否有其他玩家可以胡牌且决定胡牌，否则跳转热炮阶段
    def draw_after_gang_phase(self):
        current_player_index = self.get_current_player_index()
        current_player = self.players[current_player_index]

        #杠之后摸一张新牌
        tile = None
        if self.draw_tile:
            tile = self.draw_tile
        else:
            tile = self._draw_tile()
            if tile is None:
                print("❌杠牌后牌墙为空，无法摸牌")
                self.change_game_state(GameState.GAME_OVER)
                return
            print(f"[{current_player.name}] 摸进 [{tile}]")
            self.draw_tile = tile
        if not tile:
            raise ValueError("杠牌后摸牌错误")

        hand = copy.deepcopy(current_player.hand)
        can_hu,_ = self.rule.check_hu(hand,tile)
        can_gang = (self.rule.can_add_gang(hand,tile) or self.rule.can_self_gang(hand,tile)) and len(self.majiang_tiles)>0
        decision_list = self.get_decision_list(can_hu,can_gang,False)

        if any(decision_list) and self.make_decision_request(current_player_index,decision_list,tile):
            
            decision_result = self.get_decision_result()
            
            # 检查是否杠上开花
            if decision_result.decision_type == DecisionType.HU:
                self_index = current_player_index
                self.handle_hu([self_index],tile,self_index,Tag.GANG_SAHNG_KAI_HUA)
                return
            
            # 检查是否杠上开杠
            elif decision_result.decision_type == DecisionType.GANG:
                self.draw_tile = None
                self.gang_tile = tile
                current_player.add_tile(tile)
                self.change_game_state(GameState.GANG_PHASE)
                return
        
            # 检查是否取消
            elif decision_result.decision_type == DecisionType.CANCEL:
                self.change_game_state(GameState.REPAO_PHASE)
                current_player.add_tile(tile)
                self.reset_decision_request()
                self.hot_tile = None
                return

        # 没有杠上开花/没有杠上开杠/非等待决策，当前玩家完成摸牌判断,转热炮牌阶段
        elif not any([can_hu,can_gang]) or not self.have_decision_request():
            self.change_game_state(GameState.REPAO_PHASE)
            current_player.add_tile(tile)
            self.reset_decision_request()
            self.hot_tile = None
            return

    # 5.热炮牌阶段：检查是否有其他玩家可以胡牌且决定胡牌，否则跳转出牌
    def repao_phase(self):

        current_player_index = self.get_current_player_index()
        current_player = self.players[current_player_index]

        # 玩家热炮牌阶段：检查是否有其他玩家可以胡牌且决定胡牌，否则跳转出牌阶段
        hot_tile = None
        if self.hot_tile:
            hot_tile = self.hot_tile
            self.gang_tile = None
        elif not self.make_decision_request(current_player_index,[DecisionType.DISCARD]):
            return
        elif self.have_decision_result():
            hot_tile = self.get_decision_result().tile
            if hot_tile not in current_player.hand["concealed"]:
                print(f"REPAO_PHASE:玩家选择的热炮牌1{hot_tile}不在手牌中")
                self.hot_tile = None
                self.reset_decision_request()
                self.reset_decision_result()
                return
            self.hot_tile = hot_tile
            self.gang_tile = None
        else:
            raise ValueError("热炮牌赋值错误")
        
        if not hot_tile or hot_tile not in current_player.hand["concealed"]:
            print(f"REPAO_PHASE:玩家选择的热炮牌2{hot_tile}不在手牌中")
            current_player.print_hand()
            print("请求如下：",self.decision_request)
            print("响应如下：",self.decision_result)
            self.hot_tile = None
            self.reset_decision_request()
            self.reset_decision_result()
            return
            
        # 检查是否有其他玩家可以胡牌，是否决定胡牌。
        can_hu,hu_index = self.check_other_players_can_hu(current_player,hot_tile,default_passport=Tag.ZHUO_RE_PAO)

        if can_hu and not self.reject_hu:
            if self.make_decision_request(hu_index[0],[DecisionType.HU],hot_tile):
                tag = Tag.ZHUO_RE_PAO
                # 是否完成处理多玩家胡牌决策
                if not self.make_hu_decision(hu_index,hot_tile,current_player_index,tag):
                    return
                else:
                    if not self.winner:
                        self.reject_hu = True
                    return
        else:
            self.discard_tile = hot_tile
            self.change_game_state(GameState.DISCARD_TILE_PHASE)
            return














