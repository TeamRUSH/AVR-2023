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
        self.servo_init(4);

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
        if servo_id == 0: #Intake Start
            if command == "open": #Intake Fwd
                #self.servo_abs(4,1394+250)
                self.servo_abs(4,2000)
                self.send_message(
                        "avr/pcm/set_base_color",
                        {"wrgb": (0,255,0,0)}
                )
            elif command == "close": #Intake Rev
                #self.blink3X()
                self.send_message(
                        "avr/pcm/set_base_color",
                        {"wrgb": (0,0,255,0)}
                )
                #self.servo_abs(4,1394-210)
                self.servo_abs(4,1000)
        if servo_id == 1: #Intake Stop
            self.servo_init(4)
            self.send_message(
                    "avr/pcm/set_base_color",
                    {"wrgb": (0,0,0,0)}
            )

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
        # start = time.time()
        # if servo_id == 4:
        #     end = start + 1.0
        #     while time.time() < end:
        #         pass
        #     self.servo_pct(4,55)


    #Helper Method to Move a Servo
    def servo_pct(self,id,pct):
        self.send_message(
            "avr/pcm/set_servo_pct",
            {"servo": id, "percent": pct}
        )

    def servo_abs(self,id,abs):
        self.send_message(
            "avr/pcm/set_servo_abs",
            {"servo": id, "absolute": abs}
        )

    def servo_init(self,id):
        self.send_message(
            "avr/pcm/set_servo_abs",
            {"servo": id, "absolute": 1394}
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