import socket
import struct
import math
import sys

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

class UDPTracker:
    def __init__(self, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", port))
        self.sock.setblocking(False)  # Set socket to non-blocking
        self.last_recv_pose = [0, 0, 0, 0, 0, 0]
        self.center = [0, 0, 0, 0, 0, 0]
        self.valid_data_count = 0
        self.model_transform = [1.0, 0.0, 0.0, 0.0,
                                0.0, 1.0, 0.0, 0.0,
                                0.0, 0.0, 1.0, 0.0,
                                0.0, 0.0, 0.0, 1.0]

    def apply_transformation(self):
        # Invert Pitch, Yaw, and Roll axes
        glRotatef(-(self.last_recv_pose[4] - self.center[4]), 1.0, 0.0, 0.0)  # Pitch
        glRotatef(self.last_recv_pose[3] - self.center[3], 0.0, 1.0, 0.0)  # Yaw
        glRotatef(self.last_recv_pose[5] - self.center[5], 0.0, 0.0, 1.0)  # Roll

        # Scale down the X, Y, Z movements
        scale_factor = 0.2
        glTranslated((self.last_recv_pose[0] - self.center[0]) * scale_factor, -(self.last_recv_pose[1] - self.center[1]) * scale_factor, 0) # -(self.last_recv_pose[2] - self.center[2]) * scale_factor
        glScalef((self.last_recv_pose[2] - 15 - self.center[2]) * scale_factor, (self.last_recv_pose[2] - 15 - self.center[2]) * scale_factor, (self.last_recv_pose[2] - 15 - self.center[2]) * scale_factor)

    def run(self):
        glutInit(sys.argv)
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
        glutInitWindowSize(500, 500)
        glutInitWindowPosition(100, 100)
        glutCreateWindow(b"3D Model Visualization")

        glutDisplayFunc(self.display)
        glutIdleFunc(self.idle)

        glEnable(GL_DEPTH_TEST)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, 1.0, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

        glutKeyboardFunc(self.keyboard)  # Register the keyboard function

        glutMainLoop()

    def display(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        gluLookAt(0.0, 0.0, 10.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

        glBegin(GL_LINES)
        glColor3f(0.5, 0.5, 0.5)
        for i in range(-10, 11):
            glVertex3f(i, -10.0, 0.0)
            glVertex3f(i, 10.0, 0.0)
            glVertex3f(-10.0, i, 0.0)
            glVertex3f(10.0, i, 0.0)
        glEnd()

        glPushMatrix()
        self.apply_transformation()
        glColor3f(1.0, 0.0, 0.0)
        glutSolidCube(1.0)
        glPopMatrix()

        glutSwapBuffers()

    def idle(self):
        try:
            data, _ = self.sock.recvfrom(1024)
            if len(data) == 48:
                pose_data = struct.unpack('<6d', data)
                valid_data = True
                for val in pose_data:
                    if math.isnan(val) or math.isinf(val):
                        valid_data = False
                        break

                if valid_data:
                    self.last_recv_pose = list(pose_data)
                    self.valid_data_count += 1
                    glutPostRedisplay()
        except BlockingIOError:
            pass  # No data received, just pass

    def keyboard(self, key, x, y):
        if key == b'\r':  # Enter key is pressed
            self.center = self.last_recv_pose  # Reset the pose and set the reset flag
        glutPostRedisplay()

if __name__ == "__main__":
    UDP_PORT = 4242
    tracker = UDPTracker(UDP_PORT)
    tracker.run()