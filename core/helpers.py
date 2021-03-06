import importlib
import sys
import os
from xml.etree import ElementTree
import pkgutil

import core.config.paths


def get_cytoscape_data(steps):
    output = []
    for step in steps:
        node = {"group": "nodes", "data": {"id": steps[step]["name"]}}
        output.append(node)
        for next_step in steps[step].conditionals:
            edge_id = str(steps[step]["name"]) + str(next_step["name"])
            if next_step["name"] in steps:
                node = {"group": "edges", "data": {"id": edge_id,
                                                   "source": steps[step]["name"],
                                                   "target": next_step["name"]}}
            output.append(node)
    return output


def import_py_file(module_name, path_to_file):
    if sys.version_info[0] == 2:
        from imp import load_source
        imported = load_source(module_name, os.path.abspath(path_to_file))
    else:
        from importlib import machinery
        loader = machinery.SourceFileLoader(module_name, os.path.abspath(path_to_file))
        imported = loader.load_module(module_name)
    return imported


def import_lib(directory, module_name):
    module = None
    try:
        module = importlib.import_module('.'.join(['core', directory, module_name]))
    except ImportError:
        pass
    finally:
        return module


def construct_module_name_from_path(path):
    path = path.lstrip('.{0}'.format(os.sep))
    path = path.replace('.', '')
    return '.'.join([x for x in path.split(os.sep) if x])


def import_app_main(app_name):
    app_path = os.path.join(core.config.paths.apps_path, app_name, 'main.py')
    module_name = construct_module_name_from_path(app_path[:-3])
    try:
        return sys.modules[module_name]
    except KeyError:
        pass
    try:
        module = import_py_file(module_name, app_path)
        sys.modules[module_name] = module
        return module
    except (ImportError, IOError, OSError):
        pass


def __list_valid_directories(path):
    try:
        return [f for f in os.listdir(path)
                if (os.path.isdir(os.path.join(path, f))
                    and not f.startswith('__'))]
    except (IOError, OSError):
        return []



def list_apps(path=None):
    if path is None:
        path = core.config.paths.apps_path
    return __list_valid_directories(path)


def list_widgets(app, app_path=None):
    if app_path is None:
        app_path = core.config.paths.apps_path
    return __list_valid_directories(os.path.join(app_path, app, 'widgets'))


def list_class_functions(class_name):
    return [field for field in dir(class_name) if (not field.startswith('_')
                                                   and callable(getattr(class_name, field)))]


def load_app_function(app_instance, function_name):
    try:
        fn = getattr(app_instance, function_name)
        return fn
    except AttributeError:
        return None


def locate_workflows_in_directory(path=core.config.paths.workflows_path):
    return [workflow for workflow in os.listdir(path) if (os.path.isfile(os.path.join(path, workflow))
                                                          and workflow.endswith('.workflow'))]


def get_workflow_names_from_file(filename):
    if os.path.isfile(filename):
        tree = ElementTree.ElementTree(file=filename)
        return [workflow.get('name') for workflow in tree.iter(tag="workflow")]


__workflow_key_separator = '-'


def construct_workflow_name_key(playbook, workflow):
    return '{0}{1}{2}'.format(playbook.lstrip(__workflow_key_separator), __workflow_key_separator, workflow)


def extract_workflow_name(workflow_key, playbook_name=''):
    if playbook_name and workflow_key.startswith(playbook_name):
        return workflow_key[len('{0}{1}'.format(playbook_name, __workflow_key_separator)):]
    else:
        return __workflow_key_separator.join(workflow_key.split(__workflow_key_separator)[1:])


def combine_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z


def import_submodules(package, recursive=False):
    if isinstance(package, str):
        package = importlib.import_module(package)
    results = {}
    for loader, name, is_package in pkgutil.walk_packages(package.__path__):
        full_name = '{0}.{1}'.format(package.__name__, name)
        results[full_name] = importlib.import_module(full_name)
        if recursive and is_package:
            results.update(import_submodules(full_name))
    return results
