import os
import sys
import importlib
import builtins
import importlib.util
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def module_from_file(file,name=''):
    _spec = importlib.util.spec_from_file_location(name,file)
    mod=importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(mod)
    return mod
def load_module(name):
    if 'BUHTIG'+name.upper() not in os.environ:

        if not hasattr(modules,name.upper()):
        
            print(f'{bcolors.FAIL}{bcolors.BOLD}envar.load_module{bcolors.ENDC}{bcolors.FAIL}: failed to load module {name}!\nSet variable $BUHTIG{name.upper()} or add constant {name.upper()} to file modules.py!{bcolors.ENDC}',file=sys.stderr)
            exit(1)
        m=module_from_file(getattr(modules,name.upper()),name)
    else:
        m=module_from_file(os.environ['BUHTIG'+name.upper()],name)
    setattr(builtins,name,m)
    return m
modules=module_from_file('modules.py','modules')
