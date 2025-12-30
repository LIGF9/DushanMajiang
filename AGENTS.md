# 独山麻将 - AI友好仓库指南

## 仓库概述

**仓库类型**: 游戏开发项目
**主要功能**: 基于Pygame的独山麻将游戏，支持人机对战和AI自动对战
**开发语言**: Python 3.8+
**技术栈**: Pygame 2.6.1
**许可证**: MIT

## 核心文件结构

### 入口文件
- `majiang.py` - 游戏主入口，初始化Pygame和游戏管理器

### 核心模块
```
source/
├── game_manager.py      # 游戏逻辑核心管理
├── player.py            # 玩家类定义
├── public.py            # 公共常量和工具函数
├── rule.py              # 游戏规则实现
├── sound_manager.py     # 音效管理
├── tile.py              # 麻将牌类
└── ui_manager.py        # UI界面管理
```

### AI相关文件
- `majiangAI.py` - 主要AI算法实现

### 配置文件
- `settings.py` - 游戏全局设置
- `majiang.spec` - PyInstaller打包配置

## 游戏核心逻辑

### 初始化流程
1. 加载Pygame和游戏资源
2. 初始化Settings、GameManager、UIManager、SoundManager
3. 创建游戏窗口和渲染器
4. 进入游戏主循环

### 游戏状态管理
- `GameScreen`类：管理游戏屏幕状态（主菜单、设置、游戏中、历史记录）
- `GameManager`类：处理游戏核心逻辑（发牌、打牌、碰杠胡判断）
- `UIManager`类：负责UI渲染和用户交互
- `SoundManager`类：处理音效和背景音乐

### 关键游戏对象
- `GameManager`：游戏逻辑核心，管理玩家、牌局、游戏状态
- `Player`：玩家对象，管理手牌、打出的牌、分数
- `Tile`：麻将牌对象，包含花色、点数等属性

## 开发和运行

### 运行方式
1. 可执行文件: `dist/majiang.exe`
2. 源码运行: `python majiang.py`

### 开发依赖
- `pygame==2.6.1`

### 打包命令
```bash
pyinstaller majiang.spec
```

## 资源文件

### 资源目录结构
```
resource/
├── avatar/     # 角色头像（boy/girl）
├── font/       # 字体文件
├── sound/      # 音效和背景音乐
├── sprites/    # 游戏精灵图
├── table/      # 游戏桌子资源
└── tiles/      # 麻将牌图片
```

### 关键资源
- 麻将牌图片: 108张标准麻将牌
- 角色头像: 25个角色（14男11女）
- 背景音乐: 5首BG音乐
- 音效: 包括出牌、碰杠胡等多种音效

## 游戏特色

1. **智能AI对手**: 基于规则的决策树算法
2. **完整音效系统**: 背景音乐和游戏音效
3. **精美UI界面**: 角色头像、动画效果
4. **历史记录**: 自动保存每局游戏结果
5. **灵活设置**: 支持多种游戏参数调整

## 快速理解指南

### 游戏启动流程
1. 运行`majiang.py`或`majiang.exe`
2. 进入主菜单，选择开始游戏/设置/历史记录
3. 游戏中通过鼠标点击操作，AI自动提示最佳出牌
4. 胡牌后显示结果，自动保存历史记录

### 核心功能定位
- **游戏逻辑**: `game_manager.py`
- **AI决策**: `majiangAI.py`
- **UI渲染**: `ui_manager.py`
- **音效管理**: `sound_manager.py`

### 关键配置
- `settings.py`: 游戏全局设置
- `theme.json`: 主题配置
- 音量、AI思考时间、初始分数等可通过设置界面调整

## 扩展开发

### 添加新AI策略
编辑`majiangAI.py`，添加新的AI类实现

### 修改游戏规则
编辑`rule.py`文件，调整胡牌规则和番数计算

### 添加新角色
在`resource/avatar/`目录下添加新头像图片

---

**提示**: 该文件用于大模型agents快速理解仓库结构和核心功能，实际开发请参考完整README.md