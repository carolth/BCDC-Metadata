#!/usr/bin/env python3

import pandas as pd
import numpy as np
import os
import os.path
import re
from colors import *
from Importer import Importer

class BCDCSampleCoordination:
    def __init__(self, metadata_directory = '', sample_directory = '', year = None, quarter = None, c2m2_directory = None):
        self.import_samples(metadata_directory = metadata_directory, sample_directory = sample_directory, year = year, quarter = quarter)
        self.c2m2_directory = c2m2_directory
        if self.c2m2_directory != None:
            self.import_c2m2_dfs()
        else:
            self.dfs = {}
        for filename in self.c2m2_filenames():
            self.generate_df(filename)

    def import_c2m2_dfs(self):
        self.dfs = {filename: pd.read_csv(os.path.join(self.c2m2_directory, filename+'.tsv'), keep_default_na=False) for filename in self.c2m2_filenames() if os.path.isfile(filename)}

    def import_samples(self, metadata_directory = '', sample_directory = '', year = None, quarter = None):
        filename = os.path.join(sample_directory, 'BCDC_Metadata_' + str(year) + 'Q' + str(quarter) + '.csv')
        samples_df = pd.read_csv(filename).drop_duplicates()
        i = Importer(metadata_directory)
        print('')
        print('')
        self.d = i.d
        d = self.d
        for collection in d['Collection'].entities.values():
            collection_samples = samples_df[samples_df['Data Collection (CV)'] == collection.get_name()]
            if collection_samples.shape[0] != 0:
                collection.samples = collection_samples
            else:
                collection.samples = None

    def c2m2_filenames(self):
        return [
            'project',
            'collection',
            'collection_in_collection',
            'biosample',
            'biosample_in_collection',
            'subject',
            'subject_in_collection',
            'biosample_from_subject',
            'subject_granularity',
            'subject_role',
            'subject_role_taxonomy',
            'id_namespace',
            'file',
            'file_format',
            'data_type',
            'file_in_collection',
            'file_describes_biosample',
            'file_describes_subject',
            'project_in_project',
            'collection_defined_by_project',
            'assay_type',
            'anatomy',
            'ncbi_taxonomy',
        ]

    def inverse_r(self, entity, relation_name):
        ir = {rel.get_source() : rel for rel in entity.inverse_relations.keys() if rel.get_class_name() == relation_name}
        return ir

    def all_collections(self):
        return {collection : collection.samples for collection in self.d['Collection'].entities.values() if not collection.samples is None}

    def generate_df(self, filename):
        print('')
        print(yellow + 'Generating ' + reset + green + filename + reset)
        if not filename in self.dfs.keys():
            self.dfs[filename] = pd.DataFrame()
        df = self.dfs[filename]
        BCDC = 'cfde_id_namespace_id:BCDC'
        collections = self.all_collections()
        rows = []
        if filename == 'anatomy':
            print(red + 'Warning: ' + reset + 'Skipping.')
            # rows.append({
            #     "id" : '',
            #     "name" : '',
            #     "description" : '',
            #     "synonyms" : '',
            # })

        if filename == 'assay_type':
            print(red + 'Warning: ' + reset + 'Not clear of OBI terms should describe assay type proper or material entity type...')
            for collection, samples in collections.items():
                for modality_name in collection.r('is data of type'):
                    row = {
                        "id"          : modality_name,
                        "name"        : '',
                        "description" : '',
                        "synonyms"    : '',
                    }
                    if not row in rows:
                        rows.append(row)

        if filename == 'biosample':
            cached = ''
            for collection, samples in collections.items():
                reported_inference_yet = False
                if len(collection.r('is data of type')) == 1:
                    inferred_modality = list(collection.r('is data of type').keys())[0]
                else:
                    inferred_modality = ''
                for index, sample in samples.iterrows():
                    m = str(sample['Modality  (CV)'])
                    if not m in self.d['Modality'].entities.keys():
                        if inferred_modality != '':
                            if not reported_inference_yet:
                                print(yellow + 'Note: ' + reset + 'Using modality tagged to collection, ' + cyan + inferred_modality + reset)
                                reported_inference_yet = True
                            m = inferred_modality
                        else:
                            if cached != m:
                                print(red + 'Warning: ' + reset + yellow + m + reset + ' is technically not in the list of modalities.')
                        cached = m
                        m = ''

                    rows.append({
                        "id_namespace"         : BCDC,
                        "id"                   : sample['Sample ID'],
                        "project_id_namespace" : BCDC,
                        "project"              : sample['Project (CV)'],
                        "persistent_id"        : '',
                        "creation_time"        : '',
                        "assay_type"           : m,
                        "anatomy"              : '',
                    })

        if filename == 'biosample_from_subject':
            for collection, samples in collections.items():
                for index, sample in samples.iterrows():
                    rows.append({
                        "biosample_id_namespace" : BCDC,
                        "biosample_id"           : sample['Sample ID'],
                        "subject_id_namespace"   : BCDC,
                        "subject_id"             : str(sample['Donor id']) if not str(sample['Donor id']) == 'nan' else '',
                    })

        if filename == 'biosample_in_collection':
            for collection, samples in collections.items():
                for index, sample in samples.iterrows():
                    rows.append({
                        "biosample_id_namespace"  : BCDC,
                        "biosample_id"            : sample['Sample ID'],
                        "collection_id_namespace" : BCDC,
                        "collection_id"           : collection.get_name(),
                    })

        if filename == 'collection':
            for collection, samples in collections.items():
                rows.append({
                    'id_namespace'  : BCDC,
                    'id'            : collection.get_name(),
                    'persistent_id' : '',
                    'creation_time' : '',
                    'abbreviation'  : collection['Short title'],
                    'name'          : collection['Title'],
                    'description'   : collection['Description'],
                })

        if filename == 'collection_defined_by_project':
            for collection, samples in collections.items():
                projects = self.inverse_r(collection, 'has output')
                if len(projects) == 0:
                    print(red + 'Warning: ' + reset + 'Collection ' + cyan + collection.get_name() + reset + ' does not belong to any project somehow.')
                    continue
                if len(projects) > 1:
                    print(red + 'Warning: ' + reset + 'Collection ' + cyan + collection.get_name() + reset + ' belongs to multiple projects.')
                    continue
                else:
                    project = list(projects.keys())[0]
                rows.append({
                    'collection_id_namespace' : BCDC,
                    'collection_id'           : collection.get_name(),
                    'project_id_namespace'    : BCDC,
                    'project_id'              : project.get_name(),
                })

        if filename == 'collection_in_collection':
            print(red + 'Warning: ' + reset + 'Skipping.')
            # rows.append({
            #     "superset_collection_id_namespace" : '',
            #     "superset_collection_id"           : '',
            #     "subset_collection_id_namespace"   : '',
            #     "subset_collection_id"             : '',
            # })

        if filename == 'data_type':
            print(yellow + 'Note: ' + reset + 'To be populated by archives.')
            # rows.append({
            #     "id"          : '',
            #     "name"        : '',
            #     "description" : '',
            #     "synonyms"    : '',
            # })

        if filename == 'file':
            print(yellow + 'Note: ' + reset + 'To be populated by archives.')
            # rows.append({
            #     'id_namespace'         : 'cfde_id_namespace:DANDI?',
            #     'id'                   : m['id'][i],
            #     'project_id_namespace' : 'cfde_id_namespace:BCDC?',
            #     'project'              : 'Patch-seq MOp',
            #     'persistent_id'        : m['persistent_id'][i],
            #     'creation_time'        : '',
            #     'size_in_bytes'        : m['size_in_bytes'][i],
            #     'sha256'               : m['sha256'][i],
            #     'md5'                  : m['md5'][i],
            #     'filename'             : m['filename'][i],
            #     'file_format'          : 'NWB',
            #     'data_type'            : '?'
            # })

        if filename == 'file_describes_biosample':
            print(yellow + 'Note: ' + reset + 'To be populated by archives.')
            # rows.append({
            #     'file_id_namespace'      : 'cfde_id_namespace:DANDI',
            #     'file_id'                : dandi_file_id,
            #     'biosample_id_namespace' : 'cfde_id_namespace:NeMO',
            #     'biosample_id'           : bs
            # })

        if filename == 'file_describes_subject':
            print(yellow + 'Note: ' + reset + 'To be populated by archives.')
            # print(red + '    Shouldn\'t this information be inferred rather than specified?' + reset)
            # print(red + '    Or at least, the information here should be directly about subjects and not inferable via biosamples...' + reset)
            # rows.append({
            #     "file_id_namespace" : '',
            #     "file_id" : '',
            #     "subject_id_namespace" : '',
            #     "subject_id" : '',
            # })

        if filename == 'file_format':
            print(yellow + 'Note: ' + reset + 'To be populated by archives.')
            # rows.append({
            #         'id'          : '?',
            #         'name'        : 'NWB',
            #         'description' : '...',
            #         'synonyms'    : '...'
            # })

        if filename == 'file_in_collection':
            print(yellow + 'Note: ' + reset + 'To be populated by archives.')
            # rows.append({
            #     'file_id_namespace'       : 'cfde_id_namespace:NeMO',
            #     'file_id'                 : nfid,
            #     'collection_id_namespace' : 'cfde_id_namespace:NeMO',
            #     'collection_id'           : 'Patch-seq MOp'
            # })

        if filename == 'id_namespace':
            rows.append({
                'id'           : 'cfde_id_namespace:BCDC',
                'abbreviation' : 'BCDC',
                'name'         : 'Brain Cell Data Center',
                'description'  : ''
            })
            rows.append({
                'id'           : 'cfde_id_namespace:DANDI',
                'abbreviation' : 'DANDI',
                'name'         : 'Distributed Archives for Neurophysiology Data Integration',
                'description'  : ''
            })
            rows.append({
                'id'           : 'cfde_id_namespace:NeMO',
                'abbreviation' : 'NeMO',
                'name'         : 'Neuroscience Multi-omic Archive',
                'description'  : ''
            })
            rows.append({
                'id'           : 'cfde_id_namespace:BIL',
                'abbreviation' : 'BIL',
                'name'         : 'Brain Image Library',
                'description'  : ''
            })

        if filename == 'ncbi_taxonomy':
            print(red + 'Warning: ' + reset + 'Skipping.')
            # rows.append({
            #     "id"          : '',
            #     "clade"       : '',
            #     "name"        : '',
            #     "description" : '',
            #     "synonyms"    : '',
            # })

        if filename == 'project':
            for collection, samples in collections.items():
                projects = self.inverse_r(collection, 'has output')
                if len(projects) == 0:
                    print(red + 'Warning: ' + reset + 'Collection ' + cyan + collection.get_name() + reset + ' does not belong to any project somehow.')
                    continue
                if len(projects) > 1:
                    print(red + 'Warning: ' + reset + 'Collection ' + cyan + collection.get_name() + reset + ' belongs to multiple projects.')
                    continue
                else:
                    project = list(projects.keys())[0]
                row = ({
                    'id_namespace'  : BCDC,
                    'id'            : project.get_name(),
                    'persistent_id' : '',
                    'creation_time' : '',
                    'abbreviation'  : project['Short title'],
                    'name'          : project['Title'],
                    'description'   : project['Description'],
                })
                if not row in rows:
                    rows.append(row)

                subprograms = project.r('is part of')
                if subprograms is None:
                    continue
                if len(subprograms) == 0:
                    print(red + 'Warning: ' + reset + 'Project ' + cyan + project.get_name() + reset + ' does not belong to any subprogram somehow.')
                    continue
                if len(subprograms) > 1:
                    print(yellow + 'Note: ' + reset + 'Project ' + cyan + project.get_name() + reset + ' belongs to multiple subprograms.')

                subprograms = [self.d[name] for name in subprograms.keys()]
                for subprogram in subprograms:
                    row = ({
                        'id_namespace'  : BCDC,
                        'id'            : subprogram.get_name(),
                        'persistent_id' : '',
                        'creation_time' : '',
                        'abbreviation'  : subprogram['Short title'],
                        'name'          : subprogram['Title'],
                        'description'   : subprogram['Description'],
                    })
                    if not row in rows:
                        rows.append(row)

        if filename == 'project_in_project':
            for collection, samples in collections.items():
                projects = self.inverse_r(collection, 'has output')
                if len(projects) == 0:
                    print(red + 'Warning: ' + reset + 'Collection ' + cyan + collection.get_name() + reset + ' does not belong to any project somehow.')
                    continue
                if len(projects) > 1:
                    print(red + 'Warning: ' + reset + 'Collection ' + cyan + collection.get_name() + reset + ' belongs to multiple projects.')
                    continue
                else:
                    project = list(projects.keys())[0]

                subprograms = project.r('is part of')
                if subprograms is None:
                    continue
                if len(subprograms) == 0:
                    print(red + 'Warning: ' + reset + 'Project ' + cyan + project.get_name() + reset + ' does not belong to any subprogram somehow.')
                    continue
                if len(subprograms) > 1:
                    print(yellow + 'Note: ' + reset + 'Project ' + cyan + project.get_name() + reset + ' belongs to multiple subprograms.')

                subprograms = [self.d[name] for name in subprograms.keys()]
                for subprogram in subprograms:
                    row = ({
                        'parent_project_id_namespace'  : BCDC,
                        'parent_project_id'            : subprogram.get_name(),
                        'child_project_id_namespace'   : BCDC,
                        'child_project_id'             : project.get_name(),
                    })
                    if not row in rows:
                        rows.append(row)

        if filename == 'subject':
            for collection, samples in collections.items():
                for index, sample in samples.iterrows():
                    donor_id = str(sample['Donor id'])
                    if donor_id in ['', 'nan']:
                        # print(red + 'Warning: ' + reset + ' Sample ' + cyan + sample['Sample ID'] + reset + ' from ' + magenta + sample['Data Collection (CV)'] + reset + ' is missing the subject information.')
                        continue
                    row = ({
                        "id_namespace"         : BCDC,
                        "id"                   : str(sample['Donor id']),
                        "project_id_namespace" : BCDC,
                        "project"              : sample['Project (CV)'],
                        "persistent_id"        : '',
                        "creation_time"        : '',
                        "granularity"          : '',
                    })
                    if not row in rows:
                        rows.append(row)

        if filename == 'subject_granularity':
            print(red + 'Warning: ' + reset + 'Skipping.')
            # rows.append({
            #     "id" : '',
            #     "name" : '',
            #     "description" : '',
            # })

        if filename == 'subject_in_collection':
            missing_subjects = []
            for collection, samples in collections.items():
                for index, sample in samples.iterrows():
                    donor_id = str(sample['Donor id'])
                    if donor_id in ['', 'nan']:
                        # print(red + 'Warning: ' + reset + ' Sample ' + cyan + sample['Sample ID'] + reset + ' from ' + magenta + sample['Data Collection (CV)'] + reset + ' is missing the subject information.')
                        missing_subjects.append(sample['Sample ID'])
                        continue
                    row = ({
                        "subject_id_namespace"    : BCDC,
                        "subject_id"              : donor_id,
                        "collection_id_namespace" : BCDC,
                        "collection_id"           : sample['Data Collection (CV)'],
                    })
                    if not row in rows:
                        rows.append(row)
            if len(missing_subjects) > 0:
                print(red + 'Warning: ' + reset + ' Missing ' + cyan + str(len(missing_subjects)) + reset + ' subject fields.')

        if filename == 'subject_role':
            print(red + 'Warning: ' + reset + 'Skipping.')
            # rows.append({
            #     "id" : '',
            #     "name" : '',
            #     "description" : '',
            # })

        if filename == 'subject_role_taxonomy':
            print(red + 'Warning: ' + reset + 'Skipping.')
            # rows.append({
            #     "subject_id_namespace" : '',
            #     "subject_id" : '',
            #     "role_id" : '',
            #     "taxonomy_id" : '',
            # })

        df = df.append(rows, ignore_index=True)
        self.dfs[filename] = df

    def write_out(self):
        output_dir = self.c2m2_directory
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        for filename in self.dfs.keys():
            self.dfs[filename].to_csv(os.path.join(output_dir, filename + '.tsv'), sep='\t', index=False)
        print(yellow + 'Wrote C2M2-style TSV files to ' + reset + cyan + output_dir + reset)


sc = BCDCSampleCoordination(
    metadata_directory = '../dataset_inventory/central_store/idk_templated_csvs',
    sample_directory = 'Sample-Inventory',
    year = 2020,
    quarter = 2,
    c2m2_directory = 'bcdc_partial'
)
sc.write_out()

