#!/usr/bin/env python3


# This is a listener


import rospy
import cv2
from sensor_msgs.msg import Image # ROS Image format(Different from python Image)
from cv_bridge import CvBridge, CvBridgeError
from message_filters import TimeSynchronizer, Subscriber
import message_filters


import numpy as np


class SyncCam:
    def __init__(self):
        rospy.init_node('synchronized_camera',  anonymous=True) # the first parameter is nodename and 'annonymous' is used to avoid when same nodename occur
        self.bridge = CvBridge()
        #rospy.Subscriber("thermal", Image, self.imageCallback) # the first parameter is
        #rospy.Subscriber("rgb", Image, self.imageCallback1) # the first parameter is topicname
        #rospy.spin() # To avoid the program shutdown and wait the event occur
        rgb = message_filters.Subscriber('rgb1', Image)
        thermal = message_filters.Subscriber('rgb2', Image)
        #syns = message_filters.ApproximateTimeSynchronizer([rgb, thermal],10,0.2)
        syns = message_filters.TimeSynchronizer([rgb, thermal],10)
        syns.registerCallback(self.multiCallback)
        rospy.spin()

    def multiCallback(self, rgb_image, thermal_image):
    
    	pub_rgb = rospy.Publisher('rgb1_sync', Image, queue_size=10 ) # the first parameter is topicname
    	pub_thermal = rospy.Publisher('rgb2_sync', Image, queue_size=10 ) # the first parameter is topicname
    	pub_rgb.publish(rgb_image)
    	pub_thermal.publish(thermal_image)
    	#image_rgb = self.bridge.imgmsg_to_cv2(rgb_image)
    	#image_thermal = self.bridge.imgmsg_to_cv2(thermal_image)

        

if __name__ == '__main__':
    result = SyncCam()


