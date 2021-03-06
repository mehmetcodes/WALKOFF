import json
from abc import abstractmethod

from sqlalchemy import Integer, String

from . import database

db = database.db


class App(database.Base, object):

    __tablename__ = 'app'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String)
    devices = db.relationship("Device", back_populates="app")

    def as_json(self, with_devices=False):
        output = {'id': str(self.id), 'name': self.name}
        if with_devices:
            output['devices'] = [device.as_json() for device in self.devices]
        return output

    def __init__(self, app=None, devices=None):
        self.name = app
        if devices is not None:
            for device in devices:
                self.get_config(device)

    def get_config(self, device):
        if device:
            query = dev_class.query.filter_by(name=device).first()
            if query:
                self.config = query
        else:
            self.config = {}

    @abstractmethod
    def shutdown(self):
        return

    @abstractmethod
    def on_pause(self):
        return

    @abstractmethod
    def on_resume(self):
        return


class Device(database.Base):
    __tablename__ = 'device'

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String)
    username = db.Column(db.String(80))
    password = db.Column(db.String(80))
    ip = db.Column(db.String(15))
    port = db.Column(db.Integer())
    extra_fields = db.Column(db.String)
    app_id = db.Column(db.String, db.ForeignKey('app.name'))
    app = db.relationship(App, back_populates="devices")

    def __init__(self, name="", username="", password="", ip="0.0.0.0", port=0, extra_fields="", app_id=""):
        self.name = name
        self.username = username
        self.password = password
        self.ip = ip
        self.port = port
        self.app_id = app_id
        if self.extra_fields != "":
            self.extra_fields = extra_fields.replace("\'", "\"")
        else:
            self.extra_fields = extra_fields

    @staticmethod
    def add_device(name, username, password, ip, port, extra_fields, app_server):
        device = Device(name=name, username=username, password=password, ip=ip, port=port, extra_fields=extra_fields,
                        app_id=app_server)
        db.session.add(device)
        db.session.commit()

    def edit_device(self, form):
        if form.name.data:
            self.name = form.name.data

        if form.username.data:
            self.username = form.username.data

        if form.pw.data:
            self.password = form.pw.data

        if form.ipaddr.data:
            self.ip = form.ipaddr.data

        if form.port.data:
            self.port = form.port.data

        if form.extraFields.data:
            fields_dict = json.loads(form.extraFields.data.replace("\'", "\""))
            if self.extra_fields == "":
                self.extra_fields = form.extraFields.data
            else:
                extra_fields = json.loads(self.extra_fields)
                for field in fields_dict:
                    extra_fields[field] = fields_dict[field]
                self.extra_fields = json.dumps(extra_fields)

    def as_json(self, with_apps=True):
        output = {'id': str(self.id), 'name': self.name, 'username': self.username, 'ip': self.ip,
                  'port': str(self.port)}
        if with_apps:
            output['app'] = self.app.as_json()
        else:
            output['app'] = self.app.name
        if self.extra_fields:
            extra_fields = json.loads(self.extra_fields)
            for field in extra_fields:
                output[field] = extra_fields[field]
        return output

    def __repr__(self):
        return json.dumps({"name": self.name, "username": self.username, "password": self.password,
                           "ip": self.ip, "port": str(self.port), "app": self.app.as_json()})


dev_class = Device()
