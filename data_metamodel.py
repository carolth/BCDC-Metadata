'''
Data metamodel
==============
This module contains all of the logic for the operation of the database except
for anything that would tie it to specific datasets. Some of the operations
specified here are used in the data models to build up a template for how the
database could or should be structured. Other operations are for the population
of the database itself.

Use test_data_metamodel.py to see example usage.

Classes
=======
1. Relation
2. RelationClass
3. MultipleResults
4. Entity
5. EntityClass
6. Database
7. RelationType
8. EntityType
9. Model

The database
============
Relation, RelationClass, MultipleResults, Entity, and EntityClass are the pre-
requisites for defining the Database itself. A database instance organizes its
entities into named classes, which function as lightweight containers or namespaces,
with few behaviors of their own. An entity's internal structure is comprised of its
relations to other entities and its named primitive fields. Overloading the []
operator is used to provide a uniform syntax for accessing the classes and entities,
'sub'-entities, etc.

Type/validation mechanism
=========================
Rather than fusing the class and type functionality, which is another way of
doing things, here type checking functionality is entirely offloaded to Model
objects that layer on top the database when needed after creation. This simplifies
the database operations themselves, since they do not need to respect type. A
model is comprised mainly of RelationType and EntityType objects. Application
of a model to a database requires a mapping from the EntityClass objects to 
EntityType objects, and from the RelationClass objects to RelationType objects.
'''

from colors import *


class Relation:
    '''
    A Relation is a directed relation between two entities, with a preference for usage
    in the case where the target is regarded as a 'record field' of the source entity.
    Relation objects get registered only to their source and to their targets so entities
    can easily lookup whether or not they remain connected to something.
    Relations only support primitive fields. To access a relation itself (rather than its
    target entity), use the syntax:

        d['entity name'].r('relation class name')

    rather than the usual

        d['entity name']['relation class name']

    This will return a single Relation object if present.
    The following

        d['entity name'].r('plural relation class name')

    will return a dictionary of Relation objects if multiple are present.
    '''
    def __init__(self, relation_class, source, target):
        '''
        Not to be used directly. See RelationClass.create.

        relation_class is a RelationClass object.
        source and target are Entity objects.

        *Note the slight naming inconistency here; it is redundant to specify
        relation_class rather than just class, because we are already in a Relation,
        however class is a Python reserved word so it is not used.
        '''
        self.relation_class = relation_class
        self.source = source
        self.target = target
        self.primitives = {}

    def is_in_class(self, rc):
        return rc == self.relation_class

    def get_class_name(self, plural=False):
        return self.relation_class.get_name(plural=plural)

    def get_source(self):
        return self.source

    def get_target(self):
        return self.target

    def s(self):
        return self.source.get_class_name()

    def t(self):
        return self.target.get_class_name()

    def __getitem__(self, key):
        if key in self.primitives.keys():
            return self.primitives[key]
    def __setitem__(self, key, value):
        self.primitives[key] = value

    def __repr__(self):
        return yellow + self.source.get_name() + reset + ' ' + magenta + '== ' + self.get_class_name() + ' ==>' + reset + ' ' + yellow + self.target.get_name() + reset


class RelationClass:
    '''
    A RelationClass object is attached to each Relation object and serves as a name for
    the relation in the context of the source entity.
    The plural name of a RelationClass is used to assist in formulating queries which
    indicate whether they expect a single result or multiple results.
    '''
    def __init__(self, name, plural_name=None):
        self.name = name
        self.plural_name = plural_name

    def get_name(self, plural=False):
        if plural:
            return self.plural_name
        else:
            return self.name

    def create(self, source, target):
        '''
        Factory creation function. To be used rather than the constructor Relation().
        '''
        if source == None or target == None:
            return None
        r = Relation(self, source, target)
        target.register_inverse_relation(r)
        return r


class MultipleResults(Exception):
    '''
    Thrown when a query to an Entity field (Relation) is in singular form but the
    results would contain multiple Relations.
    '''
    def __init__(self, arg):
        self.message = arg

    def __str__(self):
        return 'Multiple results (' + self.message + ') were returned from a query which expects a single result. Promote your query.'


