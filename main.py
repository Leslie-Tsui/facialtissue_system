import sys

import cv2
import serial
from PyQt5.QtCore import Qt, QSize, QDateTime
from PyQt5.QtGui import QPixmap, QPalette, QImage, QFont
from PyQt5.QtWidgets import *

from Camera.TriggerGrab import Camera
from YOLO import mvsdk
from YOLO.yolo import detecter
import datetime


# 主界面
class MainFrame(QWidget):
    def __init__(self):
        super(MainFrame, self).__init__()
        self.initUI()
        self.co = com()
        self.co.RelayClose()

        self.detecter = detecter()  # 初始化一个yolo模型的对象
        self.model = self.detecter.model  # 预加载模型
        self.camera = Camera(self.label, self.export_table, self.statistic_table, self.detecter, self.model,
                             self.countLabel,
                             self.detcountLabel, self.totalLabel, self.alertLabel, self.co)  # 初始化打开相机

    def initUI(self):
        # 使用pyqt5初始化UI界面
        self.setGeometry(200, 200, 3300, 1300)
        self.setWindowTitle('检测')
        # self.setWindowIcon(QIcon('...'))
        self.btnQuery = QPushButton('查询', self)
        self.btnSetting = QPushButton('设置', self)

        self.label1 = QLabel(self)  # 设置的个数展示文本
        self.label2 = QLabel(self)  # 检测的个数展示文本
        self.label3 = QLabel(self)  # 已经检测的总个数
        self.label4 = QLabel(self)  # 报警个数

        self.label1.setText('|设置个数:')
        self.label2.setText('|检测个数:')
        self.label3.setText('|总检测数:')
        self.label4.setText('|报警个数:')

        self.label1.setFont(QFont("Roman times", 20, QFont.Bold))
        self.label2.setFont(QFont("Roman times", 20, QFont.Bold))
        self.label3.setFont(QFont("Roman times", 20, QFont.Bold))
        self.label4.setFont(QFont("Roman times", 20, QFont.Bold))

        self.countLabel = QLabel(self)  # 设置的个数展示文本
        self.detcountLabel = QLabel(self)  # 检测的个数展示文本
        self.totalLabel = QLabel(self)  # 设置已经检测的总个数
        self.alertLabel = QLabel(self)  # 设置报警个数

        self.countLabel.setFont(QFont("Roman times", 20, QFont.Bold))
        self.detcountLabel.setFont(QFont("Roman times", 20, QFont.Bold))
        self.totalLabel.setFont(QFont("Roman times", 20, QFont.Bold))
        self.alertLabel.setFont(QFont("Roman times", 20, QFont.Bold))

        self.countLabel.setText('12')
        self.detcountLabel.setText('0')
        self.totalLabel.setText('0')
        self.alertLabel.setText('0')

        self.label = QLabel(self)
        self.QScrollArea = QScrollArea(self)
        self.QScrollArea.setBackgroundRole(QPalette.Dark)
        self.QScrollArea.setWidget(self.label)

        self.errorlabel = QLabel(self)
        self.errorUI = QWidget()
        self.errorUI.setMinimumWidth(1200)
        self.errorUI.setMinimumSize(QSize(1600, 1200))
        QScrollArea1 = QScrollArea(self)
        QScrollArea1.setBackgroundRole(QPalette.Dark)
        QScrollArea1.setWidget(self.errorlabel)
        vbox1 = QVBoxLayout(self)
        vbox1.addWidget(QScrollArea1)
        self.errorUI.setLayout(vbox1)
        self.errorUI.hide()

        self.winid = self.label.winId()  # 获取label对象的句柄
        self.label.setStyleSheet("QLabel{background:Dark;}")
        self.loadErrorImage('../Image/grab.JPG')
        hbox = QHBoxLayout()

        hbox.addWidget(self.btnQuery)
        hbox.addWidget(self.btnSetting)
        hbox.addWidget(self.label1)
        hbox.addWidget(self.countLabel)
        hbox.addWidget(self.label2)
        hbox.addWidget(self.detcountLabel)

        hbox.addWidget(self.label3)
        hbox.addWidget(self.totalLabel)
        hbox.addWidget(self.label4)
        hbox.addWidget(self.alertLabel)

        hbox.addStretch(1)
        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.QScrollArea)

        # 加入导出表格
        self.export_table = QTableWidget(0, 4)  # 添加右侧表格
        self.export_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)  # 设置表格为自适应的伸缩模式，即可根据窗口的大小来改变网格的大小
        self.export_table.setSelectionBehavior(self.export_table.SelectRows)  # 设置选中行
        # 鼠标点选时，默认选中一个单元格---QTableWidget.SelectItems
        # QTableWidget.SelectRows   鼠标点击选中一行
        # QTableWidget.SelectColumns  鼠标点击选中一列
        self.export_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 设置为只读表格
        # static_cast<QLineEdit *>(ui->tableWidget->cellWidget(i,9))->setEnabled(false);
        # self.table.cellWidget(i,3).setEnabled(false)
        self.export_table.setHorizontalHeaderLabels(['时间', '设置数据', '检测数据', '查看'])
        self.export_table.itemDoubleClicked.connect(self.showErrorImg)

        # 加入历史查询表格
        self.inquiry_table = QTableWidget(3, 6)
        self.inquiry_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inquiry_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.statistic_table.setHorizontalHeaderLabels(['检测数量', '###', '包', '异常数量', '###', '包'])
        self.inquiry_table.verticalHeader().setVisible(False)  # 隐藏垂直表头
        self.inquiry_table.horizontalHeader().setVisible(False)  # 隐藏水平表头
        # setSpan(row, col, 从当前行向下合并的行数, 向右要合并的列数）
        inquiry_table_item1 = QTableWidgetItem("历史数据(日期选择)")
        inquiry_table_item1.setTextAlignment(Qt.AlignCenter)  # 设置居中
        inquiry_table_item1.setFont(QFont("Roman times", 20, QFont.Bold))

        inquiry_table_item2 = QTableWidgetItem("检测数量")
        inquiry_table_item2.setTextAlignment(Qt.AlignCenter)  # 设置居中
        inquiry_table_item2.setFont(QFont("Roman times", 13, QFont.Bold))

        inquiry_table_item3 = QTableWidgetItem("###")
        inquiry_table_item3.setTextAlignment(Qt.AlignCenter)  # 设置居中
        inquiry_table_item3.setFont(QFont("Roman times", 13, QFont.Bold))

        inquiry_table_item4 = QTableWidgetItem("包")
        inquiry_table_item4.setTextAlignment(Qt.AlignCenter)  # 设置居中
        inquiry_table_item4.setFont(QFont("Roman times", 13, QFont.Bold))

        inquiry_table_item5 = QTableWidgetItem("异常数量")
        inquiry_table_item5.setTextAlignment(Qt.AlignCenter)  # 设置居中
        inquiry_table_item5.setFont(QFont("Roman times", 13, QFont.Bold))

        inquiry_table_item6 = QTableWidgetItem("###")
        inquiry_table_item6.setTextAlignment(Qt.AlignCenter)  # 设置居中
        inquiry_table_item6.setFont(QFont("Roman times", 13, QFont.Bold))

        inquiry_table_item7 = QTableWidgetItem("包")
        inquiry_table_item7.setTextAlignment(Qt.AlignCenter)  # 设置居中
        inquiry_table_item7.setFont(QFont("Roman times", 13, QFont.Bold))

        inquiry_table_item8 = QTableWidgetItem("异常率")
        inquiry_table_item8.setTextAlignment(Qt.AlignCenter)  # 设置居中
        inquiry_table_item8.setFont(QFont("Roman times", 13, QFont.Bold))

        inquiry_table_item9 = QTableWidgetItem("###.##")
        inquiry_table_item9.setTextAlignment(Qt.AlignCenter)  # 设置居中
        inquiry_table_item9.setFont(QFont("Roman times", 13, QFont.Bold))

        inquiry_table_item10 = QTableWidgetItem("%")
        inquiry_table_item10.setTextAlignment(Qt.AlignCenter)  # 设置居左
        inquiry_table_item10.setFont(QFont("Roman times", 13, QFont.Bold))

        # 添加一个弹出的日期选择，设置默认值为当前日期,显示格式为年月日。
        self.btnDate = QDateTimeEdit()
        self.btnDate.setDateTime(QDateTime.currentDateTime())
        self.btnDate.setDisplayFormat("yyyy-MM-dd")
        self.btnDate.setCalendarPopup(True)
        self.inquiry_table.setCellWidget(0, 5, self.btnDate)

        self.btnDate.dateChanged.connect(self.onDateChanged)

        self.inquiry_table.setItem(0, 0, inquiry_table_item1)
        self.inquiry_table.setSpan(0, 0, 1, 5)
        self.inquiry_table.setItem(1, 0, inquiry_table_item2)
        self.inquiry_table.setItem(1, 1, inquiry_table_item3)
        self.inquiry_table.setItem(1, 2, inquiry_table_item4)
        self.inquiry_table.setItem(1, 3, inquiry_table_item5)
        self.inquiry_table.setItem(1, 4, inquiry_table_item6)
        self.inquiry_table.setItem(1, 5, inquiry_table_item7)
        self.inquiry_table.setItem(2, 0, inquiry_table_item8)
        self.inquiry_table.setItem(2, 1, inquiry_table_item9)
        self.inquiry_table.setItem(2, 2, inquiry_table_item10)
        self.inquiry_table.setSpan(1, 3, 2, 1)
        self.inquiry_table.setSpan(1, 4, 2, 1)
        self.inquiry_table.setSpan(1, 5, 2, 1)

        # 加入统计表格
        self.statistic_table = QTableWidget(3, 6)
        self.statistic_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.statistic_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.statistic_table.setHorizontalHeaderLabels(['检测数量', '###', '包', '异常数量', '###', '包'])
        self.statistic_table.verticalHeader().setVisible(False)  # 隐藏垂直表头
        self.statistic_table.horizontalHeader().setVisible(False)  # 隐藏水平表头
        # setSpan(row, col, 从当前行向下合并的行数, 向右要合并的列数）
        statistic_table_item1 = QTableWidgetItem("效率统计")
        statistic_table_item1.setTextAlignment(Qt.AlignCenter)  # 设置居中
        statistic_table_item1.setFont(QFont("Roman times", 20, QFont.Bold))

        statistic_table_item2 = QTableWidgetItem("当班检测")
        statistic_table_item2.setTextAlignment(Qt.AlignCenter)  # 设置居中
        statistic_table_item2.setFont(QFont("Roman times", 13, QFont.Bold))

        statistic_table_item3 = QTableWidgetItem("###")
        statistic_table_item3.setTextAlignment(Qt.AlignCenter)  # 设置居中
        statistic_table_item3.setFont(QFont("Roman times", 13, QFont.Bold))

        statistic_table_item4 = QTableWidgetItem("包")
        statistic_table_item4.setTextAlignment(Qt.AlignCenter)  # 设置居中
        statistic_table_item4.setFont(QFont("Roman times", 13, QFont.Bold))

        statistic_table_item5 = QTableWidgetItem("异常数量")
        statistic_table_item5.setTextAlignment(Qt.AlignCenter)  # 设置居中
        statistic_table_item5.setFont(QFont("Roman times", 13, QFont.Bold))

        statistic_table_item6 = QTableWidgetItem("###")
        statistic_table_item6.setTextAlignment(Qt.AlignCenter)  # 设置居中
        statistic_table_item6.setFont(QFont("Roman times", 13, QFont.Bold))

        statistic_table_item7 = QTableWidgetItem("包")
        statistic_table_item7.setTextAlignment(Qt.AlignCenter)  # 设置居中
        statistic_table_item7.setFont(QFont("Roman times", 13, QFont.Bold))

        statistic_table_item8 = QTableWidgetItem("异常率")
        statistic_table_item8.setTextAlignment(Qt.AlignCenter)  # 设置居中
        statistic_table_item8.setFont(QFont("Roman times", 13, QFont.Bold))

        statistic_table_item9 = QTableWidgetItem("###.##")
        statistic_table_item9.setTextAlignment(Qt.AlignCenter)  # 设置居中
        statistic_table_item9.setFont(QFont("Roman times", 13, QFont.Bold))

        statistic_table_item10 = QTableWidgetItem("%")
        statistic_table_item10.setTextAlignment(Qt.AlignCenter)  # 设置居左
        statistic_table_item10.setFont(QFont("Roman times", 13, QFont.Bold))

        self.statistic_table.setItem(0, 0, statistic_table_item1)
        self.statistic_table.setSpan(0, 0, 1, 6)
        self.statistic_table.setItem(1, 0, statistic_table_item2)
        self.statistic_table.setItem(1, 1, statistic_table_item3)
        self.statistic_table.setItem(1, 2, statistic_table_item4)
        self.statistic_table.setItem(1, 3, statistic_table_item5)
        self.statistic_table.setItem(1, 4, statistic_table_item6)
        self.statistic_table.setItem(1, 5, statistic_table_item7)
        self.statistic_table.setItem(2, 0, statistic_table_item8)
        self.statistic_table.setItem(2, 1, statistic_table_item9)
        self.statistic_table.setItem(2, 2, statistic_table_item10)
        self.statistic_table.setSpan(1, 3, 2, 1)
        self.statistic_table.setSpan(1, 4, 2, 1)
        self.statistic_table.setSpan(1, 5, 2, 1)

        tablebox = QVBoxLayout()
        tablebox.addWidget(self.statistic_table)
        tablebox.addWidget(self.inquiry_table)
        tablebox.addWidget(self.export_table)

        playout = QGridLayout()
        # 第0行第0列开始，占2行2列
        playout.addLayout(hbox, 0, 0, 2, 2)
        # 第3行第0列开始，占2行2列
        playout.addLayout(vbox, 3, 0, 2, 2)
        playout.addLayout(tablebox, 3, 3, 2, 2)
        self.setLayout(playout)

        # 使用信号槽机制连接触发事件
        self.btnSetting.clicked.connect(self.setCount)
        # self.btnQuery.clicked.connect(self.Query)
        self.show()

    # 日期控件的触发事件
    def onDateChanged(self, date):
        date = ("-".join("%s" % i for i in date.getDate()))  # 获取点击日期的值
        db = MyDButil()
        sql = "select * from history where date = '" + date + "';"
        result = db.fetch_all(sql)
        db.closeConn()
        if result:
            for item in result:
                print(item)
                self.detect_count = QTableWidgetItem(item[2])
                self.error_count = QTableWidgetItem(item[3])
                self.abnormal_rate = QTableWidgetItem(item[4])
                print(self.detect_count.text())
                try:
                    pass
                    self.inquiry_table.setItem(1, 1, self.detect_count)
                    self.inquiry_table.setItem(1, 4, self.error_count)
                    self.inquiry_table.setItem(2, 1, self.abnormal_rate)
                except Exception:
                    QMessageBox.information(self, "操作提示", "系统错误！", QMessageBox.Yes | QMessageBox.No)
        else:
            QMessageBox.information(self, "操作提示", "当天记录为空，重新选择！", QMessageBox.Yes | QMessageBox.No)

    # 设置个数
    def setCount(self):
        self.setui = Setting(self.countLabel)
        self.setui.show()
        # self.detcountLabel.setText(self.setui.getEdit())

    # 点击查看错误数据的触发事件
    def showErrorImg(self, index):
        print("item doubleClick")

        img = self.export_table.item(index.row(), 3).text()
        print(img)
        image = QImage(img)
        h = image.width()
        w = image.height()
        self.errorlabel.resize(h, w)
        self.errorlabel.setPixmap(QPixmap.fromImage(image))  # 加载图片
        self.errorlabel.setCursor(Qt.CrossCursor)
        self.errorlabel.setScaledContents(True)  # 图片自适应label大小
        # 图片居中
        self.errorlabel.setAlignment(Qt.AlignCenter)
        self.errorUI.raise_()
        self.errorUI.show()

    def loadErrorImage(self, fname):
        image = QImage(fname)
        h = image.width()
        w = image.height()
        print(h, w)
        self.label.resize(h, w)
        self.label.setPixmap(QPixmap.fromImage(image))  # 加载图片
        self.label.setCursor(Qt.CrossCursor)

    def Detect(self):
        return self.detecter.detect(self.model, 'Image/grab.JPG')

    def loop(self):
        # while True:
        i = 0
        while (cv2.waitKey(1) & 0xFF) != ord('q'):
            self.camera.getImagerollback(self.label, self.export_table, self.detecter, self.model)
            # self.loadErrorImage('Image/grab.JPG')  # 加载这个图片
            self.statistic_table.viewport().update()
            self.inquiry_table.viewport().update()
            self.export_table.viewport().update()
        # 关闭相机
        mvsdk.CameraUnInit(self.camera.hCamera)
        # 释放帧缓存
        mvsdk.CameraAlignFree(self.camera.pFrameBuffer)

    def setTable(self, i, time, n):
        time = QTableWidgetItem(time)
        orign_n = QTableWidgetItem(self.countLabel.text())
        det_n = QTableWidgetItem(n)
        self.export_table.setItem(i, 0, time)
        self.export_table.setItem(i, 1, orign_n)
        self.export_table.setItem(i, 2, det_n)


