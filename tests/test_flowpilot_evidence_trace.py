"""Focused local-only evidence/trace safety tests for FlowPilot 3.0."""
import csv
from hashlib import sha256
import tempfile
import unittest
from pathlib import Path

from flowpilot_csv_report import preview, execute, ReportRefused
from flowpilot_workflow_graph import build_graph
from flowpilot_audit_view import recent_runs


class EvidenceTraceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.src = self.root / 'source.csv'
        self.db = self.root / 'audit.sqlite'
        self._set_rows([('alice', '1.25'), ('alice', '2.75'), ('bob', '3')])

    def _set_rows(self, rows):
        with self.src.open('w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['customer', 'revenue'])
            writer.writerows(rows)

    def _plan(self):
        return preview(self.root, ['source.csv'], 'summary.csv', group='customer', amount='revenue')

    def test_trace_matches_preview_graph_and_sha(self):
        digest_before = sha256(self.src.read_bytes()).hexdigest()
        plan = self._plan()
        graph = build_graph(plan)
        record = execute(self.root, plan, approval='APPROVE_EXECUTION', audit_db=self.db)
        output_digest = sha256((self.root / 'summary.csv').read_bytes()).hexdigest()
        self.assertEqual(record['report_sha256'], output_digest)
        self.assertEqual(digest_before, sha256(self.src.read_bytes()).hexdigest())
        self.assertEqual([item['node_id'] for item in record['node_trace']],
                         [item['id'] for item in graph['nodes']])
        self.assertEqual(record['node_trace'][0]['source_sha256'], digest_before)
        self.assertEqual(record['node_trace'][-2]['report_sha256'], output_digest)
        self.assertEqual(record['audit_kind'], 'FLOWPILOT_LOCAL_EVIDENCE_NOT_SOVIA')
        self.assertEqual(recent_runs(self.db)['runs'][0]['record'], record)

    def test_spreadsheet_formula_group_refused_without_output(self):
        for group in ('=1+2', '+cmd', '-1+2', '@SUM(1,2)', '  =HYPERLINK(0)'):
            with self.subTest(group=group):
                self._set_rows([(group, '1')])
                with self.assertRaises(ReportRefused):
                    execute(self.root, self._plan(), approval='APPROVE_EXECUTION', audit_db=self.db)
                self.assertFalse((self.root / 'summary.csv').exists())
                self.assertFalse(self.db.exists())

    def test_extra_csv_columns_fail_closed(self):
        self.src.write_text('customer,revenue\nalice,1,unexpected\n', encoding='utf-8')
        with self.assertRaises(ReportRefused):
            execute(self.root, self._plan(), approval='APPROVE_EXECUTION', audit_db=self.db)
        self.assertFalse((self.root / 'summary.csv').exists())

    def test_replay_no_overwrite(self):
        plan = self._plan()
        execute(self.root, plan, approval='APPROVE_EXECUTION', audit_db=self.db)
        with self.assertRaises(ReportRefused):
            execute(self.root, plan, approval='APPROVE_EXECUTION', audit_db=self.db)
        self.assertEqual(recent_runs(self.db)['count'], 1)


if __name__ == '__main__':
    unittest.main()
