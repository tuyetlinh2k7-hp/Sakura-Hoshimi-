"""
🌸 SakuraBot - HoYoLAB Captcha & OTP Session Manager
Quản lý phiên giải Geetest Captcha trên Web và tiếp nhận mã xác thực Email OTP từ HoYoverse.
"""

import time
import asyncio
from typing import Dict, Any, Optional

ACTIVE_CAPTCHA_SESSIONS: Dict[str, Dict[str, Any]] = {}
ACTIVE_OTP_SESSIONS: Dict[str, Dict[str, Any]] = {}
USER_OTP_MAP: Dict[str, str] = {}
USER_CAPTCHA_MAP: Dict[str, str] = {}

def cleanup_expired_sessions():
    """Dọn dẹp các phiên đã quá hạn 5 phút."""
    now = time.time()
    for sid in list(ACTIVE_CAPTCHA_SESSIONS.keys()):
        if now > ACTIVE_CAPTCHA_SESSIONS[sid].get("expires_at", 0):
            sess = ACTIVE_CAPTCHA_SESSIONS.pop(sid, None)
            if sess and sess.get("future") and not sess["future"].done():
                sess["future"].cancel()

    for sid in list(ACTIVE_OTP_SESSIONS.keys()):
        if now > ACTIVE_OTP_SESSIONS[sid].get("expires_at", 0):
            sess = ACTIVE_OTP_SESSIONS.pop(sid, None)
            if sess and sess.get("future") and not sess["future"].done():
                sess["future"].cancel()

    for uid in list(USER_CAPTCHA_MAP.keys()):
        if USER_CAPTCHA_MAP[uid] not in ACTIVE_CAPTCHA_SESSIONS:
            USER_CAPTCHA_MAP.pop(uid, None)

    for uid in list(USER_OTP_MAP.keys()):
        if USER_OTP_MAP[uid] not in ACTIVE_OTP_SESSIONS:
            USER_OTP_MAP.pop(uid, None)

def create_captcha_session(session_id: str, data: Dict[str, Any]) -> None:
    """Tạo mới một phiên chờ giải Captcha trên Web."""
    cleanup_expired_sessions()
    data["created_at"] = time.time()
    data.setdefault("expires_at", time.time() + 300)
    data.setdefault("stage", "login_captcha")
    ACTIVE_CAPTCHA_SESSIONS[session_id] = data
    if "user_id" in data:
        USER_CAPTCHA_MAP[str(data["user_id"])] = session_id

def update_captcha_session(session_id: str, updates: Dict[str, Any]) -> None:
    """Cập nhật trạng thái hoặc dữ liệu MMT cho phiên Captcha."""
    sess = get_captcha_session(session_id)
    if sess:
        sess.update(updates)

def get_captcha_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Lấy thông tin phiên giải Captcha."""
    cleanup_expired_sessions()
    sid = session_id
    if sid not in ACTIVE_CAPTCHA_SESSIONS and sid in USER_CAPTCHA_MAP:
        sid = USER_CAPTCHA_MAP[sid]
    sess = ACTIVE_CAPTCHA_SESSIONS.get(sid)
    if sess and time.time() > sess.get("expires_at", 0):
        ACTIVE_CAPTCHA_SESSIONS.pop(sid, None)
        return None
    return sess

def resolve_captcha_session(session_id: str, result_data: Dict[str, Any]) -> bool:
    """Đánh dấu phiên Captcha đã được giải thành công và truyền kết quả cho bot."""
    sess = get_captcha_session(session_id)
    if not sess:
        return False
    future: Optional[asyncio.Future] = sess.get("future")
    if future and not future.done():
        future.set_result(result_data)
        return True
    return False

def create_otp_session(session_id: str, data: Dict[str, Any]) -> None:
    """Tạo mới một phiên chờ mã OTP Email."""
    cleanup_expired_sessions()
    data["created_at"] = time.time()
    data.setdefault("expires_at", time.time() + 300)
    ACTIVE_OTP_SESSIONS[session_id] = data
    if "user_id" in data:
        USER_OTP_MAP[str(data["user_id"])] = session_id

def get_otp_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Lấy thông tin phiên chờ mã OTP Email."""
    cleanup_expired_sessions()
    sid = session_id
    if sid not in ACTIVE_OTP_SESSIONS and sid in USER_OTP_MAP:
        sid = USER_OTP_MAP[sid]
    sess = ACTIVE_OTP_SESSIONS.get(sid)
    if sess and time.time() > sess.get("expires_at", 0):
        ACTIVE_OTP_SESSIONS.pop(sid, None)
        return None
    return sess

def resolve_otp_session(session_id: str, code: str) -> bool:
    """Đánh dấu đã nhận mã OTP thành công."""
    sess = get_otp_session(session_id)
    if not sess:
        return False
    future: Optional[asyncio.Future] = sess.get("future")
    if future and not future.done():
        future.set_result(code)
        return True
    return False
