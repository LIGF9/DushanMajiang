import pygame
import random
import os
import sys

def get_resource_path(relative_path: str) -> str:
    """返回运行时资源绝对路径，兼容 PyInstaller 单文件打包。

    如果程序被 PyInstaller 打包为单文件，资源会被解压到 `sys._MEIPASS`。
    否则将相对于项目根目录（source 的父目录）拼接返回。
    """
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        # 项目结构：项目根/resource，当前文件在 project/source
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    # 支持传入使用 / 的路径
    rel = relative_path.replace('/', os.path.sep).lstrip(os.path.sep)
    return os.path.join(base_path, rel)


class SoundManager:
    def __init__(self, settings):
        self.settings = settings
        self.sounds = {}
        self.bg_music_playing = False
        self.current_bg_music = None
        
        # 确保pygame.mixer已初始化
        pygame.mixer.init()
        
        # 初始化音效字典
        self._load_sounds()

    def _load_sounds(self):
        """加载所有音效文件"""
        # 加载通用音效
        sound_files = {
            'click': get_resource_path('resource/sound/点击.mp3'),
            'draw': get_resource_path('resource/sound/摸牌.mp3'),
            'discard': get_resource_path('resource/sound/打牌.mp3'),
            'draw_game': get_resource_path('resource/sound/流局.mp3'),
            'hu': get_resource_path('resource/sound/胡牌.mp3'),
            'zi_mo': get_resource_path('resource/sound/自摸.mp3'),
        }
        
        for name, path in sound_files.items():
            try:
                self.sounds[name] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"加载音效 {name} 失败: {e}")
        
        # 加载背景音乐列表
        self.bg_music_list = []
        bg_music_dir = get_resource_path('resource/sound/bgmusic')
        try:
            for filename in os.listdir(bg_music_dir):
                if filename.endswith('.mp3'):
                    self.bg_music_list.append(os.path.join(bg_music_dir, filename))
        except Exception:
            # 如果目录不存在，保持列表为空（后续播放会提示没有背景音乐）
            pass
        
    def play_bg_music(self):
        """播放背景音乐"""
        if not self.settings.bg_music_play:
            # 如果设置中不允许播放背景音乐，确保音乐已停止
            if self.bg_music_playing:
                self.stop_bg_music()
            return
            
        # 检查音乐是否真的在播放（pygame.mixer.music.get_busy()返回True表示正在播放）
        is_actually_playing = pygame.mixer.music.get_busy()
        
        if not is_actually_playing:
            # 音乐没有在播放，需要重新播放
            try:
                if not self.bg_music_list:
                    print("没有找到背景音乐文件")
                    self.bg_music_playing = False
                    return
                    
                # 随机选择一首背景音乐
                bg_music = random.choice(self.bg_music_list)
                
                # 确保pygame.mixer.music已初始化
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                    print("重新初始化了pygame.mixer")
                
                pygame.mixer.music.load(bg_music)
                # 使用设置中的音量
                pygame.mixer.music.set_volume(self.settings.bg_music_volume)
                pygame.mixer.music.play(-1)  # -1 表示循环播放
                self.bg_music_playing = True
                self.current_bg_music = bg_music
                
            except Exception as e:
                print(f"播放背景音乐失败: {e}")
                import traceback
                traceback.print_exc()
                self.bg_music_playing = False
        else:
            # 音乐已经在播放，更新状态和音量
            self.bg_music_playing = True
            pygame.mixer.music.set_volume(self.settings.bg_music_volume)
    
    def stop_bg_music(self):
        """停止背景音乐"""
        if self.bg_music_playing:
            pygame.mixer.music.stop()
            self.bg_music_playing = False
            self.current_bg_music = None
    
    def play_sound(self, sound_name):
        """播放普通音效"""
        if not self.settings.game_sound_play:
            return
            
        sound = self.sounds.get(sound_name)
        if sound:
            try:
                # 使用设置中的游戏音效音量
                volume = self.settings.game_sound_volume
                # 打牌声效小一点
                if sound_name == 'discard':
                    volume *= 0.5
                sound.set_volume(volume)
                sound.play()
            except Exception as e:
                print(f"播放音效 {sound_name} 失败: {e}")
    
    def play_card_sound(self, player, card_name):
        """根据玩家性别播放读牌音效"""
        if not self.settings.card_sound_play:
            return
            
        # 确定声音文件夹
        sound_dir = get_resource_path('resource/sound/sound_girl') if player.is_girl else get_resource_path('resource/sound/sound_boy')
        sound_path = os.path.join(sound_dir, f'{card_name}.mp3')
        
        try:
            if os.path.exists(sound_path):
                card_sound = pygame.mixer.Sound(sound_path)
                # 使用设置中的打牌读牌音效音量，女生的声效大声一点
                volume = self.settings.card_sound_volume
                volume *= 2 if player.is_girl else 1.0
                card_sound.set_volume(volume)
                card_sound.play()
        except Exception as e:
            print(f"播放读牌音效 {card_name} 失败: {e}")
    
    def play_action_sound(self, player, action_type):
        """根据玩家性别播放动作音效（碰/杠/吃胡/自摸）"""
        if not self.settings.game_sound_play:
            return
            
        # 确定声音文件夹
        sound_dir = get_resource_path('resource/sound/sound_girl') if player.is_girl else get_resource_path('resource/sound/sound_boy')
        
        # 动作类型映射到音效文件名
        action_map = {
            'peng': '碰.mp3',
            'gang': '杠.mp3',
            'hu': '胡.mp3',
            'zi_mo': '自摸.mp3'
        }
        
        sound_file = action_map.get(action_type)
        if sound_file:
            sound_path = os.path.join(sound_dir, sound_file)
            try:
                if os.path.exists(sound_path):
                    action_sound = pygame.mixer.Sound(sound_path)
                    # 使用设置中的游戏音效音量
                    action_sound.set_volume(self.settings.game_sound_volume)
                    action_sound.play()
            except Exception as e:
                print(f"播放动作音效 {action_type} 失败: {e}")
    
    def update_settings(self, new_settings):
        """更新设置"""
        # 保存旧设置和新设置的背景音乐状态
        old_bg_music_play = self.settings.bg_music_play
        new_bg_music_play = new_settings.bg_music_play
        
        # 先更新设置
        self.settings = new_settings
        
        # 如果背景音乐设置从关闭变为开启，播放背景音乐
        if not old_bg_music_play and new_bg_music_play:
            self.play_bg_music()
        # 如果背景音乐设置从开启变为关闭，停止背景音乐
        elif old_bg_music_play and not new_bg_music_play:
            self.stop_bg_music()
    
    def play_game_end_sound(self, is_draw):
        """播放本局游戏结束音效（流局或胡牌）"""
        if self.settings.game_sound_play:
            if is_draw:
                self.play_sound('draw_game')
            else:
                self.play_sound('hu')
    
    def next_bg_music(self):
        """切换到下一首背景音乐，确保与当前音乐不同"""
        if not self.bg_music_list:
            return
        
        # 停止当前播放的音乐
        if self.bg_music_playing:
            pygame.mixer.music.stop()
            self.bg_music_playing = False
            self.current_bg_music = None
        
        # 确保选择与当前不同的音乐
        previous_music = self.current_bg_music
        new_music = previous_music
        
        # 如果只有一首音乐，就直接播放
        if len(self.bg_music_list) == 1:
            pygame.mixer.music.load(self.bg_music_list[0])
            pygame.mixer.music.set_volume(self.settings.bg_music_volume)
            pygame.mixer.music.play(-1)
            self.bg_music_playing = True
            self.current_bg_music = self.bg_music_list[0]
            return
        
        # 随机选择一首不同的音乐
        while new_music == previous_music:
            new_music = random.choice(self.bg_music_list)
        
        # 播放新的背景音乐
        pygame.mixer.music.load(new_music)
        pygame.mixer.music.set_volume(self.settings.bg_music_volume)
        pygame.mixer.music.play(-1)
        self.bg_music_playing = True
        self.current_bg_music = new_music
