#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import cv2
import os
import rospy
from sensor_msgs.msg import Image # ROS Image format(Different from python Image)
from cv_bridge import CvBridge

fourcc = cv2.VideoWriter_fourcc(*'mp4v')

file_count = 0
file_name = "output" + str(file_count) + ".mp4"
while(os.path.exists(file_name)):
    file_count += 1
    file_name = "output" + str(file_count) + ".mp4"

width = 820
height = 616
fps = 21
#out = cv2.VideoWriter(file_name, fourcc, fps, (width,  height))  # 產生空的影片
def read_cam():
    rospy.init_node('rgb_camera', anonymous=True) # the first parameter is nodename and 'annonymous' is used to avoid when same nodename occur
    pub = rospy.Publisher('rgb', Image, queue_size=10 ) # the first parameter is topicname
    bridge = CvBridge()
    cap_string = "gst-launch-1.0 nvarguscamerasrc sensor-id=0 ! 'video/x-raw(memory:NVMM),width=800, height=600,framerate=20/1, format=NV12' ! fakesink"
    cap = cv2.VideoCapture('nvarguscamerasrc ! video/x-raw(memory:NVMM), width=(int)3280, height=(int)2464,format=(string)NV12, framerate=(fraction)21/1 ! nvvidconv ! video/x-raw, format=(string)BGRx ! videoconvert ! appsink drop=1', cv2.CAP_GSTREAMER)
    
    #cap = cv2.VideoCapture(cap_string, cv2.CAP_GSTREAMER)
    if cap.isOpened():
        #cv2.namedWindow("demo", cv2.WINDOW_AUTOSIZE)
        while True:
            ret_val, img = cap.read();
            img_resized = cv2.resize(img, (820, 616))
            img_to_rviz = bridge.cv2_to_imgmsg(img, "bgr8")
            pub.publish(img_to_rviz)
            #cv2.imshow('demo',img_resized)
            #out.write(img_resized)
            if cv2.waitKey(1) == ord('q'):      # 每一毫秒更新一次，直到按下 q 結束
                break
    else:
        print("camera open failed")

    cap.release()
    #out.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    
    read_cam()
   
