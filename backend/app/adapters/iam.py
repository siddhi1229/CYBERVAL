from datetime import UTC, datetime, timedelta
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.base import BaseSourceAdapter
from app.models.entities import Asset, User, UserAssetAccess

logger = logging.getLogger(__name__)

# Key core users establishing high-risk and baseline identity profiles
CORE_USERS: list[dict[str, Any]] = [
    {
        "user_id_code": "USR-001",
        "username": "admin.singh",
        "email": "admin.singh@cyberval.net",
        "display_name": "Admin Singh",
        "role": "database_admin",
        "department": "Engineering",
        "privilege_level": "critical",
        "privileged": True,
        "mfa_enabled": False,  # High risk trigger
        "account_status": "active",
        "failed_login_count": 17,  # Brute force trigger
        "risky_login": True,
        "last_login": datetime.now(UTC) - timedelta(minutes=15),
        "accessed_assets": ["PAYMENT-API-01", "PAYMENT-DB-01", "CUSTOMER-DB-01"],
    },
    {
        "user_id_code": "USR-002",
        "username": "cloud.lead",
        "email": "cloud.lead@cyberval.net",
        "display_name": "Sarah Cloud Lead",
        "role": "cloud_architect",
        "department": "CloudOps",
        "privilege_level": "critical",
        "privileged": True,
        "mfa_enabled": True,
        "account_status": "active",
        "failed_login_count": 0,
        "risky_login": False,
        "last_login": datetime.now(UTC) - timedelta(hours=2),
        "accessed_assets": ["PAYMENT-API-01", "S3-CUSTOMER-DATA", "GATEWAY-01"],
    },
    {
        "user_id_code": "USR-003",
        "username": "secops.analyst",
        "email": "secops.analyst@cyberval.net",
        "display_name": "Devin SecOps",
        "role": "security_analyst",
        "department": "SecOps",
        "privilege_level": "high",
        "privileged": True,
        "mfa_enabled": True,
        "account_status": "active",
        "failed_login_count": 1,
        "risky_login": False,
        "last_login": datetime.now(UTC) - timedelta(hours=1),
        "accessed_assets": ["GATEWAY-01", "AUTH-SERVER-01"],
    },
    {
        "user_id_code": "USR-004",
        "username": "contractor.dev",
        "email": "contractor.dev@external.cyberval.net",
        "display_name": "Alex Contractor",
        "role": "contractor_developer",
        "department": "Product",
        "privilege_level": "standard",
        "privileged": False,
        "mfa_enabled": False,
        "account_status": "active",
        "failed_login_count": 4,
        "risky_login": True,
        "last_login": datetime.now(UTC) - timedelta(days=1),
        "accessed_assets": ["PAYMENT-API-01"],
    },
    {
        "user_id_code": "USR-005",
        "username": "svc.payment.engine",
        "email": "svc-payment-engine@system.cyberval.net",
        "display_name": "Service Account - Payment Engine",
        "role": "service_account",
        "department": "Engineering",
        "privilege_level": "critical",
        "privileged": True,
        "mfa_enabled": False,  # Non-interactive API service account
        "account_status": "active",
        "failed_login_count": 0,
        "risky_login": False,
        "last_login": datetime.now(UTC) - timedelta(minutes=5),
        "accessed_assets": ["PAYMENT-API-01", "PAYMENT-DB-01"],
    },
]


class IAMSimulator:
    """Deterministic generator for realistic IAM users and asset access permissions."""

    @classmethod
    def generate(cls, count: int = 35) -> list[dict[str, Any]]:
        users: list[dict[str, Any]] = [dict(u) for u in CORE_USERS]

        roles = [
            ("dev", "Software Engineer", "Engineering", "standard", False, True),
            ("sre", "Site Reliability Engineer", "DevOps", "high", True, True),
            ("data", "Data Analyst", "Data", "standard", False, True),
            ("finance", "Financial Controller", "Finance", "standard", False, True),
            ("qa", "QA Automation Engineer", "Product", "standard", False, True),
            ("intern", "Engineering Intern", "Engineering", "standard", False, False),
            ("svc", "Service Integration Bot", "IT", "elevated", True, False),
        ]

        index = len(users) + 1
        role_idx = 0
        now = datetime.now(UTC)
        while len(users) < max(count, len(CORE_USERS)):
            prefix, role_name, dept, priv_lvl, is_priv, mfa = roles[role_idx % len(roles)]
            code = f"USR-{index:03d}"
            username = f"{prefix}.user{index:02d}"
            email = f"{username}@cyberval.net"
            display_name = f"{dept} User {index:02d}"
            failed_logins = (index * 3) % 7 if not mfa else (index % 2)
            risky = failed_logins >= 3

            # Deterministic asset access links
            accessed: list[str] = []
            if dept == "Engineering":
                accessed.extend(["PAYMENT-API-01", f"APP-{index % 10 + 1:03d}"])
            elif dept == "Data":
                accessed.extend(["CUSTOMER-DB-01", f"DB-{index % 5 + 1:03d}"])
            elif dept == "DevOps":
                accessed.extend(["GATEWAY-01", "PAYMENT-API-01", f"CLOUD-{index % 5 + 1:03d}"])
            else:
                accessed.append(f"APP-{index % 15 + 1:03d}")

            users.append({
                "user_id_code": code,
                "username": username,
                "email": email,
                "display_name": display_name,
                "role": role_name.lower().replace(" ", "_"),
                "department": dept,
                "privilege_level": priv_lvl,
                "privileged": is_priv,
                "mfa_enabled": mfa,
                "account_status": "active" if index % 12 != 0 else "suspended",
                "failed_login_count": failed_logins,
                "risky_login": risky,
                "last_login": now - timedelta(hours=index * 2),
                "accessed_assets": accessed,
            })
            index += 1
            role_idx += 1

        return users[:count]