class Entity:
    '''
    The main class for describing objects in the database.
    Entities do not directly contain other entities, but instead they have Relation
    objects that point to 'sub'-entities (or just related ones).
    Internally, the relations form a dictionary whose lookup keys are the relations
    themselves; this is a device for easy insertion and deletion.

    *Wishlist feature: A simple syntax for 'inversion of perspective' for an entity,
    giving access to relations with target the entity rather than with source the entity.
    Somehow put relations and their inverses on the same par (same plural management, etc.)
    Possibly, by having a thin wrapper object around a symmetrized version of the entity,
    whose only job is to maintain the directionality state and reroute queires to the
    appropriate half of the underlying entity. The wrapper object is instantiated at query
    time and dissipates after the query. The entity persists, of course.
    e.g. d['entity name'].i()['relation class name']
    This can be considered a workaround for the fact that we are using directed terminology
    for each relation class (for simplicity of specification), rather than registering
    separate relations for a relation and its inverse which would need to be linked explicitly.

    Usage syntax
    ------------
    The Entity lookup syntax is:
    
        d['entity name']['relation class name']   or
        d['entity class name']['entity name']['relation class name']

    where d is a Database object. The above expressions return an Entity.
    The syntax can evidently be extended to a chain, as in:

        d['entity name']['relation type name']['another relation type name'] ...

    In many cases the parts of the Entity can be constructed with the assignment
    version of the above syntax:

        d['entity name']['relation type name'] = d['other entity']
        d['entity name']['primitive field name'] = 'primitive value'

    Requirements on initialization
    ------------------------------
    The name should be a unique string for this object within the EntityClass containing
    it. Currently it is also required to be unique globally, permitting a straightforward
    lookup syntax.

    An Entity object needs access to the Database (d) that contains it because an
    Entity needs to be able to ask for the minting of a new Relation, which requires knowledge
    of the available RelationClass objects belonging to the database.

    Simple singular access
    ----------------------
    When at most 1 relation of a given RelationType appears, that relation is available in
    the single_relation_lookup dictionary by lookup with RelationType name. This allows
    efficient access of relations which act like simple fields (particularly primitives,
    which are not technically Relations).

    Multiple access
    ---------------
    Entity objects also support a seamless transition to multiple Relations with the same
    RelationType on assignment to that RelationType, defaulting to addition of a new
    relation rather than overwriting the old one. In this case these Relation objects are
    no longer available in the single_relation_lookup and must be accessed somewhat less
    computationally efficiently, though the access syntax is handy: you use a designated
    'plural' version of the RelationType name.
    The multiple set is used to keep track of which RelationTypes have multiple Relations.
    The unpluralize dictionary is a helper to lookup the unpluralized (canonical)
    RelationType name associated with a given plural form.

    Primitive fields
    ----------------
    Entities also support primitive named fields, which take precedence over RelationClass
    names during access operations.
    Of course it is recommended that these named fields do not overlap with any RelationClass name.
    *Future: This could actually be auto-checked.
    '''
    def __init__(self, entity_class, name, d):
        '''
        entity_class is an EntityClass object.
        name is a string.
        d is a Database object.
        '''
        if entity_class is None:
            raise Exception('Need to specify an entity class when creating an Entity.')
        self.entity_class = entity_class
        self.name = name
        self.relations = {}
        self.single_relation_lookup = {}
        self.unpluralize = {}
        self.multiple = set([])
        self.d = d
        self.primitives = {}
        self.inverse_relations = {}

    def get_name(self):
        return self.name

    def get_class(self):
        return self.entity_class

    def get_class_name(self):
       return self.entity_class.get_name()

    def __str__(self):
        return reset + yellow + self.name + reset

    def __repr__(self):
        s = cyan + self.entity_class.get_name() + reset + ' ' + yellow + self.name + reset + '\n'
        lengths = [len(st) for st in list(self.single_relation_lookup.keys())] + [len(st.get_class_name()) for st in list(self.relations.keys())] + [len(st) for st in list(self.primitives.keys())]
        if len(lengths) == 0:
            return ''
        pad_length = max(lengths)
        for relation_class_name, relation in self.single_relation_lookup.items():
            s = s + magenta + relation_class_name.ljust(pad_length+1) + reset + ' ' + yellow + relation.target.get_name() + reset + '\n'
        for relation in self.relations:
            relation_class_name = relation.get_class_name()
            s = s + magenta + relation_class_name.ljust(pad_length+1) + reset + ' ' + yellow + relation.target.get_name() + reset + '\n'
        for field_name, value in self.primitives.items():
            s = s + field_name.ljust(pad_length+1) + ': ' + blue + str(value) + reset + '\n'
        return s[0:(len(s)-1)]

    def r(self, key):
        # if key in self.unpluralize.keys():
        if key in self.multiple:
            if key in self.unpluralize.keys():
                relation_class_name = self.unpluralize[key]
            else:
                relation_class_name = key
            if relation_class_name in self.multiple:
                return {relation.get_target().get_name() : relation for relation in self.relations if relation.get_class_name() == relation_class_name}

        if key in self.single_relation_lookup.keys():
            relation = self.single_relation_lookup[key]
            return {relation.get_target().get_name() : relation}

    def remove_relation(self, relation):
        ir = relation.get_target().inverse_relations
        del ir[relation]
        if relation.get_class_name() in self.multiple:
            multiplicity = len([r for r in self.relations if r.get_class_name() == relation.get_class_name()])
            del self.relations[relation]
            if multiplicity == 2:
                remaining1 = [r for r in self.relations if r.get_class_name() == relation.get_class_name()][0]
                self.single_relation_lookup[relation.get_class_name()] = remaining1
                del self.relations[remaining1]
                self.multiple = self.multiple.difference(set([relation.get_class_name()]))
            elif multiplicity == 1:
                print('Warning: Prior state of entity was corrupt; only one relation of type ' + relation.get_class_name() + ', but marked as multiple.')
        else:
            del self.single_relation_lookup[relation.get_class_name()]                

    def has_multiple(self, relation_class_name):
        return relation_class_name in self.multiple

    def __getitem__(self, key):
        '''
        The key should be the singular or pluralized name of a RelationClass object.
        If the singular name is provided, and only one Relation of that type pertains
        to this entity, the return value is that Relation object.
        If the singular name is provided, but multiple Relation objects of that type
        pertain to this entity, this function will raise a MultipleResults exception.
        If the pluralized name is provided, the return value is always a dictionary
        whose values are all of the pertient Relation objects (whether this dictionary
        has 0, 1, or more items).
        If the singular and pluralized names are equal, both are treated here from the
        plural point of view.
        '''
        if key in self.unpluralize.keys():
            relation_class_name = self.unpluralize[key]
            self.targets = {}
            for relation in self.relations:
                if relation_class_name == relation.get_class_name():
                    target = relation.get_target()
                    self.targets[target.get_name()] = target
            return self.targets

        if key in self.multiple:
            relation_class_name = key
            results = [relation.get_target().get_name() for relation in self.relations if relation.get_class_name() == relation_class_name]
            raise MultipleResults(', '.join(results))

        if key in self.single_relation_lookup.keys():
            relation_class_name = key
            relation = self.single_relation_lookup[relation_class_name]
            return relation.get_target()

        if key in self.primitives.keys():
            return self.primitives[key]

    def __setitem__(self, key, value):
        '''
        The key should be the singular name of a RelationClass object.
        The value should be an Entity or primitive (int, str, bool).
        A new Relation object is added with target value.
        If the field is a primitive and not a Relation, the field is overwritten with value.
        Primitives cannot have multiplicity.
        '''
        if value is None:
            print('Warning: No value provided for target of relation "' + key + '", with source ' + self.get_name() + '.')
            return

        if key in self.unpluralize.keys():
            print('Warning: No syntax is available to use plural forms of relation names for adding new target values. Use the singluar form multiple times.')
            return

        if key in self.primitives.keys() or (not key in self.d.relation_classes):
            self.primitives[key] = value
            return

        if key in self.single_relation_lookup.keys():
            # There is exactly 1 of these class of relations existing
            relation_class_name = key
            new = self.d.create_relation(self, value, relation_class_name=relation_class_name)
            existing = self.single_relation_lookup[relation_class_name]
            # We will be leaving this entity with more than 1 of these type, so remove the single marker
            del self.single_relation_lookup[relation_class_name]
            self.multiple.add(relation_class_name)
            self.relations[existing] = existing
            self.relations[new] = new
            if new.get_class_name(plural=True) != None:
                self.unpluralize[new.get_class_name(plural=True)] = new.get_class_name()
        else:
            if not key in [relation.get_class_name() for relation in self.relations]:
                # Adding a relation of this type for the first time
                relation_class_name = key
                new = self.d.create_relation(self, value, relation_class_name=relation_class_name)
                self.single_relation_lookup[relation_class_name] = new
                return
            else:
                # Adding an additional relation of the multiple type
                relation_class_name = key
                new = self.d.create_relation(self, value, relation_class_name=relation_class_name)
                self.relations[new] = new

    def __contains__(self, key):
        '''
        Checks whether an entity is one of this given entity's relation targets.
        '''
        entity = key
        if entity.get_name() in [relation.get_target().get_name() for relation in self.relations]:
            return True
        else:
            return False

    def register_inverse_relation(self, r):
        self.inverse_relations[r] = r

    def erase(self):
        for relation in self.relations:
            relation.source = None
        for relation_class_name, relation in self.single_relation_lookup.items():
            relation.source = None
        for relation in self.inverse_relations:
            relation.target = None

