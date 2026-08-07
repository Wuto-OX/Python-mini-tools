# 导入我们需要的模块和类
import json
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QListWidget, QMessageBox, QListWidgetItem
                             )
from PyQt5.QtCore import Qt

# 我们的应用程序主窗口类
class MyFirstWindow(QMainWindow):
    def __init__(self):
        super().__init__()  # 调用父类QMainWindow的初始化方法

        """数据持久化相关设置"""
        self.data_file = "tasks.json" # 定义数据文件的路径
        self.tasks = [] # 这是我们的核心数据结构，一个字典列表，用于在内存中存储所有任务


        self.setWindowTitle("我的第一个窗口")  # 设置窗口标题
        self.resize(400, 300)  # 设置窗口大小 (宽度, 高度)

        # 创建一个中心部件（容器）
        central_widget = QWidget()
        self.setCentralWidget(central_widget) # 把这个容器色号职位主窗口的中心部件

        # 在容器里创建一个垂直布局
        layout = QVBoxLayout(central_widget)

        # 顶部输入区域(使用水平布局)
        input_layout = QHBoxLayout()

        # 创建一个输入框
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("输入新的待办事项...") # 设置提示文字

        # 创建一个按钮
        self.add_btn = QPushButton("添加")

        # 把输入框和按钮都放进水平布局里
        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.add_btn)

        # 把水平布局放进窗口的垂直布局里
        layout.addLayout(input_layout)

        # 列表区域
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget) # 把列表直接放进垂直布局里

        # 底部按钮
        self.delete_btn = QPushButton("删除选中项")
        layout.addWidget(self.delete_btn) # 把按钮直接放进垂直布局里

        self._is_updating = False
        # 绑定事件：将按钮的点击信号(clicked)连接到我们自定义的方法上
        self.add_btn.clicked.connect(self.add_task)
        self.delete_btn.clicked.connect(self.delete_task)
        self.list_widget.itemDoubleClicked.connect(self.delete_task)
        self.list_widget.itemChanged.connect(self.on_item_changed)# 监听勾选状态变化
        # 加载已保存的任务
        self.load_tasks()


    def add_task(self):
        """添加任务的逻辑"""

        # 1.获取框里面的文字，并去掉首尾的空格
        task_text = self.input_box.text().strip()

        # 2.判断：如果文字不为空
        if task_text:
            # 将任务以字典的形式存入内存列表
            self.tasks.append({"text":task_text,"completed":False})
            # 保存数据到文件
            self.save_tasks()
            # 刷新界面
            self.refresh_list()
            self.input_box.clear()
        else:
            # 如果为空，弹出一个警告框
            QMessageBox.warning(self,"提示","请输入待办内容！")


    def delete_task(self,item=None):
        """删除任务的逻辑(升级版，支持双击删除)"""
        # 1.获取要删除的项
        # 如果方法被调用时传入了item参数(即双击事件)，就用它
        # 否则，回退到使用当前选中的行（即点击删除按钮的情况）
        row = -1 # 防止变量未定义报错
        # 注意：按钮的clicked信号会自带一个bool参数，所以不能只判断 is not None
        # 要判断传进来的到底是不是一个真正的列表项
        if isinstance(item, QListWidgetItem):
            # 从传入的item对象获取它在列表中的行号
            row = self.list_widget.row(item)
        else:
            # 否则说明是点击按钮触发的，用当前选中的行号即可
            row = self.list_widget.currentRow()

        # 2.判断：如果行号>=0,说明有选中项
        if row >= 0:
            # 从内存列表中移除对应任务
            del self.tasks[row]
            # 保存数据到文件
            self.save_tasks()
            # 刷新界面
            self.refresh_list()
        else:
            # 如果没有选中项，弹出警告
            QMessageBox.warning(self,"提示","请选中要删除的事项！")

    def load_tasks(self):
        """从文件中加载任务列表"""
        try:
            # 1.尝试打开文件
            with open(self.data_file,'r',encoding='utf-8')as f:
                # 2.读取并解析Json数据
                self.tasks = json.load(f)
            # 3.将加载的数据刷新到界面上
            self.refresh_list()
            print(f"成功从{self.data_file}加载了{len(self.tasks)}条任务。")
        except(FileNotFoundError,json.JSONDecodeError):
            # 如果文件不存在或内容不是合法的JSON，就初始化一个空列表
            self.tasks = []
            print(f"未找到数据文件{self.data_file}或文件损坏，将初始化一个空的任务列表。")

    def save_tasks(self):
        """将当前的任务列表保存到文件"""
        try:
            # 1.打开文件准备写入
            with open(self.data_file,'w',encoding='utf-8')as f:
                # 2.将内存中的self.tasks列表转换为JSON格式写入文件
                json.dump(self.tasks,f,ensure_ascii=False,indent=4)
            print(f"成功将{len(self.tasks)}条任务保存到{self.data_file}。")

        except Exception as e:
            print(f"保存任务是出错：{e}")


    def refresh_list(self):
        """将内存中的任务列表同步到界面上的QListWidget"""
        # 1.清空界面上的所有项
        self.list_widget.clear()

        # 2.遍历内存中的任务列表
        for task in self.tasks:
            # 3.为每个任务创建一个QListWidgetItem
            item = QListWidgetItem(task['text'])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable) # 添加这一行
            item.setCheckState(Qt.Checked if task['completed'] else Qt.Unchecked) # 根据数据设置勾选状态

            # 4.设置样式
            if task['completed']:
                font = item.font()
                font.setStrikeOut(True)
                item.setFont(font)
                item.setForeground(Qt.gray)

            # 5.将创建好的项添加到列表控件中
            self.list_widget.addItem(item)

    def closeEvent(self, event):
        """重写关闭事件，确保在窗口关闭前保存数据"""
        self.save_tasks()
        # 调用父类的closeEvent方法，允许串口正常关闭
        super().closeEvent(event)

    def on_item_changed(self,item):
        """当列表的勾选状态发生变化时调用"""
        # 如果系统正在更新，直接返回，防止递归
        if self._is_updating:
            return
        # 打开开关--修改页面
        self._is_updating = True

        try:
            # 1.获取这一项在列表中的行号
            row = self.list_widget.row(item)

            # 2.根据行号，更新内存中对应任务的 completed 状态
            # Qt.checked 表示已勾选，Qt.Unchecked表示未勾选
            self.tasks[row]['completed'] = (item.checkState() == Qt.Checked)

            # 3.保存数据到文件
            self.save_tasks()

            # 临时阻塞列表信号
            self.list_widget.blockSignals(True)

            # 注意：这里不要直接调用 refresh_list()！
            # 因为 refresh_list 会重建所有 Item，再次触发 itemChanged
            # 应该只更新当前这一个 Item 的样式
            self.update_item_style(item)
        finally:
            # 无论是否出错，都要恢复信号+关闭开关
            self.list_widget.blockSignals(False)
            self._is_updating = False

    def update_item_style(self,item):
        """只更新单个Item的样式，避免全局刷新"""
        if item.checkState() == Qt.Checked:
            font = item.font()
            font.setStrikeOut(True)
            item.setFont(font)
            item.setForeground(Qt.gray)
        else:
            font = item.font()
            font.setStrikeOut(False)
            item.setFont(font)
            item.setForeground(Qt.black)





# 程序的入口点
if __name__ == "__main__":
    app = QApplication(sys.argv)  # 创建一个应用实例
    window = MyFirstWindow()  # 创建我们自定义窗口的实例
    window.show()  # 显示窗口
    sys.exit(app.exec_())  # 进入应用的主循环，等待用户操作