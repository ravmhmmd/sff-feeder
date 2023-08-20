from google.cloud import storage, aiplatform
import tensorflow as tf
import cv2
import time
import schedule
import RPi.GPIO as GPIO
import numpy as np
import requests
import json
import math

# capture video var
video_duration = 5

# upload video var
bucket_name = "sff-fish-video"

# video extraction var
image_shape = (200, 200)
sequence_length = 50

# send prediction var
PROJECT_NUMBER = '1024002661381'
ENDPOINT_ID = '4470262434816327680'
ENDPOINT_LOCATION = 'asia-southeast2'
endpoint_name = f"projects/{PROJECT_NUMBER}/locations/{ENDPOINT_LOCATION}/endpoints/{ENDPOINT_ID}"
endpoint = aiplatform.Endpoint(endpoint_name=endpoint_name)
 
# move servo var
servo_pin = 12
led_a_pin = 17
led_b_pin = 27

# integration with backend
URL = "http://35.187.255.170/api/report"
USER_ID = 10 # Wahyu Testing Feeder
POND_ID = 10 # Kolam Ikan Nila Wahyu
N_FISH = 8


def capture_video(duration, output_file):
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(led_a_pin, GPIO.OUT)
    
    GPIO.output(led_a_pin, 1)
    cap = cv2.VideoCapture(0)
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    out = cv2.VideoWriter(output_file, fourcc, 10.0, (640, 480))
    start_time = time.time()

    while time.time() - start_time < duration:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)

    GPIO.output(led_a_pin, 0)
    cap.release()
    out.release()
    GPIO.cleanup()


