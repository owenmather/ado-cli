import argparse
import logging
import os
import yaml
import sys
import platform

from src.actions import create_ado_work_items, open_ado_work_item, list_ado_work_items, close_ado_work_item, \
    move_ado_work_item, read_ado_work_item

logger = logging.getLogger(__name__)

if os.environ.get("ADO_CONFIG_FILE", None) is not None:
    ADO_CONFIG_FILE = os.environ["ADO_CONFIG_FILE"]
    if ADO_CONFIG_FILE.startswith("~/"):
        ADO_CONFIG_FILE = os.path.expanduser(ADO_CONFIG_FILE)
else:
    if platform.system() == "Windows":
        ADO_CONFIG_FILE = f"{os.environ['UserProfile']}/.ado/.ado-config.yml"
    else:
        ADO_CONFIG_FILE = os.path.expanduser("~/.ado/.ado-config.yml")


def parse_yaml():
    res = {}
    try:
        if os.path.isfile(ADO_CONFIG_FILE):
            with open(ADO_CONFIG_FILE) as f:
                res = yaml.load(f.read(), Loader=yaml.SafeLoader)
        else:
            print(f"No config file found {ADO_CONFIG_FILE}")
    except Exception as ex:
        print(ex)
        sys.exit(1)
    finally:
        res["system"] = platform.system()
        return res


def ado():
    print('-' * 88)
    print("Azure DevOps Work Item Management Cli")
    print('-' * 88)

    run_args = parse_yaml()
    logging.basicConfig(level=run_args.get("LOGLEVEL", logging.INFO), format='%(levelname)s: %(message)s')
    parser = argparse.ArgumentParser()
    # parser.add_argument('action', choices=['list', 'create', 'close'])
    parser.set_defaults(func=lambda x: parser.print_help())

    subparsers = parser.add_subparsers(help='sub-command help')

    # CREATE SUBPARSER ARGS
    create_parser = subparsers.add_parser('create', help='create an Azure DevOps Work Item')
    create_parser.set_defaults(func=create_ado_work_items)

    create_parser.add_argument("title", help="Title of Work Item to create")
    create_parser.add_argument("desc", help="Work Item description")
    create_parser.add_argument("-wit", help="Work Items Type to create/update/list",
                               required=False, default="Task")
    create_parser.add_argument("-p", "--parent", help="ID of the parent work item", required=False, type=int)

    # OPEN SUBPARSER ARGS
    open_parser = subparsers.add_parser('open', help='Opens an Azure DevOps Work Item in the browser based on ID')
    open_parser.set_defaults(func=open_ado_work_item)

    open_parser.add_argument("ID", help="The ID of the Azure DevOps Work Item to Open", type=int)
    open_parser.add_argument("browser", help="browser to open in", nargs='?',
                             default=run_args.get("browser", "iexplore"), choices=["iexplore", "chrome"])

    # OPEN SUBPARSER ARGS
    read_parser = subparsers.add_parser('read', help='Outputs the details of an Azure DevOps Work Item')
    read_parser.set_defaults(func=read_ado_work_item)
    read_parser.add_argument("ID", help="The ID of the Azure DevOps Work Item to Open", type=int)
    read_parser.add_argument("--json", help="Outputs JSON of Work Items", required=False, action='store_true')

    # LIST SUBPARSER ARGS
    list_parser = subparsers.add_parser("list", help="list work items assigned to current user")
    list_parser.set_defaults(func=list_ado_work_items)

    list_parser.add_argument("--all", help="list work items on all area paths", required=False, action='store_true')
    list_parser.add_argument("--allusers", help="list work items on all area paths", required=False, default=False)
    list_parser.add_argument("--tags", help="Show Tags", required=False, action='store_true')
    list_parser.add_argument("-wit", help="Work Items Type to create/update/list", required=False, default='Task')

    # CLOSE SUBPARSER ARGS
    close_parser = subparsers.add_parser("close", help="Close an Azure DevOps Work Item")
    close_parser.set_defaults(func=close_ado_work_item)
    close_parser.add_argument("ID", help="The ID of the Azure DevOps Work Item to Close", type=int)
    close_parser.add_argument("comment", help="Optional closing comment to add to Work Item", nargs="?", default=None)
    close_parser.add_argument("--state", help="Optional State of move work item too. Defaults to Done", required=False,
                              default="Done")

    # MOVE SUBPARSER ARGS
    move_parser = subparsers.add_parser("move", help="Change an Azure DevOps Work Items State")
    move_parser.set_defaults(func=move_ado_work_item)
    move_parser.add_argument("ID", help="The ID of the Azure DevOps Work Item to Close", type=int)
    move_parser.add_argument("state", help="The Work Item State to move too. Must be a valid state")
    move_parser.add_argument("comment", help="Optional comment to add to Work Item", nargs="?", default=None)

    for subparser in [create_parser, list_parser, close_parser]:
        # Add shared defaults to each subparser
        subparser.add_argument('-username', help="Email address for ADO User",
                               required=False if "username" in run_args else True,
                               default=run_args.get("username", None))
        subparser.add_argument('-o', '--org', dest="organization", help="Azure DevOps Organization",
                               required=False if "organization" in run_args else True,
                               default=run_args.get("organization", None))
        subparser.add_argument('-proj', '--project', dest="project", help="Azure DevOps Project Name",
                               required=False if "project" in run_args else True,
                               default=run_args.get("project", None))

    for subparser in [create_parser, list_parser]:
        subparser.add_argument('-ap', '--area-path', dest="areaPath", help="The Area Path to Search", required=False,
                               default=run_args.get("areaPath", None))
        subparser.add_argument("-it", "--iteration", dest="iteration", help="The Iteration Value", required=False,
                               default=run_args.get("iteration", None))

    args = parser.parse_args()
    # Merge with config from yaml
    run_args.update(vars(args))

    # Enable coloured output
    if run_args.get("color", False):
        os.system('color')
    args.func(run_args)


if __name__ == '__main__':
    ado()
