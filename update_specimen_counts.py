#!/usr/bin/env python3

from SamplesParser import SamplesParser
import sys
sys.path.append('../dataset_inventory/gui')
from Exporter import Exporter
from colors import *
import pandas as pd
pd.set_option('display.max_columns', None)

class UpdateSpecimenCounts:
    def __init__(self, samples_parser):
        self.sp = samples_parser
        self.update_counts()

    def update_counts(self):
        d = self.sp.d
        for c in d['Collection'].entities.values():
            if hasattr(c, 'samples'):
                count = c.samples.shape[0]

                subspecimen_count = sum(list(c.samples['Total Processed Subspecimens']))
                # print('                                               ' + cyan + str(sum(subspecimen_counts)) + reset)

                if not 'Reported count' in c.primitives or c['Reported count'] == '':
                    print(magenta + 'Note: ' + reset + yellow + 'Reported count' + reset + ' not recorded yet.')
                    old = '(None)'
                else:
                    old = str(c['Reported count'])

                # if old == str(count):
                #     print(blue + 'No update needed for   ' + reset + yellow + c.get_name().ljust(25) + reset + ' ' + blue + '(' + old + ')' + reset)
                #     continue

                print(green  + 'Updated ... count for             ' + reset + yellow + c.get_name().ljust(25) + reset + ' ' + red + old.ljust(9) + reset + ' => ' + green + str(count) + reset)
                c['Reported count'] = str(count)

                print(green + '            subspecimen count for ' + reset + yellow + c.get_name().ljust(25) + reset + ' ' + red + ' '.ljust(9) + reset + ' => ' + cyan + str(subspecimen_count) + reset)
                c['Reported subspecimen count'] = str(subspecimen_count)

                print()
        print(red + 'Warning: ' + reset + 'The *sub*specimen counts are not being exported. CSV38 does not support this field.')

if __name__=='__main__':
    source_directory = '../dataset_inventory/central_store/idk_templated_csvs/'
    sp = SamplesParser(source_directory)
    usc = UpdateSpecimenCounts(sp)
    e = Exporter(sp.d, 'csvs/')
