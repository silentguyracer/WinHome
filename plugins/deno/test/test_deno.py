import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src'))
sys.path.append(src_path)
import plugin
sys.path.remove(src_path)

class TestDenoPlugin(unittest.TestCase):

    @patch('plugin.shutil.which')
    def test_check_installed_true(self, mock_which):
        mock_which.return_value = "/usr/bin/deno"
        result = plugin.check_installed("req-123")
        self.assertTrue(result)

    @patch('plugin.shutil.which')
    def test_check_installed_false(self, mock_which):
        mock_which.return_value = None
        result = plugin.check_installed("req-123")
        self.assertFalse(result)

    def test_apply_empty_config(self):
        args = {"settings": {}}
        context = {}
        result = plugin.apply_config(args, context, "req-456")
        
        self.assertEqual(result, {
            "requestId": "req-456",
            "success": True,
            "changed": False,
            "data": None
        })

    @patch('plugin.get_deno_config_path')
    @patch('plugin.read_deno_config')
    @patch('plugin.write_deno_config')
    def test_apply_config_no_changes_needed(self, mock_write, mock_read, mock_path):
        mock_path.return_value = "/fake/deno.json"
        mock_read.return_value = {
            "lint": {"rules": {"tags": ["recommended"]}},
            "fmt": {"useTabs": True}
        }
        
        args = {
            "settings": {
                "lint": {"rules": {"tags": ["recommended"]}},
                "fmt": {"useTabs": True}
            }
        }
        context = {}
        
        result = plugin.apply_config(args, context, "req-789")
        
        self.assertEqual(result, {
            "requestId": "req-789",
            "success": True,
            "changed": False,
            "data": None
        })
        mock_write.assert_not_called()

    @patch('plugin.get_deno_config_path')
    @patch('plugin.read_deno_config')
    @patch('plugin.write_deno_config')
    def test_apply_config_changes_needed(self, mock_write, mock_read, mock_path):
        mock_path.return_value = "/fake/deno.json"
        mock_read.return_value = {
            "lint": {"rules": {"tags": ["recommended"]}}
        }
        
        args = {
            "settings": {
                "lint": {"rules": {"tags": ["recommended"]}},
                "fmt": {"useTabs": True},
                "typeCheckOnRun": True
            }
        }
        context = {}
        
        result = plugin.apply_config(args, context, "req-abc")
        
        self.assertEqual(result["requestId"], "req-abc")
        self.assertTrue(result["success"])
        self.assertTrue(result["changed"])
        self.assertEqual(result["data"]["path"], "/fake/deno.json")
        
        mock_write.assert_called_once()
        written_config = mock_write.call_args[0][1]
        self.assertEqual(written_config["fmt"], {"useTabs": True})
        self.assertEqual(written_config["typeCheckOnRun"], True)

    @patch('plugin.get_deno_config_path')
    @patch('plugin.read_deno_config')
    @patch('plugin.write_deno_config')
    @patch('plugin.log')
    def test_apply_config_dry_run(self, mock_log, mock_write, mock_read, mock_path):
        mock_path.return_value = "/fake/deno.json"
        mock_read.return_value = {}
        
        args = {
            "settings": {
                "unstable": ["kv"]
            }
        }
        context = {"dryRun": True}
        
        result = plugin.apply_config(args, context, "req-dry")
        
        self.assertEqual(result["requestId"], "req-dry")
        self.assertTrue(result["success"])
        self.assertTrue(result["changed"])
        self.assertEqual(result["data"]["path"], "/fake/deno.json")
        self.assertEqual(result["data"]["settings"], {"unstable": ["kv"]})
        
        mock_write.assert_not_called()
        self.assertTrue(mock_log.called)

    def test_apply_config_invalid_settings(self):
        args = {"settings": "not-a-dict"}
        context = {}
        result = plugin.apply_config(args, context, "req-inv")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "settings must be an object")

if __name__ == '__main__':
    unittest.main()
