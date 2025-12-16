# 浩讯亿通电脑店

import sys
import psutil
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QShortcut
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QPainter, QBrush, QPen, QRegion, QKeySequence

# 尝试导入音乐工具模块
try:
    import music_utils
    has_music_utils = True
except ImportError:
    has_music_utils = False
    print("未找到music_utils模块，将使用模拟音乐数据")

# 尝试导入音量控制模块
try:
    import volume_utils
    has_volume_utils = True
except ImportError:
    has_volume_utils = False
    print("未找到volume_utils模块，音量控制功能不可用")

# 音乐播放器线程类，用于后台获取音乐信息
class MusicPlayerThread(QThread):
    music_updated = pyqtSignal(str, str)  # 信号：发送歌曲名和艺术家
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.current_song = None
        self.current_artist = None
        
    def run(self):
        while self.running:
            if has_music_utils:
                try:
                    # 尝试从所有支持的播放器获取音乐信息
                    song = None
                    artist = None
                    
                    # 1. 尝试获取当前活动窗口的音乐信息
                    song, artist = music_utils.get_current_playing_music()
                    
                    # 2. 如果当前没有获取到，尝试检查所有运行的播放器
                    if not song:
                        running_players = music_utils.get_all_running_players()
                        for player_name in running_players:
                            player_song, player_artist = music_utils.get_music_from_specific_player(player_name)
                            if player_song:
                                song = player_song
                                artist = player_artist
                                break
                    
                    if song and artist:
                        # 确保信息不为空
                        song = song or "未知歌曲"
                        artist = artist or "未知艺术家"
                        
                        # 如果信息发生变化，发送信号
                        if (song != self.current_song or artist != self.current_artist):
                            self.current_song = song
                            self.current_artist = artist
                            self.music_updated.emit(song, artist)
                    else:
                        # 没有音乐播放时的处理
                        song = "无音乐播放"
                        artist = ""
                        if (song != self.current_song or artist != self.current_artist):
                            self.current_song = song
                            self.current_artist = artist
                            self.music_updated.emit(song, artist)
                except Exception:
                    # 如果出错，使用模拟数据
                    song = "示例音乐"
                    artist = "示例艺术家"
                    if song != self.current_song or artist != self.current_artist:
                        self.current_song = song
                        self.current_artist = artist
                        self.music_updated.emit(song, artist)
            else:
                # 使用模拟数据
                song = "示例音乐"
                artist = "示例艺术家"
                if song != self.current_song or artist != self.current_artist:
                    self.current_song = song
                    self.current_artist = artist
                    self.music_updated.emit(song, artist)
            
            # 每500毫秒检查一次
            self.msleep(500)
    
    def stop(self):
        self.running = False

