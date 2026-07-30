from django.apps import AppConfig


class WorkerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.worker'

    def ready(self):
        # 避免重复启动（开发服务器会reload两次）
        import os
        if os.environ.get('RUN_MAIN') != 'true':
            return

        from .runner import ChatWorker

        worker = ChatWorker()
        worker.start()