#独山麻将
#LIGF 2025-11-17

import pygame
import sys
import os
import time
from settings import Settings
from source.ui_manager import UIManager
from source.game_manager import GameManager
from source.sound_manager import SoundManager
from source.public import  DecisionType,  DecisionResult

class GameScreen:
    """游戏屏幕状态枚举"""
    MAIN_MENU = "main_menu"
    SETTINGS = "settings"
    GAME_PLAY = "game_play"
    GAME_HISTORY = "game_history"
    GAME_HISTORY_DETAIL = "game_history_detail"

class MajiangGame:
    """麻将游戏入口类"""
    
    def __init__(self):
        """初始化游戏"""
        # 首先初始化Pygame
        pygame.init()
        pygame.display.init()
        pygame.font.init()
        pygame.mixer.init()  # 初始化音频系统
        self.settings = Settings() # 创建设置实例
        
        # 1. 游戏开始运行即创建时间戳文件夹
        import datetime
        import os
        self.game_start_timestamp = datetime.datetime.now()
        # 创建文件夹，命名格式：年(后两位)月(两位)日(两位)_时(24小时制)分(两位数)秒(两位数)
        self.history_folder_name = self.game_start_timestamp.strftime("%y%m%d_%H%M%S")
        history_dir = os.path.join('data', 'history')
        self.history_folder_path = os.path.join(history_dir, self.history_folder_name)
        # 确保history目录存在
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)
        # 创建本次游戏的历史记录文件夹
        if not os.path.exists(self.history_folder_path):
            os.makedirs(self.history_folder_path)
        
        # 记录本次游戏运行期间的所有对局数据
        self.game_sessions = []

        # 创建游戏窗口，添加额外标志以提高渲染质量
        flags = pygame.DOUBLEBUF | pygame.HWSURFACE  # 使用双缓冲和硬件加速来提高渲染质量和性能
        self.screen = pygame.display.set_mode((self.settings.win_w, self.settings.win_h), flags)
        pygame.display.set_caption(self.settings.game_name) # 设置窗口标题
        # 设置窗口图标
        try:
            icon = pygame.image.load(self.settings.icon_img)
            pygame.display.set_icon(icon)
        except Exception as e:
            print(f"设置窗口图标失败: {e}")
        self.clock = pygame.time.Clock() # 帧率控制
        
        # 初始化UI管理器和游戏管理器
        self.show_all_faces = self.settings.show_all_faces
        self.game_manager = GameManager(self.settings) # 初始化游戏管理器
        self.ui_manager = UIManager(self.screen, self.game_manager)# 初始化UI管理器
        # 设置UI管理器的game属性，方便访问当前游戏的history_folder_path
        self.ui_manager.game = self
        self.sound_manager = SoundManager(self.settings) # 初始化声音管理器
        
        # 设置GameManager的声音回调函数
        self.game_manager.sound_callback = self.request_play_sound
        # 设置GameManager的toast回调函数
        self.game_manager.toast_callback = self.request_show_toast
        
        self.have_human_selected = False
        
        # 游戏状态管理
        self.current_screen = GameScreen.MAIN_MENU
        self.game_started = False
        
        # 游戏局数记录
        self.total_games = 0
        self.draw_games = 0  # 流局数
        
        # 自动再来一局相关属性
        self.game_over_time = 0  # 游戏结束时间
        self.auto_restart_timer = 0  # 自动再来一局计时器
        
        # 主菜单按钮
        self.main_menu_buttons = {
            'start_game': pygame.Rect(0, 0, 200, 60),
            'settings': pygame.Rect(0, 0, 200, 60),
            'game_history': pygame.Rect(0, 0, 200, 60)
        }
        
        # 游戏中设置按钮，更窄一点
        self.game_settings_button = pygame.Rect(90, 20, 80, 30)
        
        # 记录设置页面的来源，用于控制可修改的设置项
        self.settings_from = None
        
        # 设置页面相关属性
        self.settings_back_button = pygame.Rect(0, 0, 150, 50)
        self.settings_save_button = pygame.Rect(0, 0, 180, 60)
        self.settings_cancel_button = pygame.Rect(0, 0, 180, 60)
        
        # 删除确认弹窗相关属性
        self.show_delete_confirm = False
        self.delete_confirm_record = None
        self.delete_confirm_file_path = None
        self.delete_confirm_folder_path = None
        
        # 历史记录相关变量（已在初始化时设置）
        # self.game_start_timestamp 和 self.history_folder_path 在第36-46行已初始化
        
        # 设置项临时存储
        self.temp_settings = {}
        self.editing_setting = None  # 当前正在编辑的设置项
        self.input_text = ""  # 当前输入的文本
        self.show_confirm_dialog = False
        
        # 移除pygame_gui相关属性，使用原生Pygame实现设置页面
        # 确认对话框按钮
        self.confirm_ok_button = pygame.Rect(0, 0, 100, 40)
        self.confirm_cancel_button = pygame.Rect(0, 0, 100, 40)
        self.confirm_end_game = False
        self.confirm_player_name_change = False
        self.player_name_change_confirmed = False
        self.original_human_name = self.settings.human
        
        # 定义设置项
        self.setting_items = [
            {'name': 'human_time_limit', 'type': 'number', 'label': '人类思考时间(秒)'},
            {'name': 'ai_time_limit', 'type': 'number', 'label': 'AI思考时间(秒)'},
            {'name': 'score', 'type': 'number', 'label': '初始分数'},
            {'name': 'test_round', 'type': 'number', 'label': '测试轮数'},
            {'name': 'human', 'type': 'dropdown', 'label': '人类玩家名称', 'options': self.settings.players_boy + self.settings.players_girl},
            {'name': 'game_mode', 'type': 'dropdown', 'label': '游戏模式', 'options': ['简单', '中等', '困难']},
            {'name': 'auto_restart_time', 'type': 'number', 'label': '默认再来一局计时(秒)'},
            {'name': 'test_mode', 'type': 'bool', 'label': '测试模式'},
            {'name': 'show_all_faces', 'type': 'bool', 'label': '显示所有牌面'},
            {'name': 'show_name', 'type': 'bool', 'label': '是否显示玩家名称'},
            {'name': 'show_ai_version', 'type': 'bool', 'label': '是否显示AI玩家版本号'},
            {'name': 'bg_music_play', 'type': 'bool', 'label': '播放背景音乐', 'has_volume': True},
            {'name': 'bg_music_volume', 'type': 'volume', 'label': '', 'parent': 'bg_music_play', 'min': 0, 'max': 1},
            {'name': 'game_sound_play', 'type': 'bool', 'label': '播放游戏音效', 'has_volume': True},
            {'name': 'game_sound_volume', 'type': 'volume', 'label': '', 'parent': 'game_sound_play', 'min': 0, 'max': 2},
            {'name': 'card_sound_play', 'type': 'bool', 'label': '播放打牌读牌音效', 'has_volume': True},
            {'name': 'card_sound_volume', 'type': 'volume', 'label': '', 'parent': 'card_sound_play', 'min': 0, 'max': 2},
            {'name': 'speed_up', 'type': 'bool', 'label': '游戏加速模式'}
        ]
  
    def _draw_main_menu(self):
        """绘制主菜单页面"""
        # 绘制背景
        bg_image = pygame.image.load(self.settings.bg_img).convert()
        bg_image = pygame.transform.smoothscale(bg_image, (self.settings.win_w, self.settings.win_h))
        self.screen.blit(bg_image, (0, 0))
        
        # 绘制半透明蒙层
        overlay = pygame.Surface((self.settings.win_w, self.settings.win_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))  # 半透明黑色蒙层
        self.screen.blit(overlay, (0, 0))
        
        # 绘制游戏标题
        title_font = pygame.font.Font(self.settings.font_path, 60)
        title_surface = title_font.render(self.settings.game_name, True, self.settings.yellow)
        title_x = (self.settings.win_w - title_surface.get_width()) // 2
        title_y = 100
        self.screen.blit(title_surface, (title_x, title_y))
        
        # 计算按钮位置
        button_width = 200
        button_height = 60
        button_spacing = 30
        font_path = self.settings.font_path
        font_size = self.settings.normal_font_size
        # 计算起始y位置，包含3个按钮
        start_x = (self.settings.win_w - button_width) // 2
        start_y = (self.settings.win_h - (button_height * 3 + button_spacing * 2)) // 2
        
        # 更新按钮位置
        self.main_menu_buttons['start_game'] = pygame.Rect(start_x, start_y, button_width, button_height)
        self.main_menu_buttons['settings'] = pygame.Rect(start_x, start_y + button_height + button_spacing, button_width, button_height)
        self.main_menu_buttons['game_history'] = pygame.Rect(start_x, start_y + button_height * 2 + button_spacing * 2, button_width, button_height)
        
        # 绘制按钮
        button_font = pygame.font.Font(font_path, font_size)
        
        # 绘制开始游戏按钮
        pygame.draw.rect(self.screen, self.settings.green, self.main_menu_buttons['start_game'], border_radius=10)
        start_text = button_font.render("开始游戏", True, self.settings.white)
        start_text_x = start_x + (button_width - start_text.get_width()) // 2
        start_text_y = start_y + (button_height - start_text.get_height()) // 2
        self.screen.blit(start_text, (start_text_x, start_text_y))
        
        # 绘制设置按钮
        pygame.draw.rect(self.screen, self.settings.blue, self.main_menu_buttons['settings'], border_radius=10)
        settings_text = button_font.render("设置", True, self.settings.white)
        settings_text_x = start_x + (button_width - settings_text.get_width()) // 2
        settings_text_y = start_y + button_height + button_spacing + (button_height - settings_text.get_height()) // 2
        self.screen.blit(settings_text, (settings_text_x, settings_text_y))
        
        # 绘制历史对局按钮
        pygame.draw.rect(self.screen, self.settings.orange, self.main_menu_buttons['game_history'], border_radius=10)
        history_text = button_font.render("历史对局", True, self.settings.white)
        history_text_x = start_x + (button_width - history_text.get_width()) // 2
        history_text_y = start_y + button_height * 2 + button_spacing * 2 + (button_height - history_text.get_height()) // 2
        self.screen.blit(history_text, (history_text_x, history_text_y))
        
        # 绘制toast提示
        self.ui_manager.draw_toasts()
        
        # 更新显示
        pygame.display.flip()
    
    def _draw_settings(self):
        """绘制设置页面"""
        # 绘制背景
        bg_image = pygame.image.load(self.settings.bg_img).convert()
        bg_image = pygame.transform.smoothscale(bg_image, (self.settings.win_w, self.settings.win_h))
        self.screen.blit(bg_image, (0, 0))
        
        # 绘制半透明蒙层
        overlay = pygame.Surface((self.settings.win_w, self.settings.win_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))  # 半透明黑色蒙层
        self.screen.blit(overlay, (0, 0))
        
        # 初始化临时设置
        if not self.temp_settings:
            # 保存初始设置用于比较
            self.initial_settings = {}
            for item in self.setting_items:
                if item['name'] == 'game_mode':
                    # 根据当前opponent_ai_version_list值确定游戏模式
                    ai_version_list = getattr(self.settings, 'opponent_ai_version_list', [])
                    if ai_version_list == self.settings.mode_easy:
                        value = '简单'
                    elif ai_version_list == self.settings.mode_normal:
                        value = '中等'
                    else: # 困难
                        value = '困难'
                else:
                    value = getattr(self.settings, item['name'])
                self.temp_settings[item['name']] = value
                self.initial_settings[item['name']] = value
            # 保存原始人类玩家名称
            self.original_human_name = self.settings.human
        
        # 创建设置面板
        panel_width = 1000  # 增加面板宽度，确保所有控件都能显示
        panel_height = 650  # 增加面板高度以容纳更多设置项
        panel_x = (self.settings.win_w - panel_width) // 2
        panel_y = (self.settings.win_h - panel_height) // 2
        
        # 绘制面板背景
        panel_bg = pygame.Surface((panel_width, panel_height))
        panel_bg.fill((200, 200, 200))
        self.screen.blit(panel_bg, (panel_x, panel_y))
        
        # 绘制面板边框
        pygame.draw.rect(self.screen, (100, 100, 100), (panel_x, panel_y, panel_width, panel_height), 2)
        
        # 绘制标题
        title_font = pygame.font.Font(self.settings.font_path, self.settings.big_font_size)
        title_text = title_font.render("游戏设置", True, (0, 0, 0))
        title_x = panel_x + (panel_width - title_text.get_width()) // 2
        title_y = panel_y + 20
        self.screen.blit(title_text, (title_x, title_y))
        
        # 初始位置和间距
        start_x1 = panel_x + 50
        start_x2 = panel_x + 450
        start_y = panel_y + 80
        line_height = 60
        label_width = 150
        control_width = 150
        slider_width = 100
        slider_height = 20
        
        # 绘制设置项
        font = pygame.font.Font(self.settings.font_path, self.settings.normal_font_size)
        small_font = pygame.font.Font(self.settings.font_path, self.settings.small_font_size)
        
        # 根据设置页面来源决定可修改的设置项
        if self.settings_from == 'game':
            # 游戏中设置页面，不可修改玩家名字、初始分数和测试模式以及游戏模式
            editable_items = [item for item in self.setting_items if item['name'] not in ['human', 'score', 'test_mode', 'game_mode']]
        else:
            # 主菜单设置页面，可修改所有设置项
            editable_items = self.setting_items
        
        # 过滤掉音量设置项，先绘制非音量设置项
        non_volume_items = [item for item in editable_items if item['type'] != 'volume']
        
        for i, item in enumerate(non_volume_items):
            # 计算行列位置
            col = i % 2
            row = i // 2
            start_x = start_x1 if col == 0 else start_x2
            y = start_y + row * line_height
            
            # 绘制标签
            label_text = font.render(item['label'], True, (0, 0, 0))
            self.screen.blit(label_text, (start_x, y + 10))
            
            # 绘制控件
            # 使用固定的控件起始位置，确保所有开关对齐
            control_x = start_x + 200  # 足够大的固定位置，确保标签文字不会重叠
            control_y = y
            
            # 调整不同类型控件的宽度
            if item['name'] == 'human' and item['type'] == 'dropdown':
                ctrl_width = 140  # 人类玩家名称下拉框长一点
            elif item['type'] in ['number', 'text', 'dropdown']:
                ctrl_width = 80
            else:
                ctrl_width = 50
            
            control_rect = pygame.Rect(control_x, control_y, ctrl_width, 40)
            
            # 根据设置项类型绘制不同的控件
            if item['type'] == 'bool':
                # 绘制布尔值开关背景
                pygame.draw.rect(self.screen, (230, 230, 230), control_rect, 0, 20)
                pygame.draw.rect(self.screen, (100, 100, 100), control_rect, 2, 20)
                
                # 绘制开关滑块，根据状态改变颜色
                switch_color = (0, 150, 255) if self.temp_settings[item['name']] else (150, 150, 150)
                switch_rect = pygame.Rect(control_x + 5, control_y + 5, 20, 30)
                if self.temp_settings[item['name']]:
                    switch_rect.x = control_x + ctrl_width - 25
                pygame.draw.rect(self.screen, switch_color, switch_rect, 0, 15)
                
                # 存储控件位置用于点击检测
                self.temp_settings[item['name'] + '_rect'] = control_rect
                
                # 如果有音量设置，绘制音量滑块
                if item.get('has_volume', False):
                    # 查找对应的音量设置项
                    volume_item = next((v for v in self.setting_items if v.get('parent') == item['name']), None)
                    if volume_item:
                        # 绘制音量滑块
                        slider_x = control_x + ctrl_width + 20
                        slider_y = control_y + 10
                        slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
                        
                        # 绘制滑块背景
                        pygame.draw.rect(self.screen, (200, 200, 200), slider_rect, 0, 10)
                        pygame.draw.rect(self.screen, (100, 100, 100), slider_rect, 1, 10)
                        
                        # 计算滑块位置
                        min_val = volume_item.get('min', 0)
                        max_val = volume_item.get('max', 1)
                        current_val = self.temp_settings[volume_item['name']]
                        slider_pos = int((current_val - min_val) / (max_val - min_val) * (slider_width - 10))
                        
                        # 绘制滑块填充
                        fill_rect = pygame.Rect(slider_x, slider_y, slider_pos + 5, slider_height)
                        pygame.draw.rect(self.screen, (0, 150, 255), fill_rect, 0, 10)
                        
                        # 绘制滑块按钮
                        button_rect = pygame.Rect(slider_x + slider_pos, slider_y - 5, 20, 30)
                        pygame.draw.rect(self.screen, (0, 150, 255), button_rect, 0, 15)
                        
                        # 存储滑块位置用于点击检测
                        self.temp_settings[volume_item['name'] + '_rect'] = slider_rect
                        self.temp_settings[volume_item['name'] + '_button_rect'] = button_rect
                
                # 如果是背景音乐设置，在标签中添加"换一曲"文字按钮
                if item['name'] == 'bg_music_play':
                    # 绘制"换一曲"文字按钮
                    change_song_font = pygame.font.Font(self.settings.font_path, self.settings.small_font_size)
                    change_song_text = change_song_font.render(" | 换一曲", True, (0, 100, 200))
                    # 计算文字位置，放在标签右侧
                    label_width = font.size(item['label'])[0]
                    change_song_x = start_x + label_width
                    change_song_y = y + 10
                    
                    # 绘制文字
                    self.screen.blit(change_song_text, (change_song_x, change_song_y))
                    
                    # 存储文字按钮的点击区域
                    text_rect = change_song_text.get_rect()
                    text_rect.x = change_song_x
                    text_rect.y = change_song_y
                    self.temp_settings['next_bg_music_rect'] = text_rect
            elif item['type'] == 'dropdown':
                # 绘制下拉列表
                pygame.draw.rect(self.screen, (255, 255, 255), control_rect, 0, 5)
                pygame.draw.rect(self.screen, (0, 0, 0), control_rect, 2, 5)
                
                # 绘制当前选中的选项
                selected_option = self.temp_settings[item['name']]
                text_surface = font.render(selected_option, True, (0, 0, 0))
                self.screen.blit(text_surface, (control_x + 10, control_y + 10))
                
                # 绘制下拉箭头
                arrow_x = control_x + ctrl_width - 30
                arrow_y = control_y + 20
                pygame.draw.polygon(self.screen, (0, 0, 0), [(arrow_x, arrow_y - 5), (arrow_x + 10, arrow_y + 5), (arrow_x + 20, arrow_y - 5)])
                
                # 存储控件位置用于点击检测
                self.temp_settings[item['name'] + '_rect'] = control_rect
            else:
                # 绘制文本输入框
                pygame.draw.rect(self.screen, (255, 255, 255), control_rect, 0, 5)
                pygame.draw.rect(self.screen, (0, 0, 0), control_rect, 2, 5)
                
                # 绘制输入文本
                input_text = str(self.temp_settings[item['name']])
                if self.editing_setting == item['name']:
                    input_text = self.input_text
                    # 绘制光标
                    cursor_x = control_x + 10 + font.size(input_text)[0]
                    cursor_y = control_y + 10
                    pygame.draw.line(self.screen, (0, 0, 0), (cursor_x, cursor_y), (cursor_x, cursor_y + 20), 2)
                
                text_surface = font.render(input_text, True, (0, 0, 0))
                self.screen.blit(text_surface, (control_x + 10, control_y + 10))
                
                # 存储控件位置用于点击检测
                self.temp_settings[item['name'] + '_rect'] = control_rect
        
        # 绘制按钮
        button_width = 150
        button_height = 50
        button_y = panel_y + panel_height - 70  # 往上移动20像素，调整位置
        button_spacing = 100  # 按钮之间的间距
        
        # 根据设置页面来源确定按钮数量
        if self.settings_from == 'game':
            # 游戏中设置页面：保存设置、结束游戏、返回
            button_count = 3
        else:
            # 主菜单设置页面：保存设置、返回
            button_count = 2
        
        # 计算按钮组的总宽度
        total_buttons_width = button_count * button_width + (button_count - 1) * button_spacing
        # 计算起始x位置，使按钮组居中显示
        start_x = panel_x + (panel_width - total_buttons_width) // 2
        
        # 保存按钮
        self.settings_save_button = pygame.Rect(start_x, button_y, button_width, button_height)
        pygame.draw.rect(self.screen, (0, 150, 0), self.settings_save_button, 0, 5)
        save_text = font.render("保存设置", True, (255, 255, 255))
        save_text_x = self.settings_save_button.x + (button_width - save_text.get_width()) // 2
        save_text_y = self.settings_save_button.y + (button_height - save_text.get_height()) // 2
        self.screen.blit(save_text, (save_text_x, save_text_y))
        
        # 结束游戏按钮 - 只在游戏中显示
        if self.settings_from == 'game':
            # 结束游戏按钮
            self.end_game_button = pygame.Rect(start_x + button_width + button_spacing, button_y, button_width, button_height)
            pygame.draw.rect(self.screen, (255, 0, 0), self.end_game_button, 0, 5)
            end_game_text = font.render("结束游戏", True, (255, 255, 255))
            end_game_text_x = self.end_game_button.x + (button_width - end_game_text.get_width()) // 2
            end_game_text_y = self.end_game_button.y + (button_height - end_game_text.get_height()) // 2
            self.screen.blit(end_game_text, (end_game_text_x, end_game_text_y))
            
            # 返回按钮
            self.settings_cancel_button = pygame.Rect(start_x + 2 * (button_width + button_spacing), button_y, button_width, button_height)
        else:
            # 主菜单设置页面的返回按钮
            self.settings_cancel_button = pygame.Rect(start_x + button_width + button_spacing, button_y, button_width, button_height)
        
        # 绘制返回按钮
        pygame.draw.rect(self.screen, (150, 0, 0), self.settings_cancel_button, 0, 5)
        cancel_text = font.render("返回", True, (255, 255, 255))
        cancel_text_x = self.settings_cancel_button.x + (button_width - cancel_text.get_width()) // 2
        cancel_text_y = self.settings_cancel_button.y + (button_height - cancel_text.get_height()) // 2
        self.screen.blit(cancel_text, (cancel_text_x, cancel_text_y))
        
        # 绘制确认对话框
        if self.show_confirm_dialog:
            dialog_width = 400
            dialog_height = 200
            dialog_x = (self.settings.win_w - dialog_width) // 2
            dialog_y = (self.settings.win_h - dialog_height) // 2
            
            # 对话框背景
            dialog_bg = pygame.Surface((dialog_width, dialog_height), pygame.SRCALPHA)
            dialog_bg.fill((0, 0, 0, 200))
            self.screen.blit(dialog_bg, (dialog_x, dialog_y))
            
            # 对话框边框
            pygame.draw.rect(self.screen, (255, 255, 255), (dialog_x, dialog_y, dialog_width, dialog_height), 2)
            
            # 对话框文本
            confirm_font = pygame.font.Font(self.settings.font_path, self.settings.normal_font_size)
            
            if self.confirm_end_game:
                # 结束游戏确认
                confirm_text1 = confirm_font.render("确定要结束游戏吗？", True, (255, 255, 255))
                confirm_text2 = confirm_font.render("此操作不可恢复", True, (255, 255, 255))
                
                # 确定按钮
                ok_button_width = 100
                ok_button_height = 40
                ok_button_x = dialog_x + 70
                ok_button_y = dialog_y + 130
                ok_button_rect = pygame.Rect(ok_button_x, ok_button_y, ok_button_width, ok_button_height)
                pygame.draw.rect(self.screen, (255, 0, 0), ok_button_rect, 0, 5)
                ok_text = confirm_font.render("确定", True, (255, 255, 255))
                ok_text_x = ok_button_x + (ok_button_width - ok_text.get_width()) // 2
                ok_text_y = ok_button_y + (ok_button_height - ok_text.get_height()) // 2
                self.screen.blit(ok_text, (ok_text_x, ok_text_y))
                
                # 取消按钮
                cancel_button_rect = pygame.Rect(dialog_x + 230, ok_button_y, ok_button_width, ok_button_height)
                pygame.draw.rect(self.screen, (0, 150, 0), cancel_button_rect, 0, 5)
                cancel_text = confirm_font.render("取消", True, (255, 255, 255))
                cancel_text_x = cancel_button_rect.x + (ok_button_width - cancel_text.get_width()) // 2
                cancel_text_y = cancel_button_rect.y + (ok_button_height - cancel_text.get_height()) // 2
                self.screen.blit(cancel_text, (cancel_text_x, cancel_text_y))
                
                # 存储按钮位置
                self.confirm_ok_button = ok_button_rect
                self.confirm_cancel_button = cancel_button_rect
            elif self.confirm_player_name_change:
                # 玩家名字改变确认
                confirm_text1 = confirm_font.render("改变人类玩家名称", True, (255, 255, 255))
                confirm_text2 = confirm_font.render("所有玩家数据将被重置，请确认", True, (255, 255, 255))
                
                # 确定按钮
                ok_button_width = 100
                ok_button_height = 40
                ok_button_x = dialog_x + 70
                ok_button_y = dialog_y + 130
                ok_button_rect = pygame.Rect(ok_button_x, ok_button_y, ok_button_width, ok_button_height)
                pygame.draw.rect(self.screen, (255, 0, 0), ok_button_rect, 0, 5)
                ok_text = confirm_font.render("确定", True, (255, 255, 255))
                ok_text_x = ok_button_x + (ok_button_width - ok_text.get_width()) // 2
                ok_text_y = ok_button_y + (ok_button_height - ok_text.get_height()) // 2
                self.screen.blit(ok_text, (ok_text_x, ok_text_y))
                
                # 取消按钮
                cancel_button_rect = pygame.Rect(dialog_x + 230, ok_button_y, ok_button_width, ok_button_height)
                pygame.draw.rect(self.screen, (0, 150, 0), cancel_button_rect, 0, 5)
                cancel_text = confirm_font.render("取消", True, (255, 255, 255))
                cancel_text_x = cancel_button_rect.x + (ok_button_width - cancel_text.get_width()) // 2
                cancel_text_y = cancel_button_rect.y + (ok_button_height - cancel_text.get_height()) // 2
                self.screen.blit(cancel_text, (cancel_text_x, cancel_text_y))
                
                # 存储按钮位置
                self.confirm_ok_button = ok_button_rect
                self.confirm_cancel_button = cancel_button_rect
            else:
                # 设置保存确认
                confirm_text1 = confirm_font.render("设置已保存", True, (255, 255, 255))
                confirm_text2 = confirm_font.render("返回主菜单开始游戏", True, (255, 255, 255))
                
                # 确定按钮
                ok_button_width = 100
                ok_button_height = 40
                ok_button_x = dialog_x + (dialog_width - ok_button_width) // 2
                ok_button_y = dialog_y + 130
                ok_button_rect = pygame.Rect(ok_button_x, ok_button_y, ok_button_width, ok_button_height)
                pygame.draw.rect(self.screen, (0, 150, 0), ok_button_rect, 0, 5)
                ok_text = confirm_font.render("确定", True, (255, 255, 255))
                ok_text_x = ok_button_x + (ok_button_width - ok_text.get_width()) // 2
                ok_text_y = ok_button_y + (ok_button_height - ok_text.get_height()) // 2
                self.screen.blit(ok_text, (ok_text_x, ok_text_y))
                
                # 存储确定按钮位置
                self.confirm_ok_button = ok_button_rect
            
            confirm_text1_x = dialog_x + (dialog_width - confirm_text1.get_width()) // 2
            confirm_text1_y = dialog_y + 50
            confirm_text2_x = dialog_x + (dialog_width - confirm_text2.get_width()) // 2
            confirm_text2_y = dialog_y + 90
            self.screen.blit(confirm_text1, (confirm_text1_x, confirm_text1_y))
            self.screen.blit(confirm_text2, (confirm_text2_x, confirm_text2_y))
        
        # 更新显示
        pygame.display.flip()
    
    def _draw_game_state(self):
        """绘制游戏状态 - 应用层只负责UI渲染"""
        # 获取当前玩家和剩余牌数
        self.ui_manager.set_players(self.game_manager.players)
        current_player = self.game_manager.get_current_player()
        last_player = self.game_manager.get_players()[self.game_manager.last_player_index]
        remaining_tiles = self.game_manager.get_remaining_tiles_count()
        turn_switch_to_human = self.game_manager.turn_switch_to_human()
        turn_switch_from_human = self.game_manager.turn_switch_from_human()
        
        # 绘制UI，传入当前玩家
        self.ui_manager.draw_bg(current_player) # 绘制背景图片
        self.ui_manager.draw_indicator(current_player.position)
        self.ui_manager.draw_remaining_tiles(remaining_tiles) # 绘制剩余牌数
        self.ui_manager.draw_avtar() # 绘制头像

        # 给uimanager传递指示牌的关键信息
        self.ui_manager.current_player = current_player
        self.ui_manager.last_player = last_player
        self.ui_manager.discard_tile = self.game_manager.discard_tile
        current_tiles = current_player.get_discard_tiles()
        last_tiles = last_player.get_discard_tiles()
        if current_tiles or last_tiles:
            self.ui_manager.discard_tile_indicator = True
        else:
            self.ui_manager.discard_tile_indicator = False

        
        # 调用UI管理器绘制设置按钮和局数
        total_games = self.game_manager.total_games
        self.ui_manager.draw_settings_and_game_number(total_games, self.game_manager.is_game_over)

        # 检查是否切换至人类玩家回合
        if turn_switch_to_human and not self.have_human_selected:
            human = self.game_manager.get_human_player()
            concealed = human.get_concealed_hand()
            recommend_tile_index = human.get_recommend_tile_index()
            if recommend_tile_index >= 0:
                self.ui_manager.float_tile_list = [recommend_tile_index]
            else:
                self.ui_manager.float_tile_list = [len(concealed)-1]
        
        # 检查是否从人类玩家回合切走
        elif turn_switch_from_human:
            self.ui_manager.set_float_tile_list([])
        
        # 调用UI管理器的draw_hands方法，传递选中的牌索引        
        if self.game_manager.is_game_over:            
            self.show_all_faces = True
            self.ui_manager.set_float_tile_list([])
            self.ui_manager.fanji_tile = self.game_manager.fanji_tile
            self.ui_manager.fanji_tiles = self.game_manager.fanji_tiles
        else:
            self.show_all_faces = self.settings.show_all_faces

        show_self = True        
        self.ui_manager.draw_hands(self.show_all_faces,show_self)
        
        # 绘制碰杠胡操作按钮（在所有元素绘制完成后绘制，避免被覆盖）
        # 检查游戏管理器是否有决策请求
        if self.game_manager.have_decision_request():
            decision_player_index = self.game_manager.decision_request.player_index
            decision_player = self.game_manager.get_players()[decision_player_index]
            if decision_player.is_human:
                decision_request = self.game_manager.decision_request
                decision_types = decision_request.decision_list
                
                # 转换为UI管理器所需的操作按钮列表
                action_buttons = []
                tile = self.game_manager.decision_request.tile
                indexes = decision_player.get_tile_indexes(tile)
                for dt in decision_types:
                    if dt == DecisionType.HU:
                        action_buttons.append('hu')
                    elif dt == DecisionType.GANG:
                        action_buttons.append('gang')
                        self.ui_manager.set_float_tile_list(indexes[:3])
                    elif dt == DecisionType.PENG:
                        action_buttons.append('peng')
                        self.ui_manager.set_float_tile_list(indexes[:2])
                            
                # 添加取消按钮
                if action_buttons:
                    action_buttons.append('cancel')
                    
                    # 按优先级排序：胡 > 杠 > 碰
                    action_priority = {'hu': 3, 'gang': 2, 'peng': 1}
                    action_buttons.sort(key=lambda x: action_priority.get(x, 0), reverse=True)
                    
                    # 绘制操作按钮
                    self.ui_manager.draw_action_buttons(action_buttons)
    
        # 最后绘制toast提示，确保它在最上层显示
        self.ui_manager.draw_toasts()

        # 检查游戏是否结束
        if self.game_manager.is_game_over and self.game_manager.total_games > 0:
            
            # 检查是否有游戏结束按钮（在绘制后才会生成）
            show_overlay = not self.ui_manager.show_table
            
            # 绘制游戏结束蒙层，传入真实的总局数和流局数
            if show_overlay:
                total_games = self.game_manager.total_games if self.game_manager.total_games else 1
                draw_games = self.game_manager.draw_games
                self.ui_manager._draw_game_over_screen(self.game_manager.winner, total_games, draw_games, self.game_manager.hu_type)
        
            # 2. 每局游戏结束，调用保存结果方法
            # 添加标志防止重复保存
            if not hasattr(self, '_current_game_saved') or not self._current_game_saved:
                self._save_current_game_result()
                self._current_game_saved = True
                
        # 如果游戏暂停，绘制暂停蒙层和继续按钮
        if hasattr(self.ui_manager, 'is_paused') and self.ui_manager.is_paused:
            # 绘制半透明灰色蒙层
            overlay = pygame.Surface((self.settings.win_w, self.settings.win_h), pygame.SRCALPHA)
            overlay.fill((128, 128, 128, 150))  # 灰色半透明蒙层
            self.screen.blit(overlay, (0, 0))
            
            # 绘制继续按钮，居中显示
            if hasattr(self.ui_manager, 'continue_button_image') and self.ui_manager.continue_button_image:
                continue_x = (self.settings.win_w - 500) // 2
                continue_y = (self.settings.win_h - 500) // 2
                self.screen.blit(self.ui_manager.continue_button_image, (continue_x, continue_y))
                # 保存继续按钮区域
                self.ui_manager.continue_button_rect = pygame.Rect(continue_x, continue_y, 500, 500)
                
                # 在continue图片下方绘制红色小字
                font = pygame.font.Font(self.settings.font_path, 12)  # 使用24号字体
                text = font.render("点击广告，继续吃鸡", True, (255, 0, 0))  # 红色文字
                text_x = (self.settings.win_w - text.get_width()) // 2  # 文字居中
                text_y = continue_y + 500 + 20  # 图片下方20像素
                self.screen.blit(text, (text_x, text_y))
        
        # 更新显示
        pygame.display.flip()

    def _handle_events(self):
        """处理游戏事件"""
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:

                if self.current_screen == GameScreen.GAME_PLAY:
                    self._handle_game_play_key_down(event)
                elif self.current_screen == GameScreen.SETTINGS:
                    self._handle_settings_key_down(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:

                # 播放点击音效
                self.sound_manager.play_sound('click')

                if self.current_screen == GameScreen.MAIN_MENU:
                    self._handle_main_menu_mouse_down(event)
                elif self.current_screen == GameScreen.SETTINGS:
                    self._handle_settings_mouse_down(event)
                elif self.current_screen == GameScreen.GAME_PLAY:
                    self._handle_game_play_mouse_down(event)
                elif self.current_screen == GameScreen.GAME_HISTORY:
                    self._handle_game_history_mouse_down(event)
                
                elif self.current_screen == GameScreen.GAME_HISTORY_DETAIL:
                    # 处理历史对局详情页面鼠标点击事件
                    mouse_pos = pygame.mouse.get_pos()
                    # 播放点击音效
                    self.sound_manager.play_sound('click')
                    
                    # 检查导航按钮点击
                    if hasattr(self.ui_manager, '_detail_buttons_rects'):
                        # 返回按钮
                        if 'back' in self.ui_manager._detail_buttons_rects and self.ui_manager._detail_buttons_rects['back'].collidepoint(mouse_pos):
                            self.current_screen = GameScreen.GAME_HISTORY
                            return
                        
                        # 上一局按钮
                        if 'prev' in self.ui_manager._detail_buttons_rects and self.ui_manager._detail_buttons_rects['prev'].collidepoint(mouse_pos):
                            if self._current_detail_game_index > 0:
                                self._current_detail_game_index -= 1
                                # 同步到 UIManager，确保绘制时使用最新索引
                                try:
                                    self.ui_manager._current_detail_game_index = self._current_detail_game_index
                                except Exception:
                                    pass
                            return
                        
                        # 下一局按钮
                        if 'next' in self.ui_manager._detail_buttons_rects and self.ui_manager._detail_buttons_rects['next'].collidepoint(mouse_pos):
                            if self._current_detail_game_index < len(self._detail_game_files) - 1:
                                self._current_detail_game_index += 1
                                # 同步到 UIManager，确保绘制时使用最新索引
                                try:
                                    self.ui_manager._current_detail_game_index = self._current_detail_game_index
                                except Exception:
                                    pass
                            return
                        
                        # 查看结算详情按钮
                        if 'detail' in self.ui_manager._detail_buttons_rects and self.ui_manager._detail_buttons_rects['detail'].collidepoint(mouse_pos):
                            self.ui_manager.show_toast("结算详情功能待实现")
                            return
        
    def _update_game_state(self):
        """更新游戏状态 - 应用层只负责调用业务逻辑层"""

        # 如果游戏暂停，不更新游戏状态
        if hasattr(self.ui_manager, 'is_paused') and self.ui_manager.is_paused:
            return
            
        # 调用业务逻辑层更新游戏状态
        if not self.game_manager.is_game_over:
            # 同步当前游戏的总局数和流局数
            self.total_games = self.game_manager.total_games
            self.draw_games = self.game_manager.draw_games
            self.game_manager.update_game_state()
        else:
            # 游戏结束时增加总局数计数
            if not hasattr(self, 'game_ended_flag') or not self.game_ended_flag:
                # 检查是否流局（没有赢家）
                if not self.game_manager.winner:
                    self.draw_games += 1
                # 将更新后的总局数和流局数传递给game_manager
                self.total_games = self.game_manager.total_games
                self.draw_games = self.game_manager.draw_games
                self.game_ended_flag = True
                # 记录游戏结束时间
                self.game_over_time = time.time()
            else:
                # 游戏结束后，检查是否需要自动再来一局
                current_time = time.time()
                elapsed_time = current_time - self.game_over_time
                # 如果auto_restart_time=-1，则不自动重开
                if self.settings.auto_restart_time > 0 and elapsed_time >= self.settings.auto_restart_time and self.total_games < self.settings.test_round:
                    # 超时自动再来一局，仅当总局数小于测试轮数时
                    self.game_ended_flag = False
                    self.ui_manager.show_result_detail = False
                    self.ui_manager.show_table = False
                    # 重置游戏保存标志
                    self._current_game_saved = False
                    self.game_manager.initialize_game(self.settings.test_mode)

        player = self.game_manager.get_current_player()
        if player.is_human and self.game_manager.have_decision_request():
            self.handle_decision_request()
        
    def _handle_game_history_mouse_down(self, event):
        """处理历史对局页面鼠标按下事件"""
        mouse_pos = pygame.mouse.get_pos()

        # 如果正在显示删除确认弹窗，优先处理确认/取消按钮
        if hasattr(self.ui_manager, 'show_delete_confirm') and self.ui_manager.show_delete_confirm:
            # 确认删除
            if hasattr(self.ui_manager, '_delete_confirm_ok_rect') and self.ui_manager._delete_confirm_ok_rect.collidepoint(mouse_pos):
                folder = getattr(self.ui_manager, '_pending_delete_folder', None)
                if folder:
                    try:
                        import shutil, os
                        if os.path.exists(folder):
                            shutil.rmtree(folder)
                        self.ui_manager.show_toast("已删除历史记录")
                    except Exception:
                        self.ui_manager.show_toast("删除失败")
                self.ui_manager.show_delete_confirm = False
                if hasattr(self.ui_manager, '_pending_delete_folder'):
                    try:
                        delattr(self.ui_manager, '_pending_delete_folder')
                    except Exception:
                        pass
                return

            # 取消删除
            if hasattr(self.ui_manager, '_delete_confirm_cancel_rect') and self.ui_manager._delete_confirm_cancel_rect.collidepoint(mouse_pos):
                self.ui_manager.show_delete_confirm = False
                if hasattr(self.ui_manager, '_pending_delete_folder'):
                    try:
                        delattr(self.ui_manager, '_pending_delete_folder')
                    except Exception:
                        pass
                return

        # 播放点击音效
        self.sound_manager.play_sound('click')

        # 检查返回按钮
        if hasattr(self.ui_manager, 'back_button_rect') and self.ui_manager.back_button_rect.collidepoint(mouse_pos):
            self.current_screen = GameScreen.MAIN_MENU
            return
        # 检查上一页按钮
        if hasattr(self.ui_manager, '_prev_page_rect') and self.ui_manager._prev_page_rect and self.ui_manager._prev_page_rect.collidepoint(mouse_pos):
            current_page = getattr(self.ui_manager, '_history_page', 0)
            if current_page > 0:
                self.ui_manager._history_page -= 1
            return
        # 检查下一页按钮
        if hasattr(self.ui_manager, '_next_page_rect') and self.ui_manager._next_page_rect and self.ui_manager._next_page_rect.collidepoint(mouse_pos):
            current_page = getattr(self.ui_manager, '_history_page', 0)
            if current_page < getattr(self.ui_manager, '_total_pages', 0) - 1:
                self.ui_manager._history_page += 1
            return

        # 检查每个卡片的删除按钮
        if hasattr(self.ui_manager, '_delete_buttons'):
            for folder, rect in self.ui_manager._delete_buttons.items():
                try:
                    if rect and rect.collidepoint(mouse_pos):
                        # 弹出确认对话并记录待删除文件夹
                        self.ui_manager.show_delete_confirm = True
                        self.ui_manager._pending_delete_folder = folder
                        return
                except Exception:
                    continue
        # 检查每个卡片的“查看详情”按钮
        if hasattr(self.ui_manager, '_detail_buttons'):
            for key, rect in self.ui_manager._detail_buttons.items():
                try:
                    if rect and rect.collidepoint(mouse_pos):
                        # 切换到详情页面并准备文件列表
                        try:
                            import os
                            import json
                            import tempfile
                            from datetime import datetime
                            
                            if key == 'current':
                                # 处理当前游戏记录
                                # 使用游戏开始时创建的历史记录文件夹
                                folder = self.history_folder_path
                                folder_name = self.history_folder_name
                                
                                # 保存当前游戏的总览数据到历史记录文件夹
                                overview_data = {
                                    'timestamp': datetime.now().isoformat(),
                                    'start_timestamp': self.game_start_timestamp.isoformat(),
                                    'total_games': self.game_manager.total_games,
                                    'draw_games': self.game_manager.draw_games,
                                    'hu_type': {tag.value: count for tag, count in self.game_manager.hu_type.items()},
                                    'players': [
                                        {
                                            'name': player.name,
                                            'ai_version': getattr(player, 'ai_version', ''),
                                            'is_human': player.is_human,
                                            'score': player.score,
                                            'previous_score': getattr(player, 'previous_score', 0),
                                            'win_count': getattr(player, 'win_count', 0),
                                            'win_rate': getattr(player, 'win_rate', 0.0),
                                            'OfferingWin_count': getattr(player, 'OfferingWin_count', 0),
                                            'OfferingWin_rate': getattr(player, 'OfferingWin_rate', 0.0),
                                            'gain_ji_count': getattr(player, 'gain_ji_count', 0),
                                            'gain_ji_rate': getattr(player, 'gain_ji_rate', 0.0),
                                            'loss_ji_count': getattr(player, 'loss_ji_count', 0),
                                            'loss_ji_rate': getattr(player, 'loss_ji_rate', 0.0)
                                        }
                                        for player in self.game_manager.players
                                    ]
                                }
                                
                                # 生成总览文件名
                                overview_file = os.path.join(folder, f"{folder_name}.json")
                                with open(overview_file, 'w', encoding='utf-8') as f:
                                    json.dump(overview_data, f, ensure_ascii=False, indent=2)
                                
                                # 获取当前文件夹下的所有单局游戏记录文件
                                files = [f for f in os.listdir(folder) if f.endswith('.json') and f != f'{folder_name}.json']
                                
                                # 按照游戏局数排序，确保时间顺序
                                def get_game_number(file_name):
                                    try:
                                        # 从文件名中提取局数：game_1.json -> 1
                                        return int(file_name.split('_')[1].split('.')[0])
                                    except Exception:
                                        return 0
                                
                                files.sort(key=get_game_number)
                                # 保存到 ui_manager 和 game 对象，保证事件处理和绘制均可访问
                                self.ui_manager._current_detail_folder = folder
                                self.ui_manager._detail_game_files = files
                                self.ui_manager._current_detail_game_index = 0

                                self._current_detail_folder = folder
                                self._detail_game_files = files
                                self._current_detail_game_index = 0
                            else:
                                # 处理历史游戏记录
                                folder = key
                                folder_name = os.path.basename(folder)
                                files = [f for f in os.listdir(folder) if f.endswith('.json') and f != f'{folder_name}.json']
                                
                                # 按照游戏局数排序，确保时间顺序
                                def get_game_number(file_name):
                                    try:
                                        # 从文件名中提取局数：game_1.json -> 1
                                        return int(file_name.split('_')[1].split('.')[0])
                                    except Exception:
                                        return 0
                                
                                files.sort(key=get_game_number)
                                # 保存到 ui_manager 和 game 对象，保证事件处理和绘制均可访问
                                self.ui_manager._current_detail_folder = folder
                                self.ui_manager._detail_game_files = files
                                self.ui_manager._current_detail_game_index = 0

                                self._current_detail_folder = folder
                                self._detail_game_files = files
                                self._current_detail_game_index = 0
                        except Exception as e:
                            self.ui_manager.show_toast('读取历史文件失败')
                            return
                        self.current_screen = GameScreen.GAME_HISTORY_DETAIL
                        return
                except Exception:
                    continue
   
    def _handle_settings_mouse_down(self, event):
        """处理设置页面鼠标点击事件"""
        mouse_pos = pygame.mouse.get_pos()
        
        # 处理确认对话框
        if self.show_confirm_dialog:
            if self.confirm_ok_button.collidepoint(mouse_pos):
                self.show_confirm_dialog = False
                if self.confirm_end_game:
                    # 结束游戏，返回主菜单
                    self.current_screen = GameScreen.MAIN_MENU
                    self.game_started = False
                    self.ui_manager.show_result_detail = False
                    self.ui_manager.show_table = False
                    self.game_manager.is_game_over = False
                    self.confirm_end_game = False
                    # 重置临时设置
                    self.temp_settings = {}
                elif self.confirm_player_name_change:
                    # 玩家确认改变名字，标记为已确认并重新保存
                    self.player_name_change_confirmed = True
                    self.confirm_player_name_change = False
                    self._save_settings()
                else:
                    self.current_screen = GameScreen.MAIN_MENU if self.settings_from == 'main_menu' else GameScreen.GAME_PLAY
                    # 重置临时设置
                    self.temp_settings = {}
            elif self.confirm_cancel_button.collidepoint(mouse_pos):
                # 取消确认
                self.show_confirm_dialog = False
                self.confirm_end_game = False
                self.confirm_player_name_change = False
                self.player_name_change_confirmed = False
                # 重置临时设置
                self.temp_settings = {}
            return
        
        # 处理保存按钮
        if self.settings_save_button.collidepoint(mouse_pos):
            self._save_settings()
            return
        
        # 处理取消按钮
        if self.settings_cancel_button.collidepoint(mouse_pos):
            self._cancel_settings()
            return
        
        # 处理结束游戏按钮
        if hasattr(self, 'end_game_button') and self.end_game_button.collidepoint(mouse_pos):
            # 显示结束游戏确认对话框
            self.show_confirm_dialog = True
            self.confirm_end_game = True
            return
        
        # 根据设置页面来源决定可修改的设置项
        if self.settings_from == 'game':
            # 游戏中设置页面，不可修改玩家名字、初始分数和测试模式
            editable_items = [item for item in self.setting_items if item['name'] not in ['human', 'score', 'test_mode']]
        else:
            # 主菜单设置页面，可修改所有设置项
            editable_items = self.setting_items
        
        # 处理音量滑块
        for item in editable_items:
            if item['type'] == 'volume':
                slider_rect = self.temp_settings.get(item['name'] + '_rect')
                if slider_rect and slider_rect.collidepoint(mouse_pos):
                    # 计算新的音量值
                    min_val = item.get('min', 0)
                    max_val = item.get('max', 1)
                    # 计算点击位置在滑块上的比例
                    ratio = (mouse_pos[0] - slider_rect.x) / slider_rect.width
                    # 确保比例在0-1之间
                    ratio = max(0.0, min(1.0, ratio))
                    # 计算新的音量值
                    new_volume = min_val + ratio * (max_val - min_val)
                    # 保存新的音量值
                    self.temp_settings[item['name']] = new_volume
                    break
        else:
            # 处理非音量设置项
            # 检查是否点击了下一首背景音乐按钮
            next_bg_music_rect = self.temp_settings.get('next_bg_music_rect')
            if next_bg_music_rect and next_bg_music_rect.collidepoint(mouse_pos):
                # 切换到下一首背景音乐
                self.sound_manager.next_bg_music()
                return
            
            for item in editable_items:
                if item['type'] == 'volume':
                    continue
                    
                control_rect = self.temp_settings.get(item['name'] + '_rect')
                if control_rect and control_rect.collidepoint(mouse_pos):
                    if item['type'] == 'bool':
                        # 切换布尔值
                        self.temp_settings[item['name']] = not self.temp_settings[item['name']]
                        break
                    elif item['type'] == 'dropdown':
                        # 处理下拉列表点击，循环切换选项
                        current_value = self.temp_settings[item['name']]
                        options = item['options']
                        current_index = options.index(current_value)
                        next_index = (current_index + 1) % len(options)
                        self.temp_settings[item['name']] = options[next_index]
                        break
                    else:
                        # 开始编辑文本
                        self.editing_setting = item['name']
                        self.input_text = str(self.temp_settings[item['name']])
                        break
            else:
                # 点击了其他区域，结束编辑并保存当前数值
                current_item = None
                if self.editing_setting is not None:
                    # 查找当前编辑的设置项
                    for item in editable_items:
                        if item['name'] == self.editing_setting:
                            current_item = item
                            break
                
                if current_item and current_item['type'] == 'number':
                    # 保存当前输入的数值
                    try:
                        if '.' in self.input_text:
                            self.temp_settings[self.editing_setting] = float(self.input_text)
                        else:
                            self.temp_settings[self.editing_setting] = int(self.input_text)
                    except ValueError:
                        # 转换失败，保持原值
                        pass
                self.editing_setting = None

    def _handle_settings_key_down(self, event):
        """处理设置页面键盘事件"""
        if self.editing_setting is None:
            return
        
        # 查找当前编辑的设置项
        current_item = None
        for item in self.setting_items:
            if item['name'] == self.editing_setting:
                current_item = item
                break
        
        if not current_item:
            return
        
        if event.key == pygame.K_RETURN:
            # 结束编辑并保存数值
            if current_item['type'] == 'number':
                # 转换为数字
                try:
                    if '.' in self.input_text:
                        self.temp_settings[self.editing_setting] = float(self.input_text)
                    else:
                        self.temp_settings[self.editing_setting] = int(self.input_text)
                except ValueError:
                    # 转换失败，保持原值
                    pass
            else:
                # 保持字符串
                self.temp_settings[self.editing_setting] = self.input_text
            self.editing_setting = None
        elif event.key == pygame.K_ESCAPE:
            # 取消编辑，恢复原值
            self.input_text = str(self.temp_settings[self.editing_setting])
            self.editing_setting = None
        elif event.key == pygame.K_BACKSPACE:
            # 删除字符
            self.input_text = self.input_text[:-1]
        else:
            # 添加字符
            char = event.unicode
            if current_item['type'] == 'number':
                # 只允许数字和小数点
                if char.isdigit() or (char == '.' and '.' not in self.input_text):
                    self.input_text += char
            else:
                # 允许所有字符
                self.input_text += char
    
    def _save_settings(self):
        """保存设置"""
        # 检查人类玩家名称或游戏模式是否改变
        name_changed = 'human' in self.temp_settings and self.temp_settings['human'] != self.original_human_name
        
        # 检查游戏模式是否改变
        game_mode_changed = 'game_mode' in self.temp_settings
        if game_mode_changed:
            # 根据游戏模式获取对应的opponent_ai_version_list值
            game_mode = self.temp_settings['game_mode']
            if game_mode == '简单':
                new_ai_version_list = self.settings.mode_easy
            elif game_mode == '中等':
                new_ai_version_list = self.settings.mode_normal
            else: # 困难
                new_ai_version_list = self.settings.mode_hard
            
            # 检查opponent_ai_version_list是否真的改变了
            game_mode_changed = new_ai_version_list != getattr(self.settings, 'opponent_ai_version_list', [])
        
        # 如果名称或游戏模式改变了，需要确认
        if (name_changed or game_mode_changed) and not self.player_name_change_confirmed:
            # 如果还没有确认过，显示确认对话框
            self.show_confirm_dialog = True
            self.confirm_player_name_change = True
            return
        else:
            # 已经确认过，重置确认标志
            self.player_name_change_confirmed = False
            
            # 检查是否有对局数据
            if (name_changed or game_mode_changed) and self.game_manager.total_games > 0:
                # 1. 保存当前对局数据
                self.ui_manager._save_game_history()
                
                # 2. 重新创建时间戳文件夹
                import os
                from datetime import datetime
                
                # 重置游戏开始时间戳
                self.game_start_timestamp = datetime.now()
                # 创建新的文件夹名称
                self.history_folder_name = self.game_start_timestamp.strftime("%y%m%d_%H%M%S")
                history_dir = os.path.join('data', 'history')
                self.history_folder_path = os.path.join(history_dir, self.history_folder_name)
                # 确保新文件夹存在
                if not os.path.exists(self.history_folder_path):
                    os.makedirs(self.history_folder_path)
                
                # 3. 重置游戏管理器的相关数据
                self.game_manager.initialize_manager()
                # 重置游戏总局数
                self.game_manager.total_games = 0
                # 重置流局数
                self.game_manager.draw_games = 0
                # 重置胡牌类型统计
                self.game_manager.hu_type = {}
                # 不需要调用initialize_game，因为游戏还没有开始
                
                # 4. 重置当前游戏保存标志
                self._current_game_saved = False
                
                # 5. 重置游戏开始标志
                self.game_started = False
        
        # 处理游戏加速模式
        speed_up_changed = 'speed_up' in self.temp_settings and self.temp_settings['speed_up'] != getattr(self.settings, 'speed_up', False)
        speed_up_value = self.temp_settings.get('speed_up', getattr(self.settings, 'speed_up', False))
        
        # 保存所有临时设置到实际设置对象
        for name, value in self.temp_settings.items():
            if name == 'game_mode':
                # 根据游戏模式设置对应的opponent_ai_version_list
                if value == '简单':
                    setattr(self.settings, 'opponent_ai_version_list', self.settings.mode_easy)
                elif value == '中等':
                    setattr(self.settings, 'opponent_ai_version_list', self.settings.mode_normal)
                else: # 困难
                    setattr(self.settings, 'opponent_ai_version_list', self.settings.mode_hard)
            else:
                setattr(self.settings, name, value)
        
        # 如果游戏加速模式改变了，更新相关设置
        if speed_up_changed:
            if speed_up_value:
                # 加速模式开启，保存原值并设置新值
                self.settings.original_human_time_limit = getattr(self.settings, 'human_time_limit', 15)
                self.settings.original_ai_time_limit = getattr(self.settings, 'ai_time_limit', 2)
                self.settings.original_auto_restart_time = getattr(self.settings, 'auto_restart_time', 30)
                self.settings.original_toast_duration = getattr(self.settings, 'toast_duration', 3000)
                self.settings.original_test_round = getattr(self.settings, 'test_round', 10)
                
                self.settings.human_time_limit = 0.1
                self.settings.ai_time_limit = 0.1
                self.settings.auto_restart_time = 3
                self.settings.toast_duration = 1000
                self.settings.test_round = 1000
            else:
                # 加速模式关闭，恢复原值
                if hasattr(self.settings, 'original_human_time_limit'):
                    self.settings.human_time_limit = self.settings.original_human_time_limit
                    self.settings.ai_time_limit = self.settings.original_ai_time_limit
                    self.settings.auto_restart_time = self.settings.original_auto_restart_time
                    self.settings.toast_duration = self.settings.original_toast_duration
                    self.settings.test_round = self.settings.original_test_round
                    
                    # 删除保存的原值
                    delattr(self.settings, 'original_human_time_limit')
                    delattr(self.settings, 'original_ai_time_limit')
                    delattr(self.settings, 'original_auto_restart_time')
                    delattr(self.settings, 'original_toast_duration')
                    delattr(self.settings, 'original_test_round')
        
        # 更新游戏中使用show_all_faces的地方
        self.show_all_faces = self.settings.show_all_faces
        
        # 更新游戏管理器、声音管理器和UI管理器的设置
        self.game_manager.settings = self.settings
        self.sound_manager.update_settings(self.settings)
        self.ui_manager.settings = self.settings
        
        # 重置游戏管理器的last_human_player_name，以便重新初始化玩家
        self.game_manager.last_human_player_name = None
        
        # 生成并显示toast提示
        changed_settings = []
        for name, value in self.temp_settings.items():
            if name in self.initial_settings and self.temp_settings[name] != self.initial_settings[name]:
                changed_settings.append((name, self.initial_settings[name], self.temp_settings[name]))
        
        if not changed_settings:
            # 没有改变任何设置
            self.ui_manager.show_toast("未做任何有效更改")
        else:
            # 生成设置改变的toast消息
            changes = []
            max_changes = 3
            for i, (name, old_val, new_val) in enumerate(changed_settings[:max_changes]):
                # 查找设置项的标签
                label = name
                for item in self.setting_items:
                    if item['name'] == name:
                        label = item['label']
                        break
                changes.append(f"{label}: {old_val}--> {new_val}")
            
            # 添加省略标识
            if len(changed_settings) > max_changes:
                changes.append("等")
            
            # 生成完整消息
            message = f"设置已保存生效: {'; '.join(changes)}"
            self.ui_manager.show_toast(message)
        
        # 根据设置页面来源返回相应页面
        if self.settings_from == 'game':
            self.current_screen = GameScreen.GAME_PLAY
        else:
            self.current_screen = GameScreen.MAIN_MENU
        
        # 重置设置初始化标志和来源
        self.settings_initialized = False
        self.settings_from = None
        self.confirm_player_name_change = False
        # 重置临时设置
        self.temp_settings = {}
    
    def _cancel_settings(self):
        """取消设置，返回主菜单"""
        # 显示toast提示
        self.ui_manager.show_toast("未做任何有效更改")
        
        # 根据设置页面来源返回相应页面
        if self.settings_from == 'game':
            self.current_screen = GameScreen.GAME_PLAY
        else:
            self.current_screen = GameScreen.MAIN_MENU
        
        # 重置临时设置和相关标志
        self.temp_settings = {}
        self.settings_initialized = False
        self.settings_from = None
        self.player_name_change_confirmed = False
        self.original_human_name = self.settings.human

    def _handle_main_menu_mouse_down(self, event):
        """处理主菜单鼠标点击事件"""
        import os
        mouse_pos = pygame.mouse.get_pos()
        
        # 播放点击音效
        self.sound_manager.play_sound('click')
        
        # 检查开始游戏按钮
        if self.main_menu_buttons['start_game'].collidepoint(mouse_pos):
            self.current_screen = GameScreen.GAME_PLAY
            self.game_started = True
            self.game_ended_flag = False
            test_mode = self.settings.test_mode
            
            # 重置当前游戏已保存标志
            self._current_game_saved = False
            
            # 调用initialize_manager，它会检查是否需要重新初始化玩家
            self.game_manager.initialize_manager()
            # 调用initialize_game，但确保不会重置玩家分数
            self.game_manager.initialize_game(test_mode)
        # 检查设置按钮
        elif self.main_menu_buttons['settings'].collidepoint(mouse_pos):
            self.current_screen = GameScreen.SETTINGS
            self.settings_from = 'main_menu'
        # 检查历史对局按钮
        elif self.main_menu_buttons['game_history'].collidepoint(mouse_pos):
            # 总是进入历史对局页面，让页面自己处理是否显示空数据
            self.current_screen = GameScreen.GAME_HISTORY
        # 空白处点击也播放音效，不需要额外处理
    
    def _handle_game_play_key_down(self, event):
        """处理键盘按下事件"""
        if not self.game_started:
            return
            
        # 让game_manager处理键盘事件
        if event.key == pygame.K_LEFT:
            self.ui_manager.move_selection_left()
            self._draw_game_state()  # 立即更新显示
        elif event.key == pygame.K_RIGHT:
            self.ui_manager.move_selection_right()
            self._draw_game_state()  # 立即更新显示
        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
            if self.game_manager.have_decision_request():
                request = self.game_manager.decision_request
                float_tile_index = self.ui_manager.float_tile_list[0]
                cp = self.game_manager.get_current_player()
                reason = "用户键入Enter"
                if cp.is_human and request:
                    dc_type = DecisionType.DISCARD
                    tile = self.ui_manager.get_human_player().get_concealed_hand()[float_tile_index]
                    if DecisionType.DISCARD in request.decision_list:
                        self.set_decision_result(dc_type,True,tile,reason)
                    else:
                        self.set_decision_result(request.decision_list[0],True,None,reason)
        elif event.key == pygame.K_ESCAPE:
            if self.game_manager.have_decision_request():
                request = self.game_manager.decision_request
                float_tile_index = self.ui_manager.float_tile_list[0]
                cp = self.game_manager.get_current_player()
                reason = "用户键入Escape"
                if cp.is_human and request:
                    dc_type = DecisionType.DISCARD
                    tile = self.ui_manager.get_human_player().get_concealed_hand()[float_tile_index]
                    if DecisionType.DISCARD not in request.decision_list:
                        self.set_decision_result(DecisionType.default,False,None,reason)
    
    def _handle_game_play_mouse_down(self, event):
        """处理鼠标按下事件"""
        # 获取鼠标位置
        mouse_pos = pygame.mouse.get_pos()
        
        # 播放点击音效
        self.sound_manager.play_sound('click')
        
        # 检查游戏中设置按钮，只有点击"设置"文字时才打开设置界面
        if hasattr(self.ui_manager, 'settings_text_rect') and self.ui_manager.settings_text_rect and self.ui_manager.settings_text_rect.collidepoint(mouse_pos):
            self.current_screen = GameScreen.SETTINGS
            self.settings_from = 'game'
            return
        
        # 检查暂停按钮点击
        if hasattr(self.ui_manager, 'suspend_button') and self.ui_manager.suspend_button and self.ui_manager.suspend_button.collidepoint(mouse_pos):
            self.ui_manager.is_paused = True
            return
        
        # 检查继续按钮点击（如果游戏已暂停）
        if hasattr(self.ui_manager, 'is_paused') and self.ui_manager.is_paused:
            if hasattr(self.ui_manager, 'continue_button_rect') and self.ui_manager.continue_button_rect and self.ui_manager.continue_button_rect.collidepoint(mouse_pos):
                self.ui_manager.is_paused = False
                return
            # 如果点击了蒙层其他区域，不做任何处理
            return
        
        # 检查游戏是否结束
        if self.game_manager.is_game_over:

            # 处理游戏结束按钮点击
            if hasattr(self.ui_manager, 'game_over_buttons'):
                # 检查"再来一局"按钮
                if self.ui_manager.game_over_buttons['restart'].collidepoint(mouse_pos):
                    self.game_ended_flag = False
                    self.ui_manager.show_result_detail = False
                    self.ui_manager.show_table = False
                    # 重置游戏保存标志
                    self._current_game_saved = False
                    self.game_manager.initialize_game(self.settings.test_mode)
                    return
                # 检查"查看桌面"按钮
                if self.ui_manager.game_over_buttons['view_table'].collidepoint(mouse_pos):
                    # 切换查看桌面状态
                    self.ui_manager.show_table = not self.ui_manager.show_table
                    return
                # 检查"结算详情"按钮
                if 'result_detail' in self.ui_manager.game_over_buttons and self.ui_manager.game_over_buttons['result_detail'].collidepoint(mouse_pos):
                    # 切换结算详情显示状态
                    self.ui_manager.show_result_detail = not self.ui_manager.show_result_detail
                    return
                # 检查"返回桌面"按钮
                if 'back_to_menu' in self.ui_manager.game_over_buttons and self.ui_manager.game_over_buttons['back_to_menu'].collidepoint(mouse_pos):
                    # 返回桌面，切换到主菜单页面
                    self.current_screen = GameScreen.MAIN_MENU
                    self.game_started = False
                    self.ui_manager.show_result_detail = False
                    self.ui_manager.show_table = False
                    # 重置游戏状态
                    self.game_manager.is_game_over = False
                    return
                
                # 如果显示查看桌面，点击按钮外区域恢复蒙层
                if self.ui_manager.show_table:
                    # 检查是否点击查看桌面按钮外区域
                    if not self.ui_manager.game_over_buttons['view_table'].collidepoint(mouse_pos):
                        self.ui_manager.show_table = False
                        return
                
                # 如果显示结算详情，检查是否点击图片区域外
                if self.ui_manager.show_result_detail:
                    # 计算图片区域 - 与ui_manager.py中的逻辑保持一致
                    result_img_path = os.path.join(self.ui_manager.resource_dir, 'table', 'result.png')
                    if os.path.exists(result_img_path):
                        result_img = pygame.image.load(result_img_path).convert_alpha()
                        # 与ui_manager.py保持一致，放大为原尺寸的1.5倍
                        img_width, img_height = result_img.get_size()
                        scale = 1.5
                        new_width = int(img_width * scale)
                        new_height = int(img_height * scale)
                        
                        # 与ui_manager.py保持一致的位置计算
                        img_x = 20  # 左侧与麻将牌对齐
                        img_y = 90  # 上侧与麻将牌对齐，不盖住赢家图片
                        
                        # 检查是否点击图片区域外
                        if not pygame.Rect(img_x, img_y, new_width, new_height).collidepoint(mouse_pos):
                            self.ui_manager.show_result_detail = False
                            return
                
        # 正常游戏状态:有请求事件处理
        elif self.game_manager.have_decision_request():
            request = self.game_manager.decision_request
            discard = DecisionType.DISCARD in request.decision_list
            if request and not discard:
                if self._handle_action_button_click(mouse_pos):
                    return
            elif request and discard:
                self._handle_hand_tile_click(mouse_pos)

        # 正常游戏状态:无请求事件处理
        else:
            self._handle_hand_tile_click(mouse_pos)

    def _handle_action_button_click(self, mouse_pos):
        """处理操作按钮点击
        
        Args:
            mouse_pos: 鼠标位置
            
        Returns:
            bool: 是否处理了按钮点击
        """

        # 检查按钮点击
        action = self.ui_manager.check_button_click(mouse_pos)
        
        # 如果检测到按钮点击，直接处理
        if action:            
            decision_request = self.game_manager.decision_request
            decision_types = decision_request.decision_list
            reason = "用户点击"
            
            # 如果是弃牌决策，不处理操作按钮点击
            if DecisionType.DISCARD in decision_types:
                return False
            
            # 处理胡/杠/碰按钮点击
            if action == 'hu' and DecisionType.HU in decision_types:
                self.set_decision_result(DecisionType.HU, True, None, reason)
                return True
            elif action == 'gang' and DecisionType.GANG in decision_types:
                self.set_decision_result(DecisionType.GANG, True, None, reason)
                return True
            elif action == 'peng' and DecisionType.PENG in decision_types:
                self.set_decision_result(DecisionType.PENG, True, None, reason)
                return True
            elif action == 'cancel':
                # 取消决策，返回False表示拒绝任何行动
                self.set_decision_result(DecisionType.CANCEL, True, None, reason)
                return True
        return False

    def _handle_hand_tile_click(self, mouse_pos):
        """处理手牌点击
        
        Args:
            mouse_pos: 鼠标位置
        """
        
        # 获取牌索引
        tile_index = self.ui_manager.get_tile_index_from_position(mouse_pos)
        request = self.game_manager.have_decision_request()
        is_human = self.game_manager.get_current_player().is_human
        reason = "用户点击"
        
        # 确保索引有效、有决策请求、当前玩家是人类玩家，处理手牌上浮或打出
        if tile_index>=0 and request and is_human:
            decision_types = self.game_manager.decision_request.decision_list
            dc_type = DecisionType.DISCARD
            
            # 仅处理弃牌决策，不处理操作按钮点击
            if dc_type in decision_types:
                float_list = self.ui_manager.float_tile_list
                if float_list and tile_index!=float_list[0]:
                    self.ui_manager.set_float_tile_list([tile_index])
                    self.have_human_selected = True
                    self._draw_game_state()  # 立即更新显示
                else:
                    tile = self.ui_manager.get_human_player().get_concealed_hand()[tile_index]
                    self.have_human_selected = False
                    self.ui_manager.set_float_tile_list([])
                    self.set_decision_result(dc_type,True,tile,reason)
                return

        # 没有决策请求/不是人类玩家，但是点击了手牌，处理手牌上浮或清除上浮
        elif tile_index:
            float_list = self.ui_manager.float_tile_list
            if float_list:
                if tile_index!=float_list[0]:
                    self.ui_manager.set_float_tile_list([tile_index])
                    self._draw_game_state()  # 立即更新显示
                else:
                    self.ui_manager.set_float_tile_list([])
                    self._draw_game_state()  # 立即更新显示
            else:
                self.ui_manager.set_float_tile_list([tile_index])
                self._draw_game_state()  # 立即更新显示
            return

    def handle_decision_request(self):
        """处理决策请求
        
        从game_manager.decision_request中获取需要决策的决定，并通过UI呈现

        """
        
        request = self.game_manager.decision_request
        decision_types = request.decision_list
        decision_player_index = request.player_index
        player = self.game_manager.get_players()[decision_player_index]

        if player.is_human and DecisionType.DISCARD in decision_types and not self.have_human_selected:
            # 弃牌决策
            hand = self.game_manager.get_current_player().get_concealed_hand()
            self.ui_manager.set_float_tile_list([len(hand)-1])
            #立即更新画面
            self._draw_game_state()

    def set_decision_result(self, decision_type, result=False, tile=None, reason=None):
        """设置决策结果
        
        将决策结果赋值给gamemanager的decision_result
        
        Args:
            decision_type: 决策类型
            result: 决策结果，False表示拒绝任何行动，True表示执行decision_type
            tile: 决策相关数据（如选中的牌）
            reason: 决策原因
        """
        # 创建决策结果
        decision_result = DecisionResult(
            decision_type=decision_type,
            result=result,
            tile=tile,
            reason=reason,
        )
        # 设置给game_manager
        self.game_manager.decision_result = decision_result
    
    def request_play_sound(self, sound_type, **kwargs):
        """处理声音播放请求
        
        Args:
            sound_type: 声音类型，如'bg_music', 'click', 'draw', 'discard', 'card', 'action', 'game_end'
            **kwargs: 附加参数，根据声音类型不同而不同
        """
        if sound_type == 'bg_music':
            self.sound_manager.play_bg_music()
        elif sound_type == 'stop_bg_music':
            self.sound_manager.stop_bg_music()
        elif sound_type in ['click', 'draw', 'discard', 'draw_game', 'hu', 'zi_mo']:
            self.sound_manager.play_sound(sound_type)
        elif sound_type == 'card':
            player = kwargs.get('player')
            card_name = kwargs.get('card_name')
            if player and card_name:
                self.sound_manager.play_card_sound(player, card_name)
        elif sound_type == 'action':
            player = kwargs.get('player')
            action_type = kwargs.get('action_type')
            if player and action_type:
                self.sound_manager.play_action_sound(player, action_type)
        elif sound_type == 'game_end':
            is_draw = kwargs.get('is_draw', False)
            self.sound_manager.play_game_end_sound(is_draw)
    
    def request_show_toast(self, message, **kwargs):
        """处理toast显示请求
        
        Args:
            message: 要显示的toast消息
            **kwargs: 附加参数，如duration等
        """
        self.ui_manager.show_toast(message, **kwargs)
    
    def _save_current_game_result(self):
        """每局游戏结束时保存本局结果

        在每局游戏结束时调用，将本局游戏结果保存到历史文件夹中
        """
        import json
        import os
        from datetime import datetime

        # 检查历史文件夹是否存在
        if not hasattr(self, 'history_folder_path') or not self.history_folder_path or not os.path.exists(self.history_folder_path):
            return

        # 计算当前游戏的总局数、黄牌局数和黄牌率
        total_games = self.game_manager.total_games
        
        # 计算黄牌局数：遍历所有已保存的游戏文件，统计流局数量
        draw_games = 0
        for file in os.listdir(self.history_folder_path):
            if file.startswith('game_') and file.endswith('.json'):
                try:
                    with open(os.path.join(self.history_folder_path, file), 'r', encoding='utf-8') as f:
                        prev_game = json.load(f)
                    if prev_game.get('is_draw', False):
                        draw_games += 1
                except Exception:
                    pass
        
        # 加上本局是否流局
        draw_games += 1        
        draw_rate = (draw_games / total_games * 100) if total_games > 0 else 0
        
        # 创建本局游戏结果数据
        game_result = {
            'timestamp': datetime.now().isoformat(),
            'game_number': self.game_manager.total_games,
            'total_games': total_games,
            'draw_games': draw_games,
            'draw_rate': draw_rate,
            'hu_type': {tag.value: count for tag, count in self.game_manager.hu_type.items()},
            'is_draw': hasattr(self.game_manager, 'game_end_reason') and self.game_manager.game_end_reason == 'draw',  # 流局
            'game_end_img': self.ui_manager.game_end_img if hasattr(self.ui_manager, 'game_end_img') else [],
            'players': []
        }

        # 添加玩家数据
        for player in self.game_manager.players:
            hand = player.get_hand()
            # 处理暴露的牌
            exposed_tiles = []
            if hand["exposed"]:
                for exposed in hand["exposed"]:
                    exposed_tiles.extend([tile for tile in exposed["tiles"]])

            # 处理隐藏的手牌
            concealed_tiles = hand["concealed"]

            # 处理tags
            tags = []
            if hasattr(player, 'tags') and player.tags:
                for tag in player.tags:
                    source = tag["source"]
                    tag = tag["tag"]
                    tag = tag.value + (f'({source})' if source!='self' else '')
                    tags.append(tag)

            # 处理result对象
            result = player.result
            avatar_path = player.avatar

            player_data = {
                'name': player.name,
                'avatar_path': avatar_path,
                'ai_version': player.ai_version,
                'is_human': player.is_human,
                'score': player.score,
                'previous_score': player.previous_score,
                'concealed_tiles': concealed_tiles,
                'exposed_tiles': exposed_tiles,
                'tags': tags,
                'result': result
            }
            game_result['players'].append(player_data)

        # 生成文件名：game_{局数}.json
        filename = f"game_{self.game_manager.total_games}.json"
        file_path = os.path.join(self.history_folder_path, filename)

        # 保存到JSON文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(game_result, f, ensure_ascii=False, indent=2)

        print(f"本局游戏记录已保存到: {file_path}")
 
    def _save_game_history(self):
        """保存游戏记录到JSON文件

        在程序关闭时调用，处理总述文件和文件夹：
        1. 如果文件夹为空，删除文件夹
        2. 如果文件夹有对局数据，存储总述文件
        3. 检查并删除所有空的时间戳文件夹
        """
        import json
        import os
        import shutil
        from datetime import datetime

        # 检查历史文件夹是否存在
        history_dir = os.path.join('data', 'history')
        if os.path.exists(history_dir):
            # 3. 检查并删除所有空的时间戳文件夹（除了当前游戏的文件夹）
            for folder_name in os.listdir(history_dir):
                folder_path = os.path.join(history_dir, folder_name)
                if os.path.isdir(folder_path):
                    # 跳过当前游戏的历史记录文件夹
                    skip_this_folder = False
                    try:
                        if hasattr(self, 'history_folder_path') and folder_path == self.history_folder_path:
                            skip_this_folder = True
                    except Exception:
                        pass
                    if skip_this_folder:
                        continue
                    
                    # 检查文件夹是否为空
                    try:
                        files = os.listdir(folder_path)
                        if not files:
                            # 文件夹为空，删除
                            os.rmdir(folder_path)
                            print(f"删除空的时间戳文件夹: {folder_path}")
                    except Exception as e:
                        # 忽略无法删除的文件夹
                        pass

        # 处理当前游戏的历史记录文件夹
        if hasattr(self, 'history_folder_path') and self.history_folder_path:
            # 检查是否有对局
            has_games = self.game_manager.total_games > 0
            
            if has_games:
                # 有对局，保存总述文件
                # 确保历史记录文件夹存在
                if not os.path.exists(self.history_folder_path):
                    os.makedirs(self.history_folder_path)
                
                # 创建总述数据
                summary_data = {
                    'timestamp': datetime.now().isoformat(),
                    'start_timestamp': self.game_start_timestamp.isoformat(),
                    'total_games': self.game_manager.total_games,
                    'draw_games': self.game_manager.draw_games,
                    'win_games': self.game_manager.total_games - self.game_manager.draw_games,
                    'hu_type': {tag.value: count for tag, count in self.game_manager.hu_type.items()},
                    'players': []
                }

                # 添加玩家总述数据
                for player in self.game_manager.players:
                    player_summary = {
                        'name': player.name,
                        'avatar_path': player.avatar,
                        'ai_version': player.ai_version,
                        'is_human': player.is_human,
                        'current_score': player.score,
                        'win_count': player.win_count,
                        'win_rate': player.win_rate,
                        'OfferingWin_count': player.OfferingWin_count,
                        'OfferingWin_rate': player.OfferingWin_rate,
                        'gain_ji_count': player.gain_ji_count,
                        'gain_ji_rate': player.gain_ji_rate,
                        'loss_ji_count': player.loss_ji_count,
                        'loss_ji_rate': player.loss_ji_rate
                    }
                    summary_data['players'].append(player_summary)

                # 生成总述文件名，与文件夹同名
                summary_filename = f"{self.history_folder_name}.json"
                summary_file_path = os.path.join(self.history_folder_path, summary_filename)

                # 保存总述文件
                with open(summary_file_path, 'w', encoding='utf-8') as f:
                    json.dump(summary_data, f, ensure_ascii=False, indent=2)

                print(f"游戏总述记录已保存到: {summary_file_path}")
            else:
                # 没有对局，删除空文件夹
                if os.path.exists(self.history_folder_path):
                    # 检查文件夹是否为空
                    files = os.listdir(self.history_folder_path)
                    if len(files) == 0:
                        # 文件夹为空，删除
                        try:
                            os.rmdir(self.history_folder_path)
                            print(f"删除空的历史记录文件夹: {self.history_folder_path}")
                        except Exception as e:
                            print(f"删除空文件夹失败: {e}")
                    else:
                        # 文件夹不为空，删除总述文件，然后删除文件夹
                        try:
                            # 删除总述文件
                            summary_filename = f"{self.history_folder_name}.json"
                            summary_file_path = os.path.join(self.history_folder_path, summary_filename)
                            if os.path.exists(summary_file_path):
                                os.remove(summary_file_path)
                                print(f"删除总述文件: {summary_file_path}")
                            # 删除文件夹
                            if os.path.exists(self.history_folder_path):
                                import shutil
                                shutil.rmtree(self.history_folder_path)
                                print(f"删除历史记录文件夹: {self.history_folder_path}")
                        except Exception as e:
                            print(f"删除历史记录文件夹失败: {e}")

    def main(self):
        """游戏主循环"""
        
        self.show_all_faces = self.settings.show_all_faces # 是否显示所有牌
        self.running = True # 游戏程序运行标识
        
        # 初始化时钟
        self.clock = pygame.time.Clock()
        
        # 主循环 - 应用层核心职责：事件处理和渲染
        while self.running:
            # 1. 处理用户输入事件
            self._handle_events()
            
            # 2. 根据当前屏幕状态执行不同逻辑
            if self.current_screen == GameScreen.GAME_PLAY:
                # 游戏中状态
                if not self.game_started:
                    self.game_started = True
                    test_mode = self.settings.test_mode
                    self.game_manager.initialize_manager()
                    self.game_manager.initialize_game(test=test_mode)
                
                # 持续检查并播放背景音乐
                self.sound_manager.play_bg_music()
                
                # 更新游戏状态
                self._update_game_state()
                # 渲染游戏界面
                self._draw_game_state()
            elif self.current_screen == GameScreen.MAIN_MENU:
                # 主菜单状态
                self._draw_main_menu()
                # 绘制toast提示
                self.ui_manager.draw_toasts()
            elif self.current_screen == GameScreen.SETTINGS:
                # 设置页面状态
                self._draw_settings()
            elif self.current_screen == GameScreen.GAME_HISTORY:
                # 历史对局页面状态
                self.ui_manager._draw_game_history()
            elif self.current_screen == GameScreen.GAME_HISTORY_DETAIL:
                # 历史对局详情页面状态
                self.ui_manager._draw_game_history_detail()
            
            # 无论当前屏幕是什么状态，只要游戏在运行且设置中打开了背景音乐，就确保音乐在播放
            if self.settings.bg_music_play:
                self.sound_manager.play_bg_music()
            
            # 3. 控制帧率
            self.clock.tick(self.settings.fps)
        
        # 保存游戏记录到JSON文件
        self._save_game_history()
        
        # 退出游戏
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    # 创建游戏实例
    game = MajiangGame()
    # 运行游戏主循环
    game.main()
