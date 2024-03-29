#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import cv2

import threading
import numpy as np
import os

import rospy
from sensor_msgs.msg import Image # ROS Image format(Different from python Image)
from cv_bridge import CvBridge
#import subprocess

#command = "sudo service nvargus-daemon restart"
#subprocess.run(command, shell=True)

fourcc = cv2.VideoWriter_fourcc(*'mp4v')

file_count = 0
file_name = "output" + str(file_count) + ".mp4"
while(os.path.exists(file_name)):
    file_count += 1
    file_name = "output" + str(file_count) + ".mp4"
    
#print(file_name[:-4])

width = 820
height = 616
fps = 21
#out1 = cv2.VideoWriter(file_name[:-4] + '_up.mp4', fourcc, fps, (width,  height))  # 產生空的影片
#out2 = cv2.VideoWriter(file_name[:-4] + '_down.mp4', fourcc, fps, (width,  height))  # 產生空的影片
class CSI_Camera:

    def __init__(self):
        # Initialize instance variables
        # OpenCV video capture element
        self.video_capture = None
        # The last captured image from the camera
        self.frame = None
        self.grabbed = False
        # The thread where the video capture runs
        self.read_thread = None
        self.read_lock = threading.Lock()
        self.running = False

    def open(self, gstreamer_pipeline_string):
        try:
            self.video_capture = cv2.VideoCapture(
                gstreamer_pipeline_string, cv2.CAP_GSTREAMER
            )
            # Grab the first frame to start the video capturing
            self.grabbed, self.frame = self.video_capture.read()

        except RuntimeError:
            self.video_capture = None
            print("Unable to open camera")
            print("Pipeline: " + gstreamer_pipeline_string)


    def start(self):
        if self.running:
            print('Video capturing is already running')
            return None
        # create a thread to read the camera image
        if self.video_capture != None:
            self.running = True
            self.read_thread = threading.Thread(target=self.updateCamera)
            self.read_thread.start()
        return self

    def stop(self):
        self.running = False
        # Kill the thread
        self.read_thread.join()
        self.read_thread = None

    def updateCamera(self):
        # This is the thread to read images from the camera
        while self.running:
            try:
                grabbed, frame = self.video_capture.read()
                with self.read_lock:
                    self.grabbed = grabbed
                    self.frame = frame
            except RuntimeError:
                print("Could not read image from camera")
        # FIX ME - stop and cleanup thread
        # Something bad happened

    def read(self):
        with self.read_lock:
            frame = self.frame.copy()
            grabbed = self.grabbed
        return grabbed, frame

    def release(self):
        if self.video_capture != None:
            self.video_capture.release()
            self.video_capture = None
        # Now kill the thread
        if self.read_thread != None:
            self.read_thread.join()


""" 
gstreamer_pipeline returns a GStreamer pipeline for capturing from the CSI camera
Flip the image by setting the flip_method (most common values: 0 and 2)
display_width and display_height determine the size of each camera pane in the window on the screen
Default 1920x1080
"""


def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1640,
    capture_height=1232,
    display_width=1640,
    display_height=1232,
    framerate=21,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=%d ! "
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )


def run_cameras():
    window_title = "Dual CSI Cameras"
    left_camera = CSI_Camera()
    left_camera.open(
        gstreamer_pipeline(
            sensor_id=0,
            capture_width=1640,
            capture_height=1232,
            flip_method=0,
            display_width=1640,
            display_height=1232,
        )
    )
    left_camera.start()

    right_camera = CSI_Camera()
    right_camera.open(
        gstreamer_pipeline(
            sensor_id=1,
            capture_width=1640,
            capture_height=1232,
            flip_method=0,
            display_width=1640,
            display_height=1232,
        )
    )
    right_camera.start()
    
    rospy.init_node('rgb_camera', anonymous=True) # the first parameter is nodename and 'annonymous' is used to avoid when same nodename occur
    pub1 = rospy.Publisher('/rgb1', Image, queue_size=10 ) # the first parameter is topicname
    pub2 = rospy.Publisher('/rgb2', Image, queue_size=10 ) # the first parameter is topicname
    bridge = CvBridge()
    if left_camera.video_capture.isOpened() and right_camera.video_capture.isOpened():

        #cv2.namedWindow(window_title, cv2.WINDOW_AUTOSIZE)

        try:
            while True:
                _, left_image = left_camera.read()
                _, right_image = right_camera.read()
                # Use numpy to place images next to each other
                camera_images = np.hstack((left_image, right_image)) 
                # Check to see if the user closed the window
                # Under GTK+ (Jetson Default), WND_PROP_VISIBLE does not work correctly. Under Qt it does
                # GTK - Substitute WND_PROP_AUTOSIZE to detect if window has been closed by user
                '''
                if cv2.getWindowProperty(window_title, cv2.WND_PROP_AUTOSIZE) >= 0:
                    pass
                    #cv2.imshow(window_title, camera_images)
                else:
                    break
                '''
                #print(left_image.shape)
                #left_image = cv2.resize(left_image,(width,height))
                #right_image = cv2.resize(right_image,(width,height))
                img_to_rviz1 = bridge.cv2_to_imgmsg(left_image, "bgr8")
                img_to_rviz2 = bridge.cv2_to_imgmsg(right_image, "bgr8")
                time_stamp = rospy.Time.now()
                img_to_rviz1.header.stamp = time_stamp
                img_to_rviz2.header.stamp = time_stamp
                #img_to_rviz1.header.frame_id = "frame"
                #img_to_rviz2.header.frame_id = "frame"
                pub1.publish(img_to_rviz1)
                pub2.publish(img_to_rviz2)
                #out1.write(cv2.resize(left_image,(width,height)))
                #out2.write(cv2.resize(right_image,(width,height)))
                # This also acts as
                keyCode = cv2.waitKey(30) & 0xFF
                # Stop the program on the ESC key
                if keyCode == 27:
                    break
        finally:

            left_camera.stop()
            left_camera.release()
            right_camera.stop()
            right_camera.release()
        cv2.destroyAllWindows()
    else:
        print("Error: Unable to open both cameras")
        left_camera.stop()
        left_camera.release()
        right_camera.stop()
        right_camera.release()



if __name__ == "__main__":
    run_cameras()
