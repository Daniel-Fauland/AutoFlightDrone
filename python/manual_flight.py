from djitellopy import tello
from tabulate import tabulate
from datetime import datetime
import pandas as pd
import cv2
import time
import pygame


class ManualFlight():
    def __init__(self):
        pygame.init()  # init pygame window
        win = pygame.display.set_mode((400, 400))  # set pygame window dimensions
        self.drone = tello.Tello()  # Call tello bib
        self.drone.connect()  # Connect to drone
        time.sleep(2)
        self.drone.streamon()  # Get camera feed from drone
        battery = self.drone.get_battery()  # Get battery status from.drone
        print("Battery is at {}%".format(battery))
        df = {"Key": ["SPACE", "Q", "R", "UP", "DOWN", "LEFT", "RIGHT", "W", "A", "S", "D"],
               "Function": ["Take off", "Land drone", "Take a screenshot", "Go Up", "Go Down",
                            "Rotate Left", "Rotate Right", "Go forward", "Go left", "Go backward", "Go right"]}
        df = pd.DataFrame(df)
        print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))  # Show controls in a nice table
        self.start = time.time()  # Get current time

    def getKey(self, keyName):  # Get a key in Pygame
        ans = False
        for eve in pygame.event.get(): pass  # Weird pygame convention that is necessary somehow
        keyInput = pygame.key.get_pressed()  # Get inputs from keyboard
        myKey = getattr(pygame, 'K_{}'.format(keyName))  # Get the specific key
        if keyInput[myKey]:
            ans = True
        pygame.display.update()  # Update pygame
        return ans
    
    def findFaces(self, img, start):  # Open-CV face detection
        try:
            face_cascade = cv2.CascadeClassifier("resources/cv2_cascade/haarcascade_frontalface_default.xml")
            imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(imgGray, 1.2, 8)
    
            for (x, y, w, h) in faces:  # Iterate over each detected face
                cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)  # Draw rectangle over face
            if faces[0] is not None:
                end = time.time()  # Get current time
                if end - start > 3:  # Take a screenshot of a detected face every 3 seconds at max
                    now = datetime.now()  # Get current time
                    timestamp = now.strftime("%d_%m_%Y__%H_%M_%S")  # Get timestamp
                    cv2.imwrite("resources/images/face_{}.jpg".format(timestamp), img)  # Save image to pc
                    print("Automatic screenshot was taken successfully.")
                    start = time.time()
        except:
            pass
        return img, start
    
    
    def getKeyboardInput(self, img):  # Get manual key inputs
        lr, fb, ud, yv = 0, 0, 0, 0  # Default: no movement
        speed = 70  # Set speed for forward/backward and left/right and up/down
        speed2 = 80  # Set speed for rotation
    
        if self.getKey("w"):
            fb = speed
        elif self.getKey("s"):
            fb = -speed
    
        if self.getKey("a"):
            lr = -speed
        elif self.getKey("d"):
            lr = speed
    
        if self.getKey("UP"):
            ud = speed
        elif self.getKey("DOWN"):
            ud = -speed
    
        if self.getKey("LEFT"):
            yv = speed2
        elif self.getKey("RIGHT"):
            yv = -speed2
    
        if self.getKey("q"): self.drone.land(); time.sleep(3)  # Land drone with 'q' key
        if self.getKey("SPACE"): self.drone.takeoff(); time.sleep(1)  # Start drone with 'space' key
        if self.getKey("r"):  # Take manual screenshot with 'r' key
            now = datetime.now()
            timestamp = now.strftime("%d_%m_%Y__%H_%M_%S")
            cv2.imwrite("resources/images/img_{}.jpg".format(timestamp), img)
            print("Screenshot was taken successfully.")
            time.sleep(0.3)
        return [lr, fb, ud, yv]
    
    def run(self):
        while True:
            img = self.drone.get_frame_read().frame  # Read drone feed
            img, self.start = self.findFaces(img, self.start)  # Find faces in image
            vals = self.getKeyboardInput(img)  # Get manual keyboard inputs
            self.drone.send_rc_control(vals[0], vals[1], vals[2], vals[3])  # Send movement commands to drone
            # img = cv2.resize(img, (360, 240))  # Resize webcam feed to decrease cpu usage (not necessary)
            cv2.imshow("Image", img)  # Show Webcamfeed
            cv2.waitKey(1)
