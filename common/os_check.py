def is_trixie():
    is_debian = False
    _is_trixie = False
    try:
        with open("/etc/os-release", "r") as os_release:
            lines = os_release.readlines()
            for line in lines:
                n, v = line.split("=")
                v = v.strip()
                if v[0] == '"' and v[-1] == '"': v = v[1:-1]

                if n == "ID" and v == "debian":
                    is_debian = True
                elif n == "VERSION_CODENAME" and v == "trixie":
                    _is_trixie = True
        return is_debian and _is_trixie
    except IOError as e:
        return False