from djitellopy import tello
import cv2
import numpy as np
import pygame
import time

class AutoFlight():
    def __init__(self):  # Init necessary variables
        self.w, self.h = 360, 240
        self.fbRange = [5200, 6500]
        self.area_O = 6000
        self.pid = [0.4, 0.4, 0]
        self.p_error = 0
        self.p_error2 = 0
        self.p_error3 = 0

        pygame.init()  # init pygame window
        win = pygame.display.set_mode((400, 400))  # set pygame window dimensions
        self.drone = tello.Tello()  # Call tello bib
        self.drone.connect()  # Connect to drone
        time.sleep(2)
        self.drone.streamon()  # Get camera feed from drone
        battery = self.drone.get_battery()  # Get battery status from drone
        print("Battery is at {}%".format(battery))

    def getKey(self, keyName):  # Get a key in Pygame
        ans = False
        for eve in pygame.event.get(): pass  # Weird pygame convention that is necessary somehow
        keyInput = pygame.key.get_pressed()  # Get inputs from keyboard
        myKey = getattr(pygame, 'K_{}'.format(keyName))  # Get the specific key
        if keyInput[myKey]:
            ans = True
        pygame.display.update()  # Update pygame
        return ans

    def findFaces(self, img):  # Open-CV face detection
        face_cascade = cv2.CascadeClassifier("resources/cv2_cascade/haarcascade_frontalface_default.xml")
        imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(imgGray, 1.2, 8)
    
        face_list_c = []  # Center of face
        face_list_area = []  # Area of the face
    
        for (x, y, w, h) in faces:  # Iterate over each detected face
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)  # Draw rectangle over face
            cx = x + w // 2  # Get center x coordinate
            cy = y + h // 2  # Get center y coordinate
            area = w * h  # Get area
            # cv2.circle(img, (cx, cy), 5, (0, 0, 255), cv2.FILLED)  # Draw circle in middle of img
            face_list_c.append([cx, cy])  # append center x and y to list
            face_list_area.append(area)  # append area to list
        if len(face_list_area) != 0:  # If 1 or more faces are detected:
            i = face_list_area.index(max(face_list_area))  # Use closest face
            return img, [face_list_c[i], face_list_area[i]]
        else:
            return img, [[0, 0], 0]  # Otherwise return 0 values to prevent error

    def trackFace(self, info, w, pid, p_error, p_error2, p_error3):  # Track the face
        speed = 20  # Define speed of drone
        area = info[1]  # Get area of face
        x, y = info[0]  # Get x and y coordinate of face center
        fb = 0
        error = x - w // 2  # Calculate horizontal error (difference between center of image and center of face)
        rotation = pid[0]*error + pid[1] * (error - p_error)  # Math formula to rotate the drone. The numbers get bigger if the difference increases
        rotation = int(np.clip(rotation, -150, 150))  # Set max values for the rotation
    
        error2 = y - self.h // 2  # Calculate vertical error (difference between center of image and center of face)
        error2 = error2 + 20  # Add offset to error for better results (the camera of the drone faces downwards some degrees)
        ud = pid[0] * error2 + pid[1] * (error2 - p_error2)  # Math formula to move drone up and down. The numbers get bigger if the difference increases
        ud = int(np.clip(ud, -40, 40))  # Set max values for up/down movement
    
        if area > self.fbRange[0] and area < self.fbRange[1]:  # Don't move forward/backward if drone is inside area
            fb = 0
            # print("Green zone. Don't move.")
        elif area > self.fbRange[1]:  # Move back if drone too close
            fb = -speed
            # print("Too close. Move backwards.")
        elif area < self.fbRange[0] and area != 0:  # Move forward if drone too far away AND a face is detected
            fb = speed
            # print("Too far away. Move forwards.")
        if x == 0:  # Don't rotate if face in center of image or no face is detected
            # print("Drone at horizontal center. Don't rotate.")
            rotation = 0
            fb2 = 0
            error = 0
            error3 = 0
        if y == 0:  # Don't move up/down if face in center of image or no face is detected
            # print("Drone at vertical center. Don't move up/down.")
            ud = 0
            error2 = 0
        return error, error2, p_error3, [0, fb, -ud, rotation]
    
    def getKeyboardInput(self):  # Get manual key inputs
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

        if self.getKey("SPACE"): self.drone.takeoff(); time.sleep(1)  # Start drone with 'space' key
        return [lr, fb, ud, yv]
    
    def run(self):
        while True:
            img = self.drone.get_frame_read().frame  # Read drone feed
            img = cv2.resize(img, (self.w, self.h))  # Resize image
            img, info = self.findFaces(img)  # Find faces in image
            self.p_error, self.p_error2, self.p_error3, vals2 = self.trackFace(info, self.w, self.pid, self.p_error, self.p_error2, self.p_error3)  # Track face
            vals = self.getKeyboardInput()  # Get manual keyboard inputs
            if vals[1] == 0 and vals[2] == 0 and vals[3] == 0:  # If no manual steering:
                self.drone.send_rc_control(vals2[0], vals2[1], vals2[2], vals2[3])  # Use auto steer
            else:
                self.drone.send_rc_control(vals[0], vals[1], vals[2], vals[3])  # Else: Use manual steer
            cv2.imshow("IMG", img)  # Show webcam feed
            if cv2.waitKey(1) & 0xFF == ord("q"):  # Land drone if 'q' is pressed and exit loop
                self.drone.land()
                break