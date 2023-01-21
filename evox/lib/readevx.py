import tarfile

def readevx(filename, package):
    """Reads an eVox file and returns the data as a dictionary.
    """
    # The eVox file is a tarball, so we need to open it as such.
    with tarfile.open(filename, "r") as tar:
        # The eVox archive has the following structure:
        # - metadata/
        #  - PKGINFO
        #  - PKGDEPS
        #  - PKGTREE
        # - data/
        #   - <files>
        # - scripts/
        #   - <scripts>

        # We need to extract the PKGINFO file to get the package infos.
        # The PKGINFO has the following needed fields:
        # - name
        # - version
        # - description
        # - source
        # And the following optional fields:
        # - url
        # - license
        
        # Extract the PKGINFO file
        pkginfo = tar.extractfile(package + "/metadata/PKGINFO").read().decode("utf-8")
        # Split the PKGINFO file into lines
        pkginfo = pkginfo.splitlines()
        # Create a dictionary to store the package infos
        pkginfo_dict = {}
        # Loop through the lines
        for line in pkginfo:
            # Split the line into key and value
            key, value = line.split(" = ")
            # Add the key and value to the dictionary
            pkginfo_dict[key] = value

        # We check that the needed fields are present
        if "name" not in pkginfo_dict:
            raise Exception("Package name not found in PKGINFO")
        if "version" not in pkginfo_dict:
            raise Exception("Package version not found in PKGINFO")
        if "description" not in pkginfo_dict:
            raise Exception("Package description not found in PKGINFO")
        if "source" not in pkginfo_dict:
            raise Exception("Package source not found in PKGINFO")
        
        # We need to extract the PKGDEPS file to get the package dependencies.
        # The PKGDEPS file has the following structure:
        # - <package name>
        # - <package name>
        # - <package name>
        # - ...

        # Note that the package dependencies are optional, so we need to check if the file exists.
        if package + "/metadata/PKGDEPS" in tar.getnames():
            # Extract the PKGDEPS file
            pkgdeps = tar.extractfile(package + "/metadata/PKGDEPS").read().decode("utf-8")
            # Split the PKGDEPS file into lines
            pkgdeps = pkgdeps.splitlines()
            # Create a list to store the package dependencies
            pkgdeps_list = []
            # Loop through the lines
            for line in pkgdeps:
                # Add the line to the list
                pkgdeps_list.append(line)

            # We add the package dependencies to the package infos dictionary
            pkginfo_dict["depends"] = pkgdeps_list

        # We return the package infos dictionary
        return pkginfo_dict