# Cha, a simple and lightweight package manager

Cha is the package toolbox of [ChaOS](). It can create, build packages from source, but also install, upgrade and remove them.
It is a fork of [evox](https://github/stock-linux/evox)-1.1.1 RIP Stock Linux.

# Usage

```
Cha.

Usage:
  cha get <package>...
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
```
