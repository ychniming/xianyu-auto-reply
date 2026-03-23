#!/usr/bin/env python3
"""
基于文件监控的日志收集器
"""

import os
import re
import time
import threading
from collections import deque
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from loguru import logger


class FileLogCollector:
    """基于文件监控的日志收集器"""

    LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} - {message}"
    LOG_ROTATION = "10 MB"
    LOG_RETENTION = "7 days"

    def __init__(self, max_logs: int = 2000):
        self.max_logs = max_logs
        self.logs = deque(maxlen=max_logs)
        self.lock = threading.Lock()

        self.log_file: Optional[str] = None
        self.last_position = 0
        self._running = True

        self.setup_file_monitoring()

    def setup_file_monitoring(self):
        """设置文件监控"""
        possible_files = [
            "xianyu.log",
            "app.log",
            "system.log",
            "logs/xianyu.log",
            "logs/app.log"
        ]

        for file_path in possible_files:
            if os.path.exists(file_path):
                self.log_file = file_path
                break

        if not self.log_file:
            self.log_file = "realtime.log"

        self.setup_loguru_file_output()

        self.monitor_thread = threading.Thread(target=self.monitor_file, daemon=True)
        self.monitor_thread.start()

    def setup_loguru_file_output(self):
        """设置loguru输出到文件"""
        try:
            logger.add(
                self.log_file,
                format=self.LOG_FORMAT,
                level="DEBUG",
                rotation=self.LOG_ROTATION,
                retention=self.LOG_RETENTION,
                enqueue=False,
                buffering=1
            )
            logger.info("文件日志收集器已启动")
        except Exception as e:
            logger.warning(f"无法配置loguru文件输出: {e}")

    def monitor_file(self):
        """监控日志文件变化"""
        while self._running:
            try:
                if os.path.exists(self.log_file):
                    file_size = os.path.getsize(self.log_file)

                    if file_size > self.last_position:
                        with open(self.log_file, 'r', encoding='utf-8') as f:
                            f.seek(self.last_position)
                            new_lines = f.readlines()
                            self.last_position = f.tell()

                        for line in new_lines:
                            self.parse_log_line(line.strip())

                time.sleep(0.5)

            except Exception as e:
                logger.warning(f"监控日志文件时出错: {e}")
                time.sleep(1)

    def parse_log_line(self, line: str):
        """解析日志行"""
        if not line:
            return

        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \| (\w+) \| ([^:]+):([^:]+):(\d+) - (.*)'
        match = re.match(pattern, line)

        if match:
            timestamp_str, level, source, function, line_num, message = match.groups()

            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                timestamp = datetime.now()

            log_entry = {
                "timestamp": timestamp.isoformat(),
                "level": level,
                "source": source,
                "function": function,
                "line": int(line_num),
                "message": message
            }
        else:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "source": "system",
                "function": "unknown",
                "line": 0,
                "message": line
            }

        with self.lock:
            self.logs.append(log_entry)

    def get_logs(self, lines: int = 200, level_filter: str = None, source_filter: str = None) -> List[Dict]:
        """获取日志记录"""
        with self.lock:
            logs_list = list(self.logs)

        if level_filter:
            logs_list = [log for log in logs_list if log['level'] == level_filter]

        if source_filter:
            logs_list = [log for log in logs_list if source_filter.lower() in log['source'].lower()]

        return logs_list[-lines:] if len(logs_list) > lines else logs_list

    def clear_logs(self):
        """清空日志"""
        with self.lock:
            self.logs.clear()

    def get_stats(self) -> Dict:
        """获取日志统计信息"""
        with self.lock:
            total_logs = len(self.logs)

            level_counts: Dict[str, int] = {}
            source_counts: Dict[str, int] = {}

            for log in self.logs:
                level = log['level']
                source = log['source']

                level_counts[level] = level_counts.get(level, 0) + 1
                source_counts[source] = source_counts.get(source, 0) + 1

            return {
                "total_logs": total_logs,
                "level_counts": level_counts,
                "source_counts": source_counts,
                "max_capacity": self.max_logs,
                "log_file": self.log_file
            }

    def stop(self):
        """停止日志收集器"""
        self._running = False


_file_collector: Optional[FileLogCollector] = None


def get_file_log_collector() -> FileLogCollector:
    """获取全局文件日志收集器实例"""
    global _file_collector

    if _file_collector is None:
        with threading.Lock():
            if _file_collector is None:
                _file_collector = FileLogCollector(max_logs=2000)

    return _file_collector


def setup_file_logging():
    """设置文件日志系统"""
    collector = get_file_log_collector()
    return collector


if __name__ == "__main__":
    collector = setup_file_logging()

    logger.info("文件日志收集器测试开始")
    logger.debug("这是调试信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    logger.info("文件日志收集器测试结束")

    time.sleep(2)

    logs = collector.get_logs(10)
    print(f"收集到 {len(logs)} 条日志:")
    for log in logs:
        print(f"  [{log['level']}] {log['source']}: {log['message']}")

    stats = collector.get_stats()
    print(f"\n统计信息: {stats}")