class com():
    def __init__(self):
        super(com, self).__init__()
        self.SerialPort = "COM3"
        self.BaudRate = 9600
        self.ser = serial.Serial(self.SerialPort, self.BaudRate, timeout=0.1)
        # self.dataopen = (0x21, 0x05, 0x00, 0x00, 0xFF, 0x00, 0x8B, 0x5A)  # 控制单个继电器
        # self.dataopen = (0x21, 0x0F, 0x00, 0x00, 0x00, 0x08, 0x01, 0x69, 0x3C, 0xA3) #控制多个继电器

        self.dataopen_waiting = (0x21, 0x05, 0x00, 0x02, 0xFF, 0x00, 0xAA, 0xAA)  # 等待信号，02路
        self.dataopen_normal = (0x21, 0x05, 0x00, 0x01, 0xFF, 0x00, 0xAA, 0xAA)  # 正常信号，01路
        self.dataopen_abnormal = (0x21, 0x05, 0x00, 0x00, 0xFF, 0x00, 0xAA, 0xAA)  # 异常信号，00路

        self.dataclose_waiting = (0x21, 0x05, 0x01, 0x02, 0x00, 0x00, 0xAA, 0xAA)
        #  21 05 01 00 00 00 AA AA 断开00路
        self.dataclose_normal = (0x21, 0x05, 0x01, 0x01, 0x00, 0x00, 0xAA, 0xAA)
        self.dataclose_abnormal = (0x21, 0x05, 0x01, 0x00, 0x00, 0x00, 0xAA, 0xAA)
        self.dataclose = (0x21, 0x06, 0x00, 0x69, 0x00, 0x01, 0x9F, 0x76)

        CountTime = 1
        print("ParameterSetting：SerialPort = {},BaudRate = {}".format(self.SerialPort, self.BaudRate))

        # Open

    def RelayOpen_waiting(self):
        self.ser.write(self.dataopen_waiting)

    def RelayOpen_abnormal(self):
        self.ser.write(self.dataopen_abnormal)

    def RelayOpen_normal(self):
        self.ser.write(self.dataopen_normal)

        # Close

    def RelayClose_waiting(self):
        self.ser.write(self.dataclose_waiting)

    def RelayClose_normal(self):
        self.ser.write(self.dataopen_normal)

    def RelayClose_abnormal(self):
        self.ser.write(self.dataclose_abnormal)

    def RelayClose(self):
        self.ser.write(self.dataclose)


# 设置界面
class Setting(QWidget):
    def __init__(self, countLabel):
        super(Setting, self).__init__()
        self.countLabel = countLabel
        self.setting_count = 10
        self.initUI()

    def initUI(self):
        self.move(300, 200)
        self.setFixedSize(350, 450)
        self.setWindowTitle('设置')
        # self.setWindowIcon(QIcon('dll/GCap.ico'))
        self.edit = QLineEdit(self)
        self.edit.setText(str(self.countLabel.text()))
        self.btnConfirm = QPushButton('确定', self)

        gbox1 = QGridLayout()
        gbox1.addWidget(self.edit, 0, 0, 1, 5)
        gbox1.addWidget(self.btnConfirm, 0, 6, 1, 2)
        self.setLayout(gbox1)
        self.btnConfirm.clicked.connect(self.getEdit)
        self.show()

    # 获取编辑框的数字
    def getEdit(self):
        self.countLabel.setText(self.edit.text())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainframe = MainFrame()
    mainframe.camera.setCam()
    mainframe.camera.startCam()
    mainframe.loop()
    app.exit(app.exec_())
