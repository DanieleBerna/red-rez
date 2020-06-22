from shutil import copyfile
from subprocess import run
import os
import zipfile
import sys

_PORTABLE_PYTHON_ZIP = "portable_python_374.zip"  # zipped archive of WinPython portable interpreter
_REZ_ZIP = "rez.zip"  # zipped archive of Rez (cloned from https://github.com/nerdvegas/rez )
_DEFAULT_INSTALL_FOLDER = r"T:/"
_UGCORE_DIR = "ugcore"


def create_python_pakage_file(interpreter_folder, version):
    """
    Create a package.py file used to rez-build an embedded interpreter
    :param interpreter_folder: folder of the python.exe file
    :param version: Python (and package) version
    """
    try:
        package_build_file = open(os.path.join(interpreter_folder, "package.py"), "w+")
        package_build_file.write(f"import os\n\nname = 'python'\nversion = '{version}'\nbuild_command = {{this._bin_path}}/rezbuild.py {{install}}\n\n@early()\n"
                                 f"def _bin_path():\n\treturn os.getcwd()\n\ndef commands():\n\tglobal env\n\t"
                                 f"env['PATH'].prepend('{{this._bin_path}}')")
        package_build_file.close()
    except IOError as e:
        print(f"Error while writing package.py file for Python interpreter\n{e}")
        return False
    return True

print(f"RED REZ - Redistributable Rez installer\n")

""" The pipeline uses a portable Python 3.7.7 (WinPython) to install and then run rez.
The pipeline requires all tools to be installed in a local folder that is then remapped to a previously agreed unit."""

install_folder = input("Install folder ("+_DEFAULT_INSTALL_FOLDER+"): ") or _DEFAULT_INSTALL_FOLDER

remap_to = input("Remap folder to a new unit (no)? ") or False

if remap_to:
    try:
        remap_to = remap_to.upper()
        run(["subst", (remap_to.upper()+":"), install_folder])
        print(f"{install_folder} is remapped to {remap_to} unit")
        install_folder = remap_to+":\\"
    except:
        print(f"An error has occurred while remapping {install_folder} to {remap_to} unit")
        exit()

startup_python_folder = os.path.join(install_folder, _UGCORE_DIR)
print("Extracting portable Python...")
with zipfile.ZipFile(os.path.join(os.path.dirname(sys.argv[0]), _PORTABLE_PYTHON_ZIP), 'r') as zip_ref:
    zip_ref.extractall(startup_python_folder)
startup_python_folder = os.path.join(startup_python_folder, "python")

""" REZ install script"""
temp_rez_folder = (os.path.join(install_folder,  _UGCORE_DIR, "temp_rez"))
print("Extracting rez source...")
with zipfile.ZipFile(os.path.join(os.path.dirname(sys.argv[0]), _REZ_ZIP), 'r') as zip_ref:
    zip_ref.extractall(temp_rez_folder)
rez_folder = os.path.join(install_folder, _UGCORE_DIR, "rez")
print("Runnint rez install.py...")
run([os.path.join(startup_python_folder, "python.exe"), os.path.join(temp_rez_folder, "rez", "install.py"), "-v", os.path.join(install_folder, _UGCORE_DIR, "rez")])
rez_bin_folder = os.path.join(rez_folder, "Scripts", "rez")

include_file = True
if include_file:
    rez_config_filename = os.path.join(rez_folder, "rezconfig.py")
else:
    rez_config_filename = rez_folder

os.environ["REZ_CONFIG_FILE"] = rez_config_filename
run(["setx.exe", "REZ_CONFIG_FILE", rez_config_filename])
print(f"\nREZ_CONFIG_FILE set to: {os.environ.get('REZ_CONFIG_FILE')}\n")

local_packages_folder = os.path.join(rez_folder,'packages').replace('\\','/')
release_packages_path = input("Release rez packages folder (\\\\ASH\Storage\.rez\packages): ") or r"\\ASH\Storage\.rez\packages"
release_packages_path = os.path.join(release_packages_path, "rez", "packages").replace('\\', '/')

if include_file:
    rez_config_file = open(os.path.join(rez_config_filename), "w+")
else:
    rez_config_file = open(os.path.join(rez_config_filename, "rezconfig.py"), "w+")

rez_config_file.write(f"# The package search path. Rez uses this to find packages. A package with the\n# same name and version in an earlier path takes precedence.\npackages_path = [\n\t\"{local_packages_folder}\",\n\t\"{release_packages_path}\"]\n")
rez_config_file.write(f"#REZ_LOCAL_PACKAGES_PATH\n# The path that Rez will locally install packages to when rez-build is used\nlocal_packages_path = \"{local_packages_folder}\"\n")
rez_config_file.write(f"#REZ_RELEASE_PACKAGES_PATH\n# The path that Rez will deploy packages to when rez-release is used. For\n# production use, you will probably want to change this to a site-wide location.\nrelease_packages_path = \"{release_packages_path}\"")

env_variables = os.environ.copy()

os.chdir(startup_python_folder)
# create_python_pakage_file(startup_python_folder, "3.7.4")
run([os.path.join(rez_bin_folder, "rez-bind"), "-i", local_packages_folder, "platform"], shell=True, env=env_variables)
run([os.path.join(rez_bin_folder, "rez-bind"), "-i", local_packages_folder, "arch"], shell=True, env=env_variables)
run([os.path.join(rez_bin_folder, "rez-bind"), "-i", local_packages_folder, "os"], shell=True, env=env_variables)
run([os.path.join(rez_bin_folder, "rez-build"), "--install"])
run([os.path.join(rez_bin_folder, "rez-bind"), "-i", local_packages_folder, "rez"], shell=True, env=env_variables)
