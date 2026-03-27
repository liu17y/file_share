# backend/stats_manager.py
import os
import json
from datetime import datetime, timedelta
from pathlib import Path


class StatsManager:
    """统计管理器"""

    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.log_file = os.path.join(base_dir, '.upload_logs.json')
        self._init_log_file()

    def _init_log_file(self):
        """初始化日志文件"""
        try:
            if not os.path.exists(self.log_file):
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)
        except Exception as e:
            print(f"初始化日志文件失败: {e}")

    def log_upload(self, file_name, file_size, target_path):
        """记录上传日志"""
        try:
            # 读取现有日志
            logs = self._read_logs()

            # 添加新日志
            logs.append({
                "file_name": file_name,
                "file_size": file_size,
                "target_path": target_path,
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime('%Y-%m-%d'),
                "hour": datetime.now().strftime('%Y-%m-%d %H:00:00')
            })

            # 只保留最近90天的日志
            ninety_days_ago = datetime.now() - timedelta(days=90)
            logs = [log for log in logs if datetime.fromisoformat(log['timestamp']) > ninety_days_ago]

            # 写入日志
            self._write_logs(logs)
            return True

        except Exception as e:
            print(f"记录上传日志失败: {e}")
            return False

    def _read_logs(self):
        """读取日志"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"读取日志失败: {e}")
            return []

    def _write_logs(self, logs):
        """写入日志"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"写入日志失败: {e}")

    def get_today_uploads_count(self):
        """获取今日上传数量"""
        try:
            logs = self._read_logs()
            today = datetime.now().strftime('%Y-%m-%d')
            today_logs = [log for log in logs if log.get('date') == today]
            return len(today_logs)
        except Exception as e:
            print(f"获取今日上传数量失败: {e}")
            return 0

    def get_today_uploads_size(self):
        """获取今日上传总大小"""
        try:
            logs = self._read_logs()
            today = datetime.now().strftime('%Y-%m-%d')
            today_logs = [log for log in logs if log.get('date') == today]
            total_size = sum(log.get('file_size', 0) for log in today_logs)
            return total_size
        except Exception as e:
            print(f"获取今日上传大小失败: {e}")
            return 0

    def get_upload_trend(self, days=7):
        """获取上传趋势数据"""
        try:
            logs = self._read_logs()
            trend_data = []

            for i in range(days - 1, -1, -1):
                date = datetime.now() - timedelta(days=i)
                date_str = date.strftime('%m/%d')
                full_date = date.strftime('%Y-%m-%d')

                # 统计该天的上传数量
                day_logs = [log for log in logs if log.get('date') == full_date]
                count = len(day_logs)
                size = sum(log.get('file_size', 0) for log in day_logs)

                trend_data.append({
                    "date": date_str,
                    "full_date": full_date,
                    "count": count,
                    "size": size
                })

            return trend_data
        except Exception as e:
            print(f"获取上传趋势失败: {e}")
            return []

    def get_hourly_stats(self, date=None):
        """获取指定日期的小时统计"""
        try:
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')

            logs = self._read_logs()
            date_logs = [log for log in logs if log.get('date') == date]

            hourly_stats = {}
            for hour in range(24):
                hour_key = f"{date} {hour:02d}:00:00"
                hourly_stats[hour] = {
                    "hour": hour,
                    "count": 0,
                    "size": 0
                }

            for log in date_logs:
                if 'hour' in log:
                    hour = int(log['hour'].split(' ')[1].split(':')[0])
                    hourly_stats[hour]['count'] += 1
                    hourly_stats[hour]['size'] += log.get('file_size', 0)

            return list(hourly_stats.values())
        except Exception as e:
            print(f"获取小时统计失败: {e}")
            return []

    def get_top_files(self, limit=10):
        """获取最大的文件记录"""
        try:
            logs = self._read_logs()
            # 按文件大小排序
            sorted_logs = sorted(logs, key=lambda x: x.get('file_size', 0), reverse=True)
            return sorted_logs[:limit]
        except Exception as e:
            print(f"获取最大文件记录失败: {e}")
            return []

    def get_user_stats(self):
        """获取用户统计（如果有用户系统）"""
        # 如果没有用户系统，返回空数据
        return {
            "total_uploads": len(self._read_logs()),
            "total_size": sum(log.get('file_size', 0) for log in self._read_logs()),
            "active_users": 0
        }

    def clear_old_logs(self, days=30):
        """清理旧日志"""
        try:
            logs = self._read_logs()
            cutoff_date = datetime.now() - timedelta(days=days)
            new_logs = [log for log in logs if datetime.fromisoformat(log['timestamp']) > cutoff_date]
            self._write_logs(new_logs)
            return len(logs) - len(new_logs)
        except Exception as e:
            print(f"清理旧日志失败: {e}")
            return 0


# 创建全局实例
stats_manager = None


def init_stats_manager(base_dir):
    """初始化统计管理器"""
    global stats_manager
    stats_manager = StatsManager(base_dir)
    return stats_manager