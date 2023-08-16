from google.cloud import storage
import cv2
import time
import RPi.GPIO as GPIO

# capture video var
video_duration = 5
filename_temp = time.time()
output_file = "./videos/video_"+str(filename_temp)+".mp4"

# upload video var
bucket_name = "sff-fish-video"
destination_blob_name = "video_"+str(filename_temp)+".mp4"

# video extraction var
image_shape = (200, 200)
sequence_length = 50

# move servo var
servo_pin = 12
led_a_pin = 17
led_b_pin = 27


def capture_video(duration, output_file):
    cap = cv2.VideoCapture(0)
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    out = cv2.VideoWriter(output_file, fourcc, 10.0, (640, 480))
    start_time = time.time()

    while time.time() - start_time < duration:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)

    cap.release()
    out.release()


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


def send_prediction_request(video_gcs_url, model_name, token, pond_id):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    data = {
        'instances': [
            {
                'video_url': video_gcs_url,
                'pond_id': pond_id
            }
        ]
    }

    prediction_url = f'https://ml.googleapis.com/v1/projects/your_project_id/models/{model_name}:predict'
    response = requests.post(prediction_url, headers=headers, json=data)

    if response.status_code == 200:
        prediction_data = response.json()
        return prediction_data['predictions']
    else:
        print(
            f"Failed to get predictions. Status code: {response.status_code}")
        return []


def move_servo():
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(servo_pin, GPIO.OUT)
    GPIO.setup(led_a_pin, GPIO.OUT)
    GPIO.setup(led_b_pin, GPIO.OUT)

    servo = GPIO.PWM(servo_pin, 50)  # Frekuensi PWM 50 Hz
    servo.start(0)

    def set_servo_angle(angle):
        # Menghitung duty cycle berdasarkan sudut
        duty_cycle = 2 + (angle / 18)
        servo.ChangeDutyCycle(duty_cycle)
        time.sleep(0.5)  # Tunggu sebentar untuk servo mencapai posisi

    angle = 0

    try:
        while True:
            angle += 90
            set_servo_angle(angle)     # Putar ke posisi 0 derajat
            if (angle % 180 == 0):
                GPIO.output(led_a_pin, 1)
                GPIO.output(led_b_pin, 0)
            else:
                GPIO.output(led_a_pin, 0)
                GPIO.output(led_b_pin, 1)

            time.sleep(1)
    except KeyboardInterrupt:
        servo.stop()
        GPIO.cleanup()


def main():
    capture_video(video_duration, output_file)
    testUpload = upload_video(output_file, bucket_name, destination_blob_name)
    print(testUpload)


main()
