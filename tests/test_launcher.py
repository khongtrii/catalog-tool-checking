from __future__ import annotations

import socket
import unittest

from launcher import HOST, find_available_port, streamlit_options


class LauncherTests(unittest.TestCase):
    def test_busy_port_is_not_selected_and_released_port_is_selected(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
            occupied.bind((HOST, 0))
            port = occupied.getsockname()[1]
            with self.assertRaises(RuntimeError):
                find_available_port(port, port)

        self.assertEqual(find_available_port(port, port), port)

    def test_streamlit_is_production_only_and_loopback_bound(self) -> None:
        options = streamlit_options(8555)
        self.assertIs(options["global.developmentMode"], False)
        self.assertEqual(options["server.address"], "127.0.0.1")
        self.assertEqual(options["server.port"], 8555)
        self.assertIs(options["browser.gatherUsageStats"], False)


if __name__ == "__main__":
    unittest.main()
