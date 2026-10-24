"""Domain classes: an abstract Record base class and its concrete subclasses."""
import re
from abc import ABC, abstractmethod
from datetime import datetime

TRIAGE_LEVELS = {1: "Emergent", 2: "Urgent", 3: "Semi-urgent", 4: "Non-urgent"}
PATIENT_STATUSES = ["Waiting", "In Consultation", "Done", "Cancelled"]
GENDERS = ["Female", "Male", "Other"]
APPT_SOURCES = ["Phone Call", "SMS", "Walk-in"]
APPT_STATUSES = ["Scheduled", "Completed", "Cancelled"]
TIME_SLOTS = [f"{h:02d}:{m:02d}" for h in range(8, 17) for m in (0, 30)]
PHONE_RE = re.compile(r"^(09\d{9}|\+639\d{9})$")


# ---- validation helpers (raise ValueError with a user-friendly message) ----
def _text(value, label, max_len=100, required=True):
    value = str(value).strip()
    if required and not value:
        raise ValueError(f"{label} is required.")
    if len(value) > max_len:
        raise ValueError(f"{label} must be at most {max_len} characters.")
    return value


def _choice(value, options, label):
    if value not in options:
        raise ValueError(f"{label} must be one of: {', '.join(map(str, options))}.")
    return value


def _date(value, label="Date"):
    try:
        datetime.strptime(str(value), "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"{label} must be in YYYY-MM-DD format.") from None
    return str(value)


# ---- abstraction: every stored object must implement this interface ----
class Record(ABC):
    PREFIX = "R"

    def __init__(self, record_id=""):
        self._id = record_id  # encapsulated: read through the `id` property

    @property
    def id(self):
        return self._id

    def assign_id(self, record_id):
        self._id = record_id

    @abstractmethod
    def to_dict(self):
        """Return a JSON-serialisable dict."""

    @classmethod
    @abstractmethod
    def from_dict(cls, data):
        """Rebuild an object from a dict."""

    @abstractmethod
    def summary(self):
        """One-line description (overridden differently by each subclass)."""


class Patient(Record):
    PREFIX = "P"

    def __init__(self, name, age, gender, contact, address, triage_level=4,
                 status="Waiting", arrived_at=None, record_id=""):
        super().__init__(record_id)
        self.name = name
        self.age = age
        self.gender = gender
        self.contact = contact
        self.address = address
        self.triage_level = triage_level
        self.status = status
        self._arrived_at = arrived_at or datetime.now().isoformat(timespec="seconds")

    # encapsulation: private fields, validated through property setters
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, v):
        self._name = _text(v, "Name")

    @property
    def age(self):
        return self._age

    @age.setter
    def age(self, v):
        try:
            v = int(v)
        except (TypeError, ValueError):
            raise ValueError("Age must be a whole number.") from None
        if not 0 <= v <= 120:
            raise ValueError("Age must be between 0 and 120.")
        self._age = v

    @property
    def gender(self):
        return self._gender

    @gender.setter
    def gender(self, v):
        self._gender = _choice(v, GENDERS, "Gender")

    @property
    def contact(self):
        return self._contact

    @contact.setter
    def contact(self, v):
        v = re.sub(r"[\s-]", "", str(v))
        if not PHONE_RE.match(v):
            raise ValueError("Contact number must look like 09171234567 or +639171234567.")
        self._contact = v

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, v):
        self._address = _text(v, "Address", 200)

    @property
    def triage_level(self):
        return self._triage_level

    @triage_level.setter
    def triage_level(self, v):
        self._triage_level = _choice(int(v), list(TRIAGE_LEVELS), "Triage level")

    @property
    def triage_label(self):
        return TRIAGE_LEVELS[self._triage_level]

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, v):
        self._status = _choice(v, PATIENT_STATUSES, "Status")

    @property
    def arrived_at(self):
        return self._arrived_at

    def to_dict(self):
        return {"id": self.id, "name": self.name, "age": self.age, "gender": self.gender,
                "contact": self.contact, "address": self.address,
                "triage_level": self.triage_level, "status": self.status,
                "arrived_at": self.arrived_at}

    @classmethod
    def from_dict(cls, d):
        return cls(d["name"], d["age"], d["gender"], d["contact"], d["address"],
                   d["triage_level"], d["status"], d.get("arrived_at"), d["id"])

    def summary(self):
        return f"Patient {self.id}: {self.name} registered (triage {self.triage_level} - {self.triage_label})"


class Appointment(Record):
    PREFIX = "A"

    def __init__(self, patient_id, date, slot, source="Phone Call",
                 status="Scheduled", notes="", record_id=""):
        super().__init__(record_id)
        self._patient_id = _text(patient_id, "Patient")
        self._date = _date(date, "Appointment date")
        self._slot = _choice(slot, TIME_SLOTS, "Time slot")
        self._source = _choice(source, APPT_SOURCES, "Source")
        self._status = _choice(status, APPT_STATUSES, "Status")
        self._notes = _text(notes, "Notes", 300, required=False)

    patient_id = property(lambda s: s._patient_id)
    date = property(lambda s: s._date)
    slot = property(lambda s: s._slot)
    source = property(lambda s: s._source)
    status = property(lambda s: s._status)
    notes = property(lambda s: s._notes)

    def to_dict(self):
        return {"id": self.id, "patient_id": self.patient_id, "date": self.date,
                "slot": self.slot, "source": self.source, "status": self.status,
                "notes": self.notes}

    @classmethod
    def from_dict(cls, d):
        return cls(d["patient_id"], d["date"], d["slot"], d["source"],
                   d["status"], d.get("notes", ""), d["id"])

    def summary(self):
        return f"Appointment {self.id}: {self.patient_id} on {self.date} {self.slot} via {self.source}"


class MedicalRecord(Record):
    PREFIX = "M"

    def __init__(self, patient_id, date, symptoms, diagnosis, medication, record_id=""):
        super().__init__(record_id)
        self._patient_id = _text(patient_id, "Patient")
        self._date = _date(date, "Consultation date")
        self._symptoms = _text(symptoms, "Symptoms", 500)
        self._diagnosis = _text(diagnosis, "Diagnosis", 200)
        self._medication = _text(medication, "Medication", 200)

    patient_id = property(lambda s: s._patient_id)
    date = property(lambda s: s._date)
    symptoms = property(lambda s: s._symptoms)
    diagnosis = property(lambda s: s._diagnosis)
    medication = property(lambda s: s._medication)

    def to_dict(self):
        return {"id": self.id, "patient_id": self.patient_id, "date": self.date,
                "symptoms": self.symptoms, "diagnosis": self.diagnosis,
                "medication": self.medication}

    @classmethod
    def from_dict(cls, d):
        return cls(d["patient_id"], d["date"], d["symptoms"], d["diagnosis"],
                   d["medication"], d["id"])

    def summary(self):
        return f"Consultation {self.id} for {self.patient_id}: {self.diagnosis}"
