"""
Copyright MIT
MIT License

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: controller.py
File Description: Defines the interface of the Controller module of the racecar_core library.
"""

import abc
from enum import IntEnum


class Controller(abc.ABC):
    """
    Handles input from the controller and exposes constant input state per frame.
    """

    class Button(IntEnum):
        """
        The buttons on the controller.
        """

        A = 0  # A button
        B = 1  # B button
        X = 2  # X button
        Y = 3  # Y button
        LB = 4  # Left bumper
        RB = 5  # Right bumper
        LJOY = 6  # Left joystick button
        RJOY = 7  # Right joystick button

    class Trigger(IntEnum):
        """
        The triggers on the controller.
        """

        LEFT = 0
        RIGHT = 1

    class Joystick(IntEnum):
        """
        The joysticks on the controller.
        """

        LEFT = 0
        RIGHT = 1

    @abc.abstractmethod
    def is_down(self, button: Button) -> bool:
        """
        Returns whether a certain button is currently pressed.

        Args:
            button: Which button to check.

        Returns:
            True if button is currently pressed.

        Note:
            The button argument must be an associated value of the Button enum,
            which is defined in the Controller module.

        Example::

            # This update function will print a message for every frame in which
            # the A button is held down.  Thus, multiple messages will be printed
            # if we press and hold the A button
            def update():
                if rc.controller.is_down(rc.controller.Button.A):
                    print("The A button is currently pressed.")
        """
        pass

    @abc.abstractmethod
    def was_pressed(self, button: Button) -> bool:
        """
        Returns whether a certain button was pressed this frame.

        Args:
            button: Which button to check.

        Returns:
            True if button is currently pressed and was not pressed last frame.

        Note:
            The button argument must be an associated value of the Button enum,
            which is defined in the Controller module.

        Example::

            # This update function will print a single message each time the A
            # button is pressed on the controller
            def update():
                if rc.controller.was_pressed(rc.controller.Button.A):
                    print("The A button was pressed")
        """
        pass

    @abc.abstractmethod
    def was_released(self, button: Button) -> bool:
        """
        Returns whether a certain button was released this frame.

        Args:
            button: Which button to check.

        Returns:
            True if button is currently released and was pressed last frame.

        Note:
            The button argument must be an associated value of the Button enum,
            which is defined in the Controller module.

        Example::

            # This update function will print a single message each time the A
            # button is released on the controller
            def update():
                if rc.controller.was_released(rc.controller.Button.A):
                    print("The A button was released")
        """
        pass

    @abc.abstractmethod
    def get_trigger(self, trigger: Trigger) -> float:
        """
        Returns the position of a certain trigger as a value from 0.0 to 1.0.

        Args:
            trigger: Which trigger to check.

        Returns:
            A value ranging from 0.0 (not pressed) to 1.0 (fully pressed) inclusive.

        Note:
            The trigger argument must be an associated value of the Trigger enum,
            which is defined in the Controller module.

        Example::

            # Speed will receive a value from 0.0 to 1.0 based on how much the left
            # trigger is pressed
            speed = rc.controller.get_trigger(rc.controller.Trigger.LEFT)
        """
        pass

    @abc.abstractmethod
    def get_joystick(self, joystick: Joystick) -> tuple[float, float]:
        """
        Returns the position of a certain joystick as an (x, y) tuple.

        Args:
            joystick: Which joystick to check.

        Returns:
            The x and y coordinate of the joystick, with each axis ranging from
            -1.0 (left or down) to 1.0 (right or up).

        Note:
            The joystick argument must be an associated value of the Joystick enum,
            which is defined in the Controller module.

        Example::

            # x and y will be given values from -1.0 to 1.0 based on the position of
            # the left joystick
            (x, y) = rc.controller.get_joystick(rc.controller.Joystick.LEFT)
        """
        pass
