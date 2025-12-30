# UI管理器类
# 负责处理所有UI相关的绘制和更新功能

from token import OP
from tracemalloc import start
import pygame
from typing import List
import os
import math
from settings import Settings
from source.public import get_resource_path
from source.public import Tag
import copy

class UIManager:
    def __init__(self,screen, game_manager=None):
        """初始化UI管理器"""
        self.screen = screen
        self.settings = Settings()
        self.game_manager = game_manager
        self.players = []
        self.human_player = self.get_human_player()
        self.float_tile_list = []
        
        # 资源目录基础路径
        # 使用 get_resource_path 以兼容打包后的运行时路径
        self.resource_dir = get_resource_path('resource')
        
        # 本局详情显示控制
        self.show_result_detail = False
        # 查看桌面显示控制
        self.show_table = False
        
        # 初始化字体
        pygame.font.init()
        # 尝试加载指定字体，如果失败则使用默认字体
        try:
            # 检查字体路径是否存在
            if os.path.isfile(self.settings.font_path):
                font_path = self.settings.font_path
            # 直接使用settings中的路径（已经包含resource/前缀）
            elif not os.path.isabs(self.settings.font_path):
                font_path = self.settings.font_path
            else:
                font_path = self.settings.font_path
            
            self.font = pygame.font.Font(font_path, self.settings.normal_font_size)
        except Exception as e:
            print(f"加载字体失败: {e}，使用默认字体")
            self.font = pygame.font.SysFont(None, self.settings.normal_font_size)
        
        # 初始化图片资源
        self.bg_image = None
        self.time_bg_image = None  # 时间背景图片
        self.bg_center_image = None  # 中心背景图片
        self.number_images = {}  # 数字图片
        self.back_tile = None
        self.back_tile_self = None
        self.tiles = {}
        self.indicator_images = {}  # 玩家位置指示图片
        self.action_buttons = {}  # 存储按钮位置和类型
        self.game_settings_button = pygame.Rect(90, 20, 80, 30)  # 设置按钮区域
        self.settings_text_rect = None  # 存储设置文字的矩形区域
        self.game_number_rect = None  # 存储局数文字的矩形区域
        
        # 暂停按钮相关属性
        self.suspend_button = None  # 暂停按钮区域
        self.suspend_button_image = None  # 暂停按钮图片
        self.continue_button_image = None  # 继续按钮图片
        self.is_paused = False  # 游戏是否暂停
        
        self.concealed_hands_info = None
        self.discard_tile_indicator = False  # 当前弃牌指示器状态
        self.current_player = None  # 当前玩家对象
        self.last_player = None  # 上一个玩家对象
        self.discard_tile = None  # 当前弃牌牌对象
        self.indicator_pos = None  # 当前弃牌牌指示器位置
        self.indicator_width = None  # 当前弃牌牌指示器宽度
        
        # 加载资源
        self._load_resources()
        
        # 加载暂停和继续按钮图片
        try:
            self.suspend_button_image = pygame.image.load('resource/table/suspend.png').convert_alpha()
            self.suspend_button_image = pygame.transform.scale(self.suspend_button_image, (15, 15))  # 缩放为15*15
            self.continue_button_image = pygame.image.load('resource/table/continue.png').convert_alpha()
            self.continue_button_image = pygame.transform.scale(self.continue_button_image, (500, 500))  # 缩放为500*500
        except Exception as e:
            print(f"加载暂停/继续按钮图片失败: {e}")
    
    def set_players(self,players:List):
        """设置玩家列表"""
        self.players = players

    def get_players(self):
        """获取所有玩家"""
        return self.players

    def get_human_player(self):
        """获取人类玩家"""
        for player in self.players:
            if player.is_human:
                return player
        return None

    def set_float_tile_list(self,tile_list:List[int]):
        """设置选中的牌列表"""
        self.float_tile_list = tile_list

    def _load_resources(self):
        """加载必要的图片资源"""
        # 加载背景图片
        try:
            bg_path = self.settings.bg_img
            # settings 中已使用 get_resource_path 返回绝对路径
            self.bg_image = pygame.image.load(bg_path).convert()
            # 缩放背景图片以适应窗口大小，使用smoothscale提高质量
            self.bg_image = pygame.transform.smoothscale(self.bg_image, 
                                                  (self.settings.win_w, self.settings.win_h))
        except Exception as e:
            print(f"加载背景图片失败: {e}")
        
        # 加载中心背景图片
        try:
            bg_center_path = os.path.join(self.resource_dir, 'table', 'bg_center.png')
            self.bg_center_image = pygame.image.load(bg_center_path).convert_alpha()
        except Exception as e:
            print(f"加载中心背景图片失败: {e}")
        
        # 加载数字图片
        try:
            for i in range(10):
                num_path = os.path.join(self.resource_dir, 'table', 'number', f'blue_{i}.png')
                try:
                    self.number_images[str(i)] = pygame.image.load(num_path).convert_alpha()
                except Exception as e:
                    print(f"加载数字{i}图片失败: {e}")
        except Exception as e:
            print(f"加载数字图片时出错: {e}")
        
        # 加载玩家位置指示图片
        try:
            positions = ['east', 'south', 'west', 'north']
            for position in positions:
                img_path = os.path.join(self.resource_dir, 'table', f'light_{position}.png')
                try:
                    self.indicator_images[position] = pygame.image.load(img_path).convert_alpha()
                except Exception as e:
                    print(f"加载位置{position}的指示图片失败: {e}")
                    # 创建一个占位符图片
                    placeholder = pygame.Surface((50, 50))
                    placeholder.fill((255, 0, 0))  # 红色占位符
                    self.indicator_images[position] = placeholder
        except Exception as e:
            print(f"加载玩家位置指示图片时出错: {e}")
        
        # 加载时间背景图片
        try:
            time_bg_path = os.path.join(self.resource_dir, 'table', 'time_bg.png')
            self.time_bg_image = pygame.image.load(time_bg_path).convert_alpha()
        except Exception as e:
            print(f"加载时间背景图片失败: {e}")
        
        # 加载背面麻将牌
        try:
            # 标准尺寸背面牌，使用smoothscale提高质量
            self.back_tile = pygame.image.load(self.settings.back_tile_path).convert_alpha()
            self.back_tile = pygame.transform.smoothscale(self.back_tile, self.settings.tile_size)
            
            # 本家背面牌，保留原始分辨率不缩放，以获得更好的清晰度
            self.back_tile_self = pygame.image.load(self.settings.back_tile_path).convert_alpha()
        except Exception as e:
            print(f"加载背面麻将牌失败: {e}")
        
        # 加载所有麻将牌图片
        tile_dir = os.path.join(self.resource_dir, 'tiles')
        try:
            # 如果目录存在，尝试加载实际图片
            if os.path.exists(tile_dir):
                for filename in os.listdir(tile_dir):
                    if filename.endswith('.png') and filename != 'face-down.png':
                        tile_path = os.path.join(tile_dir, filename)
                        tile_id = filename[:-4]  # 移除.png后缀
                        
                        # 加载原始尺寸牌，不进行初始缩放，保持原始分辨率
                        try:
                            tile = pygame.image.load(tile_path).convert_alpha()
                            self.tiles[tile_id] = tile
                        except Exception as e:
                            print(f"加载麻将牌 {tile_id} 失败: {e}")
            else:
                print(f"麻将牌目录不存在: {tile_dir}")
        except Exception as e:
            print(f"加载麻将牌图片失败: {e}")
        
        # 加载碰杠胡按钮图片
        self.action_icons = {}
        action_types = ['peng', 'gang', 'hu', 'cancel', 'ignore']
        for action in action_types:
            img_path = os.path.join(self.resource_dir, 'sprites', f'{action}.png')
            if os.path.exists(img_path):
                self.action_icons[action] = pygame.image.load(img_path).convert_alpha()
                # 调整按钮大小
                self.action_icons[action] = pygame.transform.scale(self.action_icons[action], (80, 40))
            else:
                print(f"警告: 未找到动作图标 {img_path}")
    
    def get_image_path(self, category, filename):
        """获取图片的完整路径
        
        Args:
            category: 图片类别（如 'avatar', 'tiles', 'sprites' 等）
            filename: 图片文件名（包含扩展名）
        
        Returns:
            图片的完整路径
        """
        return os.path.join(self.resource_dir, category, filename)
    
    def load_image(self, image_path, size=None):
        """加载图片并可选缩放
        
        Args:
            image_path: 图片路径
            size: 可选，目标尺寸 (width, height)
        
        Returns:
            加载的图片Surface对象
        """
        try:
            # 直接使用提供的路径
            image = pygame.image.load(image_path).convert_alpha()
            
            # 如果指定了尺寸，进行缩放
            if size:
                image = pygame.transform.scale(image, size)
            
            return image
        except Exception as e:
            print(f"加载图片失败 {image_path}: {e}")
            # 创建一个占位符图片
            placeholder = pygame.Surface(size or (64, 64))
            placeholder.fill((100, 100, 100))
            # 在占位符上绘制文本
            if size:
                font_size = min(20, size[1] // 2)
                font = pygame.font.SysFont(None, font_size)
                text = font.render("?", True, (255, 255, 255))
                text_rect = text.get_rect(center=placeholder.get_rect().center)
                placeholder.blit(text, text_rect)
            return placeholder
    
    def draw_bg(self, current_player=None):
        """绘制背景"""
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))
        else:
            # 如果背景图片加载失败，使用纯色背景
            self.screen.fill((100, 100, 100))  # 灰色背景
        
        # 绘制中心背景图片
        if self.bg_center_image:
            # 计算居中位置
            screen_center_x = self.settings.win_w // 2
            screen_center_y = self.settings.win_h // 2
            img_width = self.bg_center_image.get_width()
            img_height = self.bg_center_image.get_height()
            
            # 计算绘制位置，确保图片在屏幕中心
            x = screen_center_x - img_width // 2
            y = screen_center_y - img_height // 2
            
            # 绘制图片
            self.screen.blit(self.bg_center_image, (x, y))
        
        # 绘制时间背景图片，确保其在屏幕中心显示
        if self.time_bg_image:
            # 计算居中位置
            screen_center_x = self.settings.win_w // 2
            screen_center_y = self.settings.win_h // 2
            img_width = self.time_bg_image.get_width()
            img_height = self.time_bg_image.get_height()
            
            # 计算绘制位置，确保图片在屏幕中心
            x = screen_center_x - img_width // 2
            y = screen_center_y - img_height // 2
            
            # 绘制图片
            self.screen.blit(self.time_bg_image, (x, y))
        
        # 绘制四个方向的文字显示，并传入当前玩家
        self.draw_direction_text(current_player)
    
    def draw_direction_text(self, current_player=None):
        """在四个方向显示东南西北文字
        
        在四个方向距离中心偏移direction_text_offset的距离处显示direction_text_font_size的font_path字体的方向词"东南西北
        屏幕下方为东，注意根据方向调整旋转角度
        
        Args:
            current_player: 当前玩家对象，用于高亮显示当前玩家方向
        """
        # 根据settings中的show_direction决定是否绘制方向词
        if not self.settings.show_direction:
            return
            
        # 确保字体已加载
        if not hasattr(self, 'direction_font'):
            try:
                # 检查字体路径是否存在
                if os.path.isfile(self.settings.direction_font_path):
                    font_path = self.settings.direction_font_path
                # 直接使用settings中的路径（已经包含resource/前缀）
                elif not os.path.isabs(self.settings.direction_font_path):
                    font_path = self.settings.direction_font_path
                else:
                    font_path = self.settings.direction_font_path
                
                self.direction_font = pygame.font.Font(font_path, self.settings.direction_text_font_size)
            except:
                # 如果加载失败，使用默认字体
                self.direction_font = pygame.font.SysFont(None, self.settings.direction_text_font_size)
        
        # 获取屏幕中心和偏移距离
        center_x = self.settings.win_w // 2
        center_y = self.settings.win_h // 2
        offset = self.settings.direction_text_offset
        
        # 方向配置：位置 -> (文字, x偏移, y偏移, 旋转角度)
        # 屏幕下方为东，使用settings中的direction_text配置
        directions = {
            'east': (self.settings.direction_text[0], 0, offset, 0),      # 底部，不旋转
            'south': (self.settings.direction_text[1], offset, 0, 90),    # 右侧，旋转90度
            'west': (self.settings.direction_text[2], 0, -offset, 180),   # 顶部，不旋转
            'north': (self.settings.direction_text[3], -offset, 0, -90)   # 左侧，旋转-90度
        }
        
        # 获取当前玩家位置（如果提供）
        current_position = current_player.position if current_player else None
        
        # 绘制每个方向的文字
        for direction, (text, x_offset, y_offset, rotation) in directions.items():
            # 根据是否是当前玩家方向选择颜色
            if direction == current_position:
                # 当前玩家方向使用红色高亮
                color = self.settings.red
            else:
                # 其他方向使用默认颜色
                color = self.settings.direction_text_color
            
            # 渲染文字
            text_surface = self.direction_font.render(text, True, color)
            
            # 如果需要旋转
            if rotation != 0:
                text_surface = pygame.transform.rotate(text_surface, rotation)
            
            # 计算文字位置
            text_rect = text_surface.get_rect(center=(center_x + x_offset, center_y + y_offset))
            
            # 绘制文字
            self.screen.blit(text_surface, text_rect.topleft)
    
    def draw_remaining_tiles(self, remaining_count):
        """绘制剩余牌数
        
        Args:
            remaining_count: 剩余牌数
        """
        if remaining_count < 0:
            remaining_count = 0
            
        # 显示"剩余牌数"文字 - 使用黑色字体，距离中心偏上10像素
        text_surface = self.font.render("剩余牌数", True, self.settings.black)
        text_rect = text_surface.get_rect(center=(self.settings.win_w // 2, self.settings.win_h // 2 - 10))
        self.screen.blit(text_surface, text_rect)
            
        # 将数字转换为字符串
        count_str = str(remaining_count)
        
        # 计算起始位置（屏幕中心）
        screen_center_x = self.settings.win_w // 2
        screen_center_y = self.settings.win_h // 2
        
        # 绘制每个数字
        total_width = 0
        number_imgs = []
        
        for digit in count_str:
            if digit in self.number_images:
                img = self.number_images[digit]
                # 缩小数字尺寸到原来的0.5倍
                scaled_img = pygame.transform.scale(img, (
                    int(img.get_width() * 0.5), 
                    int(img.get_height() * 0.5)
                ))
                number_imgs.append(scaled_img)
                total_width += scaled_img.get_width()
        
        # 计算起始位置，使数字居中显示，屏幕靠下10像素
        start_x = screen_center_x - total_width // 2
        start_y = screen_center_y + 10  # 屏幕靠下10像素
        
        # 绘制每个数字
        current_x = start_x
        for img in number_imgs:
            self.screen.blit(img, (current_x, start_y))
            current_x += img.get_width()
    
    def draw_indicator(self, position='east'):
        """根据玩家位置绘制对应的指示图片，不同位置有不同的偏移量
        
        Args:
            position: 玩家位置，可选值为'east'(底部), 'south'(右侧), 'west'(顶部), 'north'(左侧)，默认为'east'
        """
        # 检查是否需要显示指示器
        if not self.settings.show_indicator:
            return
            
        # 首先尝试使用高亮状态的指示器图片
        light_position = f'light_{position}'
        if light_position in self.indicator_images:
            indicator_img = self.indicator_images[light_position]
        else:
            # 如果高亮图片不存在，则检查普通位置图片
            if position not in self.indicator_images:
                print(f"无效的玩家位置: {position}，使用默认位置'east'")
                position = 'east'
                # 确保默认位置有图片
                if position not in self.indicator_images:
                    placeholder = pygame.Surface((50, 50))
                    placeholder.fill((255, 0, 0))  # 红色占位符
                    self.indicator_images[position] = placeholder
            indicator_img = self.indicator_images[position]
        if indicator_img:
            # 定义偏移距离常量
            X = 20  # 默认偏移距离为20像素
            
            # 计算居中位置
            screen_center_x = self.settings.win_w // 2
            screen_center_y = self.settings.win_h // 2
            img_width = indicator_img.get_width()
            img_height = indicator_img.get_height()
            
            # 根据位置计算偏移后的坐标
            # 从中心向各自方向偏移X像素
            if position == 'east':  # 底部位置，向下方偏移
                x = screen_center_x - img_width // 2 + 25
                y = screen_center_y + X - img_height // 2 +110
            elif position == 'south':  # 右侧位置，向右方偏移
                x = screen_center_x + X - img_width // 2 + 110
                y = screen_center_y - img_height // 2 - 25
            elif position == 'west':  # 顶部位置，向上方偏移
                x = screen_center_x - img_width // 2 + 25
                y = screen_center_y - X - img_height // 2 - 110
            elif position == 'north':  # 左侧位置，向左方偏移
                x = screen_center_x - X - img_width // 2 - 105
                y = screen_center_y - img_height // 2 - 25
            else:  # 默认居中（不应该到达这里，因为前面已经检查了位置有效性）
                x = screen_center_x - img_width // 2
                y = screen_center_y - img_height // 2
            
            # 绘制图片
            self.screen.blit(indicator_img, (x, y))
    
    def draw_avtar(self):
        """绘制玩家头像和名字
        
        Args:
            players: 玩家对象列表，每个玩家对象需要有avatar、name和position属性
        """
        
        players = self.get_players()
        # 创建位置到玩家的映射
        position_to_player = {}
        for player in players:
            position_to_player[player.position] = player
        
        # 按顺序（east, south, west, north）处理玩家
        positions_order = ["east", "south", "west", "north"]
        
        for i, position in enumerate(positions_order):
            # 确保位置在范围内
            if i < len(self.settings.avatar_positions) and position in position_to_player:
                player = position_to_player[position]
                
                # 加载头像
                avatar = self.load_image(player.avatar, self.settings.avatar_size)
                
                # 绘制头像
                avatar_pos = self.settings.avatar_positions[i]
                self.screen.blit(avatar, avatar_pos)
                
                # 绘制名字（在头像正下方居中显示）
                # 渲染文本
                if self.settings.show_name:
                    _str = player.name + f"({player.score})"
                elif self.settings.show_ai_version:
                    _str = f"{player.ai_version}({player.score})"
                else:
                    _str = f"{player.score}分"
                text_surface = self.font.render(_str, True, self.settings.white)  # 白色文字
                
                # 计算文字位置（头像正下方居中）
                text_x = avatar_pos[0] + (self.settings.avatar_size[0] - text_surface.get_width()) // 2
                text_y = avatar_pos[1] + self.settings.avatar_size[1] + 5  # 头像下方5像素
                
                # 绘制文字
                self.screen.blit(text_surface, (text_x, text_y))

    def deal_chicken_group(self,player,exposed_hands):
        """处理鸡牌组
        Args:
            player: 玩家对象
            exposed_hands: 公开手牌列表
        """
        ji_tile = self.settings.ji_tile
        Tags = [Tag.CHONG_FENG_JI,Tag.HENG_JI,Tag.YAO_JI]
        exposed_hands = copy.deepcopy(exposed_hands)
        for i,group in enumerate(exposed_hands):
            tile = group['tiles'][0]
            if self.is_chicken_tile(tile):
                # 安全检查：确保group字典中有ji_tag键
                if 'ji_tag' in group:
                    ji_tag = group['ji_tag']
                    # 安全检查：确保ji_tag在Tags列表中
                    if ji_tag in Tags:
                        tile = ji_tile[Tags.index(ji_tag)]
                        exposed_hands[i]['tiles'][0] = tile
                        return exposed_hands                
        tags = player.get_tags()
        group = {"source":None,"tiles":[]}
        for tag in tags:
            if tag['tag'] in Tags and tag['source']=="self":
                group["tiles"].append(ji_tile[Tags.index(tag['tag'])]) 
        if group["tiles"]:
            exposed_hands.insert(0,group)
        return exposed_hands

    def is_chicken_tile(self,tile):
        return tile in self.settings.chicken_tile

    def draw_hands(self,show_all_faces=False,show_self=True):
        """绘制四个方向的手牌
        Args:
            players: 玩家对象列表，每个玩家需要有position和hand属性
            show_all_faces: 布尔值，是否显示所有玩家手牌的正面（实际手牌）
                          如果为None，则使用settings中的show_all_faces配置
            selected_indices: 列表，指定需要上浮显示的手牌索引（仅对东家有效）
            game_manager: GameManager对象，用于获取自动打出的牌索引
        """

        def show_discard_tile_indicator(player,tile):
            cp = self.current_player.position
            lp = self.last_player.position if self.last_player else None
            p = player.position
            return  self.discard_tile_indicator and (cp==p or lp==p) and tile == self.discard_tile

        def draw_discard_tile_indicator(pos, size=None):
            """绘制当前弃牌指示器
            Args:
                pos: 绘制位置 (x, y)
                size: 可选，牌尺寸 (width, height)。如果为None，则使用settings.tile_size

            功能：在活动牌的同一纵坐标下，横坐标 pos.x + size.width/2 处绘制指示器，并添加上下浮动动画。
            图片路径：resource/table/tile_indicator.png（首次加载后缓存为 self.tile_indicator_img）。
            """
            try:
                x, y = pos
            except Exception:
                return

            # 使用默认牌尺寸（如果未传入）
            if size is None:
                size = self.settings.tile_size[0]

            # 确保为整数
            try:
                tile_w = int(self.settings.tile_size[0])
                tile_h = int(self.settings.tile_size[1])
            except Exception:
                tile_w = 76*0.5
                tile_h = 118*0.5

            # 指示器默认尺寸（相对于牌尺寸）：
            scale = 0.1
            ind_w = 200
            ind_h = 230
            if self.settings.tile_indicator_color != "green":
                ind_h = 200
                scale = 0.15
            ind_w = int(ind_w*scale)
            ind_h = int(ind_h*scale)

            # 延迟加载并缓存指示器图片
            if not hasattr(self, 'tile_indicator_img') or self.tile_indicator_img is None:
                color = self.settings.tile_indicator_color
                indicator_path = os.path.join(self.resource_dir, 'table', f'tile_indicator_{color}.png')
                self.tile_indicator_img = self.load_image(indicator_path, size=(ind_w, ind_h))
                # 如果load_image返回占位符但尺寸不对，确保尺寸一致
                try:
                    if self.tile_indicator_img.get_size() != (ind_w, ind_h):
                        self.tile_indicator_img = pygame.transform.smoothscale(self.tile_indicator_img, (ind_w, ind_h))
                except Exception:
                    pass

            # 将指示器以中心对齐放置在该点上方
            draw_x = int(x+(size-ind_w)/2)
            draw_y = int(y-ind_h)

            # 上下浮动动画：基于时间的正弦波
            try:
                t = pygame.time.get_ticks()  # 毫秒
                period = 800.0  # 一个周期（毫秒）
                amplitude = max(2, int(tile_h * 0.06))  # 振幅像素
                offset = int(math.sin((t % period) / period * 2 * math.pi) * amplitude)
            except Exception:
                offset = 5

            # 应用动画偏移（垂直）
            final_y = draw_y + offset

            # 绘制指示器
            try:
                self.screen.blit(self.tile_indicator_img, (draw_x, final_y))
            except Exception as e:
                # 出现任何错误时静默处理，避免影响主循环
                # print(f"绘制指示器失败: {e}")
                pass

        def source2index(player,source_name):
            player_name = player.name
            special_positions = ['south','north'] # 南北玩家的牌从下到上渲染，杠牌指向特殊调整
            if source_name == "self":
                return -1
            position = [p.name for p in self.get_players()]
            obj = {1:0,2:1,3:3,0:-1}
            index = (position.index(player_name)-position.index(source_name))%4
            if player.position in special_positions:
                obj = {1:3,2:1,3:0,0:-1}
            return obj[index]
            
        def draw_tile(tile, pos, show_face=False, rotation=0, tile_size=None):
            """绘制单个麻将牌
            Args:
                tile_id: 麻将牌ID
                pos: 绘制位置 (x, y)
                is_self: 是否是本家的牌
                show_face: 是否显示牌面
                rotation: 旋转角度（0, 90, -90）
            """
            # 确保tile是字符串
            if not isinstance(tile, str):
                return
                
            # 获取牌的尺寸
            if tile_size:
                target_size = tile_size
            else:
                target_size = self.settings.tile_size
                
            # 如果是显示正面且找到了对应的图片
            if show_face:
                # 确保tile在tiles字典中
                if tile in self.tiles:
                    tile_img = self.tiles[tile]
                else:
                    return
                tile_img = pygame.transform.smoothscale(tile_img, target_size)
            # 如果需要显示背面且有背面图片
            else:
                tile_img = self.back_tile

            # 应用旋转
            tile_img = pygame.transform.rotate(tile_img, rotation)

            self.screen.blit(tile_img, pos)

            return tile_img.get_rect(topleft=pos)
        
        def draw_self(player, selected_indices,show_all_faces):
            """绘制东家手牌（底部红框区域）
            手牌在屏幕底部红框区域水平排列
            
            Args:
                player: 玩家对象
                selected_indices: 列表，指定需要上浮显示的手牌索引
            """
            if not player.hand:
                print("本家没有手牌")
                return
            
            # 获取隐藏手牌、明牌、弃牌、头像位置
            concealed_hands = player.get_concealed_hand()
            exposed_hands = player.get_exposed_hand()
            discard_tiles = player.get_discard_tiles()
            avatar_pos = self.settings.avatar_positions[0]

            # 牌尺寸和起始位置
            tile_size = self.settings.tile_size
            base_x = avatar_pos[0] + 64 + 20
            base_y = self.settings.win_h - tile_size[1] - 20

            # 绘制本家公开手牌
            start_x = base_x - tile_size[0]
            start_y = base_y
            gap = 10
            tile_width = tile_size[0]
            exposed_hands = self.deal_chicken_group(player,exposed_hands)
            for group in exposed_hands:
                # 确保group是字典且包含tiles键
                if isinstance(group, dict) and 'tiles' in group and group['tiles']:
                    
                    tiles = group['tiles']
                    # 处理3张牌组（非幺鸡）或者没有source的组（打出的鸡牌）
                    tile = tiles[0]
                    peng_or_discard_ji = (len(tiles) == 3 and not self.is_chicken_tile(tile)) or (not group['source'])
                    if peng_or_discard_ji:
                        for tile in tiles:
                            tile_width = tile_size[0]
                            start_x += tile_width
                            start_y = base_y
                            gap = 10
                            draw_tile(tile, (start_x, start_y), show_face=show_all_faces, rotation=0)
                    
                    #杠牌和碰杠的幺鸡需要针对source索引横置一张牌
                    else:
                        rotation = 0
                        index = source2index(player, group['source'])
                        if self.is_chicken_tile(tile) and len(tiles)==3 and index==3:
                            index=2
                        for i,tile in enumerate(tiles):
                            start_x += tile_width
                            if i == index:
                                rotation = 90
                                start_y += (tile_size[1]-tile_size[0])-2
                                tile_width = tile_size[1]-2
                                gap = tile_size[1]-tile_size[0]+10
                            else:
                                rotation = 0
                                tile_width = tile_size[0]
                                gap = 10
                            draw_tile(tile, (start_x, start_y), show_face=show_all_faces, rotation=rotation)                          
                            start_y = base_y
                    start_x += gap # 每组牌之间间距

            # 绘制本家隐藏手牌
            tile_size_self = self.settings.tile_size_self
            start_x += tile_size[0] + 10 # 隐藏手牌起始位置在公开手牌右侧
            start_y = self.settings.win_h - tile_size_self[1] - 20

            # 获取手牌上浮像素值
            float_pixels = 20
            tile_width = (tile_size_self[0]-2) #减2像素让牌看起来更紧凑
            tile_height = tile_size_self[1]
            concealed_hands_info = (start_x, start_y, tile_width,tile_height,len(concealed_hands))
            self.concealed_hands_info = concealed_hands_info
            gap = 10

            # 绘制每张牌
            for i, tile in enumerate(concealed_hands):
                base_x = start_x + i * tile_width

                # 如果当前牌索引在选中列表中，则上浮显示
                if i in selected_indices:
                    y = start_y - float_pixels
                else:
                    y = start_y

                if i==len(concealed_hands)-1 and i in [1,4,7,10,13]:
                    base_x += gap

                draw_tile(tile, (base_x, y), show_face=show_all_faces, rotation=0, tile_size=tile_size_self)  # 本家始终显示正面

            # 绘制本家弃牌（基于屏幕中心定位）
            # 计算起始位置：屏幕中心偏下方
            screen_center_x = self.settings.win_w // 2
            screen_center_y = self.settings.win_h // 2
            base_x = screen_center_x
            base_y = screen_center_y + self.settings.pixes_2_center + 2  # 屏幕中心偏下
            # 绘制每张牌
            # 计算所有弃牌的总宽度并水平居中
            total_width = len(discard_tiles) * tile_size[0]
            start_x = base_x - total_width // 2
            start_y = base_y
            discard_tiles = [tile for tile in discard_tiles if not self.is_chicken_tile(tile)]
            for i, tile in enumerate(discard_tiles):
                x = start_x + i * tile_size[0]
                draw_tile(tile, (x, start_y), show_face=show_all_faces, rotation=0)  # 本家始终显示正面
                if i==len(discard_tiles)-1 and show_discard_tile_indicator(player,tile):
                    self.indicator_pos = (x, start_y)
                    self.indicator_width = tile_size[0]
        
        def draw_after(player,show_all_faces=False):
            """绘制南家手牌
            手牌在屏幕右侧红框区域垂直排列，旋转-90度
            """
            def draw_exposed_hands(exposed_hands,start_x,start_y,tile_width,exposed_rotation):
                """绘制公开手牌
                手牌在屏幕右侧红框区域垂直排列，旋转-90度
                """
                x = start_x
                y = start_y
                gap = 10
                for i,group in enumerate(exposed_hands):

                    # 确保group是字典且包含tiles键
                    if not isinstance(group, dict) or 'tiles' not in group or not group['tiles']:
                        continue

                    # 处理3张牌组（非幺鸡）或者没有source的组（打出的鸡牌）
                    tiles = group['tiles']
                    tile = tiles[0]
                    peng_or_ji = (len(tiles) == 3 and not self.is_chicken_tile(tile)) or (not group['source'])
                    if peng_or_ji:
                        for tile in tiles:
                            y += tile_width
                            x = start_x if i<=2 else base_x
                            rotation = exposed_rotation
                            tile_width = tile_size[0]
                            gap = 10
                            draw_tile(tile, (x, y), show_face=True, rotation=rotation)
                    
                    #杠牌和碰杠的幺鸡需要针对source索引横置一张牌
                    else:
                        index = source2index(player, group['source'])
                        if self.is_chicken_tile(tile) and len(tiles)==3 and index==3:
                            index=2
                        for j,tile in enumerate(tiles):
                            y += tile_width
                            if j == index:
                                rotation = 0
                                tile_width = tile_size[1]-2
                                x = (tile_size[1]-tile_size[0])-2 + start_x
                                gap = 10 + (tile_size[1]-tile_size[0])-2
                            else:
                                rotation = exposed_rotation
                                tile_width = tile_size[0]
                                x = start_x
                                gap = 10
                            draw_tile(tile, (x, y), show_face=True, rotation=rotation)
                    y += gap

                return y

            if not player.hand:
                print("南家没有手牌")
                return
            
            # 获取隐藏手牌、明牌、弃牌、头像位置
            concealed_hands = player.get_concealed_hand()
            exposed_hands = player.get_exposed_hand()
            discard_tiles = player.get_discard_tiles()
            avatar_pos = self.settings.avatar_positions[1]
            
            # 牌尺寸和起始位置
            tile_size = self.settings.tile_size
            base_y = avatar_pos[1] + 64 + 50
            base_x = avatar_pos[0] + (64-tile_size[1])

            # 绘制下家公开手牌（右侧垂直排列，旋转90度）
            start_x = base_x  - tile_size[1] - 20
            start_y = base_y  - tile_size[0]
            tile_width = tile_size[0]
            exposed_rotation = 90
            exposed_hands = self.deal_chicken_group(player,exposed_hands)
            draw_exposed_hands(exposed_hands[:3],start_x,start_y,tile_width,exposed_rotation)

            #第四组之后的公开牌渲染在隐藏手牌一列
            start_x = base_x
            start_y = base_y  - tile_size[0]
            start_y = draw_exposed_hands(exposed_hands[3:],start_x,start_y,tile_width,exposed_rotation)
            start_y += tile_size[0]

            # 绘制下家隐藏手牌（右侧垂直排列，旋转90度）
            gap = 10
            concealed_rotation = -90 if show_all_faces else 90
            for i, tile in enumerate(concealed_hands):
                y = start_y + i * tile_size[0]
                
                if i==len(concealed_hands)-1 and i in [1,4,7,10,13]:
                    y += gap
                    
                draw_tile(tile, (start_x, y), show_face=show_all_faces, rotation=-concealed_rotation)  # 根据show_all_faces决定是否显示正面
            
            # 绘制下家弃牌（基于屏幕中心定位）
            # 计算起始位置：屏幕中心偏右方
            screen_center_x = self.settings.win_w // 2
            screen_center_y = self.settings.win_h // 2
            start_x = screen_center_x + self.settings.pixes_2_center
            start_y = screen_center_y + tile_size[1]
            discard_rotation = 90
            # 绘制每张牌（垂直排列，多于6张换行）
            num = 5            
            discard_tiles = [tile for tile in discard_tiles if not self.is_chicken_tile(tile)]
            for i, tile in enumerate(discard_tiles):
                row = i // num
                col = i % num
                x = start_x + row * tile_size[1]
                y = start_y - col * tile_size[0]
                draw_tile(tile, (x, y), show_face=True, rotation=discard_rotation)
                if i==len(discard_tiles)-1 and show_discard_tile_indicator(player,tile):
                    self.indicator_pos = (x, y)
                    self.indicator_width = tile_size[1]
        
        def draw_opposite(player,show_all_faces=False):
            """绘制西家手牌（顶部红框区域）
            手牌在屏幕顶部红框区域水平排列
            """
            if not player.hand:
                print("西面玩家没有手牌")
                return
            
            # 获取隐藏手牌、明牌、弃牌、头像位置
            concealed_hands = player.get_concealed_hand()
            exposed_hands = player.get_exposed_hand()
            discard_tiles = player.get_discard_tiles()
            avatar_pos = self.settings.avatar_positions[2]

            # 牌尺寸和起始位置
            tile_size = self.settings.tile_size
            base_x = avatar_pos[0] - tile_size[0]

             # 绘制每组公开牌
            start_x = base_x
            start_y = avatar_pos[1]
            exposed_rotation = 180
            exposed_hands = self.deal_chicken_group(player,exposed_hands)
            for group in exposed_hands:
                # 确保group是字典且包含tiles键
                if not isinstance(group, dict) or 'tiles' not in group or not group['tiles']:
                    continue
                
                gap = tile_size[0]
                # 处理3张牌组（非幺鸡）或者没有source的组（打出的鸡牌）
                tile = group['tiles'][0]
                peng_or_ji = (len(group['tiles']) == 3 and not self.is_chicken_tile(tile)) or (not group['source'])
                if peng_or_ji:
                    for tile in group['tiles']:
                        start_x -= tile_size[0]
                        rotation = exposed_rotation
                        draw_tile(tile, (start_x, start_y), show_face=True, rotation=rotation)
                
                #杠牌和碰杠的幺鸡需要针对source索引横置一张牌
                else:
                    index = source2index(player, group['source'])
                    if self.is_chicken_tile(tile) and len(group['tiles'])==3 and index==3:
                        index=2
                    for i,tile in enumerate(group['tiles']):
                        if i == index:
                            rotation = 90
                            gap = tile_size[1]-2
                        else:
                            rotation = exposed_rotation
                            gap = tile_size[0]
                        start_x -=  gap
                        draw_tile(tile, (start_x, start_y), show_face=True, rotation=rotation)
                start_x -= 10

            # 绘制对面隐藏手牌（顶部水平排列）
            start_x -= tile_size[0]
            start_y = avatar_pos[1]
            gap = 10
            concealed_rotation = 180 if show_all_faces else 0
            for i, tile in enumerate(concealed_hands):
                x = start_x - i * tile_size[0]
                if i==len(concealed_hands)-1 and i in [1,4,7,10,13]:
                    x -= gap
                draw_tile(tile, (x, start_y), show_face=show_all_faces, rotation=concealed_rotation)  # 根据show_all_faces决定是否显示正面

            # 绘制对面弃牌（基于屏幕中心定位）
            # 计算起始位置：屏幕中心偏上方
            screen_center_x = self.settings.win_w // 2
            screen_center_y = self.settings.win_h // 2
            start_x = screen_center_x
            start_y = screen_center_y - tile_size[1] - self.settings.pixes_2_center - 2  # 屏幕中心偏上
            # 计算所有弃牌的总宽度并水平居中
            total_width = len(discard_tiles) * tile_size[0]
            start_x = screen_center_x + total_width // 2 - tile_size[0]
            discard_rotation = 180
            discard_tiles = [tile for tile in discard_tiles if not self.is_chicken_tile(tile)]
            for i, tile in enumerate(discard_tiles):
                x = start_x - i * tile_size[0]
                y = start_y
                draw_tile(tile, (x, y), show_face=True, rotation=discard_rotation)
                if i==len(discard_tiles)-1 and show_discard_tile_indicator(player,tile):
                    self.indicator_pos = (x, y)
                    self.indicator_width = tile_size[0]
        
        def draw_before(player,show_all_faces=False):
            """绘制北家手牌
            手牌在屏幕左侧红框区域垂直排列，旋转-90度
            """
            def draw_exposed_hands(exposed_hands,start_x,start_y,tile_width,exposed_rotation):
                
                for i,group in enumerate(exposed_hands):
                    # 确保group是字典且包含tiles键
                    if not isinstance(group, dict) or 'tiles' not in group or not group['tiles']:
                        continue
                    
                    # 处理3张牌组（非幺鸡）或者没有source的组（打出的鸡牌）
                    tiles = group['tiles']
                    tile = tiles[0]
                    peng_or_ji = (len(tiles) == 3 and not self.is_chicken_tile(tile)) or (not group['source'])
                    if peng_or_ji:
                        for tile in tiles:
                            start_y -= tile_size[0]  # 向上排列
                            rotation = exposed_rotation
                            draw_tile(tile, (start_x, start_y), show_face=True, rotation=rotation)

                    #杠牌和碰杠的幺鸡需要针对source索引横置一张牌
                    else:                    
                        index = source2index(player, group['source'])
                        if self.is_chicken_tile(tile) and len(tiles)==3 and index==3:
                            index=2                        
                        for j,tile in enumerate(tiles):
                            if j == index:
                                rotation = 0
                                current_gap = tile_size[1]-2
                                temp_x = start_x + ((tile_size[1] - tile_size[0]) // 2-10) if i < 2 else start_x
                            else:
                                rotation = exposed_rotation
                                current_gap = tile_size[0]
                                temp_x = start_x
                            
                            start_y -= current_gap
                            draw_tile(tile, (temp_x, start_y), show_face=True, rotation=rotation)
                    start_y -= 10  # 组间间隔

                return start_y

            if not player.hand:
                print("北面玩家没有手牌")
                return
            
            # 获取隐藏手牌、明牌、弃牌、头像位置
            concealed_hands = player.get_concealed_hand()
            exposed_hands = player.get_exposed_hand()
            discard_tiles = player.get_discard_tiles()
            avatar_pos = self.settings.avatar_positions[3]

            # 牌尺寸和起始位置
            tile_size = self.settings.tile_size
            tile_width = tile_size[0]
            base_x = avatar_pos[0]  # 隐藏牌横坐标与头像横坐标对齐
            base_y = avatar_pos[1] - 70  # 起始垂直位置
            
            # 绘制每组公开牌（公开牌在隐藏牌前面，横坐标更大）
            start_x = base_x + tile_size[1] + 20  # 公开牌在隐藏牌右侧（横坐标更大）
            start_y = base_y + tile_size[0]
            exposed_rotation = -90
            exposed_hands = self.deal_chicken_group(player,exposed_hands)

            # 绘制前3组公开牌
            draw_exposed_hands(exposed_hands[:3],start_x,start_y,tile_width,exposed_rotation)

            # 绘制第4组及以后的公开牌
            start_x = base_x
            start_y = base_y  + tile_size[0]
            gap = 10
            start_y = draw_exposed_hands(exposed_hands[3:],start_x,start_y,tile_width,exposed_rotation)
            start_y -= tile_size[0]

            # 绘制上家隐藏手牌（左侧垂直排列，旋转-90度）
            concealed_rotation = 90 if not show_all_faces else -90
            for i, tile in enumerate(concealed_hands):
                y = start_y - i * tile_size[0]  # 向上排列
                
                if i==len(concealed_hands)-1 and i in [1,4,7,10,13]:
                    y -= gap

                draw_tile(tile, (start_x, y), show_face=show_all_faces, rotation=concealed_rotation)  # 正确使用base_rotation

            # 绘制上家弃牌（基于屏幕中心定位）
            # 计算起始位置：屏幕中心偏左方
            screen_center_x = self.settings.win_w // 2
            screen_center_y = self.settings.win_h // 2
            base_x = screen_center_x - tile_size[1] - self.settings.pixes_2_center  # 屏幕中心偏左
            base_y = screen_center_y - self.settings.pixes_2_center  # 屏幕中心偏上
            # 绘制每张牌（垂直反向排列）
            start_x = base_x
            num = 5
            discard_rotation = -90
            discard_tiles = [tile for tile in discard_tiles if not self.is_chicken_tile(tile)]
            for i, tile in enumerate(discard_tiles):
                row = i // num
                col = i % num
                start_x = base_x - row * tile_size[1]
                start_y = base_y + col * tile_size[0]
                draw_tile(tile, (start_x, start_y), show_face=True, rotation=discard_rotation)
                if i==len(discard_tiles)-1 and show_discard_tile_indicator(player,tile):
                    self.indicator_pos = (start_x, start_y)
                    self.indicator_width = tile_size[1]

        players = self.get_players()
        selected_indices:list = self.float_tile_list

        for player in players:
            if player.position == "east":
                draw_self(player, selected_indices, show_self)
            elif player.position == "south":
                draw_after(player, show_all_faces)
            elif player.position == "west":
                draw_opposite(player, show_all_faces)
            elif player.position == "north":
                draw_before(player, show_all_faces)
            else:
                print(f"未知位置: {player.position}")
        
        # 最后绘制当前弃牌牌的指示器，防止被其他牌遮挡
        if self.discard_tile:
            draw_discard_tile_indicator(self.indicator_pos,self.indicator_width)
    
    def draw_action_buttons(self, available_actions):
        """绘制碰杠胡操作按钮
        
        Args:
            available_actions: 可用操作列表，包含'peng', 'gang', 'hu'等
        """
        # 清空之前的按钮记录
        self.action_buttons.clear()
        
        # 确保有可用操作
        if not available_actions:
            return
        
        # 过滤掉取消按钮，单独处理
        action_buttons_only = [action for action in available_actions if action != 'cancel']
        
        # 按照胡→杠→碰的优先级排序按钮
        action_priority = {'hu': 0, 'gang': 1, 'peng': 2}
        action_buttons_only.sort(key=lambda x: action_priority.get(x, 999))
        
        # 使用默认按钮尺寸，然后应用缩放比例
        default_button_width = 100
        default_button_height = 60
        
        # 应用操作按钮缩放比例
        action_button_width = int(default_button_width * 2)
        action_button_height = int(default_button_height * 2)
        
        # 计算屏幕尺寸
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # 屏幕右下角位置，留出边距
        right_margin = 50
        bottom_margin = 50
        
        # 应用取消按钮缩放比例
        cancel_button_width = int(default_button_width * 1)
        cancel_button_height = int(default_button_height * 1)
        
        # 按钮间距
        button_spacing = 10
        
        # 先处理取消按钮（放在最右边）
        cancel_x = screen_width - right_margin - cancel_button_width
        cancel_y = screen_height - bottom_margin - cancel_button_height
        
        # 然后处理操作按钮，从右往左排列
        # 计算操作按钮的起始X位置
        start_x = cancel_x - button_spacing
        
        # 绘制每个操作按钮（从右往左排列）
        for action in reversed(action_buttons_only):
            try:
                img_path = os.path.join(self.resource_dir, 'sprites', f'{action}.png')
                if os.path.exists(img_path):
                    icon = pygame.image.load(img_path).convert_alpha()
                    # 使用smoothscale替代scale以获得更好的缩放效果
                    # 保持图片原始宽高比
                    orig_width, orig_height = icon.get_size()
                    aspect_ratio = orig_width / orig_height
                    
                    # 计算保持宽高比的新尺寸
                    if action_button_width / action_button_height > aspect_ratio:
                        # 以高度为基准
                        new_height = action_button_height
                        new_width = int(new_height * aspect_ratio)
                    else:
                        # 以宽度为基准
                        new_width = action_button_width
                        new_height = int(new_width / aspect_ratio)
                    
                    icon = pygame.transform.smoothscale(icon, (new_width, new_height))
                    
                    # 计算按钮X位置，从右往左排列
                    x = start_x - action_button_width
                    y = screen_height - bottom_margin - action_button_height
                    
                    # 创建点击区域
                    click_area = pygame.Rect(x, y, action_button_width, action_button_height)
                    
                    # 计算图片在点击区域中的居中位置
                    img_x = x + (action_button_width - new_width) // 2
                    img_y = y + (action_button_height - new_height) // 2
                    
                    self.screen.blit(icon, (img_x, img_y))
                    # 记录按钮位置和类型
                    self.action_buttons[action] = click_area
                    
                    # 更新下一个按钮的起始位置
                    start_x = x - button_spacing
                    
                    # 添加调试信息
                    # pygame.draw.rect(self.screen, (255, 0, 0), click_area, 1)  # 绘制红色边框
            except Exception as e:
                print(f"绘制{action}按钮失败: {e}")
        
        # 绘制取消按钮（始终在最右边）
        try:
            cancel_path = os.path.join(self.resource_dir, 'sprites', 'cancel.png')
            if os.path.exists(cancel_path):
                cancel_icon = pygame.image.load(cancel_path).convert_alpha()
                
                # 使用smoothscale替代scale并保持宽高比
                orig_width, orig_height = cancel_icon.get_size()
                aspect_ratio = orig_width / orig_height
                
                if cancel_button_width / cancel_button_height > aspect_ratio:
                    new_height = cancel_button_height
                    new_width = int(new_height * aspect_ratio)
                else:
                    new_width = cancel_button_width
                    new_height = int(new_width / aspect_ratio)
                
                cancel_icon = pygame.transform.smoothscale(cancel_icon, (new_width, new_height))
                
                # 创建点击区域
                cancel_click_area = pygame.Rect(cancel_x, cancel_y, cancel_button_width, cancel_button_height)
                
                # 计算图片在点击区域中的居中位置
                cancel_img_x = cancel_x + (cancel_button_width - new_width) // 2
                cancel_img_y = cancel_y + (cancel_button_height - new_height) // 2
                
                self.screen.blit(cancel_icon, (cancel_img_x, cancel_img_y))
                # 记录取消按钮位置和类型
                self.action_buttons['cancel'] = cancel_click_area
                
                # 添加调试信息
                # pygame.draw.rect(self.screen, (255, 0, 0), cancel_click_area, 1)  # 绘制红色边框
        except Exception as e:
            print(f"绘制取消按钮失败: {e}")

    def check_button_click(self, pos):
        """检查鼠标点击是否击中按钮
        
        Args:
            pos: 鼠标位置坐标
            
        Returns:
            按钮类型字符串，如果没有击中任何按钮则返回None
        """
        for action, rect in self.action_buttons.items():
            if rect.collidepoint(pos):
                return action
        return None

    def show_toast(self, message, duration=None):
        """显示toast提示信息
        
        Args:
            message: 要显示的消息文本
            duration: 显示持续时间（毫秒），默认使用配置中的值
        """
        # 初始化toast相关属性
        if not hasattr(self, 'toasts'):
            self.toasts = []
        
        # 使用配置中的持续时间，如果没有指定的话
        if duration is None:
            duration = self.settings.toast_duration
        
        # 检查是否已有相同的toast消息正在显示，避免重复
        import time
        current_time = time.time() * 1000
        for toast in self.toasts:
            if toast['message'] == message and current_time - toast['start_time'] < toast['duration']:
                # 已有相同的toast正在显示，不重复添加
                return
        
        # 添加新的toast消息
        self.toasts.append({
            'message': message,
            'start_time': current_time,  # 转换为毫秒
            'duration': duration
        })
    
    def draw_toasts(self):
        """绘制所有活跃的toast提示"""
        if not hasattr(self, 'toasts') or not self.toasts:
            return
        
        import time
        current_time = time.time() * 1000
        active_toasts = []        
    
        # 自动操作Toast提示配置
        toast_bg_color = (0, 0, 0, 200)  # Toast背景颜色（RGBA）
        toast_height = 40  # Toast高度（像素）
        toast_font_color = self.settings.yellow  # Toast字体颜色
        toast_font_size = self.settings.big_font_size  # Toast字体大小
        
        # 筛选活跃的toast
        for toast in self.toasts:
            if current_time - toast['start_time'] < toast['duration']:
                active_toasts.append(toast)
        
        self.toasts = active_toasts
        
        # 创建专门用于toast的字体，使用指定的字体文件
        toast_font = pygame.font.Font(self.settings.font_path, toast_font_size)

               
        # 绘制每个活跃的toast
        toast_y = 550 # 起始Y位置，距离顶部
        for toast in self.toasts:
            # 使用配置的颜色渲染文本
            text_surface = toast_font.render(toast['message'], True, toast_font_color)
            
            # 动态计算toast背景宽度，根据文本宽度加上适当的左右边距
            # 左右各留15像素的边距，使背景稍微宽一些
            padding = 5  # 固定左右边距
            dynamic_width = text_surface.get_width() + (padding * 2)
            toast_pos_x = (self.settings.win_w - dynamic_width) // 2  # Toast显示X坐标（居中）
            
            # 创建半透明背景，使用动态宽度
            toast_surface = pygame.Surface((dynamic_width, toast_height), pygame.SRCALPHA)
            # 使用配置的背景颜色填充背景
            toast_surface.fill(toast_bg_color)
            
            # 计算文本居中位置
            text_x = (dynamic_width - text_surface.get_width()) // 2
            text_y = (toast_height - text_surface.get_height()) // 2
            
            # 绘制背景和文字
            self.screen.blit(toast_surface, (toast_pos_x, toast_y))
            self.screen.blit(text_surface, (toast_pos_x + text_x, toast_y + text_y))
            
            # 为下一个toast留出空间
            toast_y += toast_height + 5
    
    def draw_settings_and_game_number(self, total_games, is_game_over):
        """绘制设置按钮和当前局数
        
        Args:
            total_games: 总局数
            is_game_over: 游戏是否结束
        """
        # 加载字体
        font = pygame.font.Font(self.settings.font_path, self.settings.normal_font_size)
        
        # 计算当前局数
        current_game = total_games if is_game_over else (1 + total_games)
        
        # 绘制局数字符串
        # 先计算数字的宽度，然后居中显示
        number_str = str(current_game)
        # 计算3位数的总宽度（假设数字宽度为font.size("0")[0]）
        digit_width = font.size("0")[0]
        total_number_width = digit_width * 3
        # 计算居中显示的数字，使用空格填充
        centered_number_str = f"{number_str:^{total_number_width//digit_width}}"  # 居中对齐
        
        game_number_prefix = font.render("第", True, self.settings.white)
        game_number = font.render(centered_number_str, True, self.settings.yellow)
        game_number_suffix = font.render("局", True, self.settings.white)
        
        # 计算局数文本的总宽度和位置
        total_width = game_number_prefix.get_width() + game_number.get_width() + game_number_suffix.get_width()
        
        # 游戏未结束时，绘制设置按钮和暂停按钮
        if not is_game_over:
            # 绘制设置文字
            settings_text = font.render("设置", True, self.settings.white)
            settings_text_rect = settings_text.get_rect()
            settings_text_rect.x = self.game_settings_button.x + (self.game_settings_button.width - settings_text_rect.width) // 2
            settings_text_rect.y = self.game_settings_button.y + (self.game_settings_button.height - settings_text_rect.height) // 2
            self.screen.blit(settings_text, settings_text_rect)
            
            game_number_x = settings_text_rect.right + 10  # 设置文字右侧再加10像素
            
            # 保存文字区域，用于点击检测
            self.settings_text_rect = settings_text_rect
        else:
            # 游戏结束时，仅显示局数，不显示设置按钮
            game_number_x = self.game_settings_button.x
            # 清空设置按钮区域，避免点击检测
            self.settings_text_rect = None
        
        game_number_y = self.game_settings_button.y + (self.game_settings_button.height - game_number_prefix.get_height()) // 2
        
        # 绘制局数文本
        prefix_rect = game_number_prefix.get_rect()
        prefix_rect.x = game_number_x
        prefix_rect.y = game_number_y
        self.screen.blit(game_number_prefix, prefix_rect)
        
        number_rect = game_number.get_rect()
        number_rect.x = prefix_rect.right
        number_rect.y = game_number_y
        self.screen.blit(game_number, number_rect)
        
        suffix_rect = game_number_suffix.get_rect()
        suffix_rect.x = number_rect.right
        suffix_rect.y = game_number_y
        self.screen.blit(game_number_suffix, suffix_rect)
        
        # 保存局数区域，用于点击检测
        self.game_number_rect = pygame.Rect(game_number_x, game_number_y, total_width, game_number_prefix.get_height())
        
        # 游戏未结束时，绘制暂停按钮
        if not is_game_over and self.suspend_button_image:
            # 计算暂停按钮位置：局数显示右侧10像素
            suspend_button_x = suffix_rect.right + 10
            suspend_button_y = self.game_settings_button.y + (self.game_settings_button.height - 15) // 2
            # 绘制暂停按钮
            self.screen.blit(self.suspend_button_image, (suspend_button_x, suspend_button_y))
            # 保存暂停按钮区域
            self.suspend_button = pygame.Rect(suspend_button_x, suspend_button_y, 15, 15)
        else:
            # 游戏结束时，清空暂停按钮区域
            self.suspend_button = None

    def get_tile_index_from_position(self, pos):
        """根据鼠标位置获取手牌索引
        
        Args:
            pos: 鼠标位置
            
        Returns:
            牌的索引，如果不在手牌区域则返回None
        """
        # 如果隐藏手牌信息未设置，则返回None
        if self.concealed_hands_info is None:
            return -1
        
        # 从隐藏手牌信息中获取相关参数
        start_x, start_y, tile_width, tile_height, num_tiles = self.concealed_hands_info
        
        # 检查是否在隐藏手牌区域内
        if start_x <= pos[0] <= start_x + tile_width * num_tiles and start_y <= pos[1] <= start_y + tile_height:
            # 计算点击的牌索引（修正计算方式）
            index = (pos[0] - start_x) // tile_width
            # 确保索引是整数类型
            index = int(index)
            if 0 <= index < num_tiles:
                return index
        
        return -1

    def move_selection_left(self):
        """将选中牌索引向左移动"""
        concealed = self.get_human_player().get_concealed_hand()
        if not self.float_tile_list:
            selected_tile_index = 0
        else:
            selected_tile_index = self.float_tile_list[0]
        self.float_tile_list = [(selected_tile_index - 1) % len(concealed)]

    def move_selection_right(self):
        """将选中牌索引向右移动"""
        concealed = self.get_human_player().get_concealed_hand()
        if not self.float_tile_list:
            selected_tile_index = len(concealed)
        else:
            selected_tile_index = self.float_tile_list[0]
        self.float_tile_list = [(selected_tile_index + 1) % len(concealed)]

    def _draw_game_over_screen(self, winners, total_games=-1, draw_games=-1, hu_type=None):
        """绘制游戏结束屏幕
        
        在游戏结束时显示结算结果，包括所有玩家的头像、名字、手牌和标签
        
        Args:
            winners: 赢家列表
            total_games: 总局数
            draw_games: 流局数
            hu_type: 胡牌类型统计字典
        """
        # 绘制半透明蒙层
        overlay = pygame.Surface((self.settings.win_w, self.settings.win_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # 半透明黑色蒙层
        self.screen.blit(overlay, (0, 0))
        
        # 获取所有玩家
        players = self.get_players()
        
        # 1. 绘制游戏结局
        
        # 获取赢家列表
        winners = winners
        
        # 游戏结局图片路径映射
        game_result_images = {
            'draw': os.path.join(self.resource_dir, 'sprites', 'draw.png'),  # 流局
            'before': os.path.join(self.resource_dir, 'sprites', 'before_win.png'),  # 上家胜
            'opposite': os.path.join(self.resource_dir, 'sprites', 'opposite_win.png'),  # 对家胜
            'next': os.path.join(self.resource_dir, 'sprites', 'next_win.png'),  # 下家胜
            'self': os.path.join(self.resource_dir, 'sprites', 'self_win.png')  # 本家胜
        }
        
        # 位置关系映射（相对于人类玩家east）
        position_relative = {
            'north': 'before',  # 北 -> 上家
            'west': 'opposite',  # 西 -> 对家
            'south': 'next',  # 南 -> 下家
            'east': 'self'  # 东 -> 本家
        }
        
        # 加载并绘制游戏结局图片
        if not winners:
            # 流局
            self.game_end_img = [game_result_images['draw']]
            result_img = pygame.image.load(game_result_images['draw']).convert_alpha()
            # 缩小为原始尺寸的0.9倍
            scaled_width = int(result_img.get_width() * 0.9)
            scaled_height = int(result_img.get_height() * 0.9)
            result_img = pygame.transform.smoothscale(result_img, (scaled_width, scaled_height))
            # 整个屏幕居中，与上边缘的距离改为15像素
            img_x = (self.settings.win_w - scaled_width) // 2
            img_y = 15  # 与上边缘的距离改为15像素
            self.screen.blit(result_img, (img_x, img_y))
        else:
            # 多个赢家
            result_imgs = []
            game_end_image = []
            # 确保每种结局类型只显示一次
            shown_results = set()
            
            for winner in winners:
                win_pos = winner.position
                relative_pos = position_relative.get(win_pos, 'self')
                if relative_pos not in shown_results:
                    shown_results.add(relative_pos)
                    img_path = game_result_images[relative_pos]
                    try:
                        result_img = pygame.image.load(img_path).convert_alpha()
                        # 缩小为原始尺寸的0.9倍
                        scaled_width = int(result_img.get_width() * 0.9)
                        scaled_height = int(result_img.get_height() * 0.9)
                        result_img = pygame.transform.smoothscale(result_img, (scaled_width, scaled_height))
                        result_imgs.append(result_img)
                        game_end_image.append(img_path)
                    except Exception as e:
                        print(f"加载游戏结局图片失败: {e}")
            
            # 计算总宽度和起始位置 - 整个屏幕居中，与上边缘的距离改为15像素
            self.game_end_img = game_end_image
            total_width = sum(img.get_width() + 20 for img in result_imgs) - 20  # 图片间距20px
            start_x = (self.settings.win_w - total_width) // 2
            img_y = 15  # 与上边缘的距离改为15像素
            
            # 绘制所有结局图片
            current_x = start_x
            for img in result_imgs:
                self.screen.blit(img, (current_x, img_y))
                current_x += img.get_width() + 20
        
        # 2. 绘制游戏结果（右侧中部）
        # 定义不同用途的字体
        big_font = pygame.font.Font(self.settings.font_path, self.settings.big_font_size)  # 大字体
        normal_font = pygame.font.Font(self.settings.font_path, self.settings.normal_font_size)  # 正常字体
        small_font = pygame.font.Font(self.settings.font_path, self.settings.small_font_size)  # 小字体
        
        # 计算结果区域位置
        result_start_x = self.settings.win_w - 360
        result_start_y = 96
        result_width = 337
        result_height = 545
        
        # 绘制结果背景 - 使用resource\table\result_right.png并缩小为原尺寸的0.91倍
        result_bg_path = os.path.join(self.resource_dir, 'table', 'result_right.png')
        if os.path.exists(result_bg_path):
            result_bg = pygame.image.load(result_bg_path).convert_alpha()
            # 缩小为原尺寸的0.91倍
            original_width, original_height = result_bg.get_size()
            scaled_width = int(original_width * 0.91)
            scaled_height = int(original_height * 0.91)
            result_bg = pygame.transform.smoothscale(result_bg, (scaled_width, scaled_height))
            # 使用原起始x和y坐标
            self.screen.blit(result_bg, (result_start_x, result_start_y))
        else:
            # 如果图片不存在，使用默认的半透明黑色背景
            result_bg = pygame.Surface((result_width, result_height), pygame.SRCALPHA)
            result_bg.fill((0, 0, 0, 180))  # 半透明黑色背景
            self.screen.blit(result_bg, (result_start_x, result_start_y))
        
        # 绘制结果标题 - 使用big字号
        result_title = big_font.render("游戏结果", True, self.settings.black)  # 黑色文字
        self.screen.blit(result_title, (result_start_x + (result_width - result_title.get_width()) // 2 , result_start_y + 25))
        
        # 绘制分隔线 - 调整位置，靠近标题
        pygame.draw.line(self.screen, self.settings.black, 
                         (result_start_x + 21, result_start_y + 50), 
                         (result_start_x + result_width, result_start_y + 50), 2)
        
        # 绘制总局数和流局数/流局率到同一行 - 使用normal字体
        current_y = result_start_y + 65
        # 使用传入的真实总局数和流局数
        draw_rate = (draw_games / total_games * 100) if total_games > 0 else 0  # 流局率
        
        # 总局数、流局数和流局率放到同一行 - 使用normal字体
        combined_text = f"总  数: {total_games:3} 局   黄牌数: {draw_games:3} 局   黄牌率: {draw_rate:.1f}%"
        combined_surface = normal_font.render(combined_text, True, self.settings.black)  # 黑色文字
        self.screen.blit(combined_surface, (result_start_x + 30, current_y))
        current_y += 40  # 先增加Y坐标，避免与总局数行重合

        # 绘制胡牌类型统计
        if hu_type:
            # 将胡牌类型转换为列表，方便分组
            hu_type_list = list(hu_type.items())
            # 每行显示3个胡牌类型
            for i in range(0, len(hu_type_list), 3):
                # 获取当前行的3个胡牌类型
                row_types = hu_type_list[i:i+3]
                # 计算行内每个胡牌类型的位置，使它们居中对齐
                row_text = "   ".join([f"{tag.value}: {count:3} 局" for tag, count in row_types])
                row_surface = normal_font.render(row_text, True, self.settings.black)  # 黑色文字
                row_x = result_start_x + 30
                self.screen.blit(row_surface, (row_x, current_y))
                current_y += 25  # 每行间隔25像素
        else:
            # 如果没有胡牌记录，显示提示信息
            no_hu_text = "暂无胡牌记录"
            no_hu_surface = normal_font.render(no_hu_text, True, self.settings.black)  # 黑色文字
            no_hu_x = result_start_x + (result_width - no_hu_surface.get_width()) // 2
            self.screen.blit(no_hu_surface, (no_hu_x, current_y))
            current_y += 25
        
        current_y += 25  # 与排行榜标题之间的间隔
        
        # 绘制排行榜标题 - 使用big_font_size
        ranking_title = big_font.render("排行榜", True, self.settings.black)  # 黑色文字，使用大字体
        self.screen.blit(ranking_title, (result_start_x + (result_width - ranking_title.get_width()) // 2, current_y))
        current_y += 40
        
        # 计算每个玩家的积分变化和数据
        for player in players:
            # 从player.result['total_ji']获取本局总得分
            current_round_score = player.result.get('total_ji', 0) if hasattr(player, 'result') else 0
            player.round_contribution = current_round_score
            
            # 计算胡牌率和点炮率，冲锋鸡率和横鸡率
            win_rate = player.win_rate * 100  # 胡牌率
            OfferingWin_rate = player.OfferingWin_rate * 100  # 点炮率
            gain_ji_rate = player.gain_ji_rate * 100  # 冲锋鸡率
            loss_ji_rate = player.loss_ji_rate * 100  # 横鸡率
        
        # 按当前积分排序
        sorted_players = sorted(players, key=lambda p: p.score, reverse=True)
        
        # 绘制融合后的排行榜 - 每个玩家显示三行数据
        for player in sorted_players:
            # 从player.result['total_ji']获取本局总得分
            current_round_score = player.result.get('total_ji', 0) if hasattr(player, 'result') else 0
            
            # 1. 第一行：名字（统一定长字符串为3个中文字符的长度），115 = 100 + 15
            # 格式化名字，统一定长为3个中文字符
            formatted_name = f"{player.name:<6}({player.ai_version}): "  # 左对齐，宽度为3个中文字符
            # 显示积分计算式
            score_formula = f"{player.score:4} = {player.previous_score:4} {current_round_score:<+3}"
            # 使用normal字体
            color = self.settings.blue if player.is_human else self.settings.black
            first_line_surface = normal_font.render(f"{formatted_name} {score_formula}", True, color)
            self.screen.blit(first_line_surface, (result_start_x + 30, current_y))
            current_y += 20
            
            # 2. 第二行，统一定长字符串为3个中文字符的长度，显示胡牌/百分比，冲锋鸡/百分比（百分比显示2为小数）
            # 格式化胡牌数据
            win_text = f"胡牌: {player.win_count:2}局/{player.win_rate:4.1f}%"
            # 格式化冲锋鸡数据
            gain_ji_text = f"冲鸡: {player.gain_ji_count:2}分/{player.gain_ji_rate:4.1f}%"
            # 使用small字体
            second_line_surface = small_font.render(f"      {win_text}      {gain_ji_text}", True, self.settings.black)
            self.screen.blit(second_line_surface, (result_start_x + 30, current_y))
            current_y += 20
            
            # 3. 第三行，统一定长字符串为3个中文字符的长度，显示点炮/百分比，横鸡/百分比（百分比显示2为小数）
            # 格式化点炮数据
            OfferingWin_text = f"献胡: {player.OfferingWin_count:2}局/{player.OfferingWin_rate:4.1f}%"
            # 格式化横鸡数据
            loss_ji_text = f"丢鸡: {player.loss_ji_count:2}分/{player.loss_ji_rate:4.1f}%"
            # 使用small字体
            third_line_surface = small_font.render(f"      {OfferingWin_text}      {loss_ji_text}", True, self.settings.black)
            self.screen.blit(third_line_surface, (result_start_x + 30, current_y))
            current_y += 40
        
        # 确定玩家显示顺序：上家/本家/下家/对家
        display_order = []
        
        # 找到人类玩家（本家）
        human_player = None
        for p in players:
            if hasattr(p, 'is_human') and p.is_human:
                human_player = p
                break
        
        if human_player:
            # 创建位置到玩家的映射
            position_to_player = {p.position: p for p in players}
            
            # 确定上家、下家、对家的位置
            # 假设玩家位置顺序：east（本家）、south（下家）、west（对家）、north（上家）
            # 或者根据实际位置关系调整
            order = []
            
            # 添加上家（north）
            if 'north' in position_to_player:
                order.append(position_to_player['north'])
            
            # 添加本家（east）
            if 'east' in position_to_player:
                order.append(position_to_player['east'])
            
            # 添加下家（south）
            if 'south' in position_to_player:
                order.append(position_to_player['south'])
            
            # 添加对家（west）
            if 'west' in position_to_player:
                order.append(position_to_player['west'])
            
            display_order = order
        else:
            # 如果找不到人类玩家，使用默认顺序
            display_order = players
        
        # 设置初始位置和间距
        start_x = 50
        start_y = 120
        player_spacing = 130  # 玩家之间的垂直间距
        
        # 绘制每个玩家的信息：头像、名字、手牌
        for i, player in enumerate(display_order):
            # 计算当前玩家的起始Y位置
            current_y = start_y + i * player_spacing
            
            # 1. 绘制头像
            avatar = self.load_image(player.avatar, self.settings.avatar_size)
            avatar_x = start_x
            avatar_y = current_y
            self.screen.blit(avatar, (avatar_x, avatar_y))
            
            # 2. 绘制名字（头像下方）
            name = f"{player.name}(玩家)" if player.is_human else player.name
            name_font = pygame.font.Font(self.settings.font_path, self.settings.normal_font_size)
            name_surface = name_font.render(name, True, self.settings.white)
            name_x = avatar_x + (self.settings.avatar_size[0] - name_surface.get_width()) // 2
            name_y = avatar_y + self.settings.avatar_size[1] + 5
            self.screen.blit(name_surface, (name_x, name_y))
            
            # 3. 绘制手牌（公开牌 + 隐藏牌）
            hand_start_x = start_x + self.settings.avatar_size[0] + 20  # 麻将与头像之间的距离改为20像素
            hand_start_y = current_y
            
            # 绘制公开牌
            exposed_hand = player.get_exposed_hand()
            # 使用deal_chicken_group处理公开手牌，增加显示鸡牌的特殊牌
            exposed_hand = self.deal_chicken_group(player, exposed_hand)
            current_x = hand_start_x
            for group in exposed_hand:
                if isinstance(group, dict) and 'tiles' in group:
                    tiles = group['tiles']
                    for tile in tiles:
                        # 绘制单张牌，组内牌之间无间隔
                        if tile in self.tiles:
                            tile_img = self.tiles[tile]
                            scaled_img = pygame.transform.smoothscale(tile_img, self.settings.tile_size)
                            self.screen.blit(scaled_img, (current_x, hand_start_y))
                            current_x += self.settings.tile_size[0]  # 组内牌之间无间隔
                    current_x += 5  # 公开牌每组牌之间的距离改为5像素
            
            # 公开牌和隐藏牌之间间隔10像素
            if exposed_hand:
                current_x += 10  # 公开牌与隐藏牌之间距离10像素
            
            # 绘制隐藏牌
            concealed_hand = player.get_concealed_hand()
            
            # 检查是否是胡牌玩家
            is_winner = player in winners
            
            # 如果是胡牌玩家，最后一张牌与隐藏手牌之间有间距
            if is_winner and concealed_hand:
                # 隐藏手牌（除了最后一张）
                for i in range(len(concealed_hand) - 1):
                    tile = concealed_hand[i]
                    if tile in self.tiles:
                        tile_img = self.tiles[tile]
                        scaled_img = pygame.transform.smoothscale(tile_img, self.settings.tile_size)
                        self.screen.blit(scaled_img, (current_x, hand_start_y))
                        current_x += self.settings.tile_size[0]  # 组内牌之间无间隔
                
                # 胡的牌（最后一张），增加间距
                current_x += 10  # 胡牌者最后一张牌与隐藏牌之间的距离5像素
                tile = concealed_hand[-1]
                if tile in self.tiles:
                    tile_img = self.tiles[tile]
                    scaled_img = pygame.transform.smoothscale(tile_img, self.settings.tile_size)
                    self.screen.blit(scaled_img, (current_x, hand_start_y))
            else:
                # 非胡牌玩家，直接绘制所有隐藏牌
                for tile in concealed_hand:
                    if tile in self.tiles:
                        tile_img = self.tiles[tile]
                        scaled_img = pygame.transform.smoothscale(tile_img, self.settings.tile_size)
                        self.screen.blit(scaled_img, (current_x, hand_start_y))
                        current_x += self.settings.tile_size[0]  # 组内牌之间无间隔
            
            # 4. 绘制标签（第二行和第三行）
            tags = player.get_tags()
            result = player.result if hasattr(player, 'result') else {}
            
            # 4.1 绘制叫牌状态
            if result.get('jiaopai', False):
                ting_str = "已叫牌"
                color = self.settings.yellow
                if is_winner:
                    ting_str = "大赢家"
                    color = self.settings.green
            else:
                ting_str = "米叫牌"
                color = self.settings.red

            tags_font = pygame.font.Font(self.settings.font_path, self.settings.small_font_size)
            tags_surface = tags_font.render(ting_str, True, color)
            tags_x = hand_start_x
            tags_y = hand_start_y + self.settings.tile_size[1] + 10
            self.screen.blit(tags_surface, (tags_x, tags_y))

            # 4.2 绘制本局鸡牌
            ji_str = f"本局：{result.get('total_ji', 0):+3}"
            tags_str = ji_str + "     " + "、".join([tag['tag'].value for tag in tags]) if tags else ji_str
            tags_surface = tags_font.render(tags_str, True, self.settings.yellow)
            tags_x = hand_start_x + 50
            tags_y = hand_start_y + self.settings.tile_size[1] + 10
            self.screen.blit(tags_surface, (tags_x, tags_y))

            # 4.3 绘制鸡牌来源
            source = []
            # 提取鸡牌来源信息
            if result.get('hu_ji', {}).get('source'):
                source.extend(result.get('hu_ji', {}).get('source', []))
            if result.get('ji', {}).get('source'):
                source.extend(result.get('ji', {}).get('source', []))
            if result.get('gang_ji', {}).get('source'):
                source.extend(result.get('gang_ji', {}).get('source', []))
            
            if source:
                source_str = '、  '.join(source)
                tags_surface = tags_font.render(source_str, True, self.settings.white)
                tags_x = hand_start_x
                tags_y = hand_start_y + self.settings.tile_size[1] + 30
                self.screen.blit(tags_surface, (tags_x, tags_y))
        
        # 绘制翻鸡牌
        if winners:
            fanji_type = "上下鸡" if self.settings.shangxia_ji else "下鸡"
            jin_ji = True if self.fanji_tile in ['2条','9条'] else False
            
            fanji_str = f"翻鸡({fanji_type}): {' '.join([f'[{tile}]' for tile in self.fanji_tiles])} {'(🐔金鸡🐔)' if jin_ji else ''}"
            tags_surface = tags_font.render(fanji_str, True, self.settings.yellow)
            tags_x = start_x
            tags_y = start_y + player_spacing*4
            self.screen.blit(tags_surface, (tags_x, tags_y))

            # tile_img = self.tiles[self.fanji_tile]
            # scaled_img = pygame.transform.smoothscale(tile_img, self.settings.tile_size)
            # x = start_x + self.settings.avatar_size[0] + 100
            # self.screen.blit(scaled_img, (x, tags_y))

        for i,tile in enumerate(self.fanji_tiles):
            if tile in self.tiles:
                tile_img = self.tiles[tile]
                scaled_img = pygame.transform.smoothscale(tile_img, self.settings.tile_size)
                x = start_x + self.settings.avatar_size[0] + 100 + (i+1)*(self.settings.tile_size[0]+10)
                self.screen.blit(scaled_img, (x, tags_y))

        # 5. 绘制按钮（本局详情、查看桌面、再来一局、返回桌面）
        button_font = pygame.font.Font(self.settings.font_path, self.settings.normal_font_size)
        
        # 按钮尺寸和间距 - 缩小按钮宽度，增加圆角
        button_width = 90  # 宽度缩小50像素（从120变为70）
        button_height = 40
        button_spacing = 15
        corner_radius = 10  # 圆角增加15像素（从8变为23）
        
        # 计算按钮位置 - 移动到屏幕右下角，水平排列，再往下移动15像素，往右移动15像素
        button_start_y = self.settings.win_h - button_height - 15  # 底部距屏幕底部10像素，再往下移动15像素
        total_width = button_width * 4 + button_spacing * 3
        button_start_x = self.settings.win_w - total_width - 35  # 右边缘距屏幕右侧50像素，再往右移动15像素
        
        # 创建绘制圆角矩形的函数
        def draw_rounded_rect(surface, rect, color, radius):
            pygame.draw.rect(surface, color, rect, border_radius=radius)
        
        # 保存按钮区域，用于后续检测点击
        self.game_over_buttons = {
            'result_detail': pygame.Rect(button_start_x, button_start_y, button_width, button_height),  # 本局详情在左
            'view_table': pygame.Rect(button_start_x + button_width + button_spacing, button_start_y, button_width, button_height),  # 查看桌面在左中
            'restart': pygame.Rect(button_start_x + (button_width + button_spacing) * 2, button_start_y, button_width, button_height),  # 再来一局在右中
            'back_to_menu': pygame.Rect(button_start_x + (button_width + button_spacing) * 3, button_start_y, button_width, button_height)  # 返回桌面在右
        }
        
        # 绘制"本局详情"按钮（左）
        result_detail_text = button_font.render("本局详情", True, self.settings.white)
        # 使用圆角矩形
        draw_rounded_rect(self.screen, self.game_over_buttons['result_detail'], (128, 0, 128), corner_radius)  # 紫色按钮
        result_detail_text_x = button_start_x + (button_width - result_detail_text.get_width()) // 2
        result_detail_text_y = button_start_y + (button_height - result_detail_text.get_height()) // 2
        self.screen.blit(result_detail_text, (result_detail_text_x, result_detail_text_y))
        
        # 绘制"查看桌面"按钮（左中）
        view_table_text = button_font.render("查看桌面", True, self.settings.white)
        # 使用圆角矩形
        draw_rounded_rect(self.screen, self.game_over_buttons['view_table'], (0, 0, 128), corner_radius)  # 蓝色按钮
        view_table_text_x = button_start_x + button_width + button_spacing + (button_width - view_table_text.get_width()) // 2
        view_table_text_y = button_start_y + (button_height - view_table_text.get_height()) // 2
        self.screen.blit(view_table_text, (view_table_text_x, view_table_text_y))
        
        # 绘制"再来一局"按钮（右中）
        restart_text = button_font.render("再来一局", True, self.settings.white)
        # 使用圆角矩形
        draw_rounded_rect(self.screen, self.game_over_buttons['restart'], (0, 128, 0), corner_radius)  # 绿色按钮
        restart_text_x = button_start_x + (button_width + button_spacing) * 2 + (button_width - restart_text.get_width()) // 2
        restart_text_y = button_start_y + (button_height - restart_text.get_height()) // 2
        self.screen.blit(restart_text, (restart_text_x, restart_text_y))
        
        # 绘制"返回桌面"按钮（右）
        back_to_menu_text = button_font.render("返回主页", True, self.settings.white)
        # 使用圆角矩形
        draw_rounded_rect(self.screen, self.game_over_buttons['back_to_menu'], (255, 165, 0), corner_radius)  # 橙色按钮
        back_to_menu_text_x = button_start_x + (button_width + button_spacing) * 3 + (button_width - back_to_menu_text.get_width()) // 2
        back_to_menu_text_y = button_start_y + (button_height - back_to_menu_text.get_height()) // 2
        self.screen.blit(back_to_menu_text, (back_to_menu_text_x, back_to_menu_text_y))
        
        # 显示本局详情
        if self.show_result_detail:
            try:
                # 加载本局详情图片
                result_img_path = os.path.join(self.resource_dir, 'table', 'result.png')
                if os.path.exists(result_img_path):
                    result_img = pygame.image.load(result_img_path).convert_alpha()
                    # 放大为原尺寸的1.2倍
                    img_width, img_height = result_img.get_size()
                    scale = 1.5
                    new_width = int(img_width * scale)
                    new_height = int(img_height * scale)
                    result_img = pygame.transform.smoothscale(result_img, (new_width, new_height))
                    
                    # 计算图片位置，左侧/上侧与麻将牌的左侧/上侧对齐，刚好盖住麻将牌
                    # 麻将牌的起始位置（根据前面的代码：start_x + self.settings.avatar_size[0] + 30）
                    # 假设玩家信息从start_x=100开始绘制
                    img_x = 20  # 左侧与麻将牌对齐
                    img_y = 90  # 上侧与麻将牌对齐，不盖住赢家图片
                    
                    # 绘制图片
                    self.screen.blit(result_img, (img_x, img_y))
                    
                    # 取消本局详情图片的蒙层
                    
                    # 在图片上显示本局详情 - 使用黑色字体和emoji美化
                    detail_font = pygame.font.Font(self.settings.font_path, 12)  # 合适的字体大小
                    small_font = pygame.font.Font(self.settings.font_path, 14)  # 更大的字体用于关闭提示
                    line_spacing = 18
                    
                    # 头像大小 - 使用64*64
                    avatar_size = (64, 64)
                    avatar_spacing = 10
                    
                    # 确定玩家显示顺序：上家/本家/下家/对家
                    display_order = []
                    
                    # 找到人类玩家（本家）
                    human_player = None
                    for p in players:
                        if hasattr(p, 'is_human') and p.is_human:
                            human_player = p
                            break
                    
                    if human_player:
                        # 创建位置到玩家的映射
                        position_to_player = {p.position: p for p in players}
                        
                        # 确定上家、下家、对家的位置
                        # 假设玩家位置顺序：east（本家）、south（下家）、west（对家）、north（上家）
                        order = []
                        
                        # 添加上家（north）
                        if 'north' in position_to_player:
                            order.append(position_to_player['north'])
                        
                        # 添加本家（east）
                        if 'east' in position_to_player:
                            order.append(position_to_player['east'])
                        
                        # 添加下家（south）
                        if 'south' in position_to_player:
                            order.append(position_to_player['south'])
                        
                        # 添加对家（west）
                        if 'west' in position_to_player:
                            order.append(position_to_player['west'])
                        
                        display_order = order
                    else:
                        # 如果找不到人类玩家，使用默认顺序
                        display_order = players
                    
                    blue = self.settings.blue
                    black = self.settings.black
                    # 4个玩家分两行显示，每行两个玩家
                    for i, player in enumerate(display_order):
                        if hasattr(player, 'result') and player.result:
                            result = player.result
                            
                            # 计算位置
                            row = i // 2
                            col = i % 2
                            
                            # 玩家信息起始位置
                            player_x = img_x + 50 + col * (new_width // 2)
                            player_y = img_y + 50 + row * (new_height // 2)
                            current_y = player_y
                            
                            # 绘制玩家头像 - 64*64
                            avatar_img = pygame.image.load(player.avatar).convert_alpha()
                            avatar_img = pygame.transform.smoothscale(avatar_img, avatar_size)
                            self.screen.blit(avatar_img, (player_x, current_y))
                            
                            # 绘制玩家名字 - 显示在头像正下方居中
                            name_text = player.name + (f"({player.ai_version})" if hasattr(player, 'ai_version') else "")
                            name_surface = detail_font.render(name_text, True, blue)  # 黑色文字
                            name_x = player_x + (avatar_size[0] - name_surface.get_width()) // 2  # 居中显示
                            name_y = current_y + avatar_size[1] + 5  # 头像下方5像素
                            self.screen.blit(name_surface, (name_x, name_y))
                            
                            # 结算信息起始位置（头像右侧）
                            info_x = player_x + avatar_size[0] + 10  # 头像右侧10像素
                            info_y = current_y
                            
                            # 绘制叫牌状态 - 使用文字"是"/"否"，确保中文正常显示
                            # 拆分文字，分别使用不同颜色渲染
                            jiaopai_label = "叫   牌 : "
                            jiaopai_value = "是" if result.get('jiaopai') else "否"
                            if player in winners:
                                jiaopai_value = "赢家"
                                                            
                            # 渲染标签部分（黑色）
                            label_surface = detail_font.render(jiaopai_label, True, black)
                            
                            # 根据值选择颜色
                            value_color = self.settings.red if jiaopai_value == "否" else self.settings.green
                            # 渲染值部分（绿色或红色）
                            value_surface = detail_font.render(jiaopai_value, True, value_color)
                            
                            # 计算总宽度，确保对齐
                            total_width = label_surface.get_width() + value_surface.get_width()
                            
                            # 绘制标签
                            self.screen.blit(label_surface, (info_x, info_y))
                            # 绘制值（标签右侧）
                            self.screen.blit(value_surface, (info_x + label_surface.get_width(), info_y))
                            current_y = info_y + line_spacing
                            
                            # 绘制总鸡数 - 头像右侧
                            total_ji_text = f"本   局 : {result.get('total_ji', 0):<+3}"
                            total_ji_surface = detail_font.render(total_ji_text, True, black)  # 黑色文字
                            self.screen.blit(total_ji_surface, (info_x, current_y))
                            current_y += line_spacing
                            
                            # 绘制胡牌信息 - 头像右侧
                            if result.get('hu_ji', {}).get('num', 0) > 0:
                                hu_ji = result.get('hu_ji')
                                hu_ji_num = hu_ji.get('num', 0)
                                hu_ji_sources = hu_ji.get('source', [])
                                hu_ji_source_str = ', '.join(hu_ji_sources) if hu_ji_sources else ''
                                hu_ji_text = f"胡   牌 : {hu_ji_num:<+3}  {hu_ji_source_str}"
                                hu_ji_surface = detail_font.render(hu_ji_text, True, black)  # 黑色文字
                                self.screen.blit(hu_ji_surface, (info_x, current_y))
                                current_y += line_spacing
                            
                            # 绘制冲鸡信息 - 头像右侧
                            if result.get('ji', {}).get('source', ""):
                                ji = result.get('ji')
                                ji_num = ji.get('num', 0)
                                ji_sources = ji.get('source', [])
                                ji_source_str = ', '.join(ji_sources) if ji_sources else ''
                                ji_text = f"鸡   牌 : {ji_num:+3}  {ji_source_str}"
                                ji_surface = detail_font.render(ji_text, True, black)  # 黑色文字
                                self.screen.blit(ji_surface, (info_x, current_y))
                                current_y += line_spacing
                            
                            # 绘制杠牌信息 - 头像右侧
                            if result.get('gang_ji', {}).get('source', ""):
                                gang_ji = result.get('gang_ji')
                                gang_ji_num = gang_ji.get('num', 0)
                                gang_ji_sources = gang_ji.get('source', [])
                                gang_ji_source_str = ', '.join(gang_ji_sources) if gang_ji_sources else ''
                                gang_ji_text = f"杠   牌 : {gang_ji_num:+3}  {gang_ji_source_str}"
                                gang_ji_surface = detail_font.render(gang_ji_text, True, black)  # 黑色文字
                                self.screen.blit(gang_ji_surface, (info_x, current_y))
                                current_y += line_spacing
                            
                            # 绘制与其他玩家结算信息 - 头像下方，保持左边与头像左边对齐，不覆盖玩家名字
                            if result.get('count_with_other_player'):
                                # 计算头像下方的起始位置 - 玩家名字下方，不覆盖
                                # 玩家名字位置：name_x, name_y
                                # 玩家名字高度：name_surface.get_height()
                                # 头像下方的起始位置：玩家名字下方10像素
                                under_avatar_x = player_x  # 左边与头像左边对齐
                                under_avatar_y = name_y + name_surface.get_height() + 10  # 玩家名字下方10像素
                                
                                # 绘制标题 - 左边与头像左边对齐
                                other_count_title = f"结算:"  
                                other_count_title_surface = detail_font.render(other_count_title, True, black)  # 黑色文字
                                self.screen.blit(other_count_title_surface, (under_avatar_x, under_avatar_y))
                                under_avatar_y += line_spacing
                                
                                # 绘制每个玩家的结算信息 - 左边与头像左边对齐
                                for item in result['count_with_other_player']:
                                    player_name = item['name']
                                    count_num = item['num']
                                    count_source = item.get('source', '')
                                    
                                    # 处理原因部分，原因为空时不显示括号
                                    if count_source:
                                        
                                        # 支持中/英文分隔符（, 或 、），并去除多余空格
                                        reasons = [r.strip() for r in count_source.split(',') if r.strip()]
                                        
                                        # 每行最多显示3个原因，多出的换行显示
                                        if reasons:
                                            for i in range(0, len(reasons), 3):
                                                current_reasons = reasons[i:i+3]
                                                reason_text = ', '.join(current_reasons)
                                                # 第一行显示玩家名和分数，后续行只显示原因并适当缩进对齐
                                                if i == 0:
                                                    count_text = f"{player_name:4}: {count_num:<+3}  {reason_text}"
                                                else:
                                                    count_text = f"{'':14}{reason_text}"  # 缩进对齐
                                                count_surface = detail_font.render(count_text, True, black)
                                                self.screen.blit(count_surface, (under_avatar_x, under_avatar_y))
                                                under_avatar_y += line_spacing
                                        else:
                                            # 没有可显示的原因时只显示名字和分数
                                            count_text = f"{player_name:4}: {count_num:<+3}"
                                            count_surface = detail_font.render(count_text, True, black)
                                            self.screen.blit(count_surface, (under_avatar_x, under_avatar_y))
                                            under_avatar_y += line_spacing

                                    else:
                                        # 没有原因时不显示括号
                                        count_text = f"{player_name:4}: {count_num:+3}"
                                        count_surface = detail_font.render(count_text, True, black)  # 黑色文字
                                        # 左边与头像左边对齐
                                        self.screen.blit(count_surface, (under_avatar_x, under_avatar_y))
                                        under_avatar_y += line_spacing
                    
                    # 绘制关闭按钮提示 - 红色小字体，距离底边缘5像素
                    red = self.settings.red
                    close_text = small_font.render("点击图片外区域关闭", True, red)  # 红色文字
                    close_y = img_y + new_height - 5 - close_text.get_height()
                    self.screen.blit(close_text, (img_x + (new_width - close_text.get_width()) // 2, close_y))
            except Exception as e:
                print(f"加载或绘制本局详情失败: {e}")

    def _draw_game_history(self):
        """绘制历史对局页面"""
        import json
        import os
        from datetime import datetime
        
        # 初始化按钮矩形字典，确保它们在事件处理时存在
        self._delete_buttons = {}
        self._detail_buttons = {}
        
        # 绘制背景
        bg_image = pygame.image.load(self.settings.bg_img).convert()
        bg_image = pygame.transform.smoothscale(bg_image, (self.settings.win_w, self.settings.win_h))
        self.screen.blit(bg_image, (0, 0))
        
        # 绘制半透明蒙层
        overlay = pygame.Surface((self.settings.win_w, self.settings.win_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))  # 半透明黑色蒙层
        self.screen.blit(overlay, (0, 0))
        
        # 初始化历史记录数据
        history_records = []
        
        # 1. 检查并添加本次游戏运行期间的对局数据（在内存中）
        if self.game_manager.total_games > 0:
            current_record = {
                'type': 'current',
                'timestamp': datetime.now().isoformat(),
                'total_games': self.game_manager.total_games,
                'draw_games': self.game_manager.draw_games,
                'hu_type': self.game_manager.hu_type,
                'players': self.game_manager.players
            }
            history_records.append(current_record)
        
        # 2. 从存储目录中加载历史对局记录
        history_dir = os.path.join('data', 'history')
        if os.path.exists(history_dir):
            # 遍历history目录下的所有子文件夹
            for folder_name in os.listdir(history_dir):
                folder_path = os.path.join(history_dir, folder_name)
                if os.path.isdir(folder_path):
                    # 跳过当前游戏的历史记录文件夹，避免显示重复的卡片
                    # 检查是否存在game对象及其history_folder_path属性
                    skip_this_folder = False
                    try:
                        if hasattr(self, 'game'):
                            if hasattr(self.game, 'history_folder_path'):
                                if folder_path == self.game.history_folder_path:
                                    skip_this_folder = True
                    except Exception:
                        pass
                    if skip_this_folder:
                        continue
                    # 获取文件夹中的所有JSON文件
                    json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
                    
                    # 只读取与文件夹同名的JSON文件（总览文件）
                    folder_name = os.path.basename(folder_path)
                    summary_file = f"{folder_name}.json"
                    if summary_file in json_files:
                        json_path = os.path.join(folder_path, summary_file)
                        try:
                            with open(json_path, 'r', encoding='utf-8') as f:
                                record_data = json.load(f)
                            
                            # 将JSON数据转换为适合显示的格式
                            # 转换hu_type字典
                            from source.public import Tag
                            hu_type_dict = {}
                            if 'hu_type' in record_data:
                                for tag_value, count in record_data['hu_type'].items():
                                    for tag in Tag:
                                        if tag.value == tag_value:
                                            hu_type_dict[tag] = count
                                            break
                            
                            record = {
                                'type': 'history',
                                'timestamp': record_data.get('timestamp', datetime.now().isoformat()),
                                'start_timestamp': record_data.get('start_timestamp', record_data.get('timestamp', datetime.now().isoformat())),
                                'total_games': record_data.get('total_games', 0),
                                'draw_games': record_data.get('draw_games', 0),
                                'hu_type': hu_type_dict,
                                'players': [],
                                'folder_path': folder_path  # 存储记录对应的文件夹路径
                            }
                            
                            # 创建临时玩家对象用于显示
                            if 'players' in record_data:
                                for player_data in record_data['players']:
                                    class TempPlayer:
                                        def __init__(self, data):
                                            self.name = data['name']
                                            self.ai_version = data.get('ai_version', '')
                                            self.is_human = data.get('is_human', False)
                                            self.score = data.get('score', 0) if 'score' in data else data.get('current_score', 0)
                                            self.previous_score = data.get('previous_score', 0)
                                            self.win_count = data.get('win_count', 0)
                                            self.win_rate = data.get('win_rate', 0)
                                            self.OfferingWin_count = data.get('OfferingWin_count', 0)
                                            self.OfferingWin_rate = data.get('OfferingWin_rate', 0)
                                            self.gain_ji_count = data.get('gain_ji_count', 0)
                                            self.gain_ji_rate = data.get('gain_ji_rate', 0)
                                            self.loss_ji_count = data.get('loss_ji_count', 0)
                                            self.loss_ji_rate = data.get('loss_ji_rate', 0)
                                            # 为了保持兼容性，添加result属性
                                            self.result = data.get('result', {})
                                    record['players'].append(TempPlayer(player_data))
                            
                            history_records.append(record)
                        except Exception as e:
                            # 只在开发阶段打印错误
                            # print(f"读取历史记录文件失败: {folder_name}/{json_file}, 错误: {e}")
                            pass
        
        # 3. 对历史记录进行排序，确保按照时间顺序显示
        # 排序规则：
        # 1. 优先显示当前游戏记录（type='current'），再显示历史记录（type='history'）
        # 2. 历史记录按照时间戳从新到旧排序
        from datetime import datetime
        history_records.sort(key=lambda x: (
            0 if x['type'] == 'current' else 1,  # 当前游戏排在前面
            -datetime.fromisoformat(x.get('start_timestamp', x['timestamp'])).timestamp()  # 时间戳从新到旧
        ))
        
        # 4. 检查是否有历史记录
        if not history_records:
            # 显示"暂无历史对局数据"
            big_font = pygame.font.Font(self.settings.font_path, self.settings.big_font_size)
            no_data_text = big_font.render("暂无历史对局数据", True, self.settings.white)
            no_data_x = (self.settings.win_w - no_data_text.get_width()) // 2
            no_data_y = (self.settings.win_h - no_data_text.get_height()) // 2
            self.screen.blit(no_data_text, (no_data_x, no_data_y))
            
            # 绘制返回按钮
            back_button_width = 150
            back_button_height = 50
            back_button_x = (self.settings.win_w - back_button_width) // 2
            back_button_y = no_data_y + 100
            self.back_button_rect = pygame.Rect(back_button_x, back_button_y, back_button_width, back_button_height)
            pygame.draw.rect(self.screen, (150, 0, 0), self.back_button_rect, border_radius=5)
            back_font = pygame.font.Font(self.settings.font_path, self.settings.normal_font_size)
            back_text = back_font.render("返回主菜单", True, (255, 255, 255))
            back_text_x = back_button_x + (back_button_width - back_text.get_width()) // 2
            back_text_y = back_button_y + (back_button_height - back_text.get_height()) // 2
            self.screen.blit(back_text, (back_text_x, back_text_y))
            
            pygame.display.flip()
            return
        
        # 4. 分页处理
        page_size = 3
        current_page = getattr(self, '_history_page', 0)
        total_pages = (len(history_records) + page_size - 1) // page_size
        
        # 保存总页数到属性中，供事件处理使用
        self._total_pages = total_pages
        
        # 确保current_page在有效范围内
        current_page = max(0, min(current_page, total_pages - 1))
        self._history_page = current_page
        
        # 获取当前页的记录
        start_index = current_page * page_size
        end_index = start_index + page_size
        current_records = history_records[start_index:end_index]
        
        # 5. 绘制历史记录卡片
        big_font = pygame.font.Font(self.settings.font_path, self.settings.big_font_size)
        normal_font = pygame.font.Font(self.settings.font_path, self.settings.normal_font_size)
        small_font = pygame.font.Font(self.settings.font_path, self.settings.small_font_size)
        
        # 计算卡片位置
        result_bg_path = os.path.join(self.resource_dir, 'table', 'result_right.png')
        if os.path.exists(result_bg_path):
            result_bg = pygame.image.load(result_bg_path).convert_alpha()
            # 缩小为原尺寸的0.91倍
            original_width, original_height = result_bg.get_size()
            card_width = int(original_width * 0.91)
            card_height = int(original_height * 0.91)
            result_bg = pygame.transform.smoothscale(result_bg, (card_width, card_height))
        else:
            card_width = 800
            card_height = 650
        
        # 计算卡片间距和起始位置
        spacing = 20
        total_cards_width = len(current_records) * card_width + (len(current_records) - 1) * spacing
        start_x = (self.settings.win_w - total_cards_width) // 2
        start_y = 50
        
        # 绘制每个记录卡片
        
        for i, record in enumerate(current_records):
            card_x = start_x + i * (card_width + spacing)
            
            # 绘制卡片背景
            if os.path.exists(result_bg_path):
                self.screen.blit(result_bg, (card_x, start_y))
            else:
                card_surface = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
                card_surface.fill((0, 0, 0, 180))
                self.screen.blit(card_surface, (card_x, start_y))
            
            # 绘制卡片标题
            if record['type'] == 'current':
                title_text = "本次游戏记录"
            else:
                # 格式化时间戳，优先使用start_timestamp
                timestamp_str = record.get('start_timestamp', record['timestamp'])
                timestamp = datetime.fromisoformat(timestamp_str)
                title_text = timestamp.strftime("%y-%m-%d %H:%M:%S")
            title_surface = big_font.render(title_text, True, self.settings.black)
            title_x = card_x + (card_width - title_surface.get_width()) // 2
            self.screen.blit(title_surface, (title_x, start_y + 25))

            # 绘制分隔线
            pygame.draw.line(self.screen, self.settings.black, 
                             (card_x + 21, start_y + 50), 
                             (card_x + card_width - 21, start_y + 50), 2)
            
            # 移除重复的时间戳显示
            
            # 获取记录数据
            total_games = record['total_games']
            draw_games = record['draw_games']
            hu_type = record['hu_type']
            players = record['players']
            
            # 绘制总局数和流局数/流局率
            current_y = start_y + 65
            draw_rate = (draw_games / total_games * 100) if total_games > 0 else 0
            combined_text = f"总  数: {total_games:3} 局   黄牌数: {draw_games:3} 局   黄牌率: {draw_rate:.1f}%"
            combined_surface = normal_font.render(combined_text, True, self.settings.black)
            combined_x = card_x + 30
            self.screen.blit(combined_surface, (combined_x, current_y))
            current_y += 40
            
            # 绘制胡牌类型统计
            if hu_type:
                hu_type_list = list(hu_type.items())
                for j in range(0, len(hu_type_list), 3):
                    row_types = hu_type_list[j:j+3]
                    row_text = "   ".join([f"{tag.value}: {count:3} 局" for tag, count in row_types])
                    row_surface = normal_font.render(row_text, True, self.settings.black)
                    row_x = card_x + 30
                    self.screen.blit(row_surface, (row_x, current_y))
                    current_y += 25
            else:
                no_hu_text = "暂无胡牌记录"
                no_hu_surface = normal_font.render(no_hu_text, True, self.settings.black)
                no_hu_x = card_x + (card_width - no_hu_surface.get_width()) // 2
                self.screen.blit(no_hu_surface, (no_hu_x, current_y))
                current_y += 25
            
            current_y += 10
            
            # 绘制排行榜标题
            ranking_title = big_font.render("排行榜", True, self.settings.black)
            ranking_title_x = card_x + (card_width - ranking_title.get_width()) // 2
            self.screen.blit(ranking_title, (ranking_title_x, current_y))
            current_y += 40
            
            # 绘制玩家数据
            if players:
                # 按积分排序
                sorted_players = sorted(players, key=lambda p: p.score, reverse=True)
                
                for player in sorted_players:
                    
                    # 第一行：名字和积分
                    formatted_name = f"{player.name:<6}({player.ai_version}): "
                    score_formula = f"{player.score:4}"
                    color = self.settings.blue if player.is_human else self.settings.black
                    first_line_surface = normal_font.render(f"{formatted_name} {score_formula}", True, color)
                    first_line_x = card_x + 30
                    self.screen.blit(first_line_surface, (first_line_x, current_y))
                    current_y += 20
                    
                    # 第二行：胡牌和冲鸡数据
                    # 添加属性检查和默认值处理，防止HumanPlayer对象缺少属性
                    win_count = getattr(player, 'win_count', 0)
                    win_rate = getattr(player, 'win_rate', 0.0)
                    gain_ji_count = getattr(player, 'gain_ji_count', 0)
                    gain_ji_rate = getattr(player, 'gain_ji_rate', 0.0)
                    win_text = f"胡牌: {win_count:2}局/{win_rate:4.1f}%"
                    gain_ji_text = f"冲鸡: {gain_ji_count:2}分/{gain_ji_rate:4.1f}%"
                    second_line_surface = small_font.render(f"      {win_text}      {gain_ji_text}", True, self.settings.black)
                    self.screen.blit(second_line_surface, (first_line_x, current_y))
                    current_y += 20
                    
                    # 第三行：点炮和丢鸡数据
                    OfferingWin_count = getattr(player, 'OfferingWin_count', 0)
                    OfferingWin_rate = getattr(player, 'OfferingWin_rate', 0.0)
                    loss_ji_count = getattr(player, 'loss_ji_count', 0)
                    loss_ji_rate = getattr(player, 'loss_ji_rate', 0.0)
                    OfferingWin_text = f"献胡: {OfferingWin_count:2}局/{OfferingWin_rate:4.1f}%"
                    loss_ji_text = f"丢鸡: {loss_ji_count:2}分/{loss_ji_rate:4.1f}%"
                    third_line_surface = small_font.render(f"      {OfferingWin_text}      {loss_ji_text}", True, self.settings.black)
                    self.screen.blit(third_line_surface, (first_line_x, current_y))
                    current_y += 40
            
            # 定义按钮通用参数
            padding_x = 8
            padding_y = 6
            
            # 在卡片右下角绘制一个“删除”按钮（仅历史记录可删除）
            # 按钮为无背景、无边框的文本样式，仅保存可点击区域
            if record.get('type') == 'history':
                try:
                    del_text = small_font.render("删除", True, (200, 50, 50))
                    btn_w = del_text.get_width() + padding_x * 2
                    btn_h = del_text.get_height() + padding_y * 2
                    btn_x = card_x + card_width - 20 - btn_w
                    btn_y = start_y + card_height - 20 - btn_h

                    # 直接绘制文本（无背景）
                    self.screen.blit(del_text, (btn_x + padding_x, btn_y + padding_y))

                    # 保存删除按钮矩形，键为文件夹路径，事件处理将使用它
                    folder = record.get('folder_path')
                    if folder:
                        self._delete_buttons[folder] = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
                except Exception:
                    pass

            # 在卡片左下角绘制“查看详情”按钮（无背景、无边框）
            try:
                detail_text = small_font.render("查看详情", True, self.settings.blue)
                dp_w = detail_text.get_width() + padding_x * 2
                dp_h = detail_text.get_height() + padding_y * 2
                dp_x = card_x + 30
                dp_y = start_y + card_height - 20 - dp_h
                self.screen.blit(detail_text, (dp_x + padding_x, dp_y + padding_y))
                
                # 保存查看详情按钮矩形
                # 对于当前游戏记录，使用特殊键标识
                key = record.get('folder_path') if record.get('type') == 'history' else 'current'
                self._detail_buttons[key] = pygame.Rect(dp_x, dp_y, dp_w, dp_h)
            except Exception:
                pass
            
        # 6. 绘制返回按钮
        back_button_width = 150
        back_button_height = 50
        back_button_x = (self.settings.win_w - back_button_width) // 2
        back_button_y = start_y + card_height + 20
        self.back_button_rect = pygame.Rect(back_button_x, back_button_y, back_button_width, back_button_height)
        pygame.draw.rect(self.screen, (150, 0, 0), self.back_button_rect, border_radius=5)
        back_text = normal_font.render("返回主菜单", True, (255, 255, 255))
        back_text_x = back_button_x + (back_button_width - back_text.get_width()) // 2
        back_text_y = back_button_y + (back_button_height - back_text.get_height()) // 2
        self.screen.blit(back_text, (back_text_x, back_text_y))
        
        # 7. 绘制分页按钮
        # 无论多少页都显示分页控件，单页时按钮置灰
        page_button_width = 100
        page_button_height = 40
        
        # 使用与返回主菜单按钮相同的y坐标
        button_y = start_y + card_height + 20
        
        # 完全固定整个分页控件的位置，实现等距离布局
        # 右侧边距，增大数值使整个控件向左移动
        right_margin = 50
        # 固定间距：上一页按钮与页码之间，页码与下一页按钮之间的距离相等
        equal_spacing = 30
        # 固定页码显示宽度
        fixed_page_display_width = 80
        
        # 计算各元素宽度
        element_widths = {
            'prev_button': page_button_width,
            'spacing1': equal_spacing,
            'page_display': fixed_page_display_width,
            'spacing2': equal_spacing,
            'next_button': page_button_width
        }
        
        # 计算总宽度
        total_pagination_width = sum(element_widths.values())
        
        # 固定起始x位置，使整个分页控件靠右显示
        pagination_start_x = self.settings.win_w - total_pagination_width - right_margin
        
        # 绘制分页控件
        page_button_width = 100
        page_button_height = 40
        button_y = start_y + card_height + 20
        right_margin = 50
        spacing = 30
        
        # 固定页码显示位置（无论是否显示按钮）
        # 从右往左计算，确保页码位置始终相同
        next_button_x = self.settings.win_w - page_button_width - right_margin
        page_info_x = next_button_x - 80 - spacing  # 80是页码显示宽度
        prev_button_x = page_info_x - page_button_width - spacing
        
        # 2. 绘制页码信息（始终绘制）
        page_str = f"{current_page + 1}/{total_pages}"
        page_surface = normal_font.render(page_str, True, self.settings.red)
        page_text_x = page_info_x + (80 - page_surface.get_width()) // 2  # 居中显示
        self.screen.blit(page_surface, (page_text_x, button_y + (page_button_height - page_surface.get_height()) // 2))
        
        # 绘制上一页按钮
        prev_color = (0, 150, 0) if current_page > 0 else (150, 150, 150)
        pygame.draw.rect(self.screen, prev_color, (prev_button_x, button_y, page_button_width, page_button_height), border_radius=5)
        # 绘制上一页文字，明确指定白色
        prev_surface = normal_font.render("上一页", True, self.settings.black)
        prev_text_x = prev_button_x + (page_button_width - prev_surface.get_width()) // 2
        prev_text_y = button_y + (page_button_height - prev_surface.get_height()) // 2
        self.screen.blit(prev_surface, (prev_text_x, prev_text_y))
        self._prev_page_rect = pygame.Rect(prev_button_x, button_y, page_button_width, page_button_height)
        
        # 绘制下一页按钮
        next_color = (0, 150, 0) if current_page < total_pages - 1 else (150, 150, 150)
        pygame.draw.rect(self.screen, next_color, (next_button_x, button_y, page_button_width, page_button_height), border_radius=5)
        # 绘制下一页文字，明确指定白色
        next_surface = normal_font.render("下一页", True, self.settings.black)
        next_text_x = next_button_x + (page_button_width - next_surface.get_width()) // 2
        next_text_y = button_y + (page_button_height - next_surface.get_height()) // 2
        self.screen.blit(next_surface, (next_text_x, next_text_y))
        self._next_page_rect = pygame.Rect(next_button_x, button_y, page_button_width, page_button_height)
        
        # 8. 绘制删除确认弹窗（如果显示）
        if hasattr(self, 'show_delete_confirm') and self.show_delete_confirm:
            # 弹窗尺寸
            dialog_width = 400
            dialog_height = 200
            dialog_x = (self.settings.win_w - dialog_width) // 2
            dialog_y = (self.settings.win_h - dialog_height) // 2
            
            # 绘制半透明背景
            dialog_bg = pygame.Surface((dialog_width, dialog_height), pygame.SRCALPHA)
            dialog_bg.fill((0, 0, 0, 200))
            self.screen.blit(dialog_bg, (dialog_x, dialog_y))
            
            # 绘制边框
            pygame.draw.rect(self.screen, (255, 255, 255), (dialog_x, dialog_y, dialog_width, dialog_height), 2)
            
            # 绘制弹窗标题
            confirm_font = pygame.font.Font(self.settings.font_path, self.settings.normal_font_size)
            confirm_text1 = confirm_font.render("确定要删除这条历史记录吗？", True, (255, 255, 255))
            confirm_text2 = confirm_font.render("此操作不可恢复", True, (255, 255, 255))
            
            # 确定按钮
            ok_button_width = 100
            ok_button_height = 40
            ok_button_x = dialog_x + 70
            ok_button_y = dialog_y + 130
            pygame.draw.rect(self.screen, (255, 0, 0), (ok_button_x, ok_button_y, ok_button_width, ok_button_height), border_radius=5)
            # 记录确认按钮矩形，供事件处理使用
            self._delete_confirm_ok_rect = pygame.Rect(ok_button_x, ok_button_y, ok_button_width, ok_button_height)
            ok_text = confirm_font.render("确定", True, (255, 255, 255))
            ok_text_x = ok_button_x + (ok_button_width - ok_text.get_width()) // 2
            ok_text_y = ok_button_y + (ok_button_height - ok_text.get_height()) // 2
            self.screen.blit(ok_text, (ok_text_x, ok_text_y))
            
            # 取消按钮
            cancel_button_x = dialog_x + 230
            cancel_button_y = ok_button_y
            pygame.draw.rect(self.screen, (0, 150, 0), (cancel_button_x, cancel_button_y, ok_button_width, ok_button_height), border_radius=5)
            # 记录取消按钮矩形
            self._delete_confirm_cancel_rect = pygame.Rect(cancel_button_x, cancel_button_y, ok_button_width, ok_button_height)
            cancel_text = confirm_font.render("取消", True, (255, 255, 255))
            cancel_text_x = cancel_button_x + (ok_button_width - cancel_text.get_width()) // 2
            cancel_text_y = cancel_button_y + (ok_button_height - cancel_text.get_height()) // 2
            self.screen.blit(cancel_text, (cancel_text_x, cancel_text_y))
            
            # 绘制文本
            confirm_text1_x = dialog_x + (dialog_width - confirm_text1.get_width()) // 2
            confirm_text1_y = dialog_y + 50
            confirm_text2_x = dialog_x + (dialog_width - confirm_text2.get_width()) // 2
            confirm_text2_y = dialog_y + 90
            self.screen.blit(confirm_text1, (confirm_text1_x, confirm_text1_y))
            self.screen.blit(confirm_text2, (confirm_text2_x, confirm_text2_y))
        
        # 9. 更新显示
        pygame.display.flip()

    def _draw_game_history_detail(self):
        """绘制历史对局详情页面

        展示单局游戏的详细信息，包括：
        - 玩家头像和名字
        - 暴露手牌和隐藏手牌
        - 玩家标签
        - 导航按钮
        """
        import json
        import os
        from datetime import datetime
        
        # 初始化按钮矩形字典，确保它们在事件处理时存在
        self._detail_buttons_rects = {}
        
        # 绘制背景
        bg_image = pygame.image.load(self.settings.bg_img).convert()
        bg_image = pygame.transform.smoothscale(bg_image, (self.settings.win_w, self.settings.win_h))
        self.screen.blit(bg_image, (0, 0))
        
        # 绘制半透明蒙层
        overlay = pygame.Surface((self.settings.win_w, self.settings.win_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # 半透明黑色蒙层
        self.screen.blit(overlay, (0, 0))
        
        # 检查必要的属性
        if not hasattr(self, '_current_detail_folder') or not hasattr(self, '_detail_game_files') or not hasattr(self, '_current_detail_game_index'):
            # 缺少必要属性，直接返回，由调用方处理
            return
        
        # 定义字体
        big_font = pygame.font.Font(self.settings.font_path, self.settings.big_font_size)
        normal_font = pygame.font.Font(self.settings.font_path, self.settings.normal_font_size)
        small_font = pygame.font.Font(self.settings.font_path, self.settings.small_font_size)
        
        # 检查是否有游戏记录文件
        if not self._detail_game_files:
            # 没有游戏记录文件，显示友好界面
            # 绘制返回按钮
            back_button_width = 150
            back_button_height = 50
            back_button_x = (self.settings.win_w - back_button_width) // 2
            back_button_y = self.settings.win_h - 100
            pygame.draw.rect(self.screen, (150, 0, 0), (back_button_x, back_button_y, back_button_width, back_button_height), border_radius=5)
            back_text = normal_font.render("返回", True, (255, 255, 255))
            back_text_x = back_button_x + (back_button_width - back_text.get_width()) // 2
            back_text_y = back_button_y + (back_button_height - back_text.get_height()) // 2
            self.screen.blit(back_text, (back_text_x, back_text_y))
            
            # 保存返回按钮矩形
            self._detail_buttons_rects['back'] = pygame.Rect(back_button_x, back_button_y, back_button_width, back_button_height)
            
            # 显示提示信息
            no_data_text = big_font.render("暂无游戏记录文件", True, self.settings.white)
            no_data_x = (self.settings.win_w - no_data_text.get_width()) // 2
            no_data_y = (self.settings.win_h - no_data_text.get_height()) // 2
            self.screen.blit(no_data_text, (no_data_x, no_data_y))
            
            # 显示当前游戏总览信息
            # 尝试读取总览数据
            try:
                # 查找总览文件
                folder_files = os.listdir(self._current_detail_folder)
                overview_file = None
                for file in folder_files:
                    if file.endswith('.json') and '_' in file and len(file.split('_')) > 1:
                        overview_file = file
                        break
                
                if overview_file:
                    overview_path = os.path.join(self._current_detail_folder, overview_file)
                    with open(overview_path, 'r', encoding='utf-8') as f:
                        overview_data = json.load(f)
                    
                    # 绘制总览信息
                    current_y = no_data_y + 50
                    
                    # 总局数和流局数
                    total_games = overview_data.get('total_games', 0)
                    draw_games = overview_data.get('draw_games', 0)
                    draw_rate = (draw_games / total_games * 100) if total_games > 0 else 0
                    stats_text = f"总  数: {total_games:3} 局   黄牌数: {draw_games:3} 局   黄牌率: {draw_rate:.1f}%"
                    stats_surface = normal_font.render(stats_text, True, self.settings.white)
                    stats_x = (self.settings.win_w - stats_surface.get_width()) // 2
                    self.screen.blit(stats_surface, (stats_x, current_y))
                    current_y += 40
                    
                    # 胡牌类型统计
                    hu_type = overview_data.get('hu_type', {})
                    if hu_type:
                        hu_type_text = "胡牌类型统计: "
                        for tag_value, count in hu_type.items():
                            hu_type_text += f"{tag_value}: {count} 局   "
                        hu_type_surface = normal_font.render(hu_type_text, True, self.settings.white)
                        hu_type_x = (self.settings.win_w - hu_type_surface.get_width()) // 2
                        self.screen.blit(hu_type_surface, (hu_type_x, current_y))
                        current_y += 40
                    
                    # 玩家排行榜
                    players = overview_data.get('players', [])
                    if players:
                        ranking_title = big_font.render("排行榜", True, self.settings.white)
                        ranking_title_x = (self.settings.win_w - ranking_title.get_width()) // 2
                        self.screen.blit(ranking_title, (ranking_title_x, current_y))
                        current_y += 40
                        
                        # 按积分排序
                        sorted_players = sorted(players, key=lambda p: p.get('score', 0), reverse=True)
                        
                        for player in sorted_players:
                            # 名字和积分
                            name = player.get('name', '')
                            ai_version = player.get('ai_version', '')
                            score = player.get('score', 0)
                            is_human = player.get('is_human', False)
                            color = self.settings.blue if is_human else self.settings.white
                            player_text = f"{name}({ai_version}): {score} 分"
                            player_surface = normal_font.render(player_text, True, color)
                            player_x = (self.settings.win_w - player_surface.get_width()) // 2
                            self.screen.blit(player_surface, (player_x, current_y))
                            current_y += 30
            except Exception as e:
                pass
            
            # 更新显示
            pygame.display.flip()
            return
        
        # 确保索引在有效范围内
        self._current_detail_game_index = max(0, min(self._current_detail_game_index, len(self._detail_game_files) - 1))
        
        # 读取当前游戏记录文件
        current_file = self._detail_game_files[self._current_detail_game_index]
        file_path = os.path.join(self._current_detail_folder, current_file)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                game_data = json.load(f)
        except Exception as e:
            self.show_toast("读取游戏记录失败")
            return
        
        # 定义字体
        big_font = pygame.font.Font(self.settings.font_path, self.settings.big_font_size)
        normal_font = pygame.font.Font(self.settings.font_path, self.settings.normal_font_size)
        small_font = pygame.font.Font(self.settings.font_path, self.settings.small_font_size)
        
        # 使用当局保存的game_end_img
        game_end_img = game_data.get('game_end_img', [])
        
        # 如果当局没有保存game_end_img，从玩家数据中获取（兼容旧版本）
        if not game_end_img:
            players = game_data.get('players', [])
            for player in players:
                player_game_end_img = player.get('game_end_img', [])
                if player_game_end_img:
                    game_end_img = player_game_end_img
                    break
        
        # 如果仍然没有game_end_img，根据游戏结果生成
        if not game_end_img:
            # 游戏结局图片路径映射
            game_result_images = {
                'draw': os.path.join(self.resource_dir, 'sprites', 'draw.png'),  # 流局
                'before': os.path.join(self.resource_dir, 'sprites', 'before_win.png'),  # 上家胜
                'opposite': os.path.join(self.resource_dir, 'sprites', 'opposite_win.png'),  # 对家胜
                'next': os.path.join(self.resource_dir, 'sprites', 'next_win.png'),  # 下家胜
                'self': os.path.join(self.resource_dir, 'sprites', 'self_win.png')  # 本家胜
            }
            
            # 确定游戏结局类型
            is_draw = game_data.get('is_draw', False)
            if is_draw:
                # 流局
                if os.path.exists(game_result_images['draw']):
                    game_end_img.append(game_result_images['draw'])
            else:
                # 有赢家，根据玩家结果判断
                players = game_data.get('players', [])
                shown_results = set()
                
                for player in players:
                    # 检查是否为赢家
                    player_result = player.get('result', {})
                    tags = player.get('tags', [])
                    is_win = 'win' in player_result or any('胡' in str(tag) for tag in tags)
                    
                    if is_win:
                        # 根据玩家位置确定显示图片
                        is_human = player.get('is_human', False)
                        if is_human:
                            result_type = 'self'
                        else:
                            result_type = 'opposite'
                        
                        if result_type not in shown_results:
                            shown_results.add(result_type)
                            img_path = game_result_images[result_type]
                            if os.path.exists(img_path):
                                game_end_img.append(img_path)
                
                # 如果没有确定的赢家，使用默认图片
                if not game_end_img:
                    if os.path.exists(game_result_images['self']):
                        game_end_img.append(game_result_images['self'])
        
        # 绘制游戏结局图片
        if game_end_img:
            result_imgs = []
            for img_path in game_end_img:
                try:
                    result_img = pygame.image.load(img_path).convert_alpha()
                    # 缩小为原始尺寸的0.91倍
                    scaled_width = int(result_img.get_width() * 0.91)
                    scaled_height = int(result_img.get_height() * 0.91)
                    result_img = pygame.transform.smoothscale(result_img, (scaled_width, scaled_height))
                    result_imgs.append(result_img)
                except Exception as e:
                    print(f"加载游戏结局图片失败: {e}")
            
            # 计算总宽度和起始位置 - 屏幕中央上方，与上边缘距离15像素
            total_width = sum(img.get_width() + 20 for img in result_imgs) - 20  # 图片间距20px
            start_x = (self.settings.win_w - total_width) // 2 - 100 # 左移100像素
            img_y = 15  # 与上边缘的距离15像素
            
            # 绘制所有结局图片
            current_x = start_x
            for img in result_imgs:
                self.screen.blit(img, (current_x, img_y))
                current_x += img.get_width() + 20
 
        # 2. 绘制玩家信息和手牌
        players = game_data.get('players', [])
        
        # 设置初始位置和间距
        start_x = 50
        start_y = 100
        player_spacing = 130  # 玩家之间的垂直间距
        avatar_size = self.settings.avatar_size # 头像尺寸
        tile_size = self.settings.tile_size  # 牌尺寸
        
        # 绘制玩家数据：头像、名字、手牌
        for i, player_data in enumerate(players):
            # 计算当前玩家的起始Y位置
            current_y = start_y + i * player_spacing
            
            # 2.1 绘制头像（支持打包后路径解析）
            name = player_data.get('name', '')
            try:
                avatar = None
                # 优先基于玩家名字尝试查找头像（最可靠的方式）
                if name:
                    # 尝试 girl/boy 子目录
                    for gender in ('girl', 'boy'):
                        # 使用 get_resource_path 确保兼容 PyInstaller 打包
                        candidate = get_resource_path(f'resource/avatar/{gender}/{name}.jpg')
                        if os.path.exists(candidate):
                            avatar = pygame.image.load(candidate)
                            break
                
                # 如果仍未找到，尝试处理保存的 avatar_path
                if not avatar:
                    avatar_path = player_data.get('avatar_path', '')
                    if avatar_path:
                        # 提取文件名
                        filename = os.path.basename(avatar_path)
                        if filename:
                            # 尝试从 resource/avatar/girl/boy 目录查找
                            for gender in ('girl', 'boy'):
                                candidate = get_resource_path(f'resource/avatar/{gender}/{filename}')
                                if os.path.exists(candidate):
                                    avatar = pygame.image.load(candidate)
                                    break

                # 如果仍未加载到头像，使用占位色块
                if avatar:
                    avatar = pygame.transform.scale(avatar, avatar_size)
                else:
                    avatar = pygame.Surface(avatar_size, pygame.SRCALPHA)
                    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
                    avatar.fill(colors[i % len(colors)])
            except Exception:
                # 加载失败时使用颜色方块
                avatar = pygame.Surface(avatar_size, pygame.SRCALPHA)
                colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
                avatar.fill(colors[i % len(colors)])
            
            avatar_x = start_x
            avatar_y = current_y
            self.screen.blit(avatar, (avatar_x, avatar_y))
            
            # 2.2 绘制名字（头像下方）
            name = player_data.get('name', f'玩家{i+1}')
            name = (name+'(玩家)') if player_data.get('is_human', False) else name
            name_surface = normal_font.render(name, True, self.settings.white)
            name_x = avatar_x + (avatar_size[0] - name_surface.get_width()) // 2
            name_y = avatar_y + avatar_size[1] + 5
            self.screen.blit(name_surface, (name_x, name_y))
            
            # 2.3 绘制手牌（暴露牌 + 隐藏牌）
            hand_start_x = start_x + avatar_size[0] + 20  # 麻将与头像之间的距离20像素
            hand_start_y = current_y
            
            # 绘制暴露牌（优先使用牌面图片）
            current_x = hand_start_x-5
            exposed_tiles = player_data.get('exposed_tiles', [])
            previous_tile = ''
            for tile in exposed_tiles:
                tile_key = str(tile).strip()
                if previous_tile != tile:
                    current_x += 5                
                previous_tile = tile
                # 处理可能带有后缀的情形
                if tile_key.endswith('.png'):
                    tile_key = tile_key[:-4]

                tile_img = None
                try:
                    if tile_key in self.tiles:
                        # 使用加载好的原始牌面图，按需求缩放到显示尺寸
                        tile_img = pygame.transform.smoothscale(self.tiles[tile_key], tile_size)
                    else:
                        # 有时候保存的是纯数字或其他格式，尝试直接用字串作为key
                        if tile_key in self.tiles:
                            tile_img = pygame.transform.smoothscale(self.tiles[tile_key], tile_size)
                except Exception:
                    tile_img = None

                if tile_img:
                    self.screen.blit(tile_img, (current_x, hand_start_y))
                else:
                    # 回退到颜色块并显示文本
                    tile_img = pygame.Surface(tile_size, pygame.SRCALPHA)
                    tile_img.fill((200, 200, 200))
                    font = pygame.font.Font(self.settings.font_path, 12)
                    tile_text = font.render(str(tile), True, (0, 0, 0))
                    text_x = (tile_size[0] - tile_text.get_width()) // 2
                    text_y = (tile_size[1] - tile_text.get_height()) // 2
                    tile_img.blit(tile_text, (text_x, text_y))
                    self.screen.blit(tile_img, (current_x, hand_start_y))

                current_x += tile_size[0]
            
            # 暴露牌和隐藏牌之间间隔10像素
            if exposed_tiles:
                current_x += 10
            
            # 绘制隐藏牌（尝试显示牌面，否则使用背面图）
            concealed_tiles = player_data.get('concealed_tiles', [])
            for tile in concealed_tiles:
                tile_key = str(tile).strip()
                if tile_key.endswith('.png'):
                    tile_key = tile_key[:-4]

                tile_img = None
                try:
                    if tile_key in self.tiles:
                        tile_img = pygame.transform.smoothscale(self.tiles[tile_key], tile_size)
                except Exception:
                    tile_img = None

                if tile_img:
                    # 有牌面图时显示牌面（历史详情常常需要查看实际手牌）
                    self.screen.blit(tile_img, (current_x, hand_start_y))
                else:
                    # 否则显示背面图（如果存在）
                    try:
                        if hasattr(self, 'back_tile') and self.back_tile:
                            back = pygame.transform.smoothscale(self.back_tile, tile_size)
                            self.screen.blit(back, (current_x, hand_start_y))
                        else:
                            # 回退到深灰色方块
                            tile_img = pygame.Surface(tile_size, pygame.SRCALPHA)
                            tile_img.fill((128, 128, 128))
                            font = pygame.font.Font(self.settings.font_path, 12)
                            tile_text = font.render(str(tile), True, (255, 255, 255))
                            text_x = (tile_size[0] - tile_text.get_width()) // 2
                            text_y = (tile_size[1] - tile_text.get_height()) // 2
                            tile_img.blit(tile_text, (text_x, text_y))
                            self.screen.blit(tile_img, (current_x, hand_start_y))
                    except Exception:
                        tile_img = pygame.Surface(tile_size, pygame.SRCALPHA)
                        tile_img.fill((128, 128, 128))
                        self.screen.blit(tile_img, (current_x, hand_start_y))

                current_x += tile_size[0]
            
            # 2.4 绘制标签（第三行）
            tags = player_data.get('tags', [])
            result = player_data.get('result', {})
            if result.get('jiaopai', False):
                ting_str = "已叫牌"
                color = self.settings.yellow
                if player_data.get('is_winner',False):
                    ting_str = "大赢家"
                    color = self.settings.green
            else:
                ting_str = "米叫牌"
                color = self.settings.red

            tags_surface = small_font.render(ting_str, True, color)
            tags_x = hand_start_x
            tags_y = hand_start_y + tile_size[1] + 10
            self.screen.blit(tags_surface, (tags_x, tags_y))

            ji_str = f"本局：{result.get('total_ji', 0):+3}"
            tags_str = ji_str + "     " + "、".join([p for p in tags if p])
            tags_surface = small_font.render(tags_str, True, self.settings.yellow)
            tags_x = hand_start_x + 50
            tags_y = hand_start_y + tile_size[1] + 10
            self.screen.blit(tags_surface, (tags_x, tags_y))

            source = result.get('hu_ji', '').get('source', '') + result.get('ji', '').get('source', '') + result.get('gang_ji', '').get('source', '')
            tags_surface = small_font.render('、  '.join(source), True, self.settings.white)
            tags_x = hand_start_x
            tags_y = hand_start_y + tile_size[1] + 30
            self.screen.blit(tags_surface, (tags_x, tags_y))
        
        # 绘制翻鸡牌文字
        if game_data.get('winners',[]):
            fanji_type = "上下鸡" if self.settings.shangxia_ji else "下鸡"
            jin_ji = True if game_data.get('fanji_tile','') in ['2条','9条'] else False
            
            fanji_str = f"翻鸡({fanji_type}): {' '.join([f'[{tile}]' for tile in game_data.get('fanji_tiles',[])])} {'(🐔金鸡🐔)' if jin_ji else ''}"
            tags_surface = small_font.render(fanji_str, True, self.settings.yellow)
            tags_x = start_x
            tags_y = start_y + player_spacing*4
            self.screen.blit(tags_surface, (tags_x, tags_y))

            # tile_img = self.tiles[self.fanji_tile]
            # scaled_img = pygame.transform.smoothscale(tile_img, self.settings.tile_size)
            # x = start_x + self.settings.avatar_size[0] + 100
            # self.screen.blit(scaled_img, (x, tags_y))

        # 绘制翻鸡牌图片
        for i,tile in enumerate(game_data.get('fanji_tiles',[])):
            if tile in self.tiles:
                tile_img = self.tiles[tile]
                scaled_img = pygame.transform.smoothscale(tile_img, self.settings.tile_size)
                x = start_x + self.settings.avatar_size[0] + 150 + (i+1)*(self.settings.tile_size[0]+10)
                self.screen.blit(scaled_img, (x, tags_y))

        # 3. 绘制当局游戏总述（右侧）
        # 严格仿造_draw_game_history的游戏卡片样式
        result_bg_path = os.path.join(self.resource_dir, 'table', 'result_right.png')
        if os.path.exists(result_bg_path):
            result_bg = pygame.image.load(result_bg_path).convert_alpha()
            # 与历史记录卡片相同的缩放比例
            original_width, original_height = result_bg.get_size()
            card_width = int(original_width * 0.91)
            card_height = int(original_height * 0.91)
            result_bg = pygame.transform.smoothscale(result_bg, (card_width, card_height))
        else:
            card_width = 800
            card_height = 650
        
        # 计算右侧卡片位置（整体上移30像素）
        card_x = self.settings.win_w - card_width - 20
        card_y = 70
        
        # 绘制卡片背景
        if os.path.exists(result_bg_path):
            self.screen.blit(result_bg, (card_x, card_y))
        else:
            card_surface = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
            card_surface.fill((0, 0, 0, 180))
            self.screen.blit(card_surface, (card_x, card_y))
        
        # 绘制卡片标题
        title_text = f"第{game_data.get('game_number', 1)}局-排行榜"
        title_surface = big_font.render(title_text, True, self.settings.black)
        title_x = card_x + (card_width - title_surface.get_width()) // 2
        self.screen.blit(title_surface, (title_x, card_y + 25))
        
        # 绘制分隔线
        pygame.draw.line(self.screen, self.settings.black, 
                         (card_x + 21, card_y + 50), 
                         (card_x + card_width - 18, card_y + 50), 2)
        
        # 绘制排行榜标题
        current_y = card_y + 80
        
        # 绘制玩家数据：积分排序
        if players:
            # 按积分排序
            sorted_players = sorted(players, key=lambda p: p.get('score', 0), reverse=True)
            
            for player in sorted_players:
                # 第一行：名字和积分
                ai_version = player.get('ai_version', 'AI-0')
                name = player.get('name', '未知玩家')
                formatted_name = f"{name:<6}({ai_version}): "
                score = player.get('score', 0)
                previous_score = player.get('previous_score', 0)
                score_change = score - previous_score
                score_formula = f"{score:4} = {previous_score:4}{score_change:+3}"
                color = self.settings.blue if player.get('is_human', False) else self.settings.black
                first_line_surface = normal_font.render(f"{formatted_name} {score_formula}", True, color)
                first_line_x = card_x + 25
                self.screen.blit(first_line_surface, (first_line_x, current_y))
                current_y += 20
                
                # 获取玩家当局结果
                player_result = player.get('result', {})
                count_with_other_player = player_result.get('count_with_other_player', {})
                for r in count_with_other_player:
                    source = r.get('source', '')
                    length = 35
                    r_x = card_x + 25
                    if not source:
                        break
                    for i in range(3):
                        source1 = source[i*length:(i+1)*length]
                        r_surface = small_font.render(f"{r.get('name', 'nobody').replace(' ', '')} -> {source1}" if i==0 else source1, True, self.settings.black)
                        r_x = (r_x+10) if i == 0 else (r_x + 30)
                        self.screen.blit(r_surface, (r_x, current_y))
                        current_y += 15
                        if (i+1)*length >= len(source):
                            break
                
                current_y += 20
        
        # 4. 绘制导航按钮
        button_font = pygame.font.Font(self.settings.font_path, self.settings.normal_font_size)
        
        # 按钮尺寸
        button_width = 90
        button_height = 40
        corner_radius = 10
        
        # 计算按钮位置 - 底部居中，均匀分布
        button_start_y = self.settings.win_h - button_height - 30
        
        # 定义所有按钮
        buttons = [
            {'id': 'prev', 'text': '上一局', 'enabled': self._current_detail_game_index > 0},
            {'id': 'game_info', 'text': f'{self._current_detail_game_index + 1}/{len(self._detail_game_files)}', 'enabled': True},
            {'id': 'next', 'text': '下一局', 'enabled': self._current_detail_game_index < len(self._detail_game_files) - 1},
            # {'id': 'detail', 'text': '结算详情', 'enabled': True},
            {'id': 'back', 'text': '返回', 'enabled': True}
        ]
        
        # 计算总宽度
        total_button_width = 0
        game_info_width = button_font.render(buttons[1]['text'], True, (255, 255, 255)).get_width()
        
        for i, button in enumerate(buttons):
            if button['id'] == 'game_info':
                total_button_width += game_info_width
            else:
                total_button_width += button_width
        
        # 计算按钮之间的间距
        button_spacing = 20
        
        # 绘制按钮
        current_x = self.settings.win_w - total_button_width -100 
        
        # 保存按钮区域，用于后续检测点击
        self._detail_buttons_rects = {}
        
        for button in buttons:
            if button['id'] == 'game_info':
                # 绘制局数信息
                info_surface = button_font.render(button['text'], True, (255, 255, 255))
                info_x = current_x + (game_info_width - info_surface.get_width()) // 2
                self.screen.blit(info_surface, (info_x, button_start_y + (button_height - info_surface.get_height()) // 2))
                current_x += game_info_width + button_spacing
            else:
                # 绘制普通按钮
                enabled = button['enabled']
                color = (0, 128, 0) if enabled else (128, 128, 128)
                button_rect = pygame.Rect(current_x, button_start_y, button_width, button_height)
                pygame.draw.rect(self.screen, color, button_rect, border_radius=corner_radius)
                
                # 保存按钮区域
                self._detail_buttons_rects[button['id']] = button_rect
                
                # 绘制文字
                text_surface = button_font.render(button['text'], True, (255, 255, 255))
                text_x = current_x + (button_width - text_surface.get_width()) // 2
                text_y = button_start_y + (button_height - text_surface.get_height()) // 2
                self.screen.blit(text_surface, (text_x, text_y))
                
                current_x += button_width + button_spacing
        
        # 更新显示
        pygame.display.flip()





































