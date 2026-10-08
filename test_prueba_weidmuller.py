import unittest

from prueba_weidmuller import convert


class ConversionTest(unittest.TestCase):
    def test_zero_scale(self) -> None:
        value = convert(0, 0.0, 5.0)
        self.assertEqual(value.voltage_v, 0.0)
        self.assertEqual(value.current_equivalent_ma, 4.0)
        self.assertEqual(value.engineering_value, 0.0)
        self.assertEqual(value.status, "CERO_ESCALA_O_LAZO_ABIERTO")

    def test_half_scale(self) -> None:
        value = convert(2048, 0.0, 5.0)
        self.assertAlmostEqual(value.voltage_v, 5.0, places=2)
        self.assertAlmostEqual(value.current_equivalent_ma, 12.0, places=2)
        self.assertAlmostEqual(value.engineering_value, 2.5, places=2)
        self.assertEqual(value.status, "OK")

    def test_full_scale(self) -> None:
        value = convert(4095, 0.0, 5.0)
        self.assertEqual(value.voltage_v, 10.0)
        self.assertEqual(value.current_equivalent_ma, 20.0)
        self.assertEqual(value.engineering_value, 5.0)


if __name__ == "__main__":
    unittest.main()
