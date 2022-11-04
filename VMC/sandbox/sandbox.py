# Here we import our own MQTT library which takes care of a lot of boilerplate
# code related to connecting to the MQTT server and sending/receiving messages.
# It also helps us make sure that our code is sending the proper payload on a topic
# and is receiving the proper payload as well.
from bell.avr.mqtt.client import MQTTModule
from bell.avr.mqtt.payloads import (
    AvrFcmVelocityPayload,
    AvrApriltagsVisiblePayload,
    AvrPcmSetServoOpenClosePayload,
    AvrPcmSetServoPctPayload
)
import time
import math


# This imports the third-party Loguru library which helps make logging way easier
# and more useful.
# https://loguru.readthedocs.io/en/stable/
from loguru import logger


# This creates a new class that will contain multiple functions
# which are known as "methods". This inherits from the MQTTModule class
# that we imported from our custom MQTT library.
class Sandbox(MQTTModule):
    # The "__init__" method of any class is special in Python. It's what runs when
    # you create a class like `sandbox = Sandbox()`. In here, we usually put
    # first-time initialization and setup code. The "self" argument is a magic
    # argument that must be the first argument in any class method. This allows the code
    # inside the method to access class information.
    def __init__(self) -> None:
        # This calls the original `__init__()` method of the MQTTModule class.
        # This runs some setup code that we still want to occur, even though
        # we're replacing the `__init__()` method.
        super().__init__()
        # Here, we're creating a dictionary of MQTT topic names to method handles.
        # A dictionary is a data structure that allows use to
        # obtain values based on keys. Think of a dictionary of state names as keys
        # and their capitals as values. By using the state name as a key, you can easily
        # find the associated capital. However, this does not work in reverse. So here,
        # we're creating a dictionary of MQTT topics, and the methods we want to run
        # whenever a message arrives on that topic.
        # self.topic_map = {"avr/fcm/velocity": self.show_velocity}
        self.topic_map = {"avr/fcm/velocity": self.show_velocity, "avr/apriltags/visible" : self.apriltag_visible, "avr/pcm/set_servo_open_close" : self.servo_buttons, "avr/pcm/set_servo_pct" : self.second_servo}
        self.dump_fwd = True
        self.dumped = False



    # Here's an example of a custom message handler here.
    # This is what executes whenever a message is received on the "avr/fcm/velocity"
    # topic. The content of the message is passed to the `payload` argument.
    # The `AvrFcmVelocityMessage` class here is beyond the scope of AVR.
    def show_velocity(self, payload: AvrFcmVelocityPayload) -> None:
        vx = payload["vX"]
        vy = payload["vY"]
        vz = payload["vZ"]
        v_ms = (vx, vy, vz)

        # Use methods like `debug`, `info`, `success`, `warning`, `error`, and
        # `critical` to log data that you can see while your code runs.

        # This is what is known as a "f-string". This allows you to easily inject
        # variables into a string without needing to combine lots of strings together.
        # https://realpython.com/python-f-strings/#f-strings-a-new-and-improved-way-to-format-strings-in-python
        # logger.debug(f"Velocity information: {v_ms} m/s")

    # Here is an example on how to publish a message to an MQTT topic to
    # perform an action


    def servo_buttons(self, payload: AvrPcmSetServoOpenClosePayload) -> None:
        servo_id = payload["servo"]
        command = payload["action"]
        if servo_id == 0:
            if command == "open":
                if self.dump_fwd:
                    self.servo_pct(4,100)
                else:
                    self.servo_pct(4,0)
                self.dump_fwd = not self.dump_fwd

            elif command == "close":
                self.servo_pct(4,99)
        elif servo_id == 1:
            self.dumped = command == "close"

    def second_servo(self, payload: AvrPcmSetServoPctPayload) -> None:
        servo_id = payload["servo"]
        percent = payload["percent"]
        start = time.time()
        if servo_id == 4:
            if percent == 100:
                end = start + 1.0
                while time.time() < end:
                    pass
                self.servo_pct(4,55)

            elif percent == 99:
                end = start + 0.75
                while time.time() < end:
                    pass
                self.servo_pct(4,0)

            elif percent == 1:
                end = start + 0.75
                while time.time() < end:
                    pass
                self.servo_pct(4,100)

            elif percent == 0:
                end = start + 1.0
                while time.time() < end:
                    pass
                self.servo_pct(4,55)


    def servo_pct(self,id,pct):
        self.send_message(
            "avr/pcm/set_servo_pct",
            {"servo": id, "percent": pct}
        )

    def apriltag_visible(self, payload: AvrApriltagsVisiblePayload) -> None:
        tags = payload["tags"]
        dist = tags[0]["horizontal_dist"]
        id = tags[0]["id"]
        rel = tags[0]["pos_rel"]
        X_raw = rel["x"]
        Y_raw = rel["y"]
        Z_raw = rel["z"]
        head = math.radians(tags[0]["heading"])
        X_rot = X_raw*math.sin(head)+Y_raw*math.cos(head)
        Y_rot = X_raw*math.cos(head)+Y_raw*math.sin(head)

        height = (-Z_raw*0.906307787)+(Y_rot*0.422618262)
        f_dist = 41+(Z_raw*0.422618262)+(Y_rot*0.906307787)
        s_dist = X_rot

        abs_pos = (head, X_rot, Y_rot, f_dist, s_dist)
        color = (0,0,0,0)
        if id == 0:
            color = (0,255,0,0)
        elif id == 2:
            color = (0,255,0,0)
        elif id == 3:
            color = (0,255,0,0)
        elif id == 4:
            color = (0,255,0,0)

        if (abs(f_dist) <= 10.0) and (s_dist <= 20.0) and (s_dist >= 0.0):
            color = (0,0,255,0)
        elif (abs(f_dist) <= 10.0) and (s_dist <= 40.0) and (s_dist >= 20):
            color = (0,0,0,255)
        elif (abs(f_dist) <= 10.0) and (s_dist <= 0) and (s_dist >= -20.0) and not self.dumped:
            color = (0,255,255,0)

        self.send_message(
                "avr/pcm/set_temp_color",
                {"wrgb": color, "time": 0.35}
        )


        logger.debug(f"Pos: {abs_pos}")




if __name__ == "__main__":
    # This is what actually initializes the Sandbox class, and executes it.
    # This is nested under the above condition, as otherwise, if this file
    # were imported by another file, these lines would execute, as the interpreter
    # reads and executes the file top-down. However, whenever a file is called directly
    # with `python file.py`, the magic `__name__` variable is set to "__main__".
    # Thus, this code will only execute if the file is called directly.
    box = Sandbox()
    # The `run` method is defined by the inherited `MQTTModule` class and is a
    # convience function to start processing incoming MQTT messages infinitely.
    box.run()

