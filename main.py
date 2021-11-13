from resnet.model import resnet34
import platform
from Camera import mvsdk
import random
import sys
import cv2
from PyQt5.QtCore import Qt, QSize, QDateTime
from PyQt5.QtGui import QPixmap, QPalette, QImage, QFont
import json
import torch
from PIL import Image, ImageFont, ImageDraw
from torchvision import transforms
import matplotlib.pyplot as plt
import numpy as np
import os
import datetime
from PyQt5.QtWidgets import QApplication, QTableWidgetItem, QAbstractItemView, QHeaderView, QScrollArea, QWidget, \
    QLabel, QTableWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QGridLayout


# 主界面
class MainFrame(QWidget):
    def __init__(self):
        super(MainFrame, self).__init__()
        self.initUI()
        self.model = Model()
        self.cam = Camera(self.labelCam2, self.model, self.record_table, self.labelTotal_value, self.labelWarning_value,
                          self.labelResult_value)

    def initUI(self):
        # 使用pyqt5初始化UI界面
        self.setGeometry(200, 200, 3300, 1300)
        self.setWindowTitle('检测')
        # self.setWindowIcon(QIcon('...'))

        # 添加标签
        self.labelTotal = QLabel(self)  # 总包数展示文本
        self.labelWarning = QLabel(self)  # 报警个数展示文本
        self.labelResult = QLabel(self)  # 检测结果

        self.labelTotal.setText('总包数:')
        self.labelWarning.setText('|报警个数:')
        self.labelResult.setText('|检测结果:')

        self.labelTotal.setFont(QFont("Roman times", 20, QFont.Bold))
        self.labelWarning.setFont(QFont("Roman times", 20, QFont.Bold))
        self.labelResult.setFont(QFont("Roman times", 20, QFont.Bold))

        self.labelTotal_value = QLabel(self)  # 总包数
        self.labelWarning_value = QLabel(self)  # 报警个数
        self.labelResult_value = QLabel(self)  # 检测的结果

        # 设置字体，字号
        self.labelTotal_value.setFont(QFont("Roman times", 20, QFont.Bold))
        self.labelWarning_value.setFont(QFont("Roman times", 20, QFont.Bold))
        self.labelResult_value.setFont(QFont("Roman times", 20, QFont.Bold))

        # 设置初始值
        self.labelTotal_value.setText('0')
        self.labelWarning_value.setText('0')
        self.labelResult_value.setText('合格')

        # 1~4号相机的展示，对应采集正、左侧、右侧、顶（顺时针方向）
        # self.labelCam1 = QLabel(self)
        # self.QScrollArea = QScrollArea(self)
        # self.QScrollArea.setBackgroundRole(QPalette.Dark)
        # self.QScrollArea.setWidget(self.labelCam1)

        self.labelCam2 = QLabel(self)
        self.QScrollArea_Cam2 = QScrollArea(self)
        self.QScrollArea_Cam2.setBackgroundRole(QPalette.Dark)
        self.QScrollArea_Cam2.setWidget(self.labelCam2)

        # 加入表格
        self.record_table = QTableWidget(0, 3)  # 添加表格

        self.record_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)  # 设置表格为自适应的伸缩模式，即可根据窗口的大小来改变网格的大小

        # 鼠标点选时，默认选中一个单元格---QTableWidget.SelectItems
        # QTableWidget.SelectRows   鼠标点击选中一行
        # QTableWidget.SelectColumns  鼠标点击选中一列
        self.record_table.setSelectionBehavior(self.record_table.SelectRows)  # 设置选中行
        self.record_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 设置为只读表格
        # static_cast<QLineEdit *>(ui->tableWidget->cellWidget(i,9))->setEnabled(false);
        # self.table.cellWidget(i,3).setEnabled(false)
        self.record_table.setHorizontalHeaderLabels(['时间', '检测结果', '查看'])
        self.record_table.itemDoubleClicked.connect(self.showErrorImg)

        # errorUI是子界面
        self.errorUI = QWidget()
        self.errorUI.setMinimumWidth(1200)
        self.errorUI.setMinimumSize(QSize(1600, 1200))

        self.errorlabel = QLabel(self)

        QScrollArea_error = QScrollArea(self)
        QScrollArea_error.setBackgroundRole(QPalette.Dark)
        QScrollArea_error.setWidget(self.errorlabel)

        vbox_error = QVBoxLayout(self)
        vbox_error.addWidget(QScrollArea_error)
        self.errorUI.setLayout(vbox_error)
        self.errorUI.hide()

        self.winid = self.labelCam2.winId()  # 获取label对象的句柄
        self.labelCam2.setStyleSheet("QLabel{background:Dark;}")
        self.loadErrorImage('Camera/Image/grab.JPG')

        hbox_top = QHBoxLayout()
        hbox_top.addWidget(self.labelTotal)
        hbox_top.addWidget(self.labelTotal_value)
        hbox_top.addWidget(self.labelWarning)
        hbox_top.addWidget(self.labelWarning_value)
        hbox_top.addWidget(self.labelResult)
        hbox_top.addWidget(self.labelResult_value)
        hbox_top.setAlignment(Qt.AlignCenter)
        hbox_top.addStretch()
        hbox_top.setContentsMargins(106, 0, 5, 2)

        hbox_bottom = QHBoxLayout()
        hbox_bottom.addWidget(self.QScrollArea_Cam2)
        hbox_bottom.addWidget(self.record_table)

        #
        #
        # # 加入历史查询表格
        # self.inquiry_table = QTableWidget(3, 6)
        # self.inquiry_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.inquiry_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # # self.statistic_table.setHorizontalHeaderLabels(['检测数量', '###', '包', '异常数量', '###', '包'])
        # self.inquiry_table.verticalHeader().setVisible(False)  # 隐藏垂直表头
        # self.inquiry_table.horizontalHeader().setVisible(False)  # 隐藏水平表头
        # # setSpan(row, col, 从当前行向下合并的行数, 向右要合并的列数）
        # inquiry_table_item1 = QTableWidgetItem("历史数据(日期选择)")
        # inquiry_table_item1.setTextAlignment(Qt.AlignCenter)  # 设置居中
        # inquiry_table_item1.setFont(QFont("Roman times", 20, QFont.Bold))
        #
        # inquiry_table_item2 = QTableWidgetItem("检测数量")
        # inquiry_table_item2.setTextAlignment(Qt.AlignCenter)  # 设置居中
        # inquiry_table_item2.setFont(QFont("Roman times", 13, QFont.Bold))
        #
        # inquiry_table_item3 = QTableWidgetItem("###")
        # inquiry_table_item3.setTextAlignment(Qt.AlignCenter)  # 设置居中
        # inquiry_table_item3.setFont(QFont("Roman times", 13, QFont.Bold))
        #
        # inquiry_table_item4 = QTableWidgetItem("包")
        # inquiry_table_item4.setTextAlignment(Qt.AlignCenter)  # 设置居中
        # inquiry_table_item4.setFont(QFont("Roman times", 13, QFont.Bold))
        #
        # inquiry_table_item5 = QTableWidgetItem("异常数量")
        # inquiry_table_item5.setTextAlignment(Qt.AlignCenter)  # 设置居中
        # inquiry_table_item5.setFont(QFont("Roman times", 13, QFont.Bold))
        #
        # inquiry_table_item6 = QTableWidgetItem("###")
        # inquiry_table_item6.setTextAlignment(Qt.AlignCenter)  # 设置居中
        # inquiry_table_item6.setFont(QFont("Roman times", 13, QFont.Bold))
        #
        # inquiry_table_item7 = QTableWidgetItem("包")
        # inquiry_table_item7.setTextAlignment(Qt.AlignCenter)  # 设置居中
        # inquiry_table_item7.setFont(QFont("Roman times", 13, QFont.Bold))
        #
        # inquiry_table_item8 = QTableWidgetItem("异常率")
        # inquiry_table_item8.setTextAlignment(Qt.AlignCenter)  # 设置居中
        # inquiry_table_item8.setFont(QFont("Roman times", 13, QFont.Bold))
        #
        # inquiry_table_item9 = QTableWidgetItem("###.##")
        # inquiry_table_item9.setTextAlignment(Qt.AlignCenter)  # 设置居中
        # inquiry_table_item9.setFont(QFont("Roman times", 13, QFont.Bold))
        #
        # inquiry_table_item10 = QTableWidgetItem("%")
        # inquiry_table_item10.setTextAlignment(Qt.AlignCenter)  # 设置居左
        # inquiry_table_item10.setFont(QFont("Roman times", 13, QFont.Bold))
        #
        # # 添加一个弹出的日期选择，设置默认值为当前日期,显示格式为年月日。
        # self.btnDate = QDateTimeEdit()
        # self.btnDate.setDateTime(QDateTime.currentDateTime())
        # self.btnDate.setDisplayFormat("yyyy-MM-dd")
        # self.btnDate.setCalendarPopup(True)
        # self.inquiry_table.setCellWidget(0, 5, self.btnDate)
        #
        # self.btnDate.dateChanged.connect(self.onDateChanged)
        #
        # self.inquiry_table.setItem(0, 0, inquiry_table_item1)
        # self.inquiry_table.setSpan(0, 0, 1, 5)
        # self.inquiry_table.setItem(1, 0, inquiry_table_item2)
        # self.inquiry_table.setItem(1, 1, inquiry_table_item3)
        # self.inquiry_table.setItem(1, 2, inquiry_table_item4)
        # self.inquiry_table.setItem(1, 3, inquiry_table_item5)
        # self.inquiry_table.setItem(1, 4, inquiry_table_item6)
        # self.inquiry_table.setItem(1, 5, inquiry_table_item7)
        # self.inquiry_table.setItem(2, 0, inquiry_table_item8)
        # self.inquiry_table.setItem(2, 1, inquiry_table_item9)
        # self.inquiry_table.setItem(2, 2, inquiry_table_item10)
        # self.inquiry_table.setSpan(1, 3, 2, 1)
        # self.inquiry_table.setSpan(1, 4, 2, 1)
        # self.inquiry_table.setSpan(1, 5, 2, 1)
        #
        # # 加入统计表格
        # self.statistic_table = QTableWidget(3, 6)
        # self.statistic_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.statistic_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # # self.statistic_table.setHorizontalHeaderLabels(['检测数量', '###', '包', '异常数量', '###', '包'])
        # self.statistic_table.verticalHeader().setVisible(False)  # 隐藏垂直表头
        # self.statistic_table.horizontalHeader().setVisible(False)  # 隐藏水平表头
        # # setSpan(row, col, 从当前行向下合并的行数, 向右要合并的列数）
        # statistic_table_item1 = QTableWidgetItem("效率统计")
        # statistic_table_item1.setTextAlignment(Qt.AlignCenter)  # 设置居中
        # statistic_table_item1.setFont(QFont("Roman times", 20, QFont.Bold))
        #
        # statistic_table_item2 = QTableWidgetItem("当班检测")
        # statistic_table_item2.setTextAlignment(Qt.AlignCenter)  # 设置居中
        # statistic_table_item2.setFont(QFont("Roman times", 13, QFont.Bold))
        #
        # statistic_table_item3 = QTableWidgetItem("###")
        # statistic_table_item3.setTextAlignment(Qt.AlignCenter)  # 设置居中
        # statistic_table_item3.setFont(QFont("Roman times", 13, QFont.Bold))
        #
        # statistic_table_item4 = QTableWidgetItem("包")
        # statistic_table_item4.setTextAlignment(Qt.AlignCenter)  # 设置居中
        # statistic_table_item4.setFont(QFont("Roman times", 13, QFont.Bold))
        #
        # statistic_table_item5 = QTableWidgetItem("异常数量")
        # statistic_table_item5.setTextAlignment(Qt.AlignCenter)  # 设置居中
        # statistic_table_item5.setFont(QFont("Roman times", 13, QFont.Bold))
        #
        # statistic_table_item6 = QTableWidgetItem("###")
        # statistic_table_item6.setTextAlignment(Qt.AlignCenter)  # 设置居中
        # statistic_table_item6.setFont(QFont("Roman times", 13, QFont.Bold))
        #
        # statistic_table_item7 = QTableWidgetItem("包")
        # statistic_table_item7.setTextAlignment(Qt.AlignCenter)  # 设置居中
        # statistic_table_item7.setFont(QFont("Roman times", 13, QFont.Bold))
        #
        # statistic_table_item8 = QTableWidgetItem("异常率")
        # statistic_table_item8.setTextAlignment(Qt.AlignCenter)  # 设置居中
        # statistic_table_item8.setFont(QFont("Roman times", 13, QFont.Bold))
        #
        # statistic_table_item9 = QTableWidgetItem("###.##")
        # statistic_table_item9.setTextAlignment(Qt.AlignCenter)  # 设置居中
        # statistic_table_item9.setFont(QFont("Roman times", 13, QFont.Bold))
        #
        # statistic_table_item10 = QTableWidgetItem("%")
        # statistic_table_item10.setTextAlignment(Qt.AlignCenter)  # 设置居左
        # statistic_table_item10.setFont(QFont("Roman times", 13, QFont.Bold))
        #
        # self.statistic_table.setItem(0, 0, statistic_table_item1)
        # self.statistic_table.setSpan(0, 0, 1, 6)
        # self.statistic_table.setItem(1, 0, statistic_table_item2)
        # self.statistic_table.setItem(1, 1, statistic_table_item3)
        # self.statistic_table.setItem(1, 2, statistic_table_item4)
        # self.statistic_table.setItem(1, 3, statistic_table_item5)
        # self.statistic_table.setItem(1, 4, statistic_table_item6)
        # self.statistic_table.setItem(1, 5, statistic_table_item7)
        # self.statistic_table.setItem(2, 0, statistic_table_item8)
        # self.statistic_table.setItem(2, 1, statistic_table_item9)
        # self.statistic_table.setItem(2, 2, statistic_table_item10)
        # self.statistic_table.setSpan(1, 3, 2, 1)
        # self.statistic_table.setSpan(1, 4, 2, 1)
        # self.statistic_table.setSpan(1, 5, 2, 1)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox_top)
        vbox.addLayout(hbox_bottom)

        # playout = QGridLayout()
        #
        # # 第0行第0列开始，占2行2列
        # playout.addLayout(hbox_top, 0, 0, 1, 2)
        # # 第3行第0列开始，占2行2列
        # playout.addLayout(vbox_left, 3, 0, 2, 2)
        # playout.addLayout(vbox_right, 3, 3, 2, 2)
        self.setLayout(vbox)

        # 使用信号槽机制连接触发事件
        # self.btnSetting.clicked.connect(self.setCount)
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

        img = self.record_table.item(index.row(), 2).text()
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
        self.labelCam2.resize(h, w)
        self.labelCam2.setPixmap(QPixmap.fromImage(image))  # 加载图片
        self.labelCam2.setCursor(Qt.CrossCursor)

    def Detect(self):
        return self.detecter.detect(self.model, 'Image/grab.JPG')

    def loop(self):
        # while True:
        i = 0
        while (cv2.waitKey(1) & 0xFF) != ord('q'):
            self.cam.getImagerollback(self.labelCam2, self.model, self.record_table)
            # self.loadErrorImage('Image/grab.JPG')  # 加载这个图片
            self.record_table.viewport().update()

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


