"""JSON persistence, authentication, and the ClinicData service (composition)."""
import copy
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path

from models import Appointment, MedicalRecord, Patient


def data_dir():
    """Data folder beside the .exe when packaged, beside the source otherwise."""
    base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
    folder = base / "data"
    folder.mkdir(exist_ok=True)
    return folder


class JsonStore:
    def __init__(self, path, default):
        self._path = Path(path)
        self._default = default

    def load(self):
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return copy.deepcopy(self._default)

    def save(self, data):
        tmp = self._path.with_suffix(".tmp")  # write-then-replace avoids half-written files
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, self._path)


class AuthService:
    DEFAULTS = {"admin": ("admin123", "admin"),
                "nurse": ("nurse123", "nurse"),
                "doctor": ("doctor123", "doctor")}

    def __init__(self):
        self._store = JsonStore(data_dir() / "users.json", {})
        self._users = self._store.load()
        if not self._users:
            for name, (pw, role) in self.DEFAULTS.items():
                salt = os.urandom(8).hex()
                self._users[name] = {"salt": salt, "hash": self._hash(pw, salt), "role": role}
            self._store.save(self._users)

    @staticmethod
    def _hash(password, salt):
        return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000).hex()

    def login(self, username, password):
        """Return the user's role, or None if the credentials are wrong."""
        user = self._users.get(username.strip().lower())
        if user and hmac.compare_digest(user["hash"], self._hash(password, user["salt"])):
            return user["role"]
        return None


class ClinicData:
    """Owns all records and their JSON files; enforces cross-record rules."""
    CLASSES = {"patients": Patient, "appointments": Appointment, "records": MedicalRecord}

    def __init__(self):
        folder = data_dir()
        self._stores = {n: JsonStore(folder / f"{n}.json", []) for n in self.CLASSES}
        self._items = {n: [] for n in self.CLASSES}
        for name, cls in self.CLASSES.items():
            for raw in self._stores[name].load():
                try:
                    self._items[name].append(cls.from_dict(raw))
                except (KeyError, ValueError):
                    continue  # skip corrupt entries instead of crashing

    def save(self, name):
        self._stores[name].save([i.to_dict() for i in self._items[name]])

    def items(self, name):
        return list(self._items[name])

    def get(self, name, record_id):
        return next((i for i in self._items[name] if i.id == record_id), None)

    def _next_id(self, name, prefix):
        nums = [int(i.id.split("-")[1]) for i in self._items[name]
                if "-" in i.id and i.id.split("-")[1].isdigit()]
        return f"{prefix}-{max(nums, default=0) + 1:04d}"

    def _validate(self, name, obj):
        if name in ("appointments", "records") and not self.get("patients", obj.patient_id):
            raise ValueError("Selected patient does not exist.")
        if name == "appointments" and obj.status == "Scheduled":
            clash = any(a.id != obj.id and a.status == "Scheduled"
                        and a.date == obj.date and a.slot == obj.slot
                        for a in self._items["appointments"])
            if clash:
                raise ValueError(f"The {obj.slot} slot on {obj.date} is already booked.")

    def add(self, name, obj):
        self._validate(name, obj)
        obj.assign_id(self._next_id(name, obj.PREFIX))
        self._items[name].append(obj)
        self.save(name)

    def update(self, name, obj):
        self._validate(name, obj)
        for i, old in enumerate(self._items[name]):
            if old.id == obj.id:
                self._items[name][i] = obj
                self.save(name)
                return

    def remove(self, name, record_id):
        self._items[name] = [i for i in self._items[name] if i.id != record_id]
        self.save(name)
        if name == "patients":  # cascade
            for other in ("appointments", "records"):
                self._items[other] = [i for i in self._items[other] if i.patient_id != record_id]
                self.save(other)

    def patient_label(self, patient_id):
        p = self.get("patients", patient_id)
        return f"{patient_id} - {p.name}" if p else patient_id

    def queue(self):
        """Active patients ordered by triage priority first, arrival time second."""
        active = [p for p in self._items["patients"] if p.status in ("Waiting", "In Consultation")]
        return sorted(active, key=lambda p: (p.triage_level, p.arrived_at))