def upload_video(video_path, bucket_name, destination_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(video_path)

    video_gcs_url = f'gs://{bucket_name}/{destination_blob_name}'
    return video_gcs_url


def extract_video_frames(video_path):
    print(f'Extracting {video_path}')
    frames = []
    video_reader = cv2.VideoCapture(video_path)
    for frame_count in range(sequence_length):
        video_reader.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        success, frame = video_reader.read()
        if not success:
            print(f'Fail : {video_path}')
            break
        resized_frame = cv2.resize(frame, image_shape)
        normalized_frame = np.float32(resized_frame/255)
        frames.append(normalized_frame)
    video_reader.release()
    return frames
    
    
def send_prediction(features):
    path = 'Xception_RNN_10fps_RGB_19_08_2023_15_48_59_loss_0.6931692957878113_acc_0.5.pb'
    model = tf.keras.models.load_model(path)
    return model.predict(features)


def move_servo(feeding_type):
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(servo_pin, GPIO.OUT)
    GPIO.setup(led_b_pin, GPIO.OUT)

    servo = GPIO.PWM(servo_pin, 50)  # Frekuensi PWM 50 Hz
    servo.start(0)

    def set_servo_angle(angle):
        # Menghitung duty cycle berdasarkan sudut
        duty_cycle = 2 + (angle / 18)
        servo.ChangeDutyCycle(duty_cycle)
        time.sleep(0.5)  # Tunggu sebentar untuk servo mencapai posisi

    angle = 0
    cycle_count = 0
    max_cycle = 0
    
    if feeding_type == "testing":
        max_cycle = math.floor(N_FISH / 4)
    elif feeding_type == "feeding":
        max_cycle = N_FISH * 2
        
    FEED_USE = max_cycle * 5
    
    try :
        while cycle_count <= max_cycle:
            GPIO.output(led_b_pin, 1)
            angle += 90
            set_servo_angle(angle)
            cycle_count += 1
            time.sleep(1)
            
        # create new feeding data
        FEEDING_PAYLOAD = {'user_id': USER_ID, 'pond_id': POND_ID, 'feeding_type': feeding_type, 'n_fish_feed_use': FEED_USE}
        RESPONSE = requests.post(url = f"{URL}/feeding/add-report", json = FEEDING_PAYLOAD)
        
        if RESPONSE.status_code == 201:
            FEEDING_DATA = RESPONSE.json()
            print(f"New feeding data added successfully with id {FEEDING_DATA['result']['newFeeding']['id']}")
            
        else:
            print(f"Request failed with status code: {RESPONSE.status_code}")
        
    except cycle_count > max_cycle:
        GPIO.output(led_b_pin, 0)
        servo.stop()
        GPIO.cleanup()
        
def feeding_action():
    filename_temp = time.time()
    output_file = "./videos/video_"+str(filename_temp)+".mp4"
    destination_blob_name = "video_"+str(filename_temp)+".mp4"
    
    # todo: fetch add feeding data
    print("\nStarting feeder...")
    print("Feeder started\n\nFeeding fish with type testing")
    move_servo("testing")
    print("Feeding completed\n")
    
    # call capture video
    print("Capturing video from pond...")
    capture_video(video_duration, output_file)
    print("Video captured\n")
    
    # upload video and return the gcs url
    print("Uploading video to google cloud storage...")
    gcs_video_url = upload_video(output_file, bucket_name, destination_blob_name)
    print(f"Video saved in {gcs_video_url}\n")
    
    # create new hunger data
    HUNGER_PAYLOAD = {'user_id': USER_ID, 'pond_id': POND_ID, 'video_path': gcs_video_url}
    HUNGER_RESPONSE = requests.post(url = f"{URL}/hunger/add-report", json = HUNGER_PAYLOAD)
    
    if HUNGER_RESPONSE.status_code == 201:
        HUNGER_DATA = HUNGER_RESPONSE.json()
        HUNGER_DATA_ID = HUNGER_DATA['result']['newHunger']['id']
        print(f"New hunger data added successfully with id {HUNGER_DATA_ID}")
        
    else:
        print(f"Request failed with status code: {HUNGER_RESPONSE.status_code}")
    
    # extract video
    features = []
    frames = extract_video_frames(output_file)
    features.append(frames)
    features = np.asarray(features)
    print(features.shape)
    
    def update_prediction(is_hungry):
        # update prediction result to hunger data
        PREDICTION_PAYLOAD = {'is_hungry': is_hungry}
        PREDICTION_RESPONSE = requests.put(url = f"{URL}/hunger/{HUNGER_DATA_ID}/update-prediction", json = PREDICTION_PAYLOAD)
        
        if PREDICTION_RESPONSE.status_code == 200:
            NEW_HUNGER_DATA = PREDICTION_RESPONSE.json()
            print(f"Prediction result for hunger data with id {HUNGER_DATA_ID} has saved successfully")
            
        else:
            print(f"Request failed with status code: {PREDICTION_RESPONSE.status_code}")
    
    # send prediction
    print("Predicting fish condition...")
    prediction_result = send_prediction(features)
    print(f"Fish condition predicted successfully\nPrediction result is {prediction_result}")
    if prediction_result > 0.4967227:
        is_hungry = True
        update_prediction(is_hungry)
        print(f"Fish hungry condition is {is_hungry}\n")
        print("Feeding fish with type feeding")
        move_servo("feeding")
        print("Feeding Completed. Upcoming feeding testing in 5 minutes")
        time.sleep(30)
        feeding_action()
    else:
        is_hungry = False
        print(f"Fish hungry condition is {is_hungry}")
        update_prediction(is_hungry)
        print("Feeder in idle condition. Upcoming feeding testing in 180 minutes")
    

if __name__ == "__main__":
    print("\nSmart Fish Feeder - Feeder v1.0 (2023-08)")
    print("Developed by SFF Developer\n")
    time.sleep(3)
    print("Initializing feeder...\n")
    time.sleep(3)
    print("Feeder initialized. Upcoming feeding testing in 180 minutes")
    schedule.every(2).minutes.do(feeding_action)
    while True:
        schedule.run_pending()
        time.sleep(1)