class Camera:

    def __init__(self, camlabel2, model, record_table, labelTotal_value, labelWarning_value, labelResult_value):
        super(Camera, self).__init__()
        self.camlabel2 = camlabel2
        self.model = model
        self.record_table = record_table
        self.labelTotal_value = labelTotal_value
        self.labelWarning_value = labelWarning_value
        self.labelResult_value = labelResult_value

        # 错误记录的个数
        self.row = 0
        # 总包个数
        self.totalcount = 0
        # 缺陷包个数
        self.defectcount = 0

        self.quit = False
        self.monoCamera = None
        self.hCamera = None
        self.cap = None
        self.pFrameBuffer = None
        self.hCamera = self.openCam()

    # 打开相机,返回一个hcamera
    def openCam(self):
        # 枚举相机
        DevList = mvsdk.CameraEnumerateDevice()
        nDev = len(DevList)
        if nDev < 1:
            print("No camera was found!")
            return

        for i, DevInfo in enumerate(DevList):
            print("{}: {} {}".format(i, DevInfo.GetFriendlyName(), DevInfo.GetPortType()))
        i = 0 if nDev == 1 else int(input("Select camera: "))
        DevInfo = DevList[i]
        print(DevInfo)

        # 打开相机
        hCamera = 0
        try:
            hCamera = mvsdk.CameraInit(DevInfo, -1, -1)
        except mvsdk.CameraException as e:
            print("CameraInit Failed({}): {}".format(e.error_code, e.message))
            return

        # 获取相机特性描述
        self.cap = mvsdk.CameraGetCapability(hCamera)

        # 判断是黑白相机还是彩色相机
        self.monoCamera = (self.cap.sIspCapacity.bMonoSensor != 0)

        # 黑白相机让ISP直接输出MONO数据，而不是扩展成R=G=B的24位灰度
        if self.monoCamera:
            mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)
        else:
            mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_BGR8)
        return hCamera

    # 设置相机
    def setCam(self):
        # 相机模式切换成硬触发，
        # 参数
        # [in] hCamera 相机的句柄。
        # [in] iModeSel 模式选择索引号。0表示连续采集模式；1表示软件触发模式；2表示硬件触发模式。
        # 返回成功返回 CAMERA_STATUS_SUCCESS(0)。否则返回非0值的错误码, 请参考 CameraStatus.h 中错误码的定义。
        mvsdk.CameraSetTriggerMode(self.hCamera, 2)

        # 硬件外触发的信号种类
        # EXT_TRIG_LEADING_EDGE
        # 上升沿触发，默认为该方式
        #
        # EXT_TRIG_TRAILING_EDGE
        # 下降沿触发

        # EXT_TRIG_DOUBLE_EDGE
        # 双边沿触发

        # EXT_TRIG_HIGH_LEVEL
        # 高电平触发,电平宽度决定曝光时间，仅部分型号的相机支持电平触发方式。
        #
        # EXT_TRIG_LOW_LEVEL
        # 低电平触发
        #

        mvsdk.CameraSetExtTrigSignalType(self.hCamera, 'EXT_TRIG_LOW_LEVEL')
        # 设置触发抓取一帧
        mvsdk.CameraSetTriggerCount(self.hCamera, 1)

        # 设置增益值为6
        mvsdk.CameraSetAnalogGain(self.hCamera, 6)

        # 手动曝光，曝光时间2ms(2 * 1000)
        mvsdk.CameraSetAeState(self.hCamera, False)
        mvsdk.CameraSetExposureTime(self.hCamera, 10 * 1000)

    # 相机SDK启动工作
    def startCam(self):
        # 让SDK内部取图线程开始工作
        mvsdk.CameraPlay(self.hCamera)
        try:
            # 计算RGB buffer所需的大小，这里直接按照相机的最大分辨率来分配
            FrameBufferSize = self.cap.sResolutionRange.iWidthMax * self.cap.sResolutionRange.iHeightMax * (
                1 if self.monoCamera else 3)

            print("这是看尺寸的数据类型", self.cap.sResolutionRange.iWidthMax, self.cap.sResolutionRange.iHeightMax,
                  FrameBufferSize)

            # FrameBufferSize = 1080 * 1440 * 1

            # 分配RGB buffer，用来存放ISP输出的图像
            # 备注：从相机传输到PC端的是RAW数据，在PC端通过软件ISP转为RGB数据（如果是黑白相机就不需要转换格式，但是ISP还有其它处理，所以也需要分配这个buffer）
            self.pFrameBuffer = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)
        except mvsdk.CameraException as e:
            print("CameraAlignMalloc failed({}): {}".format(e.error_code, e.message))

    def getImage(self):
        pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, -1)
        mvsdk.CameraImageProcess(self.hCamera, pRawData, self.pFrameBuffer, FrameHead)
        mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)
        try:
            # 此时图片已经存储在pFrameBuffer中，对于彩色相机pFrameBuffer=RGB数据，黑白相机pFrameBuffer=8位灰度数据
            # 把图片保存到硬盘文件中"+str(i)+"
            status = mvsdk.CameraSaveImage(self.hCamera, "Image/grab", self.pFrameBuffer, FrameHead,
                                           mvsdk.FILE_BMP, 100)
            if status == mvsdk.CAMERA_STATUS_SUCCESS:
                print("Save image successfully. image_size = {}X{}".format(FrameHead.iWidth, FrameHead.iHeight))
            else:
                print("Save image failed. err={}".format(status))

        except mvsdk.CameraException as e:
            print("CameraGetImageBuffer failed({}): {}".format(e.error_code, e.message))
        return status
        # # 关闭相机
        # mvsdk.CameraUnInit(self.hCamera)

        # 释放帧缓存
        # mvsdk.CameraAlignFree(self.pFrameBuffer)

    def getImagerollback(self, camlabel2, model, record_table):
        # 设置采集回调函数
        mvsdk.CameraSetCallbackFunction(self.hCamera, self.GrabCallback, 0)

    @mvsdk.method(mvsdk.CAMERA_SNAP_PROC)
    def GrabCallback(self, hCamera, pRawData, pFrameHead, pContext):

        # self.totalCount = self.totalCount + 1
        FrameHead = pFrameHead[0]
        pFrameBuffer = self.pFrameBuffer

        mvsdk.CameraImageProcess(self.hCamera, pRawData, pFrameBuffer, FrameHead)
        mvsdk.CameraReleaseImageBuffer(hCamera, pRawData)

        # windows下取到的图像数据是上下颠倒的，以BMP格式存放。转换成opencv则需要上下翻转成正的
        # linux下直接输出正的，不需要上下翻转
        if platform.system() == "Windows":
            mvsdk.CameraFlipFrameBuffer(pFrameBuffer, FrameHead, 1)

        # 此时图片已经存储在pFrameBuffer中，对于彩色相机pFrameBuffer=RGB数据，黑白相机pFrameBuffer=8位灰度数据
        # 把pFrameBuffer转换成opencv的图像格式以进行后续算法处理
        status = mvsdk.CameraSaveImage(self.hCamera, "Camera/Image/grab.JPG", self.pFrameBuffer,
                                       FrameHead, mvsdk.FILE_JPG, 100)

        # status = mvsdk.CameraSaveImage(self.hCamera, "E:/5.15采集/grab" + str(random.random()), self.pFrameBuffer,
        #                                FrameHead, mvsdk.FILE_JPG, 100)
        if status == mvsdk.CAMERA_STATUS_SUCCESS:
            print("Save image successfully. image_size = {}X{}".format(FrameHead.iWidth, FrameHead.iHeight))
        else:
            print("Save image failed. err={}".format(status))

        image = QImage('Camera/Image/grab.JPG')

        h = image.width()
        w = image.height()

        print("执行", h, w)

        self.camlabel2.resize(h, w)
        self.camlabel2.setPixmap(QPixmap.fromImage(image))  # 加载图片
        self.camlabel2.setCursor(Qt.CrossCursor)
        self.camlabel2.setScaledContents(True)  # 图片自适应label大小

        result, possible = self.model.predict()
        print("分类结果：", result, "置信度：", possible)
        self.totalcount = self.totalcount + 1
        self.labelTotal_value.setText(str(self.totalcount))
        self.labelResult_value.setText(result)
        """
        if result！=“合格”：
            保存此条记录，记录时间、检测结果、保存路径
            更新表格
        """

        if result != '侧面合格' and result != '顶面合格' and result != '正面合格':
            self.defectcount += 1
            self.labelWarning_value.setText(str(self.defectcount))

            img = cv2.imread('Camera/Image/grab.JPG')
            file_path = '11.12/error' + str(random.random()) + '.JPG'
            cv2.imwrite(file_path, img)

            # 获取系统当前时间
            time = QDateTime.currentDateTime()
            # 设置系统时间的显示格式
            now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            time = QTableWidgetItem(now_time)
            result = QTableWidgetItem(result)
            path = QTableWidgetItem(str(file_path))

            self.record_table.insertRow(self.row)

            self.record_table.setItem(self.row, 0, time)
            self.record_table.setItem(self.row, 1, result)
            self.record_table.setItem(self.row, 2, path)
            self.row = self.row + 1


        else:
            img = cv2.imread('Camera/Image/grab.JPG')
            file_path = '11.12hege/hege' + str(random.random()) + '.JPG'
            cv2.imwrite(file_path, img)
        # self.detcountLabel.setText(str(n))
        # self.totalLabel.setText(str(self.totalCount))
        #
        # if n == 0:
        #     self.com.RelayOpen_waiting()
        #
        # # 设置个数不符合或者不为0的时候，报警！
        # if self.countLabel.text() != str(n) and n != 0:
        #     # img = cv2.imread('../Image/grab.JPG')
        #     # cv2.imwrite('E:/5.15采集/error' + str(random.random()) + '.JPG', img, 100)
        #     I = Image.open('../Image/grab.JPG')
        #     file_name = 'E:/5.15采集/error' + str(random.random()) + '.JPG'
        #     I.save(file_name)
        #
        #     self.errorCount = self.errorCount + 1
        #     now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        #     time = QTableWidgetItem(now_time)
        #     orign_n = QTableWidgetItem(self.countLabel.text())
        #     det_n = QTableWidgetItem(str(n))
        #     path = QTableWidgetItem(str(file_name))
        #     # 设置报警个数标签
        #     self.alertLabel.setText(str(self.errorCount))
        #
        #     self.export_table.insertRow(self.i)
        #     self.export_table.setItem(self.i, 0, time)
        #     self.export_table.setItem(self.i, 1, orign_n)
        #     self.export_table.setItem(self.i, 2, det_n)
        #     self.export_table.setItem(self.i, 3, path)
        #
        #     self.i = self.i + 1
        #     self.com.RelayOpen_abnormal()
        #
        # else:
        #     self.com.RelayOpen_normal()
        #
        # print("执行完了detect")
        # totaldetect_count = QTableWidgetItem(str(self.totalCount))
        # abnormal_count = QTableWidgetItem(str(self.i))
        # abnormal_rate = QTableWidgetItem(str((self.i / self.totalCount) * 100))
        # self.statistic_table.setItem(1, 1, totaldetect_count)
        # self.statistic_table.setItem(1, 4, abnormal_count)
        # self.statistic_table.setItem(2, 1, abnormal_rate)
        #
        # # 将记录更新到数据库
        # now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # temp = datetime.datetime.now().strftime('%Y-%m-%d')
        # trigger_time1 = datetime.datetime.strptime("" + temp + " 12:00:00", "%Y-%m-%d %H:%M:%S")
        # trigger_time2 = datetime.datetime.strptime("" + temp + " 23:59:59", "%Y-%m-%d %H:%M:%S")
        # trigger_time1 = trigger_time1.strftime('%Y-%m-%d %H:%M:%S')
        # trigger_time2 = trigger_time2.strftime('%Y-%m-%d %H:%M:%S')
        # if trigger_time1 <= now_time <= trigger_time2:
        #     print("触发保存当班记录事件")
        #     try:
        #         db = MyDButil()
        #         sql = "select * from history where date = '" + temp + "';"
        #         print(sql)
        #         result = db.fetch_all(sql)
        #         print(len(result))
        #         if len(result) > 0:
        #             sql = "update history set detect_count='" + totaldetect_count.text() + "', error_count='" + abnormal_count.text() + "',abnormal_rate='" + abnormal_rate.text() + "' where date='" + temp + "'; "
        #             print(sql)
        #             db.update(sql)
        #         else:
        #             sql = "insert into history(date,detect_count,error_count,abnormal_rate) values ('" + temp + "','" + totaldetect_count.text() + "','" + abnormal_count.text() + "','" + abnormal_rate.text() + "');"
        #             print(sql)
        #             db.update(sql)
        #     except Exception as data:
        #         print(data)
        #         msgBox = QMessageBox(QMessageBox.Warning, '提示', '数据库保存结果失败')
        #         msgBox.exec()
        #     db.closeConn()
        # else:
        #     print("没触发")


class Model:
    def __init__(self):
        # device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        self.device = torch.device('cpu')

        # create model
        self.model = resnet34(num_classes=6).to(self.device)

        # load model weights
        weights_path = "resnet/2021.11.11_resNet34.pth"
        assert os.path.exists(weights_path), "file: '{}' dose not exist.".format(weights_path)
        self.model.load_state_dict(torch.load(weights_path, map_location=self.device))

    def predict(self):
        # read class_indict
        json_path = 'resnet/class_indices.json'
        assert os.path.exists(json_path), "file: '{}' dose not exist.".format(json_path)

        json_file = open(json_path, "r")
        class_indict = json.load(json_file)

        # 输入模型的图片
        img_path = "Camera/Image/grab.JPG"
        data_transform = transforms.Compose(
            [transforms.Resize(256),
             transforms.CenterCrop(224),
             transforms.ToTensor(),
             transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

        assert os.path.exists(img_path), "file: '{}' dose not exist.".format(img_path)
        img = Image.open(img_path)

        # [N, C, H, W]
        img = data_transform(img)
        # expand batch dimension
        img = torch.unsqueeze(img, dim=0)

        self.model.eval()

        with torch.no_grad():
            # predict class
            output = torch.squeeze(self.model(img.to(self.device))).cpu()
            predict = torch.softmax(output, dim=0)
            predict_cla = torch.argmax(predict).numpy()

        print_res = "class: {}   prob: {:.3}".format(class_indict[str(predict_cla)],
                                                     predict[predict_cla].numpy())
        return class_indict[str(predict_cla)], predict[predict_cla].numpy()


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
    mainframe.cam.setCam()
    mainframe.cam.startCam()
    mainframe.loop()

    app.exit(app.exec_())
