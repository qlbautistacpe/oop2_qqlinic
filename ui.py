"""All PyQt6 windows, pages and dialogs."""
from datetime import date

from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDateEdit, QDialog, QDialogButtonBox, QFormLayout,
    QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QMainWindow,
    QMessageBox, QPushButton, QSpinBox, QStackedWidget, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget)

from models import (APPT_SOURCES, APPT_STATUSES, GENDERS, PATIENT_STATUSES, TIME_SLOTS,
                    TRIAGE_LEVELS, Appointment, MedicalRecord, Patient)


def make_table(headers):
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setAlternatingRowColors(True)
    t.verticalHeader().setVisible(False)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    return t


def add_row(table, cells, key=None):
    r = table.rowCount()
    table.insertRow(r)
    for c, text in enumerate(cells):
        table.setItem(r, c, QTableWidgetItem(str(text)))
    if key is not None:
        table.item(r, 0).setData(Qt.ItemDataRole.UserRole, key)


# ============================== Login window ==============================
class LoginWindow(QWidget):
    logged_in = pyqtSignal(str, str)  # username, role

    def __init__(self, auth):
        super().__init__()
        self._auth = auth
        self.setWindowTitle("Clinic Queue System - Login")
        self.setFixedSize(380, 340)

        title = QLabel("Clinic Queue System")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.error = QLabel("")
        self.error.setObjectName("error")
        self.error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button = QPushButton("Log In")
        button.clicked.connect(self._submit)
        self.password.returnPressed.connect(self._submit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        for w in (title, self.username, self.password, self.error, button):
            layout.addWidget(w)

    def _submit(self):
        user, pw = self.username.text().strip(), self.password.text()
        if not user or not pw:
            self.error.setText("Please enter both username and password.")
            return
        role = self._auth.login(user, pw)
        if role is None:
            self.error.setText("Invalid username or password.")
            self.password.clear()
            return
        self.error.setText("")
        self.password.clear()
        self.logged_in.emit(user, role)


# ================================ Dialogs =================================
class FormDialog(QDialog):
    """Base dialog: subclasses add fields, build() an object; errors show inline."""
    COLLECTION = ""
    TITLE = ""

    def __init__(self, clinic, item=None, parent=None):
        super().__init__(parent)
        self.clinic, self.item = clinic, item
        self.setWindowTitle(("Edit " if item else "Add ") + self.TITLE)
        self.setMinimumWidth(430)
        self.form = QFormLayout()
        self.error = QLabel("")
        self.error.setObjectName("error")
        self.error.setWordWrap(True)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(self.form)
        layout.addWidget(self.error)
        layout.addWidget(buttons)
        self.build_fields()
        if item:
            self.fill(item)

    def build_fields(self): raise NotImplementedError
    def fill(self, item): raise NotImplementedError
    def build(self): raise NotImplementedError

    def accept(self):
        try:
            obj = self.build()
            if self.item:
                self.clinic.update(self.COLLECTION, obj)
            else:
                self.clinic.add(self.COLLECTION, obj)
        except ValueError as e:
            self.error.setText(str(e))
            return
        super().accept()

    def _patient_combo(self):
        combo = QComboBox()
        for p in self.clinic.items("patients"):
            combo.addItem(f"{p.id} - {p.name}", p.id)
        return combo

    def _rid(self):
        return self.item.id if self.item else ""


class PatientDialog(FormDialog):
    COLLECTION, TITLE = "patients", "Patient"

    def build_fields(self):
        self.name_edit = QLineEdit()
        self.age = QSpinBox()
        self.age.setRange(0, 120)
        self.gender = QComboBox()
        self.gender.addItems(GENDERS)
        self.contact = QLineEdit()
        self.contact.setPlaceholderText("09171234567")
        self.address = QLineEdit()
        self.triage = QComboBox()
        for lvl, label in TRIAGE_LEVELS.items():
            self.triage.addItem(f"{lvl} - {label}", lvl)
        self.triage.setCurrentIndex(len(TRIAGE_LEVELS) - 1)
        self.status = QComboBox()
        self.status.addItems(PATIENT_STATUSES)
        for label, w in (("Full name", self.name_edit), ("Age", self.age), ("Gender", self.gender),
                         ("Contact no.", self.contact), ("Address", self.address),
                         ("Triage level", self.triage), ("Ticket status", self.status)):
            self.form.addRow(label, w)

    def fill(self, p):
        self.name_edit.setText(p.name)
        self.age.setValue(p.age)
        self.gender.setCurrentText(p.gender)
        self.contact.setText(p.contact)
        self.address.setText(p.address)
        self.triage.setCurrentIndex(self.triage.findData(p.triage_level))
        self.status.setCurrentText(p.status)

    def build(self):
        return Patient(self.name_edit.text(), self.age.value(), self.gender.currentText(),
                       self.contact.text(), self.address.text(), self.triage.currentData(),
                       self.status.currentText(),
                       arrived_at=self.item.arrived_at if self.item else None,
                       record_id=self._rid())


class AppointmentDialog(FormDialog):
    COLLECTION, TITLE = "appointments", "Appointment"

    def build_fields(self):
        self.patient = self._patient_combo()
        self.date = QDateEdit(QDate.currentDate())
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat("yyyy-MM-dd")
        if not self.item:
            self.date.setMinimumDate(QDate.currentDate())  # no booking in the past
        self.slot = QComboBox()
        self.slot.addItems(TIME_SLOTS)
        self.source = QComboBox()
        self.source.addItems(APPT_SOURCES)
        self.status = QComboBox()
        self.status.addItems(APPT_STATUSES)
        self.notes = QLineEdit()
        for label, w in (("Patient", self.patient), ("Date", self.date), ("Time slot", self.slot),
                         ("Request source", self.source), ("Status", self.status),
                         ("Notes", self.notes)):
            self.form.addRow(label, w)

    def fill(self, a):
        self.patient.setCurrentIndex(self.patient.findData(a.patient_id))
        self.date.setDate(QDate.fromString(a.date, "yyyy-MM-dd"))
        self.slot.setCurrentText(a.slot)
        self.source.setCurrentText(a.source)
        self.status.setCurrentText(a.status)
        self.notes.setText(a.notes)

    def build(self):
        if self.patient.currentData() is None:
            raise ValueError("Register a patient first.")
        return Appointment(self.patient.currentData(), self.date.date().toString("yyyy-MM-dd"),
                           self.slot.currentText(), self.source.currentText(),
                           self.status.currentText(), self.notes.text(), self._rid())


class RecordDialog(FormDialog):
    COLLECTION, TITLE = "records", "Medical Record"

    def build_fields(self):
        self.patient = self._patient_combo()
        self.date = QDateEdit(QDate.currentDate())
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat("yyyy-MM-dd")
        self.symptoms = QTextEdit()
        self.symptoms.setFixedHeight(80)
        self.diagnosis = QLineEdit()
        self.medication = QLineEdit()
        for label, w in (("Patient", self.patient), ("Date", self.date),
                         ("Symptoms", self.symptoms), ("Diagnosis", self.diagnosis),
                         ("Medication", self.medication)):
            self.form.addRow(label, w)

    def fill(self, r):
        self.patient.setCurrentIndex(self.patient.findData(r.patient_id))
        self.date.setDate(QDate.fromString(r.date, "yyyy-MM-dd"))
        self.symptoms.setPlainText(r.symptoms)
        self.diagnosis.setText(r.diagnosis)
        self.medication.setText(r.medication)

    def build(self):
        if self.patient.currentData() is None:
            raise ValueError("Register a patient first.")
        return MedicalRecord(self.patient.currentData(), self.date.date().toString("yyyy-MM-dd"),
                             self.symptoms.toPlainText(), self.diagnosis.text(),
                             self.medication.text(), self._rid())


# ============================== Table pages ===============================
class TablePage(QWidget):
    """Reusable CRUD page; subclasses supply headers, cells() and a dialog."""
    changed = pyqtSignal()
    COLLECTION = ""
    NOUN = ""
    HEADERS = []
    DIALOG = None
    EDIT_ROLES = set()

    def __init__(self, clinic, role):
        super().__init__()
        self.clinic = clinic
        heading = QLabel(self.NOUN + "s")
        heading.setObjectName("heading")
        self.search = QLineEdit()
        self.search.setPlaceholderText(f"Search {self.NOUN.lower()}s by ID, name or any column...")
        self.search.textChanged.connect(self.refresh)
        self.add_btn = QPushButton(f"Add {self.NOUN}")
        self.edit_btn = QPushButton("Edit")
        self.del_btn = QPushButton("Delete")
        self.del_btn.setObjectName("danger")
        self.add_btn.clicked.connect(self.add)
        self.edit_btn.clicked.connect(self.edit)
        self.del_btn.clicked.connect(self.delete)
        allowed = role in self.EDIT_ROLES
        for b in (self.add_btn, self.edit_btn, self.del_btn):
            b.setEnabled(allowed)
            b.setToolTip("" if allowed else f"Your role ({role}) cannot modify this data.")
        self.table = make_table(self.HEADERS)
        self.table.doubleClicked.connect(lambda *_: self.edit())

        self.bar = QHBoxLayout()
        self.bar.addWidget(self.search, 1)
        for b in (self.add_btn, self.edit_btn, self.del_btn):
            self.bar.addWidget(b)
        layout = QVBoxLayout(self)
        layout.addWidget(heading)
        layout.addLayout(self.bar)
        layout.addWidget(self.table)
        self.refresh()

    def visible_items(self): return self.clinic.items(self.COLLECTION)
    def cells(self, obj): raise NotImplementedError

    def refresh(self):
        term = self.search.text().strip().lower()
        self.table.setRowCount(0)
        for obj in self.visible_items():
            cells = self.cells(obj)
            if term and term not in " ".join(cells).lower():
                continue
            add_row(self.table, cells, obj.id)

    def selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "No selection", f"Please select a {self.NOUN.lower()} first.")
            return None
        return self.clinic.get(self.COLLECTION, self.table.item(row, 0).data(Qt.ItemDataRole.UserRole))

    def _done(self):
        self.refresh()
        self.changed.emit()

    def add(self):
        if self.DIALOG(self.clinic, parent=self).exec():
            self._done()

    def edit(self):
        obj = self.selected()
        if obj and self.DIALOG(self.clinic, obj, self).exec():
            self._done()

    def delete(self):
        obj = self.selected()
        if not obj:
            return
        answer = QMessageBox.question(self, "Confirm delete",
                                      f"Delete {obj.id}? This cannot be undone.")
        if answer == QMessageBox.StandardButton.Yes:
            self.clinic.remove(self.COLLECTION, obj.id)
            self._done()


