from source.public import Tag
from source.public import get_jpg_names
from source.public import get_resource_path
import random

class Settings(object):
    game_name = 'Dushan Majiang 2025'
    test_mode = False  # 是否测试模式
    # show_all_faces = True  # 是否显示所有牌
    test_mode = True  # 是否测试模式
    show_all_faces = False  # 是否显示所有牌
    win_w = 1280
    win_h = 720
    fps = 60  # 游戏帧率
    bg_img = get_resource_path('resource/table/bgimg.jpg')
    icon_img = get_resource_path('resource/icon.png')
    tile_indicator_color = "red"  # 牌面指示器颜色:黄绿红
    bg_music_play = True  # 是否播放背景音乐
    game_sound_play = False   # 是否播放游戏音效
    card_sound_play = False  # 是否播放打牌读牌音效  
    bg_music_volume = 0.5  # 背景音乐音量 (0.0-1.0)
    game_sound_volume = 1.0  # 游戏音效音量 (0.0-1.0)
    card_sound_volume = 0.8  # 打牌读牌音效音量 (0.0-2.0)
    # 玩家名字配置
    players_girl = get_jpg_names('resource/avatar/girl')
    players_boy = get_jpg_names('resource/avatar/boy')
    human = "云天明" if random.randint(0, 1) == 0 else "大圣"  # 人类玩家默认名字
    score = 100  # 玩家初始积分
    show_name = True  # 是否显示玩家名字，否则显示ai_version/scores
    show_ai_version = False  # 是否显示AI玩家版本号
    position_order = ['east', 'south', 'west', 'north']
    chicken_tile = ['1条','冲','2']  # 幺鸡牌
    ji_tile = ['冲','2','1条']  #冲锋鸡和横鸡的名称，用于显示tiles文件夹下不用的图片
    emoji = " 🔄🐔🚀🍗⚠️🎉✅🎯❌🔥 🀄🏆🎁🌸💡🏷️💣💥🌟⚡💔🟡"
    
    # 游戏设置
    human_time_limit = 15  # 人类玩家思考超时时间（秒），最低0.1
    ai_time_limit = 2  # AI玩家思考时间（秒），最低0.1
    toast_duration = 3000  # Toast显示持续时间（毫秒）
    auto_restart_time = -1  # 超时自动再来一局的时间（秒）
    test_round = 10  # 测试轮数/自动再来一局自动点击次数
    speed_up = False  # 是否加速游戏(采集对局数据模式)，即减少思考时间/自动重开时间/toast显示时间等
    cli_print = {'draw':True,'discard':True,'peng':True,'gang':True,'tag':False,'erro':True,'game_result':True,'game_info':True}
    # cli_print = {'draw':True,'discard':True,'peng':True,'gang':True,'tag':True,'erro':True,'game_result':True,'game_info':True}
    mode_easy = [0,1,0]
    mode_normal = [1,0,1]
    mode_hard = [1,1,1]
    human_ai_version="1"
    opponent_ai_version_list = mode_easy
    fan_ji = True  # 是否计算翻鸡数
    shangxia_ji = True  # 翻鸡是否计算上下鸡数，默认仅计算下鸡
    # mantang_ji = True  # 是否计算满堂鸡 ，未实现

    # 牌型番数配置
    majiang_scores = {
        "self_hu": {
            Tag.ZI_MO: 3,# 自摸
            Tag.TIAN_HU: 23,#天胡
            Tag.GANG_SAHNG_KAI_HUA: 3,# 杠上开花
            Tag.MIAO_SHOU_HUI_CHUN: 3,# 妙手回春
        },
        "qiuren_hu": {
            Tag.ZHUO_PAO: 3,#捉炮
            Tag.ZHUO_RE_PAO: 3,#捉热炮
            Tag.QIANG_GANG_HU: 3,#抢杠胡
            Tag.HAI_DI_LAO_YUE: 3,#海底捞月
        },
        "hu_type": {
            Tag.BAO_JIAO: 10,#报叫
            Tag.LONG_QI_DUI: 23,#龙七对
            Tag.QING_YI_SE: 10,#清一色
            Tag.DAN_DIAO: 10,#单钓将
            Tag.XIAO_QI_DUI: 10,#小七对
            Tag.DA_DUI_ZI: 5,#大对子
            Tag.PING_HU: 0,#平胡
        },
        "ji_type": {
            Tag.CHONG_FENG_JI: 3,#冲锋鸡
            Tag.HENG_JI: 2,#横鸡
            Tag.YAO_JI: 1,#幺鸡
        },
        "other_tag": {
            Tag.GANG: 3,#杠
            Tag.FANG_RE_PAO: -3,#放热炮
            Tag.FANG_PAO: -3,#放炮
        }
    }

    # 头像大小配置，4个玩家头像距离背景左上角的横纵坐标距离
    avatar_size = (64, 64)
    avatar_positions = [
        (114, 605),  # 东家（底部）
        (1180, 30),   # 南家（右侧）
        (1100,30), # 西家（顶部）
        (30, 606)   # 北家（左侧）
    ]
    
    # 字体配置
    font_path = get_resource_path('resource/font/zhunyuan.ttf')  # 字体文件路径
    small_font_size = 13  # 小字体大小
    normal_font_size = 15  # 字体大小 
    big_font_size = 20  # 大字体大小
    super_font_size = 30  # 超大字体大小

    # 颜色定义
    white = (255, 255, 255)
    black = (0, 0, 0)
    red = (255, 0, 0)
    green = (0, 255, 0)
    blue = (0, 0, 255)
    yellow = (255, 255, 0)
    gray = (128, 128, 128)
    orange = (255, 165, 0)  # 橙色，用于历史对局按钮

    # 麻将牌配置
    tile_size = (76*0.5, 118*0.5)  # 麻将牌大小
    tile_size_self = (76*0.8, 118*0.8)  # 东家麻将牌大小（更大一些）
    back_tile_path = get_resource_path('resource/tiles/face-down.png')  # 背面麻将牌路径
    
    # 显示设置
    # 方向文字配置
    pixes_2_center = 66 + 30  # 弃牌区域中心距离（像素）
    direction_text_color = white  # 方向文字颜色（默认黑色）
    direction_text_font_size = 20  # 方向文字字体大小
    direction_text_offset = 78  # 方向文字到中心的距离（像素）
    show_indicator = True  # 是否显示出牌指示器
    show_direction = True  # 是否显示方向词语
    direction_font_path = font_path  # 方向文字字体路径
    # direction_text = ['自玄武', '右白虎', '北朱雀', '左青龙'] #顺序[本，下，对，上]
    direction_text = ['东', '南', '西', '北'] #顺序[本，下，对，上]

    