class IAMAdapter(BaseSourceAdapter):
    """Adapter for ingesting and normalizing enterprise identity data and asset access grants."""

    @property
    def source_name(self) -> str:
        return "iam"

    def fetch(self, count: int = 35, **kwargs) -> list[dict[str, Any]]:
        return IAMSimulator.generate(count=count)

    def normalize(self, raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for r in raw_records:
            code = r.get("user_id_code") or r.get("user_id") or r.get("id_code")
            email = r.get("email") or f"{code or 'user'}@cyberval.net"
            uname = r.get("username") or email.split("@")[0]
            display = r.get("display_name") or uname.replace(".", " ").title()
            priv_lvl = str(r.get("privilege_level", "standard")).lower()
            priv = bool(r.get("privileged", priv_lvl in ("critical", "high", "elevated")))
            mfa = bool(r.get("mfa_enabled", True))
            failed = int(r.get("failed_login_count", 0))
            risky = bool(r.get("risky_login", failed >= 5 or (priv and not mfa)))

            normalized.append({
                "user_id_code": code.strip().upper() if code else None,
                "email": email.strip().lower(),
                "username": uname.strip().lower(),
                "display_name": display.strip(),
                "role": str(r.get("role", "employee")).strip(),
                "department": str(r.get("department", "IT")).strip(),
                "privilege_level": priv_lvl if priv_lvl in ("standard", "elevated", "high", "critical") else "standard",
                "privileged": priv,
                "mfa_enabled": mfa,
                "account_status": str(r.get("account_status", "active")).lower(),
                "failed_login_count": failed,
                "risky_login": risky,
                "last_login": r.get("last_login"),
                "accessed_assets": r.get("accessed_assets", []),
            })
        return normalized

    def validate(self, normalized_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        valid: list[dict[str, Any]] = []
        for r in normalized_records:
            if r.get("email") and "@" in r["email"]:
                valid.append(r)
        return valid

    def ingest(self, db: Session, records: list[dict[str, Any]] | None = None, count: int = 35, **kwargs) -> int:
        if records is None:
            raw = self.fetch(count=count)
        else:
            raw = records

        normalized = self.normalize(raw)
        validated = self.validate(normalized)

        # Pre-fetch existing assets mapped by asset_id_code and name
        assets_by_code: dict[str, Asset] = {}
        for a in db.scalars(select(Asset)).all():
            if a.asset_id_code:
                assets_by_code[a.asset_id_code.upper()] = a
            assets_by_code[a.name.upper()] = a

        ingested_count = 0
        for item in validated:
            email = item["email"]
            code = item["user_id_code"]

            user = None
            if code:
                user = db.scalar(select(User).where(User.user_id_code == code))
            if not user:
                user = db.scalar(select(User).where(User.email == email))

            if not user:
                user = User(email=email, display_name=item["display_name"], role=item["role"])
                db.add(user)

            user.user_id_code = code or user.user_id_code
            user.username = item["username"]
            user.display_name = item["display_name"]
            user.role = item["role"]
            user.department = item["department"]
            user.privilege_level = item["privilege_level"]
            user.privileged = item["privileged"]
            user.mfa_enabled = item["mfa_enabled"]
            user.account_status = item["account_status"]
            user.failed_login_count = item["failed_login_count"]
            user.risky_login = item["risky_login"]
            user.last_login = item["last_login"]
            db.flush()

            # Create or update asset access relationships
            for asset_key in item.get("accessed_assets", []):
                target_asset = assets_by_code.get(str(asset_key).strip().upper())
                if target_asset:
                    existing_access = db.scalar(
                        select(UserAssetAccess).where(
                            UserAssetAccess.user_id == user.id,
                            UserAssetAccess.asset_id == target_asset.id,
                        )
                    )
                    if not existing_access:
                        access_level = "admin" if user.privileged else "read"
                        db.add(
                            UserAssetAccess(
                                user_id=user.id,
                                asset_id=target_asset.id,
                                access_level=access_level,
                                status="active",
                            )
                        )

            ingested_count += 1

        db.commit()
        return ingested_count
