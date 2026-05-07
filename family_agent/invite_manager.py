"""
Invite Manager
Generates invite links and QR codes for family joining
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json
import hashlib
import qrcode
from io import BytesIO


class InviteManager:
    """Manage family invite links"""

    def __init__(self, data_dir: str = "data", expiry_days: int = 7):
        self.data_dir = Path(data_dir)
        self.invite_file = self.data_dir / "invites.json"
        self.expiry_days = expiry_days
        self._load_invites()

    def _load_invites(self):
        """Load invites data"""
        if self.invite_file.exists():
            with open(self.invite_file, 'r', encoding='utf-8') as f:
                self.invites = json.load(f)
        else:
            self.invites = []

    def _save_invites(self):
        """Save invites data"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.invite_file, 'w', encoding='utf-8') as f:
            json.dump(self.invites, f, ensure_ascii=False, indent=2)

    def create_invite(self, family_id: str, creator: str) -> Dict:
        """
        Create a new invite
        Returns: {'code': str, 'url': str, 'expires_at': str}
        """
        # Generate unique code
        raw = f"{family_id}_{creator}_{datetime.now().isoformat()}"
        code = hashlib.md5(raw.encode()).hexdigest()[:12]

        invite = {
            'code': code,
            'family_id': family_id,
            'creator': creator,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=self.expiry_days)).isoformat(),
            'used': False
        }

        self.invites.append(invite)
        self._save_invites()

        return {
            'code': code,
            'url': f"http://localhost:3000/join?code={code}",  # Update with actual domain
            'expires_at': invite['expires_at']
        }

    def validate_invite(self, code: str) -> Optional[Dict]:
        """
        Validate an invite code
        Returns: invite dict if valid, None if invalid/expired
        """
        for invite in self.invites:
            if invite['code'] == code:
                # Check if used
                if invite['used']:
                    return None
                # Check if expired
                expires_at = datetime.fromisoformat(invite['expires_at'])
                if datetime.now() > expires_at:
                    return None
                return invite
        return None

    def mark_used(self, code: str):
        """Mark invite as used"""
        for invite in self.invites:
            if invite['code'] == code:
                invite['used'] = True
                break
        self._save_invites()

    def generate_qr_code(self, code: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Generate QR code for invite
        Returns: path to QR code image, or None if failed
        """
        invite = self.validate_invite(code)
        if not invite:
            return None

        url = f"http://localhost:3000/join?code={code}"  # Update with actual domain

        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            if output_path is None:
                output_path = str(self.data_dir / f"invite_{code}.png")

            img.save(output_path)
            return output_path
        except Exception:
            return None

    def cleanup_expired(self):
        """Remove expired invites"""
        before_count = len(self.invites)
        self.invites = [
            i for i in self.invites
            if datetime.now() < datetime.fromisoformat(i['expires_at'])
        ]
        self._save_invites()
        return before_count - len(self.invites)
