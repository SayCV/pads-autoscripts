#!/usr/bin/env python3

import sys
from regpath import *
from pathlib import Path as path

def main():
    application_list = []

    p = RegistryPath('HKCR')
    for key in p.EnumKey():
        if 'Application' in key:
            application_list.append(key)

    p = RegistryPath('HKCU')
    for key in p.EnumKey():
        if 'Application' in key:
            application_list.append(key)

    p = RegistryPath('HKLM')
    for key in p.EnumKey():
        if 'Application' in key:
            application_list.append(key)

    output_file = path.cwd() / 'data' / 'query_application_in_winreg.txt'
    output_file.parent.mkdir(exist_ok=True)
    output_file.write_text('\n'.join(application_list))

if __name__ == '__main__':
    print(sys.argv)
    main()
