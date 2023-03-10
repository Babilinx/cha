"""Cha 1.0.0

Usage:
  cha get [-y] <package>...
  cha remove <package>...
  cha upgrade
  cha info <package>
  cha search <expr>
  cha sync
  cha init
  cha tree <package>
  cha (-h | --help)
  cha (-v | --version)

Options:
  get           Download and install a package
  remove        Remove a package (and optionnally its dependencies)
  search        Search a package
  info          Show information about an installed package
  sync          Sync the repos
  upgrade       Upgrade the system
  init          Initialize the default structure following the configuration
  tree          Show the dependencies of an installed package, and the dependencies of their dependencies
  -h --help     Show this screen.
  -v --version     Show version.

"""

import shutil
from docopt import docopt

import os

import lib.instpkg as instpkg
import lib.log as log
import lib.config as config
import lib.rmpkg as rmpkg
import lib.db as db
import lib.net as net

from lib.root import *

def find_dependencies(package):
    tree = {}
    tree[package] = {}
    # We get the dependencies of the package
    dependencies = db.get_local_package_pkgdeps(package)
    # We loop through the dependencies
    for dependency in dependencies:
        # We get the dependencies of the dependency
        tree[package][dependency] = find_dependencies(dependency)[dependency]
    return tree

def print_dependencies(tree, level=1, already_printed=[]):
    # We loop through the dependencies
    for dependency in tree:
        if not dependency in already_printed:
            # We print the dependency
            print("--" * level + ">" + dependency)
            # We print the dependencies of the dependency
            print_dependencies(tree[dependency], level + 1, already_printed)

            already_printed.append(dependency)

