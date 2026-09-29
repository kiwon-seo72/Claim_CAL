"""Owner isolation regression checks using a small local SQL database."""

import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

import storage


class StorageIsolationTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        with self.engine.begin() as db:
            db.execute(text("""CREATE TABLE cases (
                id INTEGER PRIMARY KEY, owner_id INTEGER NOT NULL, name TEXT, injury TEXT,
                status TEXT, created_at TEXT, rows_json TEXT, notes TEXT)"""))
            db.execute(text("""CREATE TABLE documents (
                id INTEGER PRIMARY KEY, case_id INTEGER, filename TEXT, mime_type TEXT,
                content BLOB, extracted_text TEXT, analysis TEXT DEFAULT '', created_at TEXT DEFAULT '')"""))
        self.patch = patch.object(storage, "get_engine", return_value=self.engine)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.engine.dispose()

    def test_each_user_only_sees_and_changes_their_own_case_and_documents(self):
        a = storage.create_case(1, "A 고객", "골절")
        b = storage.create_case(2, "B 고객", "염좌")
        self.assertEqual([row[0] for row in storage.list_cases(1)], [a])
        self.assertEqual([row[0] for row in storage.list_cases(2)], [b])

        storage.save_case(2, a, status="종결")
        self.assertEqual(storage.list_cases(1)[0][3], "접수")
        with self.assertRaises(Exception):
            storage.add_document(2, a, "wrong.pdf", "application/pdf", b"private", "")

        doc_id = storage.add_document(1, a, "medical.pdf", "application/pdf", b"private", "text")
        self.assertEqual(storage.list_documents(2, a), [])
        self.assertIsNone(storage.get_document(2, a, doc_id))
        storage.save_analysis(2, a, doc_id, {"leak": True})
        self.assertEqual(storage.get_document(1, a, doc_id)["analysis"], "")
        storage.save_analysis(1, a, doc_id, {"ok": True})
        self.assertIn('"ok": true', storage.get_document(1, a, doc_id)["analysis"])

    def test_password_hash_is_salted_and_verified(self):
        first = storage._hash_password("correct horse battery")
        second = storage._hash_password("correct horse battery")
        self.assertNotEqual(first, second)
        self.assertTrue(storage._verify_password("correct horse battery", first))
        self.assertFalse(storage._verify_password("wrong", first))


if __name__ == "__main__":
    unittest.main()