class DynamicIsland(QWidget):
    def __init__(self):
        super().__init__()
        self.draggable = False
        self.drag_position = QPoint()
        self.click_pos = QPoint()  # 记录点击位置，用于区分点击和拖拽
        self.expanded = False  # 展开状态标志
        
        # 初始化音乐信息
        self.current_song = "示例音乐"
        self.current_artist = "示例艺术家"
        
        # 初始化音乐播放器线程
        self.music_thread = MusicPlayerThread()
        self.music_thread.music_updated.connect(self.update_music_info)
        self.music_thread.start()
        
        self.initUI()
        
    def initUI(self):
        # 设置窗口大小
        self.original_width = 220
        self.original_height = 40
        
        # 设置窗口标题
        self.setWindowTitle('Dynamic Island')
        
        # 计算屏幕居中位置（顶部居中）
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = (screen_geometry.width() - self.original_width) // 2
        y = 10  # 距离顶部10像素
        self.setGeometry(x, y, self.original_width, self.original_height)
        
        # 设置窗口样式
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setFocusPolicy(Qt.StrongFocus)  # 设置焦点策略以接收键盘事件
        self.activateWindow()  # 激活窗口以确保接收键盘事件
        
        # 设置背景色和透明度
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0, 200))  # 半透明黑色
        self.setPalette(palette)
        
        # 初始化动画存储变量
        self.active_animations = []
        
        # 创建布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(15)
        
        # 创建状态图标标签
        self.volume_label = QLabel(self)
        self.volume_label.setText("🔊")
        self.volume_label.setFont(QFont('Arial', 14))
        self.volume_label.setStyleSheet("color: white;")
        self.volume_label.setToolTip("点击调节音量")
        
        # 音量控制相关
        self.volume_percent_label = QLabel(self)
        self.volume_percent_label.setText("50%")
        self.volume_percent_label.setFont(QFont('Arial', 10))
        self.volume_percent_label.setStyleSheet("color: white;")
        self.volume_percent_label.hide()  # 默认隐藏音量百分比
        
        
        
        self.battery_label = QLabel(self)
        self.battery_label.setText("🔋")
        self.battery_label.setFont(QFont('Arial', 14))
        self.battery_label.setStyleSheet("color: white;")
        self.battery_label.hide()  # 默认隐藏电池图标
        
        # 创建日历图标标签
        self.calendar_label = QLabel(self)
        self.calendar_label.setText("📅")
        self.calendar_label.setFont(QFont('Arial', 14))
        self.calendar_label.setStyleSheet("color: white;")
        self.calendar_label.setToolTip("点击查看日期")
        self.calendar_label.hide()  # 默认隐藏日历图标
        
        # 日历详情标签
        self.calendar_detail_label = QLabel(self)
        self.calendar_detail_label.setFont(QFont('Arial', 10))
        self.calendar_detail_label.setStyleSheet("color: white;")
        self.calendar_detail_label.hide()  # 默认隐藏日历详情
        
        # 创建时间标签
        self.time_label = QLabel(self)
        self.time_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("color: white;")
        
        # 创建通知图标
        self.notification_label = QLabel(self)
        self.notification_label.setText("🔔")
        self.notification_label.setFont(QFont('Arial', 14))
        self.notification_label.setStyleSheet("color: white;")
        
        # 展开时的额外信息
        self.extra_info_label = QLabel(self)
        self.extra_info_label.setText(f"正在播放: {self.current_song} - {self.current_artist}")
        self.extra_info_label.setFont(QFont('Arial', 10))
        self.extra_info_label.setStyleSheet("color: white;")
        self.extra_info_label.hide()
        
        # 添加到布局
        layout.addWidget(self.volume_label)
        layout.addWidget(self.volume_percent_label)
        layout.addWidget(self.battery_label)
        layout.addWidget(self.calendar_label)
        layout.addWidget(self.calendar_detail_label)
        layout.addWidget(self.time_label)
        layout.addWidget(self.notification_label)
        layout.addWidget(self.extra_info_label)
        
        # 更新时间、音量和电池信息
        self.update_time()
        self.update_volume_info()
        self.update_battery_info()
        
        # 设置定时器，每秒更新时间和音量
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        
        # 设置音量更新定时器
        self.volume_timer = QTimer(self)
        self.volume_timer.timeout.connect(self.update_volume_info)
        self.volume_timer.start(1000)
        
        # 设置电池电量更新定时器
        self.battery_timer = QTimer(self)
        self.battery_timer.timeout.connect(self.update_battery_info)
        self.battery_timer.start(5000)  # 每5秒更新一次电池信息
        
        # 创建全局快捷键
        self.shortcut_volume_up = QShortcut(QKeySequence("Ctrl+Up"), self)
        self.shortcut_volume_up.activated.connect(self.volume_up)
        
        self.shortcut_volume_down = QShortcut(QKeySequence("Ctrl+Down"), self)
        self.shortcut_volume_down.activated.connect(self.volume_down)
        
        self.shortcut_volume_mute = QShortcut(QKeySequence("Ctrl+M"), self)
        self.shortcut_volume_mute.activated.connect(self.toggle_mute)
    
    def paintEvent(self, event):
        # 绘制圆角窗口
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景
        rect = self.rect()
        painter.setBrush(QBrush(QColor(0, 0, 0, 200)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 20, 20)
    
    def mousePressEvent(self, event):
        # 鼠标按下事件，用于拖动窗口和点击切换展开/收起
        if event.button() == Qt.LeftButton:
            # 记录点击位置和拖拽起始位置
            self.click_pos = event.pos()
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            
            # 设置拖动状态为False，后续根据移动距离判断
            self.draggable = False
            event.accept()
    
    def mouseMoveEvent(self, event):
        # 鼠标移动事件，用于拖动窗口
        if event.buttons() & Qt.LeftButton:
            # 计算鼠标移动距离
            distance = (event.pos() - self.click_pos).manhattanLength()
            
            # 如果移动距离超过阈值，标记为拖拽状态
            if distance > 5:  # 5像素阈值
                self.draggable = True
                
                # 使用统一的方法停止所有动画，避免拖动时与动画冲突
                self.stop_all_animations()
                
                # 移动窗口
                self.move(event.globalPos() - self.drag_position)
            
            event.accept()
    
    def mouseReleaseEvent(self, event):
        # 鼠标释放事件
        if event.button() == Qt.LeftButton:
            # 计算鼠标移动距离
            distance = (event.pos() - self.click_pos).manhattanLength()
            
            # 如果移动距离小于阈值，认为是点击操作，执行展开/收起
            if distance < 5 and self.rect().contains(self.click_pos):
                self.toggle_expand()
            
            # 重置拖动状态
            self.draggable = False
    
    def stop_all_animations(self):
        # 停止并移除所有活动动画
        for attr_name in ['hover_animation', 'expand_animation', 'collapse_animation', 'bell_animation']:
            if hasattr(self, attr_name):
                animation = getattr(self, attr_name)
                # 检查动画是否正在运行
                from PyQt5.QtCore import QParallelAnimationGroup, QPropertyAnimation, QSequentialAnimationGroup
                if isinstance(animation, QPropertyAnimation) and animation.state() == QPropertyAnimation.Running:
                    animation.stop()
                elif isinstance(animation, (QParallelAnimationGroup, QSequentialAnimationGroup)) and animation.state() == QParallelAnimationGroup.Running:
                    animation.stop()
                delattr(self, attr_name)
    
    def toggle_expand(self):
        # 切换展开/收起状态
        self.expanded = not self.expanded
        
        # 首先停止所有可能的动画
        self.stop_all_animations()
        
        if self.expanded:
            # 展开时的动画
            new_width = self.original_width + 100
            new_height = self.original_height + 30
            
            # 获取当前窗口位置
            current_geometry = self.geometry()
            
            # 保持窗口中心位置不变，计算新的x坐标
            current_center = current_geometry.x() + current_geometry.width() // 2
            new_x = current_center - new_width // 2
            new_y = 10  # 固定在顶部10像素处
            
            # 显示额外信息
            self.extra_info_label.show()
            
            # 增加背景透明度
            palette = self.palette()
            palette.setColor(QPalette.Window, QColor(0, 0, 0, 240))
            self.setPalette(palette)
            
            # 确保动画结束后窗口位置正确
            def on_expand_finished():
                self.setGeometry(new_x, new_y, new_width, new_height)
            
            # 创建新的窗口矩形
            from PyQt5.QtCore import QRect
            new_rect = QRect(new_x, new_y, new_width, new_height)
            
            # 使用新的几何动画方法
            self.expand_animation = self.create_geometry_animation(
                current_geometry,
                new_rect,
                duration=400,
                finished_callback=on_expand_finished
            )
            
            # 启动动画
            self.expand_animation.start()
            
        else:
            # 获取当前窗口位置
            current_geometry = self.geometry()
            
            # 保持窗口中心位置不变，计算新的x坐标
            current_center = current_geometry.x() + current_geometry.width() // 2
            new_x = current_center - self.original_width // 2
            new_y = 10  # 固定在顶部10像素处
            
            # 隐藏额外信息
            self.extra_info_label.hide()
            
            # 恢复背景透明度
            palette = self.palette()
            palette.setColor(QPalette.Window, QColor(0, 0, 0, 200))
            self.setPalette(palette)
            
            # 确保动画结束后窗口位置正确
            def on_collapse_finished():
                self.setGeometry(new_x, new_y, self.original_width, self.original_height)
            
            # 创建新的窗口矩形
            from PyQt5.QtCore import QRect
            new_rect = QRect(new_x, new_y, self.original_width, self.original_height)
            
            # 使用新的几何动画方法
            self.collapse_animation = self.create_geometry_animation(
                current_geometry,
                new_rect,
                duration=400,
                finished_callback=on_collapse_finished
            )
            
            # 启动动画
            self.collapse_animation.start()
    
    def enterEvent(self, event):
        # 鼠标进入事件，放大窗口
        if not self.expanded:  # 只有在未展开状态下才执行悬停动画
            # 停止所有动画
            self.stop_all_animations()
            
            new_width = self.original_width + 40
            new_height = self.original_height + 10
            
            # 获取当前窗口位置
            current_geometry = self.geometry()
            
            # 保持窗口中心位置不变，计算新的x坐标
            current_center = current_geometry.x() + current_geometry.width() // 2
            new_x = current_center - new_width // 2
            new_y = 10  # 固定在顶部10像素处
            
            # 增加背景透明度
            palette = self.palette()
            palette.setColor(QPalette.Window, QColor(0, 0, 0, 230))
            self.setPalette(palette)
            
            # 确保动画结束后窗口位置正确
            def on_hover_enter_finished():
                self.setGeometry(new_x, new_y, new_width, new_height)
            
            # 创建新的窗口矩形
            from PyQt5.QtCore import QRect
            new_rect = QRect(new_x, new_y, new_width, new_height)
            
            # 使用新的几何动画方法
            self.hover_animation = self.create_geometry_animation(
                current_geometry,
                new_rect,
                duration=300,
                finished_callback=on_hover_enter_finished
            )
            
            # 启动动画
            self.hover_animation.start()
        
    def leaveEvent(self, event):
        # 鼠标离开事件，恢复原始大小
        if not self.expanded:  # 只有在未展开状态下才执行悬停动画
            # 停止所有动画
            self.stop_all_animations()
            
            # 获取当前窗口位置
            current_geometry = self.geometry()
            
            # 保持窗口中心位置不变，计算新的x坐标
            current_center = current_geometry.x() + current_geometry.width() // 2
            new_x = current_center - self.original_width // 2
            new_y = 10  # 固定在顶部10像素处
            
            # 恢复背景透明度
            palette = self.palette()
            palette.setColor(QPalette.Window, QColor(0, 0, 0, 200))
            self.setPalette(palette)
            
            # 确保动画结束后窗口位置正确
            def on_hover_leave_finished():
                self.setGeometry(new_x, new_y, self.original_width, self.original_height)
            
            # 创建新的窗口矩形
            from PyQt5.QtCore import QRect
            new_rect = QRect(new_x, new_y, self.original_width, self.original_height)
            
            # 使用新的几何动画方法
            self.hover_animation = self.create_geometry_animation(
                current_geometry,
                new_rect,
                duration=300,
                finished_callback=on_hover_leave_finished
            )
            
            # 启动动画
            self.hover_animation.start()
    
    def contextMenuEvent(self, event):
        # 右键菜单事件
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        exit_action = menu.addAction("退出")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == exit_action:
            QApplication.quit()
        
    def create_animation(self, property_name, start_value, end_value, duration=300, finished_callback=None):
        # 不直接支持geometry属性的动画
        if property_name == b"geometry":
            # 使用几何动画方法替代
            from PyQt5.QtCore import QRect
            if isinstance(start_value, QRect) and isinstance(end_value, tuple):
                end_rect = QRect(*end_value)
                return self.create_geometry_animation(start_value, end_rect, duration, finished_callback)
            return None
            
        # 创建并配置动画
        animation = QPropertyAnimation(self, property_name)
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.OutQuad)
        
        # 设置起始值和结束值
        animation.setStartValue(start_value)
        animation.setEndValue(end_value)
        
        if finished_callback:
            animation.finished.connect(finished_callback)
        return animation
        
    def create_geometry_animation(self, start_rect, end_rect, duration=300, finished_callback=None):
        # 创建位置和大小的动画组
        from PyQt5.QtCore import QParallelAnimationGroup
        
        # 创建位置动画
        pos_animation = QPropertyAnimation(self, b"pos")
        pos_animation.setDuration(duration)
        pos_animation.setEasingCurve(QEasingCurve.OutQuad)
        pos_animation.setStartValue(start_rect.topLeft())
        pos_animation.setEndValue(end_rect.topLeft())
        
        # 创建大小动画
        size_animation = QPropertyAnimation(self, b"size")
        size_animation.setDuration(duration)
        size_animation.setEasingCurve(QEasingCurve.OutQuad)
        size_animation.setStartValue(start_rect.size())
        size_animation.setEndValue(end_rect.size())
        
        # 创建动画组
        animation_group = QParallelAnimationGroup(self)
        animation_group.addAnimation(pos_animation)
        animation_group.addAnimation(size_animation)
        
        if finished_callback:
            animation_group.finished.connect(finished_callback)
        
        return animation_group
    
    def ring_bell_animation(self):
        # 实现铃铛摇摆动画
        # 首先停止所有可能的铃铛动画
        if hasattr(self, 'bell_rotation_timer'):
            self.bell_rotation_timer.stop()
            delattr(self, 'bell_rotation_timer')
        
        # 初始化旋转角度和动画状态
        self.bell_rotation_angle = 0
        self.bell_rotation_direction = 1  # 1表示向右旋转，-1表示向左旋转
        self.bell_rotation_step = 0
        self.bell_rotation_steps = 10
        self.bell_rotation_max_angle = 15
        
        # 创建定时器控制摇摆动画
        self.bell_rotation_timer = QTimer(self)
        self.bell_rotation_timer.timeout.connect(self.update_bell_rotation)
        self.bell_rotation_timer.start(50)
    
    def update_bell_rotation(self):
        # 更新铃铛旋转角度
        self.bell_rotation_step += 1
        
        if self.bell_rotation_step <= self.bell_rotation_steps:
            # 计算当前旋转角度
            progress = self.bell_rotation_step / self.bell_rotation_steps
            if self.bell_rotation_direction == 1:
                self.bell_rotation_angle = self.bell_rotation_max_angle * progress
            else:
                self.bell_rotation_angle = self.bell_rotation_max_angle - (self.bell_rotation_max_angle * 2) * progress
        else:
            # 切换旋转方向
            self.bell_rotation_direction *= -1
            self.bell_rotation_step = 0
            
            # 检查是否完成了一个完整的摇摆周期
            if self.bell_rotation_direction == 1 and self.bell_rotation_angle == 0:
                # 动画完成，停止定时器
                self.bell_rotation_timer.stop()
                delattr(self, 'bell_rotation_timer')
                return
        
        # 应用旋转效果
        from PyQt5.QtGui import QFont
        font = QFont('Arial', 14)
        self.notification_label.setFont(font)
        
        # 使用HTML和CSS变换来实现旋转效果
        rotation_style = f"style='transform: rotate({self.bell_rotation_angle}deg); display: inline-block;'"
        self.notification_label.setText(f"<span {rotation_style}>🔔</span>")
    
    def update_music_info(self, song, artist):
        # 更新音乐信息
        self.current_song = song
        self.current_artist = artist
        self.extra_info_label.setText(f"正在播放: {song} - {artist}")
    
    def update_volume_info(self):
        # 更新音量显示信息
        if has_volume_utils and volume_utils.volume_initialized:
            try:
                volume_percent = volume_utils.get_volume_percentage()
                mute = volume_utils.get_mute()
                
                # 更新音量图标
                if mute:
                    self.volume_label.setText("🔇")
                elif volume_percent == 0:
                    self.volume_label.setText("🔈")
                elif volume_percent < 50:
                    self.volume_label.setText("🔉")
                else:
                    self.volume_label.setText("🔊")
                
                # 更新音量百分比
                self.volume_percent_label.setText(f"{volume_percent}%")
            except Exception:
                # 如果出现错误，使用默认值
                self.volume_label.setText("🔊")
                self.volume_percent_label.setText("50%")
        else:
            # 如果音量功能不可用，使用默认值
            self.volume_label.setText("🔊")
            self.volume_percent_label.setText("50%")
    
    def update_battery_info(self):
        # 更新电池信息显示
        try:
            battery = psutil.sensors_battery()
            if battery:
                percent = int(battery.percent)
                plugged = battery.power_plugged
                
                # 根据充电状态和电量选择合适的图标
                if plugged:
                    # 充电状态
                    if percent == 100:
                        self.battery_label.setText("🔋100%")
                    else:
                        self.battery_label.setText(f"🔌{percent}%")
                else:
                    # 放电状态
                    if percent > 80:
                        self.battery_label.setText(f"🔋{percent}%")
                    elif percent > 20:
                        self.battery_label.setText(f"🔋{percent}%")
                    else:
                        self.battery_label.setText(f"🪫{percent}%")
            else:
                # 如果无法获取电池信息
                self.battery_label.setText("🔋")
        except Exception:
            # 如果出现错误，使用默认值
            self.battery_label.setText("🔋")
    
    def volume_up(self):
        # 增加音量
        if has_volume_utils and volume_utils.volume_initialized:
            volume_utils.increase_volume(step=0.05)
            self.update_volume_info()
    
    def volume_down(self):
        # 减少音量
        if has_volume_utils and volume_utils.volume_initialized:
            volume_utils.decrease_volume(step=0.05)
            self.update_volume_info()
    
    def toggle_mute(self):
        # 切换静音状态
        if has_volume_utils and volume_utils.volume_initialized:
            volume_utils.toggle_mute()
            self.update_volume_info()
    
    def mousePressEvent(self, event):
        # 鼠标按下事件，用于拖动窗口和点击切换展开/收起
        if event.button() == Qt.LeftButton:
            # 激活窗口以确保接收键盘事件
            self.setFocus()
            self.activateWindow()
            
            # 检查是否点击了音量图标
            if self.volume_label.geometry().contains(event.pos()):
                # 点击音量图标切换静音
                self.toggle_mute()
            # 检查是否点击了日历图标
            elif self.calendar_label.geometry().contains(event.pos()):
                # 点击日历图标切换日历详情显示
                if self.calendar_detail_label.isVisible():
                    self.calendar_detail_label.hide()
                else:
                    self.calendar_detail_label.show()
            # 检查是否点击了铃铛图标
            elif self.notification_label.geometry().contains(event.pos()):
                # 点击铃铛图标触发摇摆动画
                self.ring_bell_animation()
            else:
                # 记录点击位置和拖拽起始位置
                self.click_pos = event.pos()
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                
                # 设置拖动状态为False，后续根据移动距离判断
                self.draggable = False
            event.accept()
    
    def mouseReleaseEvent(self, event):
        # 鼠标释放事件
        if event.button() == Qt.LeftButton:
            # 计算鼠标移动距离
            distance = (event.pos() - self.click_pos).manhattanLength() if hasattr(self, 'click_pos') else 0
            
            # 如果移动距离小于阈值，认为是点击操作，执行展开/收起
            if distance < 5 and self.rect().contains(self.click_pos):
                # 检查是否点击了音量图标或日历图标
                if not self.volume_label.geometry().contains(event.pos()) and not self.calendar_label.geometry().contains(event.pos()):
                    self.toggle_expand()
            
            # 重置拖动状态
            self.draggable = False
    
    def enterEvent(self, event):
        # 鼠标进入事件，放大窗口
        if not self.expanded:  # 只有在未展开状态下才执行悬停动画
            # 停止所有动画
            self.stop_all_animations()
            
            new_width = self.original_width + 40
            new_height = self.original_height + 10
            
            # 使用availableGeometry获取可用屏幕区域（排除任务栏）
            screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            new_x = (screen_geometry.width() - new_width) // 2
            new_y = 10  # 固定在顶部10像素处
            
            # 获取当前窗口位置作为动画起始点
            current_geometry = self.geometry()
            
            # 增加背景透明度
            palette = self.palette()
            palette.setColor(QPalette.Window, QColor(0, 0, 0, 230))
            self.setPalette(palette)
            
            # 显示音量百分比、电池图标和日历图标
            self.volume_percent_label.show()
            self.battery_label.show()
            self.calendar_label.show()
            # 不自动显示日历详情，只有点击后才显示
            self.calendar_detail_label.hide()
            
            # 确保动画结束后窗口位置正确
            def on_hover_enter_finished():
                self.setGeometry(new_x, new_y, new_width, new_height)
            
            # 使用统一的动画创建方法
            self.hover_animation = self.create_animation(
                b"geometry",
                current_geometry,
                (new_x, new_y, new_width, new_height),
                duration=300,
                finished_callback=on_hover_enter_finished
            )
            
            # 启动动画
            self.hover_animation.start()
    
    def leaveEvent(self, event):
        # 鼠标离开事件，恢复原始大小
        if not self.expanded:  # 只有在未展开状态下才执行悬停动画
            # 停止所有动画
            self.stop_all_animations()
            
            # 使用availableGeometry获取可用屏幕区域（排除任务栏）
            screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            new_x = (screen_geometry.width() - self.original_width) // 2
            new_y = 10  # 固定在顶部10像素处
            
            # 获取当前窗口位置作为动画起始点
            current_geometry = self.geometry()
            
            # 恢复背景透明度
            palette = self.palette()
            palette.setColor(QPalette.Window, QColor(0, 0, 0, 200))
            self.setPalette(palette)
            
            # 隐藏音量百分比、日历详情、电池图标和日历图标
            self.volume_percent_label.hide()
            self.calendar_detail_label.hide()
            self.battery_label.hide()
            self.calendar_label.hide()
            
            # 确保动画结束后窗口位置正确
            def on_hover_leave_finished():
                self.setGeometry(new_x, new_y, self.original_width, self.original_height)
            
            # 使用统一的动画创建方法
            self.hover_animation = self.create_animation(
                b"geometry",
                current_geometry,
                (new_x, new_y, self.original_width, self.original_height),
                duration=300,
                finished_callback=on_hover_leave_finished
            )
            
            # 启动动画
            self.hover_animation.start()
    
    def keyPressEvent(self, event):
        # 键盘事件处理，实现音量控制快捷键
        modifiers = event.modifiers()
        key = event.key()
        
        # 检查是否按下了Ctrl键
        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_Up or key == Qt.Key_Equal:  # Ctrl+Up 或 Ctrl+=
                self.volume_up()
            elif key == Qt.Key_Down or key == Qt.Key_Minus:  # Ctrl+Down 或 Ctrl+-  
                self.volume_down()
            elif key == Qt.Key_M:  # Ctrl+M
                self.toggle_mute()
        
        event.accept()
    
    def toggle_expand(self):
        # 切换展开/收起状态
        self.expanded = not self.expanded
        
        # 首先停止所有可能的动画
        self.stop_all_animations()
        
        if self.expanded:
            # 展开时的动画
            new_width = self.original_width + 100
            new_height = self.original_height + 30
            
            # 使用availableGeometry获取可用屏幕区域（排除任务栏）
            screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            new_x = (screen_geometry.width() - new_width) // 2
            new_y = 10  # 固定在顶部10像素处
            
            # 获取当前窗口位置作为动画起始点
            current_geometry = self.geometry()
            
            # 显示额外信息
            self.extra_info_label.show()
            self.volume_percent_label.show()  # 展开时显示音量百分比
            self.battery_label.show()  # 展开时显示电池图标
            self.calendar_label.show()  # 展开时显示日历图标
            # 不自动显示日历详情，只有点击后才显示
            self.calendar_detail_label.hide()
            
            # 增加背景透明度
            palette = self.palette()
            palette.setColor(QPalette.Window, QColor(0, 0, 0, 240))
            self.setPalette(palette)
            
            # 确保动画结束后窗口位置正确
            def on_expand_finished():
                self.setGeometry(new_x, new_y, new_width, new_height)
            
            # 使用统一的动画创建方法
            self.expand_animation = self.create_animation(
                b"geometry",
                current_geometry,
                (new_x, new_y, new_width, new_height),
                duration=400,
                finished_callback=on_expand_finished
            )
            
            # 启动动画
            self.expand_animation.start()
            
        else:
            # 使用availableGeometry获取可用屏幕区域（排除任务栏）
            screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            new_x = (screen_geometry.width() - self.original_width) // 2
            new_y = 10  # 固定在顶部10像素处
            
            # 获取当前窗口位置作为动画起始点
            current_geometry = self.geometry()
            
            # 隐藏额外信息
            self.extra_info_label.hide()
            self.volume_percent_label.hide()  # 收起时隐藏音量百分比
            self.calendar_detail_label.hide()  # 收起时隐藏日历详情
            self.battery_label.hide()  # 收起时隐藏电池图标
            self.calendar_label.hide()  # 收起时隐藏日历图标
            
            # 恢复背景透明度
            palette = self.palette()
            palette.setColor(QPalette.Window, QColor(0, 0, 0, 200))
            self.setPalette(palette)
            
            # 确保动画结束后窗口位置正确
            def on_collapse_finished():
                self.setGeometry(new_x, new_y, self.original_width, self.original_height)
            
            # 使用统一的动画创建方法
            self.collapse_animation = self.create_animation(
                b"geometry",
                current_geometry,
                (new_x, new_y, self.original_width, self.original_height),
                duration=400,
                finished_callback=on_collapse_finished
            )
            
            # 启动动画
            self.collapse_animation.start()
    
    def contextMenuEvent(self, event):
        # 右键菜单事件
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        
        # 音量控制菜单项
        if has_volume_utils and volume_utils.volume_initialized:
            volume_menu = menu.addMenu("音量控制")
            volume_up_action = volume_menu.addAction("增加音量")
            volume_down_action = volume_menu.addAction("减少音量")
            mute_action = volume_menu.addAction("切换静音")
            menu.addSeparator()
            
            # 连接信号
            volume_up_action.triggered.connect(self.volume_up)
            volume_down_action.triggered.connect(self.volume_down)
            mute_action.triggered.connect(self.toggle_mute)
        
        exit_action = menu.addAction("退出")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == exit_action:
            QApplication.quit()
    
    def update_time(self):
        from datetime import datetime
        current_datetime = datetime.now()
        current_time = current_datetime.strftime('%H:%M')
        current_date = current_datetime.strftime('%m-%d')
        
        # 更新时间标签
        self.time_label.setText(f"{current_date} {current_time}")
        
        # 更新日历详情
        week_day = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][current_datetime.weekday()]
        full_date = current_datetime.strftime('%Y年%m月%d日')
        self.calendar_detail_label.setText(f"{full_date} {week_day}")
    
    def keyPressEvent(self, event):
        # 键盘事件处理，用于音量控制快捷键
        modifiers = event.modifiers()
        key = event.key()
        
        # 音量增加：Ctrl + Up或Ctrl + 上箭头
        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_Up or key == Qt.Key_Equal:
                self.volume_up()
            # 音量减少：Ctrl + Down或Ctrl + 减号
            elif key == Qt.Key_Down or key == Qt.Key_Minus:
                self.volume_down()
            # 静音切换：Ctrl + M
            elif key == Qt.Key_M:
                self.toggle_mute()
        
        event.accept()
    
    def closeEvent(self, event):
        # 窗口关闭时停止音乐播放器线程
        self.music_thread.stop()
        self.music_thread.wait()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    island = DynamicIsland()
    island.show()
    sys.exit(app.exec_())