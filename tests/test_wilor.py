import torch
import cv2
from wilor_mini.pipelines.wilor_hand_pose3d_estimation_pipeline import WiLorHandPose3dEstimationPipeline
device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
dtype = torch.float16

pipe = WiLorHandPose3dEstimationPipeline(device=device, dtype=dtype)
img_path = "/home/n/photo/主从多核.jpg"
image = cv2.imread(img_path)
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
outputs = pipe.predict(image)
