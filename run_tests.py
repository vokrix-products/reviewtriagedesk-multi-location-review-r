import unittest

from processor import ALLOWED_STATUSES, process_file


class ProcessorTests(unittest.TestCase):
    def setUp(self):
        self.csv_bytes = (
            b"review_id,source_platform,reviewer_name,location_name,response_status\n"
            b"1001,Google,Alice Johnson,Downtown Cafe,draft_generated\n"
            b"1002,Yelp,Bob Smith,Uptown Cafe,new\n"
        )

    def test_process_csv_returns_list(self):
        records = process_file(self.csv_bytes)
        self.assertIsInstance(records, list)
        self.assertTrue(len(records) >= 1)

    def test_record_shape_and_status(self):
        records = process_file(self.csv_bytes)
        for record in records:
            self.assertIn("title", record)
            self.assertIn("status", record)
            self.assertIn("details", record)
            self.assertIn("due_date", record)
            self.assertIsInstance(record["details"], dict)
            self.assertIn(record["status"], ALLOWED_STATUSES)

    def test_due_date_is_top_level_only(self):
        csv_with_due_date = (
            b"review_id,sla_due_at\n"
            b"2001,2025-02-01T09:30:00Z\n"
        )
        records = process_file(csv_with_due_date)
        self.assertTrue(len(records) >= 1)
        record = records[0]
        self.assertEqual(record["due_date"], "2025-02-01T09:30:00Z")
        self.assertNotIn("due_date", record["details"])
        self.assertNotIn("sla_due_at", record["details"])

    def test_fallback_text_extraction(self):
        records = process_file(b"hello world\nsecond line\n")
        self.assertIsInstance(records, list)
        self.assertTrue(len(records) >= 1)


if __name__ == "__main__":
    unittest.main()
