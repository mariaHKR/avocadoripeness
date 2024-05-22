import boto3
from botocore.exceptions import NoCredentialsError
import picamera
from datetime import datetime
import time
import RPi.GPIO as GPIO
import io

# AWS S3 setup
s3_client = boto3.client('s3')
bucket_name = 'unifiedvalues'
s3_folder = 'cnn/'  # Folder in the S3 bucket

# Setup for button
BUTTON_GPIO = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
button_pressed_previously = False

# Function to upload file to S3
def upload_to_s3(file_buffer, bucket, object_name):
    try:
        s3_client.upload_fileobj(file_buffer, bucket, object_name)
    except NoCredentialsError:
        print("Credentials not available")
        return False
    return True

# Function to capture and upload image with timestamp
def capture_and_upload():
    with picamera.PiCamera() as camera:
        camera.rotation = 180   # To correct the upside-down camera
        camera.resolution = (3280, 2464)
        camera.exposure_mode = 'auto'
        camera.iso = 200
        camera.start_preview()
        time.sleep(2)

        # Create a timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

        # Define the S3 object name (including folder path)
        s3_object_name = f"{s3_folder}image_{timestamp}.jpg"

        # Capture the image to a BytesIO object
        image_stream = io.BytesIO()
        camera.capture(image_stream, 'jpeg')
        image_stream.seek(0)  # Rewind the buffer

        # Upload to S3
        if upload_to_s3(image_stream, bucket_name, s3_object_name):
            print("Upload successful")
        else:
            print("Upload failed")

def check_button():
    global button_pressed_previously
    input_state = GPIO.input(BUTTON_GPIO)
    if input_state == False and not button_pressed_previously:
        print("Button pressed")
        button_pressed_previously = True
        capture_and_upload()
    elif input_state == True:
        button_pressed_previously = False

try:
    # Keep the script running to listen for button press
    while True:
        check_button()
        time.sleep(0.1)
except KeyboardInterrupt:
    # Graceful exit on keyboard interrupt
    print("Exiting program")
    GPIO.cleanup() # Clean up GPIO to ensure all pins are reset
