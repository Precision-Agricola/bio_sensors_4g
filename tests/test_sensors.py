import unittest
from src.sensors.base import Sensor, register_sensor, get_sensor_by_model

@register_sensor("DUMMY", "TEST")
class DummySensor(Sensor):
    def _read_implementation(self):
        return {"dummy": 123}

class TestSensors(unittest.TestCase):
    def test_sensor_read(self):
        sensor = DummySensor(name="Dummy", model="dummy", protocol="test", vin=3.3, signal="dummy")
        self.assertEqual(sensor.read(), {"dummy": 123})

    def test_sensor_registry(self):
        sensor_cls = get_sensor_by_model("dummy", "test")
        self.assertIsNotNone(sensor_cls)
        sensor = sensor_cls(name="Dummy", model="dummy", protocol="test", vin=3.3, signal="dummy")
        self.assertEqual(sensor.read(), {"dummy": 123})

if __name__ == "__main__":
    unittest.main()
