from os import listdir
from os.path import isfile, join
import csv
import json

from data_model import *
from data_metamodel import *
from colors import *

class Importer(object):
    _instances = {}

    def instance(cls, source, source_type='IDK YAML templated CSVs'):
        if not source_type in cls._instances.keys():
            cls._instances[source_type] = Importer(source, source_type=source_type)
            return cls._instances[source_type]
        else:
            return cls._instances[source_type]

    def __init__(self, source, model=DatasetMetadataModel(), source_type='IDK YAML templated CSVs'):
        if not source_type in ['IDK YAML templated CSVs', 'BICCN quarterly', 'Project inventory brain map']:
            print('Source type ' + source_type + ' not supported.')
            return
        self.d = Database()
        self.dm = model
        self.source = source
        self.source_type = source_type
        self.do_import()

    def get_database(self):
        return self.d

    def get_datamodel(self):
        return self.dm

    def get_header(self, filename):
        header = []
        with open(filename, 'r',  encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=',', quotechar='"')
            header = next(reader)
        return header

    def do_import(self):
        if self.source_type == 'Project inventory brain map':
            known_headers = self.project_inventory_brain_map_markup()
            directory = self.source
            files = [filename for filename in listdir(directory) if isfile(join(directory, filename)) and self.is_csv(filename)]
            if len(files) == 0:
                print('Warning: No CSV files in directory ' + str(directory))
                return
            headers = {}
            for filename in files:
                headers[filename] = self.get_header(join(directory,filename)) 
            ok_files = []
            bad_files = []
            for filename, header in headers.items():
                for category, h in known_headers.items():
                    if not filename in h.keys():
                        continue
                    known_header = list(h[filename].keys())
                    if known_header != header:
                        print(known_header)
                        print(header)
                        bad_files.append(filename)
                    else:
                        ok_files.append(filename)

            if len(ok_files) > 0:
                print('Headers check out in files:\n' + green + '\n'.join(ok_files) + reset + '\n')
            if len(bad_files) > 0:
                print('Bad headers found in files:\n' + red + '\n'.join(bad_files) + reset + '\n')
            if len(bad_files) == 0:
                print('All headers match expected format.')
                print()

            d = self.d
            dm = self.dm
            for relation_type_name, relation_type in dm.relation_types.items():
                d.create_relation_class(relation_type_name, plural_name=relation_type.plural_name)
            markup = self.project_inventory_brain_map_markup()
            markup_headers = markup['core entity manifest']
            for filename in markup_headers:
                markup_header = markup_headers[filename]
                header = list(markup_header.keys())
                print('Processing ' + green + filename + reset)
                with open(join(directory,filename), 'r',  encoding='utf-8') as file:
                    reader = csv.reader(file, delimiter=',', quotechar='"')
                    row = next(reader)
                    for row in reader:
                        if len(row)==0:
                            break
                        primary_entity = None
                        project_types = {'data collection project' : 'Project', 'sub program' : 'Subprogram', 'sub-program' : 'Subprogram', 'program' : 'Program'}
                        if 'project_type' in header:
                            primary_entity_class_name = project_types[[row[i] for i in range(len(row)) if header[i] == 'project_type'][0]]
                        else:
                            primary_entity_class_name = None
                        for i, column in enumerate(header):
                            access_sequence = list(markup_header.values())[i]
                            if len(access_sequence) == 0:
                                continue
                            entry = row[i]
                            if len(access_sequence) == 1:
                                if primary_entity_class_name == None:
                                    primary_entity = d.create_entity(access_sequence[0], entry)
                                else:
                                    primary_entity = d.create_entity(primary_entity_class_name, entry)
                            elif len(access_sequence) > 1:
                                if access_sequence[1] in dm.entity_types:
                                    if entry != '':
                                        if d[entry] == None:
                                            auxiliary_entity = d.create_entity(access_sequence[1], entry)
                                        else:
                                            auxiliary_entity = d[entry]
                                        primary_entity[access_sequence[1]] = auxiliary_entity
                                elif access_sequence[1] in d.relation_classes:
                                    if entry != '':
                                        primary_entity[access_sequence[1]] = d[entry]
                                else:
                                    primary_entity[access_sequence[1]] = entry

        if self.source_type == 'BICCN quarterly':
            known_headers = self.biccn_quarterly_markup()
            directory = self.source
            files = [filename for filename in listdir(directory) if isfile(join(directory, filename)) and self.is_csv(filename)]
            if len(files) == 0:
                print('Warning: No CSV files in directory ' + str(directory))
                return
            headers = {}
            for filename in files:
                headers[filename] = self.get_header(join(directory,filename)) 
            ok_files = []
            bad_files = []
            for filename, header in headers.items():
                for category, h in known_headers.items():
                    if not filename in h.keys():
                        continue
                    known_header = list(h[filename].keys())
                    if known_header != header:
                        print(known_header)
                        print(header)
                        bad_files.append(filename)
                    else:
                        ok_files.append(filename)

            if len(ok_files) > 0:
                print('Headers check out in files:\n' + green + '\n'.join(ok_files) + reset + '\n')
            if len(bad_files) > 0:
                print('Bad headers found in files:\n' + red + '\n'.join(bad_files) + reset + '\n')
            if len(bad_files) == 0:
                print('All headers match expected format.')
                print()

            d = self.d
            dm = self.dm
            for relation_type_name, relation_type in dm.relation_types.items():
                d.create_relation_class(relation_type_name, plural_name=relation_type.plural_name)
            markup = self.biccn_quarterly_markup()
            markup_headers = markup['core entity manifest']
            for filename in markup_headers:
                markup_header = markup_headers[filename]
                header = list(markup_header.keys())
                print('Processing ' + green + filename + reset)
                with open(join(directory,filename), 'r',  encoding='utf-8') as file:
                    reader = csv.reader(file, delimiter=',', quotechar='"')
                    row = next(reader)
                    for row in reader:
                        if len(row)==0:
                            break
                        primary_entity = None
                        project_types = {'data collection project' : 'Project', 'sub program' : 'Subprogram', 'sub-program' : 'Subprogram', 'program' : 'Program'}
                        if 'project_type' in header:
                            primary_entity_class_name = project_types[[row[i] for i in range(len(row)) if header[i] == 'project_type'][0]]
                        else:
                            primary_entity_class_name = None
                        for i, column in enumerate(header):
                            access_sequence = list(markup_header.values())[i]
                            if len(access_sequence) == 0:
                                continue
                            entry = row[i]
                            if len(access_sequence) == 1:
                                if primary_entity_class_name == None:
                                    primary_entity = d.create_entity(access_sequence[0], entry)
                                else:
                                    primary_entity = d.create_entity(primary_entity_class_name, entry)
                            elif len(access_sequence) > 1:
                                if access_sequence[1] in dm.entity_types:
                                    if entry != '':
                                        if d[entry] == None:
                                            auxiliary_entity = d.create_entity(access_sequence[1], entry)
                                        else:
                                            auxiliary_entity = d[entry]
                                        primary_entity[access_sequence[1]] = auxiliary_entity
                                elif access_sequence[1] in d.relation_classes:
                                    if entry != '':
                                        primary_entity[access_sequence[1]] = d[entry]
                                else:
                                    primary_entity[access_sequence[1]] = entry

        if self.source_type == 'IDK YAML templated CSVs':
            directory = self.source
            files = [filename for filename in listdir(directory) if isfile(join(directory, filename)) and self.is_csv(filename)]
            if len(files) == 0:
                print('Warning: No CSV files in directory ' + str(directory))
                return
            headers = {}
            for filename in files:
                headers[filename] = self.get_header(join(directory,filename)) 
            known_headers = self.idk_template_markup()
            ok_files = []
            bad_files = []
            for filename, header in headers.items():
                for category, h in known_headers.items():
                    if not filename in h.keys():
                        continue
                    known_header = list(h[filename].keys())
                    if known_header != header:
                        bad_files.append(filename)
                    else:
                        ok_files.append(filename)

            if len(ok_files) > 0:
                print('Headers check out in files:\n' + green + '\n'.join(ok_files) + reset + '\n')
            if len(bad_files) > 0:
                print('Bad headers found in files:\n' + red + '\n'.join(bad_files) + reset + '\n')
            if len(bad_files) == 0:
                print('All headers match expected format.')
                print()

            d = self.d
            dm = self.dm
            for relation_type_name, relation_type in dm.relation_types.items():
                d.create_relation_class(relation_type_name, plural_name=relation_type.plural_name)
            markup = self.idk_template_markup()

            markup_headers = markup['vocab']
            for filename in markup_headers:
                markup_header = markup_headers[filename]
                header = list(markup_header.keys())
                print('Processing ' + green + filename + reset)
                with open(join(directory,filename), 'r', encoding='utf-8') as file:
                    reader = csv.reader(file, delimiter=',', quotechar='"')
                    row = next(reader)
                    for row in reader:
                        if len(row)==0:
                            break
                        primary_entity = None
                        for i, column in enumerate(header):
                            access_sequence = list(markup_header.values())[i]
                            entry = row[i]
                            if len(access_sequence) == 1:
                                primary_entity = d.create_entity(access_sequence[0], entry)
                            else:
                                print('Warning: File ' + filename + ' is not a "vocab" file.')

            # markup_headers = markup['core entity manifest']
            # for filename in markup_headers:
            m1 = markup['core entity manifest']
            m2 = markup['auxiliary entity manifest']
            markup_headers = {**m1, **m2}
            for filename in markup_headers:
                markup_header = markup_headers[filename]
                header = list(markup_header.keys())
                print('Processing ' + green + filename + reset)
                with open(join(directory,filename), 'r',  encoding='utf-8') as file:
                    reader = csv.reader(file, delimiter=',', quotechar='"')
                    row = next(reader)
                    for row in reader:
                        if len(row)==0:
                            break
                        primary_entity = None
                        project_types = {'data collection project' : 'Project', 'sub program' : 'Subprogram', 'sub-program' : 'Subprogram', 'program' : 'Program'}
                        if 'project_type' in header:
                            primary_entity_class_name = project_types[[row[i] for i in range(len(row)) if header[i] == 'project_type'][0]]
                        else:
                            primary_entity_class_name = None
                        for i, column in enumerate(header):
                            access_sequence = list(markup_header.values())[i]
                            if len(access_sequence) == 0:
                                continue
                            entry = row[i]
                            if len(access_sequence) == 1:
                                if primary_entity_class_name == None:
                                    primary_entity = d.create_entity(access_sequence[0], entry)
                                else:
                                    primary_entity = d.create_entity(primary_entity_class_name, entry)
                            elif len(access_sequence) > 1:
                                if access_sequence[1] in dm.entity_types:
                                    if entry != '':
                                        if d[entry] == None:
                                            auxiliary_entity = d.create_entity(access_sequence[1], entry)
                                        else:
                                            auxiliary_entity = d[entry]
                                        primary_entity[access_sequence[1]] = auxiliary_entity
                                elif access_sequence[1] in d.relation_classes:
                                    if entry != '':
                                        primary_entity[access_sequence[1]] = d[entry]
                                else:
                                    primary_entity[access_sequence[1]] = entry

            m1 = markup['core entity linkages']
            m2 = markup['linkages plus']
            markup_headers = {**m1, **m2}
            # markup_headers = markup['core entity linkages']
            for filename in markup_headers:
                markup_header = markup_headers[filename]
                header = list(markup_header.keys())
                print('Processing ' + green + filename + reset)
                with open(join(directory,filename), 'r',  encoding='utf-8') as file:
                    reader = csv.reader(file, delimiter=',', quotechar='"')
                    row = next(reader)
                    for row in reader:
                        if len(row)==0:
                            break
                        primary_entity == None
                        for i, column in enumerate(header):
                            access_sequence = list(markup_header.values())[i]
                            entry = row[i]
                            if len(access_sequence) == 1:
                                primary_entity = d[entry]
                            elif len(access_sequence) == 2:
                                if d[entry] == None or entry == '':
                                    # print('Warning: entry "' + entry + '" in column ' + column + ' not in the database. Can\'t link.')
                                    continue
                                else:
                                    secondary_entity = d[entry]
                                    primary_entity[access_sequence[1]] = secondary_entity
                            elif len(access_sequence) == 3:
                                if not access_sequence[2] in ['priority order', 'email address']:
                                    print('Warning: Association table parser only knows about priority order and email address for access sequences this long.')
                                    # need to allow 3rd entries which are not priority order, e.g. contact person email address
                                    # interestingly it is still a relation primitive...
                                    break
                                primary_entity.r(access_sequence[1])[secondary_entity.get_name()][access_sequence[2]] = entry
                        if primary_entity == None or secondary_entity == None:
                            print('Warning: row ' + str(row) + ' of association table is missing required values.')

            m1 = markup['dc props']
            m2 = markup['proj props']
            markup_headers = {**m1, **m2}
            # markup_headers = markup['dc props']
            for filename in markup_headers:
                markup_header = markup_headers[filename]
                header = list(markup_header.keys())
                print('Processing ' + green + filename + reset)
                with open(join(directory,filename), 'r',  encoding='utf-8') as file:
                    reader = csv.reader(file, delimiter=',', quotechar='"')
                    row = next(reader)
                    for row in reader:
                        if len(row)==0:
                            break
                        primary_entity = None
                        for i, column in enumerate(header):
                            access_sequence = list(markup_header.values())[i]
                            if len(access_sequence) == 0:
                                continue
                            entry = row[i]
                            if len(access_sequence) == 1:
                                primary_entity = d[entry]
                                if primary_entity is None:
                                    print('Warning: ' + entry + ' wasn\'t found in the database. Skipping record ' + str(row) + '.')
                                    break
                            elif len(access_sequence) > 1:
                                if access_sequence[1] in dm.entity_types:
                                    if entry != '':
                                        if d[entry] == None:
                                            auxiliary_entity = d.create_entity(access_sequence[1], entry)
                                        else:
                                            auxiliary_entity = d[entry]
                                        primary_entity[access_sequence[1]] = auxiliary_entity
                                elif access_sequence[1] in d.relation_classes:
                                    if entry != '':
                                        primary_entity[access_sequence[1]] = d[entry]
                                else:
                                    primary_entity[access_sequence[1]] = entry

    def is_csv(self, filename):
        parts = filename.split('.')
        if parts[len(parts)-1] in ['csv','CSV']:
            return True
        return False

    def idk_template_markup(self):
        data = json.load(open('idk_templates_markup.json', 'r'))
        return data

    def biccn_quarterly_markup(self):
        data = json.load(open('../central_store/biccn_titles_descriptions/biccn_quarterly_markup.json', 'r'))
        return data

    def project_inventory_brain_map_markup(self):
        data = json.load(open('../central_store/project_inventory_brain_map/project_inventory_brain_map_markup.json', 'r'))
        return data

if __name__=='__main__':
    i = Importer('../central_store/idk_templated_csvs/')
    d = i.d
    dm = i.dm
    dm.check(d)
    dm.report()
    dm.why()