class PatientsPage(TablePage):
    COLLECTION, NOUN, DIALOG = "patients", "Patient", PatientDialog
    HEADERS = ["Patient ID", "Name", "Age", "Gender", "Contact", "Triage", "Ticket Status"]
    EDIT_ROLES = {"nurse", "admin"}

    def __init__(self, clinic, role):
        super().__init__(clinic, role)
        self.status_box = QComboBox()
        self.status_box.addItems(PATIENT_STATUSES)
        apply_btn = QPushButton("Update Ticket Status")
        apply_btn.clicked.connect(self.apply_status)
        self.bar.addWidget(self.status_box)
        self.bar.addWidget(apply_btn)

    def cells(self, p):
        return [p.id, p.name, p.age, p.gender, p.contact,
                f"{p.triage_level} - {p.triage_label}", p.status]

    def apply_status(self):
        p = self.selected()
        if p:
            p.status = self.status_box.currentText()
            self.clinic.save("patients")
            self._done()


class AppointmentsPage(TablePage):
    COLLECTION, NOUN, DIALOG = "appointments", "Appointment", AppointmentDialog
    HEADERS = ["ID", "Patient", "Date", "Time", "Source", "Status"]
    EDIT_ROLES = {"admin", "nurse"}

    def visible_items(self):
        return sorted(self.clinic.items("appointments"), key=lambda a: (a.date, a.slot))

    def cells(self, a):
        return [a.id, self.clinic.patient_label(a.patient_id), a.date, a.slot, a.source, a.status]


