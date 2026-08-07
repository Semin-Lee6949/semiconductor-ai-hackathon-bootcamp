import unittest

import pandas as pd

from lessons.data_quality_visualization_demo import (
    build_report,
    iqr_outlier_mask,
    prepare_visualization_view,
)


class DataQualityVisualizationTests(unittest.TestCase):
    def test_iqr_flags_extreme_value_without_deleting_it(self):
        series = pd.Series([1, 1, 2, 2, 2, 3, 100])
        mask = iqr_outlier_mask(series)
        self.assertTrue(mask.iloc[-1])
        self.assertEqual(len(mask), len(series))

    def test_report_counts_noise_and_visual_view_keeps_raw_unchanged(self):
        raw = pd.DataFrame(
            {
                "tool_id": ["T1", "T1", "T2", "T2", "T2"],
                "sequence": [1, 1, 2, 3, 4],
                "value": [1.0, 1.0, None, 3.0, 100.0],
            }
        )
        original = raw.copy(deep=True)
        report = build_report(raw)
        view = prepare_visualization_view(raw)

        self.assertEqual(report["exact_duplicate_rows"], 1)
        self.assertEqual(report["missing_by_column"]["value"], 1)
        self.assertEqual(len(view), 4)
        self.assertFalse(view["value"].isna().any())
        pd.testing.assert_frame_equal(raw, original)


if __name__ == "__main__":
    unittest.main()
