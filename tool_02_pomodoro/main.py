import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QComboBox, QSystemTrayIcon, QMenu, QMessageBox,
                             QInputDialog,
                             )

from PyQt5.QtCore import (Qt, QTimer, QRect)
from PyQt5.QtGui import QPainter, QColor, QFont, QIcon, QPen

"""核心功能
番茄钟模式：25分钟专注 → 5分钟休息 → 循环
自由倒计时：自定义任意时间
圆形进度环：用 QPainter 绘制，随时间流逝"吃豆人"式缩减
开始 / 暂停 / 重置控制
好玩拓展
系统托盘通知：时间到了弹窗提醒 + 提示音
番茄统计：记录你今天完成了几个番茄，数据保存到本地
窗口置顶 + 半透明：让它像个小挂件一样浮在桌面上
双主题：工作模式红色系，休息模式绿色系，自动切换
"""
class PomodorWindow(QWidget):
    def __init__(self):
        super().__init__()
        # ====状态变量====
        self.time_left = 25*60 # 剩余秒数(默认25min)
        self.total_time = 25*60 # 总时长
        self.is_running = False # 计时器是否在运行
        self.is_work_mode = True # 工作模式，False是休息模式
        self.tomato_count = 0 # 完成的番茄数
        self.progress = 1.0 # 进度值(0.0~1.0)用于绘制进度环，1.0表示圆满，0.0表示空圆(时间到)


        self.init_ui() # 调用这个方法 把界面上的按钮、文字都摆好（这是自定义的方法）

        # 创建定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick) # 每当计时器倒计时到0，就调用tick方法

    def init_ui(self):
        """搭建界面布局"""

        # 设置窗口标题及大小
        self.setWindowTitle("🍅 番茄钟")
        self.setFixedSize(350,480) # 固定大小，禁止用户拖拽改变窗口

        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter) # 让布局所有控件居中对齐

        # 第一个控件 ：模式标签(显示"专注时间"或“休息时间”)
        self.model_label = QLabel("🍅 专注时间")
        self.model_label.setAlignment(Qt.AlignCenter)
        self.model_label.setFont(QFont("Microsoft YaHei",14,QFont.Bold)) # 设置字体

        main_layout.addWidget(self.model_label) # 将标签放进主布局

        # 第二个控件：时间显示
        self.time_label = QLabel("25:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setFont(QFont("consolas",42,QFont.Bold)) # consolas等宽字体，数字宽度一样，变换数字时不会左右跳动

        main_layout.addWidget(self.time_label)

        # 第三个控件：番茄计数（显示今天完成了几个番茄）
        self.count_label = QLabel("今日番茄：0 🍅")
        self.count_label.setAlignment(Qt.AlignCenter)
        self.count_label.setFont(QFont("Microsoft YaHei",11))

        main_layout.addWidget(self.count_label)

        # 第四个区域-----"模式:"文字和下拉框要左右并排，所以要用一个水平布局
        mode_layout = QHBoxLayout() # QHBoxLayout水平盒子布局，控件从左到右排列
        mode_layout.addWidget(QLabel("模式：")) # 添加一个静态文字标签“模式”

        self.mode_combo = QComboBox() # QCombox睡觉哦下拉选择框
        # addItems 一次性添加多个选项，用户点击下拉框就能看到这些选项
        self.mode_combo.addItems([
            "番茄钟(25min)",
            "短休息(5min)",
            "长休息(15min)",
            "自定义"
        ])

        # currentIndexChanged是一个"信号"，当用户切换选项就会自动触发，Index参数就是用户选中的选项索引
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        main_layout.addWidget(self.mode_combo)


        # 第五个区域：控制按钮(开始/暂停 + 重置)
        # 两个按钮左右并排，所以也用水平布局
        btn_layout = QHBoxLayout()

        self.start_btn = QPushButton("▶开始")
        self.start_btn.setFixedHeight(40)
        self.start_btn.clicked.connect(self.toggle_timer) # toggle转换切换
        btn_layout.addWidget(self.start_btn)

        # 重置按钮
        self.reset_btn = QPushButton("↻ 重置")
        self.reset_btn.setFixedHeight(40)
        self.reset_btn.clicked.connect(self.reset_timer)
        btn_layout.addWidget(self.reset_btn)

        main_layout.addLayout(btn_layout)




        # 第6个控件：置顶按钮

        self.top_btn = QPushButton("📌 窗口置顶: 关")
        self.top_btn.setCheckable(True) # setCheckable(True)让按钮有"按下/弹起"两种状态

        self.top_btn.clicked.connect(self.toggle_top)
        main_layout.addWidget(self.top_btn)


        # 将布局"安装"到窗口上
        self.setLayout(main_layout)


    def tick(self):
        """
                每秒执行一次，负责：
                1. 把剩余时间减 1 秒
                2. 刷新界面上的时间显示
                3. 如果时间到了（减到 0），停止计时并提醒用户
        """

        # 剩余时间减一秒
        self.time_left -= 1

        # 调用 update_display 刷新2界面上的“MM:SS”显示
        self.update_display()

        # 重新计算进度比例，并触发窗口重新绘制(自动调用paintEvent)
        self.progress = self.time_left/self.total_time if self.total_time>0 else 0
        self.update() # 通知系统"我需要重绘"，系统会调用paintEvent


        # 判断时间是否到了
        if self.time_left <= 0:
            # 停止计时器
            self.timer.stop()

            # 把运行状态改为 False
            self.is_running = False

            # 把按钮文字改回"▶ 开始"（因为计时结束了）
            self.start_btn.setText("▶ 开始")

            # 如果是工作模式结束，番茄数 +1
            if self.is_work_mode:
                self.tomato_count += 1
                self.count_label.setText(f"今日番茄：{self.tomato_count}🍅")
            # 弹出提醒框
            if self.is_work_mode:
                msg = "专注时间结束！休息一下吧"
            else:
                msg = "休息结束！准备开始新的番茄钟吧"
            QMessageBox.information(self,"番茄钟提醒",msg)




    def toggle_timer(self):
        """
        开始/暂停切换。
        如果is_running = False ->启动计时器，开始倒计时
        反之                  ->停止定时器，暂停倒计时
        :return:
        """
        if not self.is_running:
            # 启动定时器

                # 检查剩余时间是否大于0(防止时间为0还能点开始)
            if self.time_left <= 0:
                return

            # 启动定时器，触发后会自动调用tick方法
            self.timer.start(1000) # 1000毫秒 = 1秒

            # 更新状态
            self.is_running = True

            # 把按钮改成暂停，提示用户再次点击可以暂停
            self.start_btn.setText("⏸ 暂停")
        else:
            # 暂停定时器
            self.timer.stop()

            # 更新状态
            self.is_running = False

            # 把文字按钮改回开始
            self.start_btn.setText("▶ 开始")




    def reset_timer(self):
        """
        重置倒计时。
        停止倒计时，把time_left恢复为total_time
        :return:
        """

        # 停止定时器
        self.timer.stop()

        # 重置状态
        self.is_running = False

        # 将剩余时间恢复为总时长
        self.time_left = self.total_time

        # 刷新界面上的时间显示
        self.update_display()

        # 该按钮为开始
        self.start_btn.setText("▶ 开始")


    def on_mode_changed(self,index):
        """
        用户切换下拉框选项时调用，
        自定义选项后续会弹出输入框
        :return:
        """

        # 停止计时器
        self.timer.stop()
        self.is_running = False

        # 根据选项编号，设定对应时长
        if index == 0:
            # 25min
            self.total_time = 25*60
            self.is_work_mode = True
            self.model_label.setText("🍅 专注时间")
        elif index == 1:
            # 5min
            self.total_time = 5*60
            self.is_work_mode = False
            self.model_label.setText("☕ 短休息")
        elif index == 2:
            # 15min
            self.total_time = 15*60
            self.is_work_mode = False
            self.model_label.setText("🌴 长休息")
        elif index == 3:
            # 自定义模式 ：弹出输入框让用户输入分钟数
            #   QInputDialog 是一个系统自带的输入对话框
            minutes,ok = QInputDialog.getInt(
                self, # 父窗口
                "自定义倒计时",
                "请输入分钟数：",
                10, # 默认值
                1, # 最小值
                999, # 最大值

            )# ok是bool值
            if ok:
                self.total_time = minutes * 60
                self.is_work_mode = True
                self.model_label.setText(f"⏱ 自定义({minutes}min)")
            else:
                # 用户取消了，恢复第一个选项
                self.mode_combo.setCurrentIndex(0)
                return

        # 将剩余时间也同步改成新的总时长
        self.time_left = self.total_time

        # 刷新显示
        self.update_display()

        # 改按钮为开始
        self.start_btn.setText("▶ 开始")





    def toggle_top(self):
        """
        切换窗口是否置顶
        如果置顶：设置窗口标志为"永远在所有窗口最前面"
        如果取消：恢复正常窗口模式
        :return:
        """

        if self.top_btn.isChecked():
            # ----开启置顶----
            # setWindowFlags 设置窗口的"标志位"
            # Qt.WindowStaysOnTopHint 的意思是“永远在最前面”
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.top_btn.setText("📌 窗口置顶: 开")
        else:
            # ----关闭置顶----
            # ~Qt,WindowStayOnTopHint表示是“去掉置顶标志”
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.top_btn.setText("📌 窗口置顶: 关")

        # 修改完窗口标志后，必须要调用show()才能生效
        # 改了flags不show的话不会刷新
        self.show()

    def update_display(self):
        """
        刷新时间显示
        把time_left(秒数)转换成"MM:SS"格式显示在界面上
        比如1500秒 -->“25:00
        :return:
        """
        minutes = self.time_left //60 # //是整除 - 只取整数部分
        seconds = self.time_left % 60 # %取余
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}") # :2d表示至少两位数，不足补零

        pass

    def paintEvent(self, event):
        """
        绘制圆形进度环
        这个方法不需要我们手动调用
        每当窗口需要重新绘制时(如窗口刚打开、被遮挡后露出)
        PyQt会自动调用这个方法
        我们只需要在里面写"怎么画"的逻辑就行
        :param event:
        :return:
        """

        # 第1步：创建 QPainter 对象
        painter = QPainter(self) # 创建QPainter对象
        painter.setRenderHint(QPainter.Antialiasing) # 开启抗锯齿--边缘平滑

        # 第2步：确定圆环的位置和大小
        # QRect 定义一个矩形区域，圆就画在这个矩形的内切圆位置
        ring_size = 260 # 设置园的直径
        x = (self.width()-ring_size)/2# 计算圆环左上角坐标，让它居中
        y = 60 # 从顶部往下60像素开始画(给模式标签留空间)
        # QRect(左上角x, 左上角y, 宽度, 高度)
        rect = QRect(int(x),int(y),ring_size,ring_size) # 当宽度等于高度时，这就是一个正圆

        # 第3步：画背景轨道（浅灰色完整圆环）
        bg_pen = QPen(QColor(230,230,230),12)# QPen(颜色, 线条宽度)
        # 设置笔的“端点样式”为圆角
        bg_pen.setCapStyle(Qt.RoundCap) # Qt.RoundCap:线条的起点和终点都是圆形，看起来更加柔和

        painter.setPen(bg_pen) # 将这只笔交给画家

        # 画圆弧 drawArc(矩形区域，起始角度，跨越角度)
        painter.drawArc(rect,90*16,360*16)

        # 第四步：画前景进度弧

        # 根据当权模式选择颜色
        if self.is_work_mode:
            # 工作模式：红色
            fg_color = QColor("red")
        else:
            # 休息模式：绿色
            fg_color = QColor("green")

        # 创建前景的“笔”
        fg_pen = QPen(fg_color,12)
        fg_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(fg_pen)

        # 计算进度弧的跨越角度
        span_angle = int(self.progress*360*16)

        # 画进度狐
        # PyQt5中正角度是逆时针方向，所以圆弧会从正上方开始，逆时针“缩短”
        painter.drawArc(rect,90*16,span_angle)

        # 第五步：结束绘制，每次必须调用end(),否则会导致绘图异常或内存泄露
        painter.end()











if __name__ =="__main__":
    app = QApplication(sys.argv)
    window = PomodorWindow()
    window.show()
    sys.exit(app.exec_())