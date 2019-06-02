import tempfile
import zipfile
import yaml
import os
from chimerax.core import models, io


class GaudiModel(object):
    def __init__(self, path, session, *args, **kwargs):
        self.path = path
        self.basedir = os.path.dirname(path)
        self.data, self.headers, self.keys = self.parse()
        self.tempdir = tempfile.mkdtemp("gaudiviewx")
        self.session = session

    def parse(self):
        with open(self.path, "r") as f:
            self.first_line = f.readline()
            self.raw_data = yaml.safe_load(f)
        datarray = [[k] + v for k, v in self.raw_data["GAUDI.results"].items()]
        keys = list(self.raw_data["GAUDI.results"].keys())
        header = ["Filename"] + list(
            map(lambda text: text.split()[0], self.raw_data["GAUDI.objectives"])
        )
        return datarray, header, keys

    def parse_zip(self, path):
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
            return models

    def save_models(self):
        modelsdict = {}

        for key in self.keys:
            models = self.parse_zip(os.path.join(self.basedir, key))
            modelsdict[key] = models
        return modelsdict
