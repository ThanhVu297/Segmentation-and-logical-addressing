import unittest

from core.validator import validate_table
from gui.memory_map import addr_to_y, compute_layout, draw_memory_map
from tests.helpers import FakeCanvas, example_table, make_table


class TestLayout(unittest.TestCase):
    def test_addr_to_y_endpoints_and_middle(self):
        self.assertEqual(addr_to_y(0, 5000, 30, 400), 30)
        self.assertEqual(addr_to_y(5000, 5000, 30, 400), 430)
        self.assertEqual(addr_to_y(2500, 5000, 30, 400), 230)

    def test_addr_to_y_clamps_out_of_range(self):
        self.assertEqual(addr_to_y(-10, 5000, 30, 400), 30)
        self.assertEqual(addr_to_y(9999, 5000, 30, 400), 430)

    def test_layout_sorted_by_base_and_proportional(self):
        blocks = compute_layout(example_table(), 5000, top=0, height=500)
        self.assertEqual([b.seg_id for b in blocks], [0, 1, 2])
        # 500 px cho 5000 byte => 0.1 px/byte
        self.assertAlmostEqual(blocks[0].y0, 100)   # base 1000
        self.assertAlmostEqual(blocks[0].y1, 140)   # end 1400
        self.assertAlmostEqual(blocks[1].y0, 200)   # base 2000
        self.assertEqual(blocks[0].label, "Seg 0: 1000-1399 (limit 400, R-X)")

    def test_tiny_segment_gets_minimum_height(self):
        table = make_table([(0, 100, 1, "R--")])
        blk = compute_layout(table, 5000, top=0, height=400, min_block_px=14)[0]
        self.assertGreaterEqual(blk.y1 - blk.y0, 14)

    def test_tiny_segment_at_bottom_does_not_overflow(self):
        table = make_table([(0, 4999, 1, "R--")])
        blk = compute_layout(table, 5000, top=0, height=400, min_block_px=14)[0]
        self.assertLessEqual(blk.y1, 400)
        self.assertGreaterEqual(blk.y1 - blk.y0, 14)

    def test_segment_beyond_memory_is_clamped(self):
        table = make_table([(0, 4800, 1000, "R--")])
        blk = compute_layout(table, 5000, top=0, height=400)[0]
        self.assertLessEqual(blk.y1, 400)

    def test_invalid_mem_size_raises(self):
        with self.assertRaises(ValueError):
            compute_layout(example_table(), 0)


class TestDraw(unittest.TestCase):
    def test_draw_shows_every_segment_and_highlight(self):
        canvas = FakeCanvas()
        blocks = draw_memory_map(canvas, example_table(), 5000, highlight_addr=1100)
        self.assertEqual(len(blocks), 3)
        self.assertTrue(canvas.named("delete"))                     # xóa hình cũ
        self.assertGreaterEqual(len(canvas.named("create_rectangle")), 4)
        self.assertIn("1100", canvas.texts())                       # nhãn địa chỉ
        self.assertTrue(canvas.named("create_line"))                # đường đánh dấu

    def test_draw_ignores_highlight_outside_memory(self):
        canvas = FakeCanvas()
        draw_memory_map(canvas, example_table(), 5000, highlight_addr=6000)
        self.assertFalse(canvas.named("create_line"))

    def test_draw_fault_banner(self):
        canvas = FakeCanvas()
        draw_memory_map(canvas, example_table(), 5000,
                        fault_msg="Offset 1200 vượt limit 1000 của segment 1")
        self.assertTrue(any("CẢNH BÁO" in t and "1200" in t
                            for t in canvas.texts()))

    def test_draw_marks_segments_with_issues_in_red(self):
        table = make_table([(0, 1000, 500, "R--"), (1, 1400, 300, "RW-"),
                            (2, 3000, 100, "R--")])
        canvas = FakeCanvas()
        draw_memory_map(canvas, table, 5000, issues=validate_table(table))
        red = [c for c in canvas.named("create_rectangle")
               if c[2].get("outline") == "#d00000" and c[2].get("width") == 3]
        self.assertEqual(len(red), 2)   # chỉ seg 0 và seg 1 bị viền đỏ


if __name__ == "__main__":
    unittest.main()
