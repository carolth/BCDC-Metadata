#!/usr/bin/env python3

from SamplesParser import SamplesParser
from colors import *
import pandas as pd
pd.set_option('display.max_columns', None)

class ReportStats:
    def __init__(self, samples_parser):
        self.sp = samples_parser
        self.stats()

    def stats(self):
        d = self.sp.d
        figures = {}
        figures['Number of NIH grants'] = len(d['Grant'].entities)

        people = []
        for c in d['Project'].entities.values():
            if c.r('has contributor') != None:
                people = people + list(c.r('has contributor').values())
        people = list(set(people))
        figures['Number of credited data contributors'] = len(people)

        figures['Number of data collections'] = len(d['Collection'].entities)
        count = 0
        for c in d['Collection'].entities.values():
            if hasattr(c, 'samples'):
                count = count + c.samples.shape[0]
        figures['Number of samples'] = count

        m = {}
        t = {}
        mc = {}
        tc = {}
        for modality in d['Modality'].entities.values():
            m['(samples) ' + modality.get_name()] = self.count_samples_of_modality(modality)
        for technique in d['Technique'].entities.values():
            t['(samples) ' + technique.get_name()] = self.count_samples_of_technique(technique)
        for modality in d['Modality'].entities.values():
            mc['(collections) ' + modality.get_name()] = self.count_collections_of_modality(modality)
        for technique in d['Technique'].entities.values():
            tc['(collections) ' + technique.get_name()] = self.count_collections_of_technique(technique)

        m_order = sorted(list(m.items()), key=lambda item: item[1])
        t_order = sorted(list(t.items()), key=lambda item: item[1])
        figures_m = {}
        figures_t = {}
        for item in m_order:
            figures_m[item[0]] = item[1]
        for item in t_order:
            figures_t[item[0]] = item[1]
        mc_order = sorted(list(mc.items()), key=lambda item: item[1])
        tc_order = sorted(list(tc.items()), key=lambda item: item[1])
        figures_mc = {}
        figures_tc = {}
        for item in mc_order:
            figures_mc[item[0]] = item[1]
        for item in tc_order:
            figures_tc[item[0]] = item[1]

        wr = [
            'is highlighted by',
            'has view resource',
            'is subject of resource',
            'has information resource',
        ]
        all_wr = []
        for c in d['Collection'].entities.values():
            wrs = [list(c.r(rel).keys()) for rel in wr if c.r(rel) != None]
            wrsl = []
            for elt in wrs:
                wrsl = wrsl + elt
            all_wr = all_wr + wrsl
        # figures['External resources'] = [''] + sorted(all_wr)

        # number of data collections
        # number of samples (brain sections, cells, etc.)
        # for each modality, number of samples (then cherry pick)
        # for each technique, number of samples (then cherry pick)
        # number of data contributors

        print('')
        print('Stats')
        print('-----')
        l = max([len(f) for f in figures])
        for figure in figures:
            if type(figures[figure]) == list:
                val = '\n'.join(figures[figure])
            else:
                val = figures[figure]
            print(magenta + figure.ljust(l+1) + reset + ': ' + yellow + str(val) + reset)
        l = max([len(f) for f in figures_m])
        for figure in figures_m:
            if type(figures_m[figure]) == list:
                val = '\n'.join(figures_m[figure])
            else:
                val = figures_m[figure]
            print(magenta + figure.ljust(l+1) + reset + ': ' + yellow + str(val) + reset)
        l = max([len(f) for f in figures_t])
        for figure in figures_t:
            if type(figures_t[figure]) == list:
                val = '\n'.join(figures_t[figure])
            else:
                val = figures_t[figure]
            print(magenta + figure.ljust(l+1) + reset + ': ' + yellow + str(val) + reset)
        l = max([len(f) for f in figures_mc])
        for figure in figures_mc:
            if type(figures_mc[figure]) == list:
                val = '\n'.join(figures_mc[figure])
            else:
                val = figures_mc[figure]
            print(magenta + figure.ljust(l+1) + reset + ': ' + yellow + str(val) + reset)
        l = max([len(f) for f in figures_tc])
        for figure in figures_tc:
            if type(figures_tc[figure]) == list:
                val = '\n'.join(figures_tc[figure])
            else:
                val = figures_tc[figure]
            print(magenta + figure.ljust(l+1) + reset + ': ' + yellow + str(val) + reset)

    def remove_biccn(self):
        d = self.sp.d
        biccn_projects = [d[name] for name in d['Project'].entities if not 'is part of' in d[name].multiple and not 'is part of' in d[name]['is part of'].multiple and d[name]['is part of']['is part of'].get_name() == 'BICCN']
        biccn_collections = []
        subprogram_whitelist = ['U19 Zeng']
        for p in biccn_projects:
            if p['is part of'].get_name() in subprogram_whitelist:
                continue
            if 'has output' in p.multiple:
                biccn_collections = biccn_collections + list(p['has outputs'].values())
            else:
                biccn_collections.append(p['has output'])

        for c in biccn_collections:
            del d[c.get_name()]

        for p in biccn_projects:
            if p['is part of'].get_name() in subprogram_whitelist:
                continue
            del d[p.get_name()]

    def count_collections_of_modality(self, modality):
        basin = modality.inverse_relations
        collections = [rel.get_source() for rel in basin if rel.get_class_name() == 'is data of type']
        return len(collections)

    def count_samples_of_modality(self, modality):
        basin = modality.inverse_relations
        collections = [rel.get_source() for rel in basin if rel.get_class_name() == 'is data of type']
        count = 0
        for collection in collections:
            if hasattr(collection, 'samples'):
                count = count + collection.samples.shape[0]
        return count

    def count_collections_of_technique(self, technique):
        basin = technique.inverse_relations
        collections = [rel.get_source() for rel in basin if rel.get_class_name() == 'was collected using']
        return len(collections)

    def count_samples_of_technique(self, technique):
        basin = technique.inverse_relations
        collections = [rel.get_source() for rel in basin if rel.get_class_name() == 'was collected using']
        count = 0
        for collection in collections:
            if hasattr(collection, 'samples'):
                count = count + collection.samples.shape[0]
        return count


if __name__=='__main__':
    source_directory = '../dataset_inventory/central_store/idk_templated_csvs/'
    sp = SamplesParser(source_directory)
    gs = ReportStats(sp)
