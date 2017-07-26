#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: flatpak
version_added: "0.0.1"
supports_check_mode: yes
author: 
    - John Kwiatkoski (@jaykayy)
short_description: install and remove flatpaks
description:
    - The flatpak module allows users to manage installation and removal of flatpaks.
options:
  name:
    description:
      - Name of the flatpak in `https://...` url format. Reverse dns format can optionally be used with `state=absent` ex: name=org.gnome.gedit.
    required: false
    default: ''
    aliases: []
  remote:
    description:
      - The flatpak remote repo to be used in the flatpak operation.
    required: false
    default: '' 
  state:
    description:
      - Set to `present` will install the flatpak and/or remote. Set to `absent` will remove the flatpak and/or remote.
    required: false
    default: present
'''

EXAMPLES = '''
# Example from Ansible Playbooks

#install the spotify flatpak
-- flatpak:
    name:  https://s3.amazonaws.com/alexlarsson/spotify-repo/spotify.flatpakref
    state: present 

#add the gnome remote andd install gedit flatpak
-- flatpak:
    name: https://git.gnome.org/browse/gnome-apps-nightly/plain/gedit.flatpakref
    remote: https://sdk.gnome.org/gnome-apps.flatpakrepo
    state: absent 

#remove the gedit flatpak and remote
-- flatpak:
    name: org.gnome.gedit
    remote: https://sdk.gnome.org/gnome-apps.flatpakrepo
    state: absent 

#remove the gedit package
-- flatpak:
    name: org.gnome.gedit
    state: absent 

#Example Output

#failure:
{
    "failed": true, 
    "invocation": {
        "module_args": {
            "name": "htt", 
            "remote": "https://sdk.gnome.org/gnome.flatpakrepo", 
            "state": "present"
        }
    }, 
    "msg": "error while installing flatpak htt", 
    "reason": "error: Error opening file /home/jkwiatko/github/modules/flatpak-module-ansible/htt: No such file or directory\n"
}

#success
{
    "changed": true, 
    "invocation": {
        "module_args": {
            "name": "https://git.gnome.org/browse/gnome-apps-nightly/plain/gedit.flatpakref", 
            "remote": "https://sdk.gnome.org/gnome.flatpakrepo", 
            "state": "present"
        }
    }
}

'''

from ansible.module_utils.basic import AnsibleModule
import json
import subprocess


def install_flat(flat):
    command = "flatpak install -y --from {}".format(flat)
    output, error, rc = flatpak_command(command)
    if 'error' in output and 'already installed' not in output:
        return 1, output 
    else:
        return 0, output

def uninstall_flat(flat):
    common_name = parse_flat(flat)
    command = "flatpak uninstall {}".format(common_name)
    output, error, rc = flatpak_command(command)
    if 'error' in output and 'not installed' not in output:
        return 1, output
    else:
        return 0, output


def parse_remote(remote):
    name = remote.split('/')[-1]
    if '.' not in name:
        return name
    else:
        return name.split('.')[0]

def parse_flat(name):
    if 'http://' in name or 'https://' in name:
       app = name.split('/')[-1].split('.')[0]
       org = name.split('/')[2].split('.')
       org_str = "{}.{}".format(org[-1],org[-2])
       common_name = "{}.{}".format(org_str, app)
    else:
       common_name=name

    return common_name


def add_remote(remote):
    remote_name = parse_remote(remote)
    command = "flatpak remote-add --if-not-exists {} {}".format(remote_name, remote)
    output, error, rc = flatpak_command(command)
    print output
    if 'error' in output:
        return 1, output
    else:
        return 0, output

def remove_remote(remote):
    remote_name = parse_remote(remote)
    command = "flatpak remote-delete --force {} ".format(remote_name)
    output, error, rc = flatpak_command(command)
    if 'error' in output and 'not found' not in output:
        return 1, output
    else:
        return 0, output

def is_present_remote(remote):
    remote_name = parse_remote(remote) + " "
    command = "flatpak remote-list"
    output, error, rc = flatpak_command(command)
    if remote_name in output:
            return True
    return False

def is_present_flat(name):
    command = "flatpak list --app"
    flat = parse_flat(name)
    output, error, rc = flatpak_command(command)
    if  flat in output:
            return True
    return False

def flatpak_command(command):
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, error = process.communicate()
    return output, error, process.returncode

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name    = dict(required=False,default=''),
            remote = dict(required=False,default=''),
            state   = dict(required=False,default="present",choices=['present','absent'])
        ),
        supports_check_mode=True
    )
    params = module.params
    name  =params['name']
    remote=params['remote']
    state =params['state']
    module_changed = False
       
    if state == 'present':
        if remote != '' and not is_present_remote(remote):
            if module.check_mode:
    # Check if any changes would be made but don't actually make those changes
                module.exit_json(changed=True)

            rc, output = add_remote(remote)
            if rc == 1:
                module.fail_json(msg="error while adding remote: {}".format(remote),reason=output)
            else:
                module_changed = True
        if name != '' and not is_present_flat(name):
            if module.check_mode:
    # Check if any changes would be made but don't actually make those changes
                module.exit_json(changed=True)

            rc, output = install_flat(name)
            if rc == 1:
                module.fail_json(msg="error while installing flatpak {}".format(name),reason=output)
            else:
                module_changed = True
    else:
        if remote != '' and is_present_remote(remote):
            if module.check_mode:
    # Check if any changes would be made but don't actually make those changes
                module.exit_json(changed=True)
            rc, output = remove_remote(remote)
            if rc == 1:
                module.fail_json(msg="error while adding remote: {}".format(remote),reason=output)
            else:
                module_changed = True
        if name != '' and is_present_flat(name):
            if module.check_mode:
    # Check if any changes would be made but don't actually make those changes
                module.exit_json(changed=True)

            rc, output = uninstall_flat(name)
            if rc == 1:
                module.fail_json(msg="error while uninstalling flatpak:{ }".format(name),reason=output)
            else:
                module_changed = True
 
    module.exit_json(changed=module_changed)
    

if __name__ == '__main__':
    main()
