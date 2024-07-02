"""
Copyright MIT
MIT License

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: controller_real.py
File Description: Contains the Controller module of the racecar_core library
"""

from controller import Controller

# General
import copy

# ROS2
import rclpy as ros2
from sensor_msgs.msg import Joy


class ControllerReal(Controller):
    # The ROS topic from which we read joystick information
    __TOPIC = "/joy"

    # The minimum amount that the trigger must be pressed to register a
    # non-zero value
    __TRIGGER_DEAD_ZONE = 0.05

    # The minimum amount that the joystick must be moved along an axis to
    # register a non-zero value along that axis
    __JOYSTICK_DEAD_ZONE = 0.2

    # The index of each button the message.buttons
    __BUTTON_MAP = [
        0,
        1,
        2,
        3,
        4,
        5,
        9,
        10,
    ]

    # The index of the start button in message.buttons
    __START_MAP = 7

    # The index of the back button in message.buttons
    __BACK_MAP = 6

    # The index of the triggers in message.axes
    __TRIGGER_MAP = [2, 5]

    # The indices of the (x, y) joystick axes in message.axes
    __JOYSTICK_MAP = [(0, 1), (3, 4)]

    def __init__(self, racecar):
        self.__racecar = racecar
        # print(f"Length of self.Button: {len(self.Button)}")
        # Button state at the start of last frame
        self.__was_down = [False] * len(self.Button)
        # print(f"Length of __was_down: {len(self.__was_down)}")
        # Button state at the start of this frame
        self.__is_down = [False] * len(self.Button)
        # Button state received since the start of this frame
        self.__cur_down = [False] * len(self.Button)

        # Trigger state at the start of this frame
        self.__last_trigger = [0, 0]
        # Trigger state received since the start of this frame
        self.__cur_trigger = [0, 0]

        # Joystick state at the start of this frame
        self.__last_joystick = [[0, 0], [0, 0]]
        # Joystick state received since the start of this frame
        self.__cur_joystick = [[0, 0], [0, 0]]

        # Current start and back button state
        self.__cur_start = 0
        self.__cur_back = 0

        # ROS node
        self.node = ros2.create_node("controller")

        # subscribe to the controller topic, which will call
        # __controller_callback every time the controller state changes
        self.__subscriber = self.node.create_subscription(
            Joy, self.__TOPIC, self.__controller_callback, 1
        )

    def is_down(self, button: Controller.Button) -> bool:
        return self.__is_down[button.value]

    def was_pressed(self, button: Controller.Button) -> bool:
        return self.__is_down[button.value] and not self.__was_down[button.value]

    def was_released(self, button: Controller.Button) -> bool:
        return not self.__is_down[button.value] and self.__was_down[button.value]

    def get_trigger(self, trigger: Controller.Trigger) -> float:
        return self.__last_trigger[trigger.value]

    def get_joystick(self, joystick: Controller.Joystick) -> tuple[float, float]:
        return self.__last_joystick[joystick.value]

    def __controller_callback(self, message):
        """
        Updates the state of Controller in response to a change in controller state.

        Args:
            message: (ROS controller message object) An object encoding the
                physical state of the controller.
        """
        for i in range(0, len(self.__BUTTON_MAP)):
            self.__cur_down[i] = bool(message.buttons[self.__BUTTON_MAP[i]])

        for i in range(0, len(self.__TRIGGER_MAP)):
            self.__cur_trigger[i] = self.__convert_trigger_value(
                message.axes[self.__TRIGGER_MAP[i]]
            )

        for i in range(0, len(self.__JOYSTICK_MAP)):
            self.__cur_joystick[i] = self.__convert_joystick_values(
                message.axes[self.__JOYSTICK_MAP[i][0]],
                message.axes[self.__JOYSTICK_MAP[i][1]],
            )

        start = message.buttons[self.__START_MAP]
        if start != self.__cur_start:
            self.__cur_start = start
            if start:
                if self.__cur_back:
                    self.__racecar._RacecarReal__handle_exit()
                else:
                    self.__racecar._RacecarReal__handle_start()

        back = message.buttons[self.__BACK_MAP]
        if back != self.__cur_back:
            self.__cur_back = back
            if back:
                if self.__cur_start:
                    self.__racecar._RacecarReal__handle_exit()
                else:
                    self.__racecar._RacecarReal__handle_back()

    def __update(self):
        """
        Updates the input registers when the current frame ends.
        """
        self.__was_down = copy.deepcopy(self.__is_down)
        self.__is_down = copy.deepcopy(self.__cur_down)
        self.__last_trigger = copy.deepcopy(self.__cur_trigger)
        self.__last_joystick = copy.deepcopy(self.__cur_joystick)

    def __convert_trigger_value(self, value: float) -> float:
        """
        Converts a received trigger value into the desired range.

        Args:
            value: The value of the trigger provided in the ROS message.
        """
        value = (1.0 - value) / 2
        if value < self.__TRIGGER_DEAD_ZONE:
            return 0
        return value

    def __convert_joystick_values(self, x: float, y: float) -> tuple[float, float]:
        """
        Converts a received joystick axis value into the desired range.

        Args:
            x: The value of the joystick x-axis provided in the ROS message.
            y: The value of the joystick y-axis provided in the ROS message.
        """
        x = -x

        if abs(x) < self.__JOYSTICK_DEAD_ZONE:
            x = 0
        if abs(y) < self.__JOYSTICK_DEAD_ZONE:
            y = 0

        return x, y
