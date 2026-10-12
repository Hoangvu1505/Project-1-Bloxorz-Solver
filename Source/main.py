"""
Điểm khởi chạy chính của trò chơi Bloxorz (GUI Pygame).
"""

import sys
import os

source_dir = os.path.dirname(os.path.abspath(__file__))
if source_dir not in sys.path:
    sys.path.insert(0, source_dir)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from gui.app import BloxorzGUI


#hàm cần code lại
def main():
    """Khởi động trò chơi Bloxorz với giao diện đồ hoạ tương tác Pygame."""
    print("=" * 60)
    print("   KHỞI ĐỘNG TRÒ CHƠI BLOXORZ SOLVER (FIT HCMUS)")
    print("=" * 60)
    app = BloxorzGUI()
    app.run()


if __name__ == "__main__":
    main()

