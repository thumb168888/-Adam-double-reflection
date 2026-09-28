import unittest

from PIL import Image

from app import reflect_region, selected_image_box


class ReflectionTests(unittest.TestCase):
    def test_reflection_rotates_both_axes_without_resizing(self):
        image = Image.new("RGB", (3, 2))
        values = [(1, 0, 0), (2, 0, 0), (3, 0, 0), (4, 0, 0), (5, 0, 0), (6, 0, 0)]
        image.putdata(values)

        reflected = reflect_region(image, (1, 0, 3, 2))

        self.assertEqual(reflected.size, (2, 2))
        pixels = lambda picture: [
            picture.getpixel((x, y))
            for y in range(picture.height)
            for x in range(picture.width)
        ]
        self.assertEqual(pixels(reflected), [values[5], values[4], values[2], values[1]])
        self.assertEqual(pixels(image), values)

    def test_selection_scales_and_clamps_to_image(self):
        self.assertEqual(
            selected_image_box((20, 20), (150, 70), (10, 10, 110, 60), (200, 100)),
            (20, 20, 200, 100),
        )
        self.assertIsNone(
            selected_image_box((20, 20), (21, 21), (10, 10, 110, 60), (200, 100))
        )


if __name__ == "__main__":
    unittest.main()
