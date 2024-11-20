#!/usr/bin/env python3

import rospy
import cv2

from sensor_msgs.msg import CompressedImage
from detection_msgs.msg import BoundingBox, BoundingBoxes
from cv_bridge import CvBridge
from ultralytics import YOLO


class YOLOInferenceNode:
    def __init__(self):
        rospy.init_node("yolo_inference_node", anonymous=True)

        self.bridge = CvBridge()
        self.image_topic = "/main_camera/image_raw/compressed"
        self.bbox_pub_topic = "/detected_bboxes"
        self.bbox_msg = BoundingBoxes()
        self.bbox_pub = rospy.Publisher(
            self.bbox_pub_topic, BoundingBoxes, queue_size=10
        )
        rospy.Subscriber(self.image_topic, CompressedImage, self.image_callback)

        PATH = "model/best.pt"
        self.model = YOLO(PATH)

    def image_callback(self, img_msg):
        cv_image = self.bridge.compressed_imgmsg_to_cv2(
            img_msg, desired_encoding="bgr8"
        )

        results = self.model(cv_image, device="cpu")[0]

        self.bbox_msg = BoundingBoxes()
        self.bbox_msg.header = img_msg.header

        for result in results.boxes:
            x_min, y_min, x_max, y_max = map(int, result.xyxy[0].tolist())

            # 신뢰도
            confidence = float(result.conf[0])

            # Class ID: int
            class_id = int(result.cls[0])

            # Class Name: str
            class_name = self.model.names[class_id]

            if class_name == "en" or class_name == "ent":
                cv2.rectangle(cv_image, (x_min, y_min), (x_max, y_max), (0, 0, 255), 2)
            else:
                cv2.rectangle(cv_image, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)

            label = "{} {:.2f}".format(class_name, confidence)
            cv2.putText(
                cv_image,
                label,
                (x_min, y_min - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2,
            )

            bbox = BoundingBox()
            bbox.Class = class_name
            bbox.xmin = x_min
            bbox.ymin = y_min
            bbox.xmax = x_max
            bbox.ymax = y_max
            bbox.probability = confidence

            self.bbox_msg.bounding_boxes.append(bbox)

        self.bbox_pub.publish(self.bbox_msg)

        cv2.imshow("YOLO Inference", cv_image)
        cv2.waitKey(1)


if __name__ == "__main__":
    try:
        YOLOInferenceNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass

