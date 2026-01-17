import subprocess
import os
import json
from pathlib import Path

class Extractor:
    def process_xcresult(self, xcresult_path: Path, output_dir: Path):
        """Extract screenshots from an xcresult bundle."""
        if not xcresult_path.exists():
            return

        # 1. Get Root Info
        root_json = self._run_xcresulttool(['get', 'object', '--path', str(xcresult_path), '--format', 'json'])
        if not root_json: 
            print("Failed to get root json")
            return
        
        # 'actions' -> _values -> 'actionResult' -> 'testsRef'
        actions = root_json.get('actions', {}).get('_values', [])
        
        for action in actions:
            action_result = action.get('actionResult', {})
            if action_result:
                # testsRef is directly inside actionResult
                tests_ref = action_result.get('testsRef', {}).get('id', {}).get('_value')
                if tests_ref:
                    self._traverse_tests(xcresult_path, tests_ref, output_dir)

    def _traverse_action_result(self, xcresult_path, ref_id, output_dir):
        # Get Action Result
        res = self._run_xcresulttool(['get', 'object', '--path', str(xcresult_path), '--id', ref_id, '--format', 'json'])
        if not res: 
            return
        
        # Look for TestRef
        tests_ref = res.get('testsRef', {}).get('id', {}).get('_value')
        if tests_ref:
            self._traverse_tests(xcresult_path, tests_ref, output_dir)
            
    def _traverse_tests(self, xcresult_path, ref_id, output_dir):
        res = self._run_xcresulttool(['get', 'object', '--path', str(xcresult_path), '--id', ref_id, '--format', 'json'])
        if not res: 
            return
        
        # 'summaries' -> _values -> 'testableSummaries' -> ...
        summaries = res.get('summaries', {}).get('_values', [])
        
        for summary in summaries:
            testables = summary.get('testableSummaries', {}).get('_values', [])
            for testable in testables:
                # Tests (Groups)
                tests = testable.get('tests', {}).get('_values', [])
                self._walk_tests_groups(xcresult_path, tests, output_dir)

    def _walk_tests_groups(self, xcresult_path, nodes, output_dir):
        for node in nodes:
            # Check for subtests or direct activitySummaries (unlikely in groups but possible)
            subtests = node.get('subtests', {}).get('_values', [])
            if subtests:
                self._walk_tests_groups(xcresult_path, subtests, output_dir)
            
            # Check if this node is a test case with a summaryRef
            # Check if this node is a test case with a summaryRef
            summary_ref = node.get('summaryRef', {}).get('id', {}).get('_value')
            if summary_ref:
                # Fetch the detailed summary for this test case
                self._process_test_summary(xcresult_path, summary_ref, output_dir)

    def _process_test_summary(self, xcresult_path, ref_id, output_dir):
        res = self._run_xcresulttool(['get', 'object', '--path', str(xcresult_path), '--id', ref_id, '--format', 'json'])
        if not res: 
            return
        
        # Now we look for activitySummaries
        activity_summaries = res.get('activitySummaries', {}).get('_values', [])
        self._walk_activity_summaries(xcresult_path, activity_summaries, output_dir)

    def _walk_activity_summaries(self, xcresult_path, nodes, output_dir):
        for node in nodes:
            self._extract_from_activity_summaries(xcresult_path, node, output_dir)
            
            # Recurse into subactivities
            sub_activities = node.get('subactivities', {}).get('_values', [])
            if sub_activities:
                self._walk_activity_summaries(xcresult_path, sub_activities, output_dir)

    def _extract_from_activity_summaries(self, xcresult_path, node, output_dir):
        # Find attachments
        attachments = node.get('attachments', {}).get('_values', [])
        for attachment in attachments:
            name = attachment.get('name', {}).get('_value')
            filename = attachment.get('filename', {}).get('_value')
            payload_ref = attachment.get('payloadRef', {}).get('id', {}).get('_value')
            
            if name and payload_ref:
                out_name = f"{name}.png"
                out_path = output_dir / out_name
                
                subprocess.run([
                    'xcrun', 'xcresulttool', 'export', '--legacy',
                    '--path', str(xcresult_path),
                    '--id', payload_ref,
                    '--output-path', str(out_path),
                    '--type', 'file'
                ], check=False, capture_output=True, text=True)

    def _run_xcresulttool(self, args):
        cmd = ['xcrun', 'xcresulttool'] + args
        if args[0] == 'get' and '--legacy' not in args:
             # Insert --legacy after 'object' if present, else after 'get'
             if 'object' in args:
                 idx = args.index('object')
                 args.insert(idx + 1, '--legacy')
             else:
                 args.insert(1, '--legacy')
             cmd = ['xcrun', 'xcresulttool'] + args

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(res.stdout)
        except subprocess.CalledProcessError as e:
            print(f"   stderr: {e.stderr}")
            return None
