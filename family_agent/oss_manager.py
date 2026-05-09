"""
阿里云 OSS 管理模块
支持图片上传、删除、URL 生成
"""
import os
import logging
from typing import Optional
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class OSSManager:
    """阿里云 OSS 管理器"""

    def __init__(self):
        self.enabled = False
        self.bucket = None
        self.bucket_name = ""
        self.endpoint = ""
        self.public_url = ""

        access_key_id = os.getenv("OSS_ACCESS_KEY_ID", "")
        access_key_secret = os.getenv("OSS_ACCESS_KEY_SECRET", "")
        self.bucket_name = os.getenv("OSS_BUCKET_NAME", "")
        self.endpoint = os.getenv("OSS_ENDPOINT", "")
        self.public_url = os.getenv("OSS_PUBLIC_URL", "")

        if not all([access_key_id, access_key_secret, self.bucket_name, self.endpoint]):
            logger.warning("OSS 配置不完整，使用本地存储")
            return

        try:
            import oss2
            auth = oss2.Auth(access_key_id, access_key_secret)
            self.bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)
            # 测试连接
            self.bucket.get_bucket_info()
            self.enabled = True
            logger.info(f"✅ 阿里云 OSS 初始化成功: {self.bucket_name}")
        except Exception as e:
            logger.warning(f"⚠️ OSS 初始化失败，使用本地存储: {e}")

    def upload_file(self, local_path: str, remote_path: str) -> Optional[str]:
        """上传文件到 OSS

        Args:
            local_path: 本地文件路径
            remote_path: OSS 远程路径

        Returns:
            文件的公开访问 URL，失败返回 None
        """
        if not self.enabled:
            return None
        try:
            self.bucket.put_object_from_file(remote_path, local_path)
            if self.public_url:
                return urljoin(self.public_url.rstrip("/") + "/", remote_path)
            return urljoin(
                f"https://{self.bucket_name}.{self.endpoint}/",
                remote_path
            )
        except Exception as e:
            logger.error(f"OSS 上传失败: {e}")
            return None

    def upload_bytes(self, data: bytes, remote_path: str, content_type: str = "") -> Optional[str]:
        """上传字节数据到 OSS"""
        if not self.enabled:
            return None
        try:
            headers = {"Content-Type": content_type} if content_type else {}
            self.bucket.put_object(remote_path, data, headers=headers)
            if self.public_url:
                return urljoin(self.public_url.rstrip("/") + "/", remote_path)
            return urljoin(
                f"https://{self.bucket_name}.{self.endpoint}/",
                remote_path
            )
        except Exception as e:
            logger.error(f"OSS 上传失败: {e}")
            return None

    def delete_file(self, remote_path: str) -> bool:
        """从 OSS 删除文件"""
        if not self.enabled:
            return False
        try:
            self.bucket.delete_object(remote_path)
            return True
        except Exception as e:
            logger.error(f"OSS 删除失败: {e}")
            return False

    def get_url(self, remote_path: str) -> Optional[str]:
        """获取文件的公开访问 URL"""
        if not self.enabled:
            return None
        if self.public_url:
            return urljoin(self.public_url.rstrip("/") + "/", remote_path)
        return urljoin(
            f"https://{self.bucket_name}.{self.endpoint}/",
            remote_path
        )

    def generate_signed_url(self, remote_path: str, expires: int = 3600) -> Optional[str]:
        """生成签名 URL（私有权限时使用）"""
        if not self.enabled:
            return None
        try:
            return self.bucket.sign_url("GET", remote_path, expires)
        except Exception as e:
            logger.error(f"OSS 签名 URL 生成失败: {e}")
            return None


# 全局单例
_oss_instance: Optional[OSSManager] = None


def get_oss_manager() -> OSSManager:
    global _oss_instance
    if _oss_instance is None:
        _oss_instance = OSSManager()
    return _oss_instance