class EntityClass:
    def __init__(self, name):
        self.name = name
        self.entities = {}

    def get_name(self):
        return self.name

    def __getitem__(self, key):
        if key in self.entities:
            return self.entities[key]
        else:
            fields = {}
            for entity in self.entities.values():
                if entity[key] != None:
                    if type(entity[key]) is Entity:
                        fields[entity.get_name()] = yellow + entity[key].get_name() + reset
                    else:
                        fields[entity.get_name()] = magenta + str(entity[key]) + reset
            if len(fields) > 0:
                length = max([len(str(key)) for key in fields])
                for name in fields:
                    field = fields[name]
                    print((yellow+name+reset+':') + ' '*(length-len(name)+2) + ' ' + field)
            return None

    def __setitem__(self, key, value):
        if key in self.entities:
            raise Exception('I am refusing to overwrite an entity with the same name in EntityClass ' + self.name + '.')
        else:
            self.entities[key] = value

    def __delitem__(self, key):
        if key in self.entities:
            e = self.entities[key]
            e.erase()
            del self.entities[key]

    def __repr__(self):
        return yellow + '\n'.join([val.name for val in self.entities.values()]) + reset

class Database:
    def __init__(self):
        self.entity_classes = {}
        self.entity_class_lookup = {}
        self.relation_classes = {}
        self.entity_classes[''] = EntityClass('')
        self.relation_classes[''] = RelationClass('', plural_name='s')

    def create_entity_class(self, class_name):
        if class_name == '':
            print('Warning: Anonymous entity class is reserved.')
            return
        if not class_name in self.entity_classes:
            self.entity_classes[class_name] = EntityClass(class_name)

    def create_entity(self, *args, or_lookup=False):
        '''
        You supply 'class_name, name' or 'name'.
        Creates a new entity and returns the Entity object.
        name must be unique in the namespace provided by the EntityClass named
        class_name; multiple entities with the same name are not allowed.
        If class_name is absent, the new entity goes into the anonymous namespace.
        '''
        if len(args) == 1:
            name = args[0]
            class_name = ''
        elif len(args) == 2:
            name = args[1]
            class_name = args[0]
        if not class_name in self.entity_classes:
            self.create_entity_class(class_name)
        ec = self.entity_classes[class_name]
        if name in ec.entities:
            print('Warning: Entity ' + name + ' already exists in EntityClass ' + class_name + '.')
            if or_lookup:
                return self[name]
            return
        elif name in self.entity_class_lookup:
            print('Warning: ' + name + ' is not globally unique, already contained in class ' + self.entity_class_lookup[name])
            return
        else:
            entity = Entity(ec, name, self)
            ec[name] = entity
            self.entity_class_lookup[name] = class_name
            return entity

    def create_relation_class(self, relation_class_name, plural_name=None):
        if relation_class_name == '':
            print('Warning: Anonymous relation class is reserved.')
            return
        if not relation_class_name in self.relation_classes:
            self.relation_classes[relation_class_name] = RelationClass(relation_class_name, plural_name=plural_name)

    def create_relation(self, source, target, relation_class_name=''):
        if not relation_class_name in self.relation_classes:
            return None
        relation_class = self.relation_classes[relation_class_name]
        return relation_class.create(source, target)

    def __getitem__(self, key):
        if key in self.entity_class_lookup:
            class_name = self.entity_class_lookup[key]
            ec = self.entity_classes[class_name]
            if not key in ec.entities:
                print('Warning: Corrupted entity_class_lookup or mismatch with entity_class ' + class_name + '\'s own roster. Tried to find entity ' + key + '.')
                return None
            return ec[key]
        if key in self.entity_classes:
            return self.entity_classes[key]
        if key in self.relation_classes:
            return self.relation_classes[key]
        return None

    def __delitem__(self, key):
        if key in self.entity_class_lookup:
            class_name = self.entity_class_lookup[key]
            ec = self.entity_classes[class_name]
            if not key in ec.entities:
                print('Warning: Corrupted entity_class_lookup or mismatch with entity_class ' + class_name + '\'s own roster. Tried to find entity ' + key + '.')
                return
            ec.entities[key].erase()
            del ec.entities[key]
            if len(ec.entities) == 0:
                del self.entity_classes[class_name]
            del self.entity_class_lookup[key]
            return

        if key in self.entity_classes:
            class_name = key
            ec = self.entity_classes[class_name]
            for entity in ec.entities:
                name = ec[entity].get_name()
                if name in self.entity_class_lookup:
                    del self.entity_class_lookup[name]
            del self.entity_classes[class_name]
            return


