'''
This module, unlike the data_metamodel, contains the data model for the GUI
application for managing dataset metadata.
All of the syntax and operations in the metamodel were developed to make this
module easier to read and write.
'''

from data_metamodel import *


class DatasetMetadataModel(Model):
    def __init__(self):
        Model.__init__(self)
        et = self.add_entity_type
        rt = self.add_relation_type

        et('Program')
        et('Subprogram')
        et('Project', require = self.project_checker)
        et('Collection')

        et('Modality')
        et('Species')
        et('Specimen type')
        et('Technique')

        et('Person')
        et('Web resource')
        et('Protocol')
        et('Publication')
        et('Grant')
        et('Organization')
        et('License')

        et('Access control',    require = lambda e: e.get_name() in ['open',         'controlled'])
        et('Completion state',  require = lambda e: e.get_name() in ['in progress',  'complete'])
        et('Web resource type', require = lambda e: e.get_name() in ['view',         'information',  'download',                 'explore'])

        rt('has information resource', require = lambda r: (
            (r.s() == 'Project' and r.t() == 'Web resource'       ) or
            (r.s() == 'Subprogram' and r.t() == 'Web resource'    ) or
            (r.s() == 'Program' and r.t() == 'Web resource'       ) or
            (r.s() == 'License' and r.t() == 'Web resource'       )     ))

        rt('is part of', plural_name='is part of (multiple)', require = lambda r: (
            (r.s() == 'Subprogram' and r.t() == 'Program'         ) or
            (r.s() == 'Project'    and r.t() == 'Subprogram'      )     ))

        rt('has output', plural_name='has outputs', require = lambda r: (
            (r.s() == 'Project' and r.t() == 'Collection'         )     ))

        rt('has contributor', plural_name='has contributors', require = lambda r: (
            (r.s() == 'Project' and r.t() == 'Person'             ) and
            (r['priority order'] != None                          )     ))

        rt('has contact person', require = lambda r: (
            (r.s() == 'Project' and r.t() == 'Person'             ) and
            (r['email address'] != None                           )     ))

        rt('has creator', require = lambda r: (
            (r.s() == 'Project' and r.t() == 'Person'             ) or
            (r.s() == 'Project' and r.t() == 'Organization'       )     ))

        rt('is data of type', plural_name='is data of types', require = lambda r: (
            (r.s() == 'Collection' and r.t() == 'Modality'        )     ))
        rt('is data about', require = lambda r: (
            (r.s() == 'Collection' and r.t() == 'Species'         )     ))
        rt('has samples of type', require = lambda r: (
            (r.s() == 'Collection' and r.t() == 'Specimen type'   )     ))
        rt('was collected using', require = lambda r: (
            (r.s() == 'Collection' and r.t() == 'Technique'       )     ))

        rt('involves data of type', plural_name='involves data of types', require = lambda r: (
            (r.s() == 'Project' and r.t() == 'Modality'           )     ))
        rt('involves data about', require = lambda r: (
            (r.s() == 'Project' and r.t() == 'Species'            )     ))
        rt('collected samples of type', require = lambda r: (
            (r.s() == 'Project' and r.t() == 'Specimen type'      )     ))
        rt('used', require = lambda r: (
            (r.s() == 'Project' and r.t() == 'Technique'          )     ))

        rt('has methodology specification', require = lambda r: (
            (r.s() == 'Project' and r.t() == 'Protocol'           )     ))

        rt('refers to real entity', require = lambda r: (
            (r.s() == 'Web resource' and r.t() == 'Collection'    ) or
            (r.s() == 'Web resource' and r.t() == 'Protocol'      ) or
            (r.s() == 'Web resource' and r.t() == 'Publication'   )     ))

        rt('published', require = lambda r: (
            (r.s() == 'Organization' and r.t() == 'Collection'    )     ))

        # rt('published output of', require = lambda r: (
        #     (r.s() == 'Organization' and r.t() == 'Project'       )     ))

        rt('has publisher', require = lambda r: (
            (r.s() == 'Project' and r.t() == 'Organization'       )     ))

        rt('has use of results limited by', require = lambda r: (
            (r.s() == 'Project' and r.t() == 'License'            )     ))

        rt('is about', require = lambda r: (
            (r.s() == 'Publication' and r.t() == 'Project'        ) or
            (r.s() == 'Publication' and r.t() == 'Collection'     )     ))

        rt('has first author', require = lambda r: (
            (r.s() == 'Publication' and r.t() == 'Person'         )     ))

        rt('has view resource', require = lambda r: (
            (r.s() == 'Protocol' and r.t() == 'Web resource'      )     ))

        rt('from funding agency', require = lambda r: (
            (r.s() == 'Grant' and r.t() == 'Organization'         )     ))

        rt('awarded to', require = lambda r: (
            (r.s() == 'Grant' and r.t() == 'Organization'         )     ))

        rt('is subject of publication', require = lambda r: (
            (r.s() == 'Collection' and r.t() == 'Publication'     ) or
            (r.s() == 'Project' and r.t() == 'Publication'        )     ))

        rt('is subject of resource', require = lambda r: (
            (r.s() == 'Collection' and r.t() == 'Web resource'    )     ))

        rt('is highlighted by', require = lambda r: (
            (r.s() == 'Project' and r.t() == 'Web resource'       )     ))

        rt('is funded by', require = lambda r: (
            (r.s() == 'Project' and r.t() == 'Grant'              )     ))

        # rt('funded', require = lambda r: (
        #     (r.s() == 'Grant' and r.t() == 'Project'              ) or
        #     (r.s() == 'Donor' and r.t() == 'Project'              ) or
        #     (r.s() == 'Organization' and r.t() == 'Project'       )     ))

        # related to, project project

    def project_checker(self, project, strict=False):
        '''
        Checks that a project is associated with at least one output data collection.
        If strict is True, also checks:
        If there are 2 or more, and the titles of these 2 or more are not all equal, then
        the project title must be different from all of these data collections' titles.
        Similarly for short titles and decriptions.
        '''
        if not project.has_multiple('has output'):
            collection = project['has output']
            if collection == None:
                return False
        elif strict:
            collections = project['has outputs']
            for field in ['Title', 'Short title', 'Description']:
                collection_fields = [collection[field] for collection in collections.values()]
                if len(list(set(collection_fields))) > 1:
                    if project[field] in collection_fields:
                        print()
                        print('  Project ' + field + ' "' + blue + project[field] + reset + '" is one of the Collections\' ' + field + 's:')
                        for cf in collection_fields:
                            print('  ' + blue + cf + reset)
                        return False
        return True



