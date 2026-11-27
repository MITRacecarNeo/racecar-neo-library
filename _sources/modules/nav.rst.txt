Nav
===============================================

.. code-block:: python

   rc.nav

``rc.nav`` sends the car to points on the loaded map with the car's
navigator, as ``racecar nav`` and the Planner (``http://<car>:8090``) do. A
goal holds the driving, not the program: ``update()`` keeps running, and
``rc.drive`` calls are ignored until the goal ends. A second goal while one
runs is refused. In RacecarSim the status is always ``"off"``.

Each call stands on parts you built earlier in the course:

- the pose on the map: ``rc.slam.get_pose()`` and your localization.
- path planning: compare ``get_path()`` with the path your planner finds.
- path following: what your controller did with ``rc.drive``.
- obstacles: what your lidar code saw before the planner did.

.. code-block:: python

   def update():
       if rc.controller.was_pressed(rc.controller.Button.A):
           rc.nav.go_to(2.0, 1.0)          # map meters, any heading
       if rc.controller.was_pressed(rc.controller.Button.B):
           rc.nav.cancel()
       if rc.nav.get_status() == rc.nav.ARRIVED:
           print("Made it")

The program holds the car from ``create_racecar()`` until it exits, and a
notebook until its kernel is shut down. While something else drives (an app,
a Planner mission), ``rc.drive`` and ``rc.nav`` do nothing and the terminal
says who drives, once.

.. automodule:: nav
   :members:
