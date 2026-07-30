import os
import sys
import django

# 把项目根目录加入 Python 路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

# 指定 Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django.setup()

from apps.worker.tasks import start_worker

if __name__ == "__main__":
    print("[Worker] starting...")
    start_worker()