"""
Invite Manager - PostgreSQL版
Generates invite links and QR codes for family joining
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
import hashlib
import qrcode
from io import BytesIO


class InviteManager:
    """Manage family invite links - PostgreSQL版"""

    def __init__(self, db_manager=None, data_dir: str = "data", expiry_days: int = 7):
        """
        初始化邀请管理器
        Args:
            db_manager: DatabaseManager 实例
            data_dir: 数据目录（用于QR码存储）
            expiry_days: 邀请有效期天数
        """
        self.db = db_manager
        self.data_dir = data_dir
        self.expiry_days = expiry_days

    def create_invite(self, family_id: str, creator: str) -> Dict:
        """
        Create a new invite
        Returns: {'code': str, 'url': str, 'expires_at': str}
        """
        # Generate unique code
        raw = f"{family_id}_{creator}_{datetime.now().isoformat()}"
        code = hashlib.md5(raw.encode()).hexdigest()[:12]

        expires_at = (datetime.now() + timedelta(days=self.expiry_days)).isoformat()

        if self.db:
            self.db.add_invite(
                code=code,
                family_id=family_id,
                creator=creator,
                expires_at=expires_at
            )

        return {
            'code': code,
            'url': f"http://localhost:3000/join?code={code}",
            'expires_at': expires_at
        }

    def validate_invite(self, code: str) -> Optional[Dict]:
        """
        Validate an invite code
        Returns: invite dict if valid, None if invalid/expired
        """
        if not self.db:
            return None

        invite = self.db.get_invite(code)
        if not invite:
            return None

        # Check if used
        if invite.get('used'):
            return None

        # Check if expired
        expires_at = datetime.fromisoformat(invite['expires_at'])
        if datetime.now() > expires_at:
            return None

        return dict(invite)

    def mark_used(self, code: str):
        """Mark invite as used"""
        if self.db:
            self.db.mark_invite_used(code)

    def generate_qr_code(self, code: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Generate QR code for invite
        Returns: path to QR code image, or None if failed
        """
        invite = self.validate_invite(code)
        if not invite:
            return None

        url = f"http://localhost:3000/join?code={code}"

        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            if output_path is None:
                from pathlib import Path
                data_dir = Path(self.data_dir)
                data_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(data_dir / f"invite_{code}.png")

            img.save(output_path)
            return output_path
        except Exception:
            return None

    def cleanup_expired(self) -> int:
        """Remove expired invites from database"""
        if not self.db:
            return 0

        invites = self.db.execute_query(
            "SELECT code FROM invites WHERE expires_at < %s AND used = FALSE",
            (datetime.now().isoformat(),)
        )
        count = len(invites)
        for invite in invites:
            # Mark as used (we use 'used' field to indicate expired)
            self.db.mark_invite_used(invite['code'])
        return count
