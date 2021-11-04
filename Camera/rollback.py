# coding=utf-8
import os
import sys
import time

import cv2
import numpy as np
import mvsdk
import platform


class Camera():
    def __init__(self):
        super(Camera, self).__init__()
        self.monoCamera = None
        self.hCamera = None
        self.cap = None
        self.pFrameBuffer = None
        self.hCamera = self.openCam()
        self.quit = False

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

        mvsdk.CameraSetExtTrigSignalType(self.hCamera, 'EXT_TRIG_LEADING_EDGE')
        # 设置触发抓取一帧
        mvsdk.CameraSetTriggerCount(self.hCamera, 1)

        # 手动曝光，曝光时间30ms(30 * 1000)
        mvsdk.CameraSetAeState(self.hCamera, True)
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

    def getImage1(self):
        # 设置采集回调函数
        self.quit = False
        mvsdk.CameraSetCallbackFunction(self.hCamera, self.GrabCallback, 0)
        # 等待退出
        while not self.quit:
            # time.sleep(0.1)
            pass

    def getImage(self):
        pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, 4294967295)
        mvsdk.CameraImageProcess(self.hCamera, pRawData, self.pFrameBuffer, FrameHead)
        mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)
        try:
            # 此时图片已经存储在pFrameBuffer中，对于彩色相机pFrameBuffer=RGB数据，黑白相机pFrameBuffer=8位灰度数据
            # 把图片保存到硬盘文件中"+str(i)+"
            status = mvsdk.CameraSaveImage(self.hCamera, "Image/grab", self.pFrameBuffer, FrameHead,
                                           mvsdk.FILE_JPG, 100)
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

    def main_loop(self):
        i = 0
        while (cv2.waitKey(1) & 0xFF) != ord('q'):
            i = i + 1
            start = time.time()
            pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, -1)
            mvsdk.CameraImageProcess(self.hCamera, pRawData, self.pFrameBuffer, FrameHead)
            mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)
            try:
                # 此时图片已经存储在pFrameBuffer中，对于彩色相机pFrameBuffer=RGB数据，黑白相机pFrameBuffer=8位灰度数据
                # 该示例中我们只是把图片保存到硬盘文件中"+str(i)+"
                # status = mvsdk.CameraSaveImage(self.hCamera, "../Image/grab" + str(i) + "", self.pFrameBuffer, FrameHead,
                #                                mvsdk.FILE_JPG, 100)

                status = mvsdk.CameraSaveImage(self.hCamera, "E:/5.15采集/grab" + str(i) + "", self.pFrameBuffer,
                                               FrameHead,
                                               mvsdk.FILE_JPG, 100)
                end = time.time()
                print("拍照时间", end - start)
                if status == mvsdk.CAMERA_STATUS_SUCCESS:
                    print("Save image successfully. image_size = {}X{}".format(FrameHead.iWidth, FrameHead.iHeight))
                else:
                    print("Save image failed. err={}".format(status))

            except mvsdk.CameraException as e:
                print("CameraGetImageBuffer failed({}): {}".format(e.error_code, e.message))

        # 关闭相机
        stat = mvsdk.CameraUnInit(self.hCamera)
        print(stat)
        # 释放帧缓存
        mvsdk.CameraAlignFree(self.pFrameBuffer)

    @mvsdk.method(mvsdk.CAMERA_SNAP_PROC)
    def GrabCallback(self, hCamera, pRawData, pFrameHead, pContext):
        # pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, 4294967295)
        # mvsdk.CameraImageProcess(self.hCamera, pRawData, self.pFrameBuffer, FrameHead)
        # mvsdk.CameraReleaseImageBuffer(hCamera, pRawData)
        # print("进入")
        # try:
        #     # 此时图片已经存储在pFrameBuffer中，对于彩色相机pFrameBuffer=RGB数据，黑白相机pFrameBuffer=8位灰度数据
        #     # 把图片保存到硬盘文件中"+str(i)+"
        #     status = mvsdk.CameraSaveImage(hCamera, "Image/grab", self.pFrameBuffer, FrameHead,
        #                                    mvsdk.FILE_JPG, 100)
        #     if status == mvsdk.CAMERA_STATUS_SUCCESS:
        #         print("Save image successfully. image_size = {}X{}".format(FrameHead.iWidth, FrameHead.iHeight))
        #     else:
        #         print("Save image failed. err={}".format(status))
        #
        # except mvsdk.CameraException as e:
        #     print("CameraGetImageBuffer failed({}): {}".format(e.error_code, e.message))
        # if (cv2.waitKey(1) & 0xFF) == ord('q'):
        #     self.quit = True

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
        status = mvsdk.CameraSaveImage(self.hCamera, "Image/grab", self.pFrameBuffer, FrameHead, mvsdk.FILE_JPG, 100)
        if status == mvsdk.CAMERA_STATUS_SUCCESS:
            print("Save image successfully. image_size = {}X{}".format(FrameHead.iWidth, FrameHead.iHeight))
        else:
            print("Save image failed. err={}".format(status))

        # frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(pFrameBuffer)
        # frame = np.frombuffer(frame_data, dtype=np.uint8)
        # frame = frame.reshape(
        #     (FrameHead.iHeight, FrameHead.iWidth, 1 if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8 else 3))
        #
        # frame = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_LINEAR)
        # cv2.imshow("Press q to end", frame)
        # if (cv2.waitKey(1) & 0xFF) == ord('q'):
        #     self.quit = True


if __name__ == '__main__':
    camera = Camera()
    camera.setCam()
    camera.startCam()
    camera.getImage1()
    # camera.getImage()
