from djitellopy import Tello
import cv2
import pygame
from pygame.locals import *
import numpy as np
import time

# Speed of the drone
S = 60
# Frames per second of the pygame window display
FPS = 25


class FrontEnd(object):
    """ Maintains the Tello display and moves it through the keyboard keys.
        Press escape key to quit.
        The controls are:
            - T: Takeoff
            - L: Land
            - Arrow keys: Forward, backward, left and right.
            - A and D: Counter clockwise and clockwise rotations
            - W and S: Up and down.
    """

    def __init__(self):
        # Init pygame
        pygame.init()

        # Creat pygame window
        pygame.display.set_caption("Tello video stream")
        self.screen = pygame.display.set_mode([960, 720])

        # Init Tello object that interacts with the Tello drone
        self.tello = Tello()

        self.faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml')

        # Drone velocities between -100~100
        self.for_back_velocity = 0
        self.left_right_velocity = 0
        self.up_down_velocity = 0
        self.yaw_velocity = 0
        self.speed = 10
        self.show_stats = False

        self.send_rc_control = False

        # create update timer
        pygame.time.set_timer(USEREVENT + 1, 50)

    def run(self):

        if not self.tello.connect():
            print("Tello not connected")
            return

        if not self.tello.set_speed(self.speed):
            print("Not set speed to lowest possible")
            return

        # In case streaming is on. This happens when we quit this program without the escape key.
        if not self.tello.streamoff():
            print("Could not stop video stream")
            return

        if not self.tello.streamon():
            print("Could not start video stream")
            return

        frame_read = self.tello.get_frame_read()

        should_stop = False
        while not should_stop:
            frameRet = frame_read.frame

            for event in pygame.event.get():
                if event.type == USEREVENT + 1:
                    self.update()
                elif event.type == QUIT:
                    should_stop = True
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        should_stop = True
                    else:
                        self.keydown(event.key)
                elif event.type == KEYUP:
                    self.keyup(event.key)

            if frame_read.stopped:
                frame_read.stop()
                break

            self.screen.fill([0, 0, 0])

            gray  = cv2.cvtColor(frameRet, cv2.COLOR_BGR2GRAY)
            faces = self.faceCascade.detectMultiScale(gray, scaleFactor=1.5, minNeighbors=2)

            for (x, y, w, h) in faces:
                fbCol = (255, 0, 0) #BGR 0-255 
                fbStroke = 2
                end_cord_x = x + w
                end_cord_y = y + h
                cv2.rectangle(frameRet, (x, y), (end_cord_x, end_cord_y), fbCol, fbStroke)

            if self.show_stats:
                cv2.putText(frameRet, "Batt: " + str(self.tello.get_battery()),(0,32),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2)
                cv2.putText(frameRet, "Wifi: " + str(self.tello.get_wifi()),(0,64),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2)
                cv2.putText(frameRet, "Faces: " + str(len(faces)),(0,96),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2)

            frameRet = cv2.cvtColor(frameRet,cv2.COLOR_BGR2RGB)

            frameRet = np.rot90(frameRet)
            frameRet = np.flipud(frameRet)

            frame = pygame.surfarray.make_surface(frameRet)

            self.screen.blit(frame, (0, 0))
            pygame.display.update()

            time.sleep(1 / FPS)

        # Call it always before finishing. I deallocate resources.
        self.tello.end()

    def keydown(self, key):
        """ Update velocities based on key pressed
        Arguments:
            key: pygame key
        """
        if key == pygame.K_UP:  # set forward velocity
            self.for_back_velocity = S
        elif key == pygame.K_DOWN:  # set backward velocity
            self.for_back_velocity = -S
        elif key == pygame.K_LEFT:  # set left velocity
            self.left_right_velocity = -S
        elif key == pygame.K_RIGHT:  # set right velocity
            self.left_right_velocity = S
        elif key == pygame.K_w:  # set up velocity
            self.up_down_velocity = S
        elif key == pygame.K_s:  # set down velocity
            self.up_down_velocity = -S
        elif key == pygame.K_a:  # set yaw clockwise velocity
            self.yaw_velocity = -S
        elif key == pygame.K_d:  # set yaw counter clockwise velocity
            self.yaw_velocity = S

    def keyup(self, key):
        """ Update velocities based on key released
        Arguments:
            key: pygame key
        """
        if key == pygame.K_UP or key == pygame.K_DOWN:  # set zero forward/backward velocity
            self.for_back_velocity = 0
        elif key == pygame.K_LEFT or key == pygame.K_RIGHT:  # set zero left/right velocity
            self.left_right_velocity = 0
        elif key == pygame.K_w or key == pygame.K_s:  # set zero up/down velocity
            self.up_down_velocity = 0
        elif key == pygame.K_a or key == pygame.K_d:  # set zero yaw velocity
            self.yaw_velocity = 0
        elif key == pygame.K_t:  # takeoff
            self.tello.takeoff()
            self.send_rc_control = True
        elif key == pygame.K_l:  # land
            self.tello.land()
            self.send_rc_control = False
        elif key == pygame.K_h: # stats
            self.show_stats = not self.show_stats

    def update(self):
        """ Update routine. Send velocities to Tello."""
        if self.send_rc_control:
            self.tello.send_rc_control(self.left_right_velocity, self.for_back_velocity, self.up_down_velocity,
                                       self.yaw_velocity)


def main():
    frontend = FrontEnd()

    # run frontend
    frontend.run()


if __name__ == '__main__':
    main()
