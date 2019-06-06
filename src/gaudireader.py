import tempfile
import zipfile
import yaml
import os
from chimerax.core import models, io
from chimerax.core.commands import run, concise_model_spec


class GaudiModel(object):
    def __init__(self, controller, path, session, *args, **kwargs):
        self.path = path
        self.controller = controller
        self.basedir = os.path.dirname(path)
        self.data, self.headers, self.keys = self.parse()
        self.tempdir = tempfile.mkdtemp("gaudiviewx")
        self.session = session
        self.models = {}

    def parse(self):
        with open(self.path, "r") as f:
            self.first_line = f.readline()
            self.raw_data = yaml.safe_load(f)
        datarray = [[k] + v for k, v in self.raw_data["GAUDI.results"].items()]
        keys = self.raw_data["GAUDI.results"].keys()
        header = ["Filename"] + list(
            map(lambda text: text.split()[0], self.raw_data["GAUDI.objectives"])
        )
        return datarray, header, keys

    def parse_zip(self, key):
        path = os.path.join(self.basedir, key)
        name = os.path.splitext(os.path.basename(path))[0]
        try:
            z = zipfile.ZipFile(path)
        except:
            print("{} is not a valid GAUDI result".format(path))
        else:
            tmp = os.path.join(self.tempdir, name)
            try:
                os.mkdir(tmp)
            except OSError:
                pass
            z.extractall(tmp)
            mol2 = [
                os.path.join(tmp, name)
                for name in z.namelist()
                if name.endswith(".mol2")
            ]
            models = []
            for mol2_file in mol2:
                if "Protein" in mol2_file:
                    mol2_name = "Protein_" + name
                elif "Metal" in mol2_file:
                    mol2_name = "Metal_" + name
                elif "Ligand" in mol2_file:
                    mol2_name = "Ligand_" + name
                model, _ = io.open_data(
                    self.session, mol2_file, format=None, name=mol2_name
                )
                models += model
            z.close()
            self.controller.models[key] = models


class GaudiController(object):
    def __init__(self, session, *args, **kwargs):
        self.session = session
        self.gaudimodel = []
        self.models = {}

    def add_gaudimodel(self, path):
        self.gaudimodel.append(GaudiModel(self, path, self.session))

    def display(self, key):

        if key in self.models:
            if not all(
                i in [actmodel._name for actmodel in self.session.models.list()]
                for i in [m._name for m in self.models[key]]
            ):
                self.session.models.add(self.models[key])
            else:
                show(self.session, self.models[key])
        else:
            for gm in self.gaudimodel:
                if key in gm.keys:
                    gm.parse_zip(key)
            self.session.models.add(self.models[key])

    def not_display(self, key):
        hide(self.session, self.models[key])


def equal_objectives(path):
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    header = ["Filename"] + list(
        map(lambda text: text.split()[0], data["GAUDI.objectives"])
    )
    return header


def show(session, models):
    run(session, "show %s target m" % concise_model_spec(session, models))


def hide(session, models):
    run(session, "hide %s target m" % concise_model_spec(session, models))