class RecordsPage(TablePage):
    COLLECTION, NOUN, DIALOG = "records", "Medical Record", RecordDialog
    HEADERS = ["ID", "Patient", "Date", "Diagnosis", "Medication"]
    EDIT_ROLES = {"doctor", "admin"}

    def cells(self, r):
        return [r.id, self.clinic.patient_label(r.patient_id), r.date, r.diagnosis, r.medication]


# ================================ Dashboard ===============================
class DashboardPage(QWidget):
    def __init__(self, clinic):
        super().__init__()
        self.clinic = clinic
        self.values = {}
        cards = QHBoxLayout()
        for key, label in (("patients", "Registered Patients"), ("waiting", "Waiting in Queue"),
                           ("appointments", "Upcoming Appointments"), ("records", "Medical Records")):
            card = QFrame()
            card.setObjectName("card")
            box = QVBoxLayout(card)
            value = QLabel("0")
            value.setObjectName("cardValue")
            caption = QLabel(label)
            caption.setObjectName("cardLabel")
            box.addWidget(value)
            box.addWidget(caption)
            cards.addWidget(card)
            self.values[key] = value

        q_head = QLabel("Active Queue (sorted by triage priority)")
        q_head.setObjectName("heading")
        self.queue = make_table(["Patient ID", "Name", "Triage", "Ticket Status"])
        a_head = QLabel("Recent Activity")
        a_head.setObjectName("heading")
        self.activity = QListWidget()
        self.activity.setMaximumHeight(140)

        layout = QVBoxLayout(self)
        layout.addLayout(cards)
        for w in (q_head, self.queue, a_head, self.activity):
            layout.addWidget(w)
        self.refresh()

    def refresh(self):
        c, today = self.clinic, date.today().isoformat()
        queue = c.queue()
        self.values["patients"].setText(str(len(c.items("patients"))))
        self.values["waiting"].setText(str(sum(p.status == "Waiting" for p in queue)))
        self.values["appointments"].setText(str(sum(
            a.status == "Scheduled" and a.date >= today for a in c.items("appointments"))))
        self.values["records"].setText(str(len(c.items("records"))))

        self.queue.setRowCount(0)
        for p in queue:
            add_row(self.queue, [p.id, p.name, f"{p.triage_level} - {p.triage_label}", p.status])

        self.activity.clear()
        for name in ("patients", "appointments", "records"):
            for rec in c.items(name)[-3:]:
                self.activity.addItem(rec.summary())  # polymorphic call


