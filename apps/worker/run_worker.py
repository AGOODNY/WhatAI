import os
import django

# 初始化 Django 环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.worker.tasks import start_worker

if __name__ == "__main__":
    print("[Worker] starting...")
    start_worker()