class RelationType:
    '''
    A RelationType object is responsible for checking that its member Relation objects
    conform to a standard specified by a single validator, the 'require' function, which
    is supplied on creation.
    '''
    def __init__(self, name, plural_name=None, require=lambda relation : True):
        '''
        require should be a function of the relation that decides whether it really satisfies
        the conditions of the type.
        '''
        self.name = name
        self.plural_name = plural_name
        self.require = require

    def get_name(self):
        return self.name

    def check(self, r, verbose=[]):
        result = self.require(r)
        if verbose == []:
            return result
        else:
            if not result:
                if 'failing' in verbose:
                    print(red   + 'Failed' + reset + '  ' + yellow + r.source.get_name() + reset + magenta + ' == ' + self.name + ' =/ /=> ' + reset + yellow + r.target.get_name() + reset)
            else:
                if 'passing' in verbose:
                    print(green + 'Passed' + reset + '  ' + yellow + r.source.get_name() + reset + magenta + ' == ' + self.name + ' ==> ' + reset + yellow + r.target.get_name() + reset)
            return result

class EntityType:
    '''
    Used for delayed or infrequent type checking of Entity objects, typically in large
    validation batches.
    You supply a function, the require function, that evaluates the candidate to be of
    this EntityType.
    EntityTypes can be layered by means of the super_types parameter. That is,
    one EntityType can serve as an amalgamation of several previously-defined types.
    No acyclicity check is performed. Don't make circular super_type dependencies.
    '''
    def __init__(self, name, require=lambda entity:True, super_types=[]):
        self.name = name
        self.require = require
        self.super_types = super_types

    def get_name(self):
        return self.name

    def check(self, entity, verbose=[]):
        for t in self.super_types:
            result = t.check(entity, verbose=verbose)
            if result == False:
                return False
        result = self.require(entity)
        if verbose == []:
            return result
        else:
            if not result:
                if 'failing' in verbose:
                    print(red   + 'Failed' + reset + '  ' + yellow + entity.get_name() + reset + ' is not a ' + cyan + self.name + reset)
            else:
                if 'passing' in verbose:
                    print(green + 'Passed' + reset + '  ' + yellow + entity.get_name() + reset + ' is a ' + cyan + self.name + reset)
            return result

    def __repr__(self):
        return 'EntityType: ' + self.name


class Model:
    '''
    Stores a collection of EntityType objects and RelationType objects, which together
    serve as the data model for a Database object.

    EntityClass objects act as containers and namespaces for the Entity objects in
    the database. EntityClass and EntityType instances may often be in one to one
    correspondence, but they have different functions; the former is for storage and
    lookup convenience, the aspect of 'type' which is about category assignment, and the
    latter is for deeper internal analysis and validation of the contents of an entity.

    Before a model can validate a database, it must be 'connected'. Connection attempts
    to automatically determine, by names, which EntityType to apply to a given EntityClass
    object in the Database. In the future, EntityType objects may be endowed with their
    own 'targeting' function that crawls the database looking for entities to which it
    ought to apply. This idea is inspired by SHACL targets.

    RelationType checking should be similar. Currently it is unimplemented.
    '''
    def __init__(self):
        self.relation_types = {}
        self.entity_types = {}
        self.entity_class_type_mapping = {}
        self.relation_class_type_mapping = {}

    def add_relation_type(self, name, plural_name=None, require=lambda relation:True):
        rt = RelationType(name, plural_name=plural_name, require=require)
        if name in self.relation_types:
            print('Warning: ' + name + ' is already the name of a RelationType.')
            return
        self.relation_types[name] = rt

    def add_entity_type(self, name, require=lambda entity:True, super_types=[]):
        et = EntityType(name, require=require, super_types=super_types)
        if name in self.entity_types:
            print('Warning: ' + name + ' is already the name of an EntityType.')
            return
        self.entity_types[name] = et

    def __getitem__(self, key):
        if key in self.entity_types:
            return self.entity_types[key]
        if key in self.relation_types:
            return self.relation_types[key]

    def connect(self, d):
        self.d = d
        self.entity_class_type_mapping = {}
        for entity_class_name in d.entity_classes:
            if entity_class_name in self.entity_types:
                et = self.entity_types[entity_class_name]
                ec = d.entity_classes[entity_class_name]
                self.entity_class_type_mapping[ec] = et

        self.relation_class_type_mapping = {}
        for relation_class_name in d.relation_classes:
            if relation_class_name in self.relation_types:
                rt = self.relation_types[relation_class_name]
                rc = d.relation_classes[relation_class_name]
                self.relation_class_type_mapping[rc] = rt

        if len(self.entity_class_type_mapping) == 0:
            print('Warning: No entity classes could be connected to a type in the model.')
            return False
        if len(self.relation_class_type_mapping) == 0 and len(d.relation_classes) > 0:
            print('Warning: No relation classes could be connected to a type in the model.')
        return True

    def check(self, d):
        r = self._full_check(d)
        return r

    def why(self):
        if self.result == True:
            print('The database conforms to the model.')
        else:
            print('The database ' + red + 'does not' + reset + ' conform to the model:')
            self._full_check(None, verbose=['failing'])

    def report(self):
        print('All checks:')
        self._full_check(None, verbose=['passing', 'failing'])
        print()

    def _full_check(self, d, verbose=[]):
        if not d is None:
            self.connected = self.connect(d)
        if not self.connected:
            print('Nothing to check. No connection to database.')
            return
        result = True
        for ec, et in self.entity_class_type_mapping.items():
            for entity in list(ec.entities.values()):
                if not et.check(entity, verbose=verbose):
                    result = False
                for rc, rt in self.relation_class_type_mapping.items():
                    for relation in [relation for relation in list(entity.relations.values()) if relation.is_in_class(rc)]:
                        if not rt.check(relation, verbose=verbose):
                            result = False
                    for relation in [relation for relation in list(entity.single_relation_lookup.values()) if relation.is_in_class(rc)]:
                        if not rt.check(relation, verbose=verbose):
                            result = False
        self.result = result
        return result

    def number_failing(self, entity_class):
        ec = entity_class
        if not ec in self.entity_class_type_mapping:
            return 0
        et = self.entity_class_type_mapping[ec]
        return sum([1 for e in ec.entities.values() if not et.check(e)])

    def stats(self):
        counts = { name: len(self.d.entity_classes[name].entities) for name in self.d.entity_classes}
        counts = { name : counts[name] for name in sorted(list(counts.keys()))}
        failing = { name : self.number_failing(self.d.entity_classes[name]) for name in counts}
        padlength = max([len(name) for name in counts])
        print(padlength)
        for i in range(len(counts)):
            name = list(counts.keys())[i]
            total_number = counts[name]
            number_failing = failing[name]
            number_passing = total_number - number_failing
            if name == '':
                name = '<anonymous>'
            extra = ''
            if number_failing > 0:
                extra = ' (' + red + str(number_failing) + reset + ')'
            print(cyan + (name + ':').ljust(padlength + 2) + reset + green + str(number_passing) + reset + extra)