# =============================== Main window ==============================
class MainWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self, clinic, username, role):
        super().__init__()
        self.setWindowTitle("Clinic Queue Management")
        self.resize(1050, 680)
        self.pages = {"Dashboard": DashboardPage(clinic),
                      "Patients": PatientsPage(clinic, role),
                      "Appointments": AppointmentsPage(clinic, role),
                      "Medical Records": RecordsPage(clinic, role)}
        self.stack = QStackedWidget()
        for page in self.pages.values():
            self.stack.addWidget(page)
        self.setCentralWidget(self.stack)

        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self._action("Log out", self.logout_requested.emit))
        file_menu.addAction(self._action("Exit", self.close, "Ctrl+Q"))
        view_menu = menubar.addMenu("&View")
        new_menu = menubar.addMenu("&New")
        new_menu.addAction(self._action("Patient", lambda: self.quick_add("Patients"), "Ctrl+N"))
        new_menu.addAction(self._action("Appointment", lambda: self.quick_add("Appointments")))
        new_menu.addAction(self._action("Medical Record", lambda: self.quick_add("Medical Records")))
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self._action("About", self.about))

        toolbar = self.addToolBar("Navigation")
        toolbar.setMovable(False)
        for name in self.pages:
            act = self._action(name, lambda n=name: self.show_page(n))
            view_menu.addAction(act)
            toolbar.addAction(act)

        self.statusBar().showMessage(f"Logged in as {username} ({role})")
        self.show_page("Dashboard")

    def _action(self, text, slot, shortcut=None):
        act = QAction(text, self)
        act.triggered.connect(lambda *_: slot())
        if shortcut:
            act.setShortcut(shortcut)
        return act

    def show_page(self, name):
        page = self.pages[name]
        page.refresh()
        self.stack.setCurrentWidget(page)

    def quick_add(self, name):
        self.show_page(name)
        self.pages[name].add()
        self.pages["Dashboard"].refresh()

    def about(self):
        QMessageBox.about(self, "About", "Clinic Queue Management\nPyQt6 desktop app with JSON storage.")