if __name__ == '__main__':
    arguments = docopt(__doc__, version='Cha 1.0.0')

    if arguments['get']:
        for package in arguments['<package>']:
            instpkg.install_pkg(package, auto_accept=arguments['-y'])

    if arguments['init']:
        # We just need to create the /var/evox/packages directory, the /var/evox/repos directory
        # We can use the os.makedirs function
        os.makedirs(root + "/var/evox/packages", exist_ok=True)
        os.makedirs(root + "/var/evox/repos", exist_ok=True)
        os.makedirs(root + "/etc", exist_ok=True)
        # We also need to copy the /etc/evox.conf file only if ROOT isn't /
        if root != "/":
            shutil.copyfile("/etc/evox.conf", root + "/etc/evox.conf")
        # For each repository, we create a directory
        # When we get the config, we get a dictionary of the repositories
        # The dictionary is structured like this:
        # {"repo_name": {"path": "path", "url": "url"}}
        # We can use the config.get_config() function to get the dictionary
        for repo in config.get_config():
            os.makedirs(root + "/var/evox/repos/" + repo, exist_ok=True)

        # We also need to create the /var/evox/packages/DB file
        # We can use the open function
        open(root + "/var/evox/packages/DB", "w").close()

        # We can log a success message
        log.log_success("The default structure has been created.")

    if arguments['remove']:
        for package in arguments['<package>']:
            # First, we check if the package is installed
            # We can use the lib.instpkg.is_installed function
            if instpkg.is_package_installed(package):
                # If it is, we remove it
                rmpkg.rmpkg(package)
                if not instpkg.is_package_installed(package):
                    # If it is removed, we log a success message
                    log.log_success("The package " + package +
                                    " has been removed.")
            else:
                # If it isn't, we log an error
                log.log_error("The package " + package + " is not installed.")

    if arguments['sync']:
        # We get the config
        repos = config.get_config()

        # We loop through the repositories
        for repo in repos:
            # We get the URL of the repository
            url = repos[repo]["url"]
            # The path of the repository is /var/evox/repos/repo
            path = root + "/var/evox/repos/" + repo

            # If the repository doesn't exist, we create it
            # We can use the os.path.exists function
            if not os.path.exists(path):
                # We can use the os.makedirs function
                os.makedirs(path, exist_ok=True)

            # We simply get the INDEX file from the repository with net.download
            index = net.download(url + "/INDEX", path + "/INDEX", False)

            # We can log a success message
            log.log_success("The repository " + repo + " has been synced.")

    if arguments['upgrade']:
        # We get the installed packages
        installed_packages = db.get_installed_packages()

        # We loop through the packages
        for package in installed_packages:
            # We check if the package is in the repository thanks to the os.path.exists function
            if os.path.exists(root + "/var/evox/packages/" + package):
                # If it is, we get the version of the package
                version = installed_packages[package]
                # We get the version of the package in the repository
                repo_version = db.get_remote_package_version(package)
                local_pkgrel = db.get_local_package_pkgrel(package)
                remote_pkgrel = db.get_remote_package_pkgrel(package)
                # If the version of the package in the repository is higher than the installed version
                if repo_version != version or local_pkgrel < remote_pkgrel:
                    # Log an info message
                    log.log_info("The package " + package + " is being upgraded from version " + version + "-" + str(
                        local_pkgrel) + " to version " + repo_version + "-" + str(remote_pkgrel) + ".")
                    # First, we need to move the old package to /var/evox/packages/<package>.old
                    # We can use the os.rename function
                    shutil.move(root + "/var/evox/packages/" + package,
                              root + "/var/evox/packages/" + package + ".old")

                    # We unregister the package
                    db.unregister_local(package)

                    # Then, we need to install the new package
                    instpkg.install_pkg(package, auto_accept=True, upgrade=True)

                    # After that, we need to remove the old package 
                    # But be careful, we need to only remove the old files and not the new ones
                    # So to do that, we need to get the files of the old package and the new package
                    # We read the PKGTREE file of the old package
                    old_pkgtree = open(root + "/var/evox/packages/" + package + ".old/PKGTREE", "r").readlines()
                    # We read the PKGTREE file of the new package
                    new_pkgtree = open(root + "/var/evox/packages/" + package + "/PKGTREE", "r").readlines()

                    # We create a list of the old files
                    old_files = []
                    # We loop through the old PKGTREE
                    for line in old_pkgtree:
                        # We add the file to the list
                        old_files.append(line.strip())

                    # We create a list of the new files
                    new_files = []
                    # We loop through the new PKGTREE
                    for line in new_pkgtree:
                        # We add the file to the list
                        new_files.append(line.strip())

                    files_to_remove = []
                    # We loop through the old files
                    for file in old_files:
                        # We check if the file is not in the new files
                        if file not in new_files:
                            # If it isn't, we add it to the list of files to remove
                            files_to_remove.append(file)

                    # We give the list of files to remove to the rmpkg.rmtree function
                    rmpkg.rmtree(files_to_remove)

                    # Finally, we remove the old package
                    shutil.rmtree(root + "/var/evox/packages/" + package + ".old")

                    # We log a success message
                    log.log_success("The package " + package + " has been upgraded from version " + version + "-" + str(
                        local_pkgrel) + " to version " + repo_version + "-" + str(remote_pkgrel) + ".")

    if arguments['search']:
        # We get the config
        repos = config.get_config()
        # We get the expression
        expr = arguments['<expr>']
        # We create a list of packages
        packages = db.get_remote_packages()
        installed_packages = db.get_installed_packages()
        # We loop through the packages
        for package in packages:
            # If the package contains the expression
            if expr in package[0]:
                if instpkg.is_package_installed(package[0]):
                    local_pkgrel = db.get_local_package_pkgrel(package[0])
                    # We log the package
                    log.log_info(package[0] + " (" + package[1] + "-" + package[2] + ")[Installed " +
                                 installed_packages[package[0]] + "-" + str(local_pkgrel) + "]")
                else:
                    # We log the package
                    log.log_info(
                        package[0] + " (" + package[1] + "-" + package[2] + ")")

    if arguments['info']:
        # We get the config
        repos = config.get_config()
        # We get the package
        package = arguments['<package>'][0]
        # We get the package info
        info = db.get_local_package_info(package)
	# Assignate info to variables
        name = info['name']
        version = info['version']
        description = info['description']
        source = info['source']
        if 'license' in info: license = info['license']
        else: license = 'unknown'
        if 'url' in info: url = info['url']
        else: url = 'unknown'
        if 'maintainer' in info: maintainer = info['maintainer']
        else: maintainer = 'unknown'
        # Add spacers for good UI
        name_spacer = ' ' * (len(name) + 4 - len('name'))
        version_spacer = ' ' * (len(version) + 4 - len('version'))
        description_spacer = ' ' * (len(description) + 4 - len('description'))
        license_spacer = ' ' * (len(license) + 4 - len('license'))
        maintainer_spacer = ' ' * (len(maintainer) + 4 - len('maintainer'))
        source_spacer = ' ' * (len(source) + 4 - len('source'))
        # We log the info
        print(f'\n{Style.BRIGHT}Name{name_spacer}Version{version_spacer}Description{description_spacer}License{license_spacer}Maintainer{maintainer_spacer}Source{source_spacer}{url}')
	print(f'{name}    {version}    {description}    {license}    {maintainer}    {source}    {url}')


    if arguments['tree']:
        package = arguments['<package>'][0]
        if not instpkg.is_package_installed(package):
            log.log_error(f"The package {package} is not installed.")
            exit(1)
        tree = find_dependencies(package)
        print(package)
        print_dependencies(tree[package])
