import RPi.GPIO as GPIO
import time

servo_pin = 12  # Ganti dengan pin GPIO yang sesuai
led_a_pin = 17
led_b_pin = 27

GPIO.setmode(GPIO.BCM)
GPIO.setup(servo_pin, GPIO.OUT)
GPIO.setup(led_a_pin, GPIO.OUT)
GPIO.setup(led_b_pin, GPIO.OUT)

servo = GPIO.PWM(servo_pin, 50)  # Frekuensi PWM 50 Hz
servo.start(0)

def set_servo_angle(angle):
    duty_cycle = 2 + (angle / 18)  # Menghitung duty cycle berdasarkan sudut
    servo.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)  # Tunggu sebentar untuk servo mencapai posisi
angle = 0

try:
    while True:
        angle += 90
        set_servo_angle(angle)     # Putar ke posisi 0 derajat
        if(angle%180 ==0):
            GPIO.output(led_a_pin,1)
            GPIO.output(led_b_pin,0)
        else:
            GPIO.output(led_a_pin,0)
            GPIO.output(led_b_pin,1)
        
        time.sleep(1)
except KeyboardInterrupt:
    servo.stop()
    GPIO.cleanup()
