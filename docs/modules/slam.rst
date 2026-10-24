Slam
===============================================

.. code-block:: python

   rc.slam

Maps are built and loaded with ``racecar map`` on the car or in the map viewer
(``http://<car>:8084``); ``rc.slam`` reads the car's position on the map, the
map itself, and whether the position can be trusted. In RacecarSim the mode is
always ``"off"``.

.. code-block:: python

   def update():
       if rc.slam.is_localized():
           x, y, heading = rc.slam.get_pose()        # meters, meters, degrees
           m = rc.slam.get_map()
           if m.value_at(x + 0.5, y) == 100:         # wall 0.5 m along the map's x axis
               rc.drive.set_speed_angle(0, 0)

.. automodule:: slam
   :members:
