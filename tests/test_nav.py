"""rc.nav and rc.drive's hold on the car: NavReal against a test navigator, DriveReal against a test lease, the simulator stub."""

import pytest

import racecar_utils
from nav import Nav

rclpy = pytest.importorskip("rclpy")


@pytest.fixture
def ros(monkeypatch):
    monkeypatch.setenv("ROS_DOMAIN_ID", "95")  # away from a running car
    rclpy.init()
    from rclpy.executors import SingleThreadedExecutor

    executor = SingleThreadedExecutor()
    yield executor
    executor.shutdown()
    rclpy.try_shutdown()


# -- rc.drive: one source at a time --


class FakeLease:
    def __init__(self):
        self.free = True
        self.holder = "Planner is driving."
        self.nav = False
        self.held = True
        self.released = False

    def hold(self):
        self.held = self.free
        return self.held

    def refused(self):
        return self.holder

    def release(self):
        self.released = True


@pytest.fixture
def drive(ros):
    from drive_real import DriveReal

    lease = FakeLease()
    d = DriveReal(lease)
    sent = []
    d._DriveReal__publisher = type("P", (), {"publish": lambda self, m: sent.append(m.drive.speed)})()
    return d, lease, sent


def tick(d, n=1):
    for _ in range(n):
        d._DriveReal__update()


def test_drives_while_it_holds_the_car(drive):
    d, lease, sent = drive
    d.set_speed_angle(1.0, 0.0)
    tick(d)
    assert sent == [0.25] and d.holds_car() and d.refused_by() == ""


def test_refused_says_so_once_and_sends_nothing(drive, capsys):
    d, lease, sent = drive
    lease.free = False
    d.set_speed_angle(0.5, 0.0)
    tick(d, 5)
    out = capsys.readouterr().out
    told = "Planner is driving. rc.drive will not drive the car until it stops."
    assert sent == [] and out.count(told) == 1
    assert not d.holds_car() and d.refused_by() == "Planner is driving."
    lease.holder = "Web Teleop is driving."
    tick(d)
    assert "Web Teleop is driving." in capsys.readouterr().out


def test_free_again_it_drives_from_a_stop(drive, capsys):
    d, lease, sent = drive
    lease.free = False
    d.set_speed_angle(0.5, 0.0)
    tick(d)
    lease.free = True
    tick(d, 2)
    assert sent == [0.0, 0.0]  # still asking to move: zero until it stops
    told = "Planner has stopped driving. rc.drive will now drive the car again after a speed reset to 0."
    assert told in capsys.readouterr().out
    d.set_speed_angle(0.0, 0.0)
    tick(d)
    d.set_speed_angle(0.4, 0.0)
    tick(d)
    assert sent[-1] == pytest.approx(0.1)


def test_while_nav_drives_drive_calls_are_ignored(drive, capsys):
    d, lease, sent = drive
    d.set_speed_angle(1.0, 0.0)
    d._nav_drives(True)
    assert lease.nav
    d.set_speed_angle(1.0, 0.0)
    d.stop()
    tick(d, 3)
    assert sent == [] and capsys.readouterr().out.count("rc.drive does nothing while rc.nav drives.") == 1
    d._nav_drives(False)
    tick(d)
    assert sent == [0.0] and not lease.nav  # at zero until the next drive call


def test_without_the_driver_it_drives_as_before(ros, monkeypatch):
    import drive_real

    monkeypatch.setattr(drive_real, "program_lease", lambda: None)
    d = drive_real.DriveReal()
    assert d.holds_car() and d.refused_by() == ""


# -- rc.nav against a test navigator --


class FakeLink:
    def __init__(self, node):
        self.alive = True
        self.state = {"state": "idle", "owner": "", "reason": "", "left": None}
        self.sent = []
        self.answer = (True, "")

    def view(self):
        return dict(self.state)

    def command(self, verb, wait=None, **fields):
        self.sent.append((verb, fields))
        if verb == "start" and self.answer[0]:
            self.state = {**self.state, "state": "running", "owner": fields["owner"], "left": 3.0}
        if verb == "stop" and self.state["state"] in ("running", "paused"):
            self.state = {**self.state, "state": "stopped"}
        return self.answer

    def notify(self, verb, **fields):
        self.sent.append((verb, fields))


class FakeSlam:
    def __init__(self):
        self.pose = (1.0, 2.0, 90.0)
        self.map = "hall"

    def get_pose_async(self):
        return self.pose

    def get_map_name(self):
        return self.map


class FakeDrive:
    def __init__(self):
        self.nav = []

    def _nav_drives(self, on):
        self.nav.append(on)


@pytest.fixture
def nav(ros, tmp_path, monkeypatch):
    from racecar_neo_ros2_driver import missions
    from nav_real import NavReal

    monkeypatch.setenv("RACECAR_MAP_ROOT", str(tmp_path))
    links = []

    def modules():
        def make(node):
            links.append(FakeLink(node))
            return links[-1]

        return make, missions

    drive, slam = FakeDrive(), FakeSlam()
    n = NavReal(drive, slam, modules=modules, executor=ros)
    n.links, n.drive_, n.slam_, n.missions = links, drive, slam, missions
    return n


def link(n):
    return n.links[0]


def test_nothing_before_the_first_call(nav):
    assert nav.node is None and nav.links == []
    nav.cancel()
    assert nav.node is None


def test_go_to_holds_the_driving_until_it_arrives(nav):
    assert nav.go_to(2.0, 1.0, 180) and nav.is_active() and nav.get_status() == Nav.NAVIGATING
    verb, fields = link(nav).sent[0]
    assert verb == "start" and fields["heartbeat"] and fields["name"] == "Program"
    assert fields["mission"]["waypoints"][0]["heading_deg"] == 180.0
    assert nav.drive_.nav == [True] and nav.get_distance_left() == 3.0
    nav._NavReal__tick()
    assert link(nav).sent[-1][0] == "alive"
    link(nav).state["state"] = "arrived"
    nav._NavReal__tick()
    assert nav.get_status() == Nav.ARRIVED and not nav.is_active() and nav.drive_.nav == [True, False]
    assert nav.get_distance_left() is None


@pytest.mark.parametrize(
    "state, word",
    [("dwelling", Nav.WAITING), ("relocalizing", Nav.LOST), ("paused", Nav.PAUSED)],
)
def test_status_words_that_hold_the_driving(nav, state, word):
    nav.go_to(2.0, 1.0)
    link(nav).state["state"] = state
    assert nav.get_status() == word and nav.is_active()


@pytest.mark.parametrize(
    "state, word",
    [("failed", Nav.FAILED), ("stalled", Nav.STALLED), ("stopped", Nav.CANCELED)],
)
def test_endings(nav, state, word):
    nav.go_to(2.0, 1.0)
    link(nav).state["state"] = state
    nav._NavReal__tick()
    assert nav.get_status() == word and not nav.is_active()


def test_seeing_the_end_gives_the_driving_back_at_once(nav):
    nav.go_to(2.0, 1.0)
    link(nav).state["state"] = "arrived"
    assert nav.get_status() == Nav.ARRIVED and nav.drive_.nav == [True, False]
    assert nav.get_status() == Nav.ARRIVED  # stays until the next goal


def test_another_front_end_taking_over_reads_canceled(nav):
    nav.go_to(2.0, 1.0)
    link(nav).state["owner"] = "planner"
    assert nav.get_status() == Nav.CANCELED


def test_a_second_call_while_one_runs_is_refused_once(nav, capsys):
    nav.go_to(2.0, 1.0)
    for _ in range(30):
        assert not nav.go_to(3.0, 1.0)
    assert capsys.readouterr().out.count("rc.nav is already driving.") == 1
    assert [v for v, _ in link(nav).sent].count("start") == 1


def test_refused_by_the_navigator_says_why_once(nav, capsys):
    nav.go_to(0, 0)  # connects
    nav.cancel()
    link(nav).answer = (False, "Planner is driving.")
    for _ in range(10):
        assert not nav.go_to(2.0, 1.0)
    assert capsys.readouterr().out.count("Planner is driving.") == 1
    assert nav.drive_.nav[-1] is False and nav.get_status() == Nav.CANCELED


def test_idle_and_off(nav):
    assert nav.get_status() == Nav.IDLE
    link(nav).alive = False
    assert nav.get_status() == Nav.OFF and not nav.go_to(1, 1)


def test_cancel_stops_only_its_own_goal(nav):
    nav.get_status()
    nav.cancel()
    assert link(nav).sent == []
    nav.go_to(2.0, 1.0)
    nav.cancel()
    assert link(nav).sent[-1][0] == "stop" and nav.get_status() == Nav.CANCELED
    assert nav.drive_.nav == [True, False]


def test_move_along_the_heading(nav):
    assert nav.move(2.0)
    wp = link(nav).sent[0][1]["mission"]["waypoints"][0]
    assert (wp["x"], wp["y"], wp["heading_deg"]) == (pytest.approx(1.0), pytest.approx(4.0), 90.0)
    nav.cancel()
    nav.slam_.pose = None
    assert not nav.move(1.0)


def test_missions_run_without_recording(nav):
    nav.missions.save("hall", "loop", {"loops": 2, "record": {"on": True}, "waypoints": [{"x": 1, "y": 2}]})
    assert nav.get_missions() == ["loop"]
    assert nav.run_mission("loop")
    mission = link(nav).sent[0][1]["mission"]
    assert mission["loops"] == 2 and mission["record"]["on"] is False
    nav.cancel()
    assert not nav.run_mission("none")
    nav.slam_.map = ""
    assert nav.get_missions() == [] and not nav.run_mission("loop")


def test_a_bad_goal_is_refused(nav, capsys):
    assert not nav.go_to(float("nan"), 0.0)
    assert "Not a goal" in capsys.readouterr().out


def test_the_path_while_driving(nav):
    from nav_msgs.msg import Path
    from geometry_msgs.msg import PoseStamped

    nav.go_to(2.0, 1.0)
    msg = Path(poses=[PoseStamped(), PoseStamped()])
    msg.poses[1].pose.position.x = 2.0
    nav._NavReal__on_plan(msg)
    assert nav.get_path() == [(0.0, 0.0), (2.0, 0.0)]
    nav.cancel()
    assert nav.get_path() == []


def test_wait_returns_the_ending(nav):
    nav.go_to(2.0, 1.0)
    link(nav).state["state"] = "arrived"
    nav._NavReal__tick()
    assert nav.wait(timeout=1.0) == Nav.ARRIVED


def test_without_the_driver_everything_is_off(ros, monkeypatch):
    from nav_real import NavReal

    warnings = []
    monkeypatch.setattr(racecar_utils, "print_warning", warnings.append)
    n = NavReal(FakeDrive(), FakeSlam(), modules=lambda: None, executor=ros)
    assert not n.go_to(1, 1) and n.get_status() == Nav.OFF and n.get_missions() == []
    assert n.node is None and len(warnings) == 1


def test_sim_stub_reports_off_and_warns_once(monkeypatch):
    from nav_sim import NavSim

    warnings = []
    monkeypatch.setattr(racecar_utils, "print_warning", warnings.append)
    s = NavSim()
    assert not s.go_to(1, 1) and not s.move(1) and not s.run_mission("x")
    assert s.get_status() == Nav.OFF and s.wait() == Nav.OFF and s.get_path() == []
    assert len(warnings) == 1
