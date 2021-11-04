# coding=utf-8
import os
import random
import sys
import time
import datetime

from PIL import Image
from PyQt5.QtCore import Qt
import cv2
import numpy as np

from PyQt5.QtCore import QThread
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox

import mvsdk
import platform

from DateBase.DButil import MyDButil


class Camera:

    def __init__(self, label, export_table, statistic_table, detecter, model, countLabel, detcountLabel, totalLabel,
                 alertLabel, com):
        super(Camera, self).__init__()
        self.i = 0
        self.quit = False
        self.monoCamera = None
        self.hCamera = None
        self.cap = None
        self.pFrameBuffer = None
        self.hCamera = self.openCam()

        self.errorCount = 0
        self.totalCount = 0
        self.label = label
        self.export_table = export_table
        self.statistic_table = statistic_table
        self.countLabel = countLabel
        self.detcountLabel = detcountLabel
        self.detecter = detecter
        self.model = model
        self.totalLabel = totalLabel
        self.alertLabel = alertLabel
        self.com = com

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

    def getImagerollback(self, label, table, detecter, model):
        # 设置采集回调函数
        mvsdk.CameraSetCallbackFunction(self.hCamera, self.GrabCallback, 0)

    @mvsdk.method(mvsdk.CAMERA_SNAP_PROC)
    def GrabCallback(self, hCamera, pRawData, pFrameHead, pContext):
        global db
        self.com.RelayClose()
        self.totalCount = self.totalCount + 1
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
        status = mvsdk.CameraSaveImage(self.hCamera, "../Image/grab", self.pFrameBuffer,
                                       FrameHead, mvsdk.FILE_JPG, 100)

        # status = mvsdk.CameraSaveImage(self.hCamera, "E:/5.15采集/grab" + str(random.random()), self.pFrameBuffer,
        #                                FrameHead, mvsdk.FILE_JPG, 100)
        if status == mvsdk.CAMERA_STATUS_SUCCESS:
            print("Save image successfully. image_size = {}X{}".format(FrameHead.iWidth, FrameHead.iHeight))
        else:
            print("Save image failed. err={}".format(status))

        image = QImage('../Image/grab.JPG')
        h = image.width()
        w = image.height()

        print("执行", h, w)

        self.label.resize(h, w)

        self.label.setPixmap(QPixmap.fromImage(image))  # 加载图片
        self.label.setCursor(Qt.CrossCursor)
        self.label.setScaledContents(True)  # 图片自适应label大小
        n = self.detecter.detect(self.model, '../Image/grab.JPG')
        print("检测的n", n)

        self.detcountLabel.setText(str(n))
        self.totalLabel.setText(str(self.totalCount))

        if n == 0:
            self.com.RelayOpen_waiting()

        # 设置个数不符合或者不为0的时候，报警！
        if self.countLabel.text() != str(n) and n != 0:
            # img = cv2.imread('../Image/grab.JPG')
            # cv2.imwrite('E:/5.15采集/error' + str(random.random()) + '.JPG', img, 100)
            I = Image.open('../Image/grab.JPG')
            file_name = 'E:/5.15采集/error' + str(random.random()) + '.JPG'
            I.save(file_name)

            self.errorCount = self.errorCount + 1
            now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            time = QTableWidgetItem(now_time)
            orign_n = QTableWidgetItem(self.countLabel.text())
            det_n = QTableWidgetItem(str(n))
            path = QTableWidgetItem(str(file_name))
            # 设置报警个数标签
            self.alertLabel.setText(str(self.errorCount))

            self.export_table.insertRow(self.i)
            self.export_table.setItem(self.i, 0, time)
            self.export_table.setItem(self.i, 1, orign_n)
            self.export_table.setItem(self.i, 2, det_n)
            self.export_table.setItem(self.i, 3, path)

            self.i = self.i + 1
            self.com.RelayOpen_abnormal()

        else:
            self.com.RelayOpen_normal()

        print("执行完了detect")
        totaldetect_count = QTableWidgetItem(str(self.totalCount))
        abnormal_count = QTableWidgetItem(str(self.i))
        abnormal_rate = QTableWidgetItem(str((self.i / self.totalCount) * 100))
        self.statistic_table.setItem(1, 1, totaldetect_count)
        self.statistic_table.setItem(1, 4, abnormal_count)
        self.statistic_table.setItem(2, 1, abnormal_rate)

        # 将记录更新到数据库
        now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        temp = datetime.datetime.now().strftime('%Y-%m-%d')
        trigger_time1 = datetime.datetime.strptime("" + temp + " 12:00:00", "%Y-%m-%d %H:%M:%S")
        trigger_time2 = datetime.datetime.strptime("" + temp + " 23:59:59", "%Y-%m-%d %H:%M:%S")
        trigger_time1 = trigger_time1.strftime('%Y-%m-%d %H:%M:%S')
        trigger_time2 = trigger_time2.strftime('%Y-%m-%d %H:%M:%S')
        if trigger_time1 <= now_time <= trigger_time2:
            print("触发保存当班记录事件")
            try:
                db = MyDButil()
                sql = "select * from history where date = '" + temp + "';"
                print(sql)
                result = db.fetch_all(sql)
                print(len(result))
                if len(result) > 0:
                    sql = "update history set detect_count='" + totaldetect_count.text() + "', error_count='" + abnormal_count.text() + "',abnormal_rate='" + abnormal_rate.text() + "' where date='" + temp + "'; "
                    print(sql)
                    db.update(sql)
                else:
                    sql = "insert into history(date,detect_count,error_count,abnormal_rate) values ('" + temp + "','" + totaldetect_count.text() + "','" + abnormal_count.text() + "','" + abnormal_rate.text() + "');"
                    print(sql)
                    db.update(sql)
            except Exception as data:
                print(data)
                msgBox = QMessageBox(QMessageBox.Warning, '提示', '数据库保存结果失败')
                msgBox.exec()
            db.closeConn()
        else:
            print("没触发")

#
# if __name__ == '__main__':
#     camera = Camera()
#     camera.setCam()
#     camera.startCam()
#     camera.mainframe.loop()
#     # camera.main_loop()
#     # camera.getImage()
#     # camera.getImagerollback()
