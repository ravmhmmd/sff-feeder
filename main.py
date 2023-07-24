import os
import time
import schedule
import RPi.GPIO as GPIO
from google.cloud import storage
from google.auth.transport.requests import Request
from google.auth.transport import grpc
from google.auth.credentials import Credentials
from googleapiclient.discovery import build
import requests
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Fungsi untuk mengirimkan permintaan prediksi ke model di Vertex AI menggunakan Interface Online Prediction
def send_prediction_request(video_gcs_url, model_name, token, pond_id):
  credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
  request = google.auth.transport.requests.Request()
  credentials.refresh(request)
  request = google.auth.transport.grpc.Request(request)
  http_request = google.auth.transport.grpc.AuthorizedHttp(credentials)
  service = build('ml', 'v1', http=http_request)
  name = f'projects/YOUR_PROJECT_ID/locations/YOUR_REGION/models/{model_name}'
  payload = {
    'instances': [
      {
        'input_uri': video_gcs_url,
        'pond_id': pond_id,
      }
    ]
  }
  parent = f'projects/YOUR_PROJECT_ID/locations/YOUR_REGION'
  response = service.projects().predict(name=name, body=payload).execute()
  return response['predictions']

# Fungsi untuk menggerakkan servo berdasarkan hasil prediksi
def move_servo():
    # ... (kode untuk menggerakkan servo seperti yang telah dijelaskan sebelumnya)

# Fungsi untuk menyimpan token dan pond id dalam file .env
def save_token_and_pond_id(token, pond_id):
  # Simpan token ke dalam file .env
  with open('.env', 'w') as env_file:
    env_file.write(f'TOKEN={token}\n')
    env_file.write(f'POND_ID={pond_id}')

# Fungsi untuk membaca token dan pond id dari file .env
def get_token_and_pond_id():
  # Baca token dan pond id dari file .env
  with open('.env', 'r') as env_file:
    env_lines = env_file.readlines()
    for line in env_lines:
      key, value = line.strip().split('=')
      if key == 'TOKEN':
        token = value
      elif key == 'POND_ID':
        pond_id = value

  return token, pond_id

# Fungsi untuk mengambil video, mengunggah ke GCS, dan melakukan permintaan prediksi
def capture_and_upload_video():
    # ... (kode untuk mengambil video dan mengunggah ke GCS seperti yang telah dijelaskan sebelumnya)

  # Jika token belum ada atau pond id belum diatur, minta user untuk login dan mengatur pond id melalui website
  if not os.path.exists('.env'):
      # Implementasikan kode untuk menjalankan website sederhana untuk login dan mengatur pond id
      # Gunakan library Flask atau Django untuk membuat web server di Raspberry Pi

      # Setelah user berhasil login dan mengatur pond id, simpan token dan pond id
      token = 'your_jwt_token'  # Ganti dengan token yang didapatkan setelah login
      pond_id = 'your_pond_id'  # Ganti dengan pond id yang diatur oleh user

      save_token_and_pond_id(token, pond_id)

  # Jika token dan pond id sudah ada, baca dari file .env
  token, pond_id = get_token_and_pond_id()

  # Ganti 'your_model_name' dengan nama model yang telah diunggah ke Vertex AI
  model_name = 'your_model_name'

  # Kirim permintaan prediksi ke model dengan menyertakan token dan pond id
  prediction_data = send_prediction_request(gcs_video_url, model_name, token, pond_id)

  # Lakukan tindakan berdasarkan hasil prediksi
  for prediction in prediction_data:
      if prediction['condition'] == 'pemberian_pakan':
          # Jika hasil prediksi menunjukkan kondisi pemberian pakan, gerakkan servo
          move_servo()
      else:
          # Jika hasil prediksi tidak menunjukkan kondisi pemberian pakan, biarkan servo dalam keadaan idle

if __name__ == '__main__':
    # ... (kode untuk pengaturan GPIO seperti yang telah dijelaskan sebelumnya)

    # Ganti 'your_video_path' dengan path tempat menyimpan video di Raspberry Pi
    video_path = 'your_video_path'

    # Ganti 'your_gcs_bucket' dengan nama bucket GCS tujuan
    # Ganti 'your_gcs_blob_name' dengan nama blob/file di dalam GCS
    gcs_bucket = 'your_gcs_bucket'
    gcs_blob_name = 'your_gcs_blob_name'

    # Ganti 'your_servo_pin' dengan nomor pin GPIO yang terhubung ke servo
    your_servo_pin = 17

    # Ganti 'your_servo_position' dengan posisi servo yang ingin diatur
    # Anda dapat menyesuaikan nilai ini berdasarkan posisi yang sesuai untuk memberikan pakan atau posisi idle
    your_servo_position = 7.5

    # Ganti 'your_api_endpoint' dengan URL endpoint API Anda yang akan menyimpan hasil prediksi
    your_api_endpoint = 'your_api_endpoint'

    # Jadwal pengambilan video dan pengiriman ke GCS setiap 3 jam sekali (sesuai kebutuhan)
    schedule.every(3).hours.do(capture_and_upload_video)

    while True:
        schedule.run_pending()
        time.sleep(1)
