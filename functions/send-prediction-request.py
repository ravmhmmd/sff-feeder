import os
import cv2
import numpy as np
import tensorflow as tf
from datetime import datetime
from tensorflow.keras.applications import Xception
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, TimeDistributed, GlobalAveragePooling2D, Conv2D
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.utils import plot_model, to_categorical
from tensorflow.keras.callbacks import EarlyStopping
from matplotlib import pyplot as plt
from sklearn.model_selection import train_test_split

path = '/content/Xception_RNN_10fps_RGB_15_08_2023_14_28_58_loss_0.6975820064544678_acc_0.3333333432674408.h5'

model = tf.keras.models.load_model(path)

features = []

video_path = '/content/drive/MyDrive/Experiment 1/lapar/lapar_20.mp4'
frames = extract_video_frames(video_path)
features.append(frames)
features = np.asarray(features)
print(features.shape)

model.predict(features)
