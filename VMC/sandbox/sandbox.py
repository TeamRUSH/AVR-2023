# Team RUSH Bell AVR 2022 Sandbox Code
from bell.avr.mqtt.client import MQTTModule
from bell.avr.mqtt.payloads import (
    AvrFcmVelocityPayload,
    AvrApriltagsVisiblePayload,
    AvrPcmSetServoOpenClosePayload,
    AvrPcmSetServoPctPayload
)
import time
import math

from loguru import logger

class Sandbox(MQTTModule):
    def __init__(self) -> None:
        super().__init__()
        self.topic_map = {"avr/fcm/velocity": self.show_velocity, "avr/apriltags/visible" : self.apriltag_visible, "avr/pcm/set_servo_open_close" : self.servo_buttons, "avr/pcm/set_servo_pct" : self.second_servo}
        self.dump_fwd = True
        self.dumped = False
        self.dumping = False

    # Get Drone velocity components
    def show_velocity(self, payload: AvrFcmVelocityPayload) -> None:
        vx = payload["vX"]
        vy = payload["vY"]
        vz = payload["vZ"]
        v_ms = (vx, vy, vz)

#Listen to servo open/close buttons
    def servo_buttons(self, payload: AvrPcmSetServoOpenClosePayload) -> None:
        servo_id = payload["servo"]
        command = payload["action"]
        if servo_id == 0: #Dump Large Dumper
            if command == "open": #Dump Half
                self.dumping = True
                self.blink3X()
                if self.dump_fwd:
                    self.servo_pct(4,100)
                else:
                    self.servo_pct(4,0)
                self.dump_fwd = not self.dump_fwd

            elif command == "close": #Dump Full
                self.dumping = True
                self.blink3X()
                self.servo_pct(4,99)
        elif servo_id == 1: #Dump Small Dumper
            self.dumped = command == "close"
            if self.dumped:
                self.dumping = True
                self.blink3X()
                self.servo_pct(5,0)
                start = time.time()
                while time.time() < start + 0.5:
                    pass
                self.dumping = False
            else:
                self.servo_pct(5,100)

    #Blink Lights 3X before dropping
    def blink3X(self):
        for x in range(3):
            start = time.time()
            while time.time() < start + 0.26:
                pass
            self.led_blink((0,255,255,255),0.13)

    #Handle custom servo commands
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

            elif percent == 55:
                self.dumping = False

    #Helper Method to Move a Servo
    def servo_pct(self,id,pct):
        self.send_message(
            "avr/pcm/set_servo_pct",
            {"servo": id, "percent": pct}
        )

    #Reacting to Apriltags
    def apriltag_visible(self, payload: AvrApriltagsVisiblePayload) -> None:
        tags = payload["tags"]
        dist = tags[0]["horizontal_dist"]
        id = tags[0]["id"]
        rel = tags[0]["pos_rel"]
        X_raw = rel["x"]
        Y_raw = rel["y"]
        Z_raw = rel["z"]

        #Calculate relative location to Apriltag in Camera Reference Frame
        head = math.radians(tags[0]["heading"])
        X_rot = -X_raw*math.sin(head)+Y_raw*math.cos(head)
        Y_rot = X_raw*math.cos(head)+Y_raw*math.sin(head)
        #Relative location in Drone Reference Frame
        height = (-Z_raw*0.906307787)+(Y_rot*0.422618262)
        f_dist = 41+(Z_raw*0.422618262)+(Y_rot*0.906307787)
        s_dist = X_rot

        abs_pos = (f_dist, s_dist)
        color = (0,0,0,0) #Blank color if nothing visible
        if not self.dumping:
            if id <=6:
                color = (0,255,0,0)

            # if (abs(f_dist) <= 10.0) and (s_dist <= 19.0) and (s_dist >= -3.0):
            #     color = (0,0,255,0)
            # elif (abs(f_dist) <= 10.0) and (s_dist <= 30.0) and (s_dist >= 19.0):
            #     color = (0,0,0,255)
            # elif (abs(f_dist) <= 10.0) and (s_dist <= -3.0) and (s_dist >= -25.0) and not self.dumped:
            #     color = (0,255,255,0)

            self.led_blink(color,2)
        logger.debug(f"Pos: {abs_pos}")

    #Helper Method to Blink LED
    def led_blink(self,color,time):
        self.send_message(
                "avr/pcm/set_temp_color",
                {"wrgb": color, "time": time}
        )

if __name__ == "__main__":
    box = Sandbox()
    box.run()