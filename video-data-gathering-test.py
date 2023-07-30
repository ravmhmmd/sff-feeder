from google.cloud import storage
import cv2
import time

def capture_video(duration, output_file):
	cap = cv2.VideoCapture(0)
	fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
	out = cv2.VideoWriter(output_file, fourcc, 20.0, (640, 480))
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
	
duration = 10
filename_temp = time.time()
output_file = "./video-test/video_"+str(filename_temp)+".mp4"
capture_video(duration, output_file)

bucket_name = "sff-pond-video-test"
destination_blob_name = "video_"+str(filename_temp)+".mp4"
testUpload = upload_video(output_file, bucket_name, destination_blob_name)
print(testUpload)
