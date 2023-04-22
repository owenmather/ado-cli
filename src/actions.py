import logging
import os
import tabulate

tabulate.PRESERVE_WHITESPACE = True

from src.azureapi import get_source_work_items_from_wiql, build_wiql, get_work_items_batch, create_source_work_item, \
    update_work_item, get_comments

logger = logging.getLogger(__name__)

W = '\033[0m'  # white (normal)
R = '\033[31m'  # red
G = '\033[32m'  # green
O = '\033[38;5;208m'  # orange
B = '\033[34m'  # blue
P = '\033[35m'  # purple
Y = '\033[33m'  # Yellow
# Can change to add custom colors to work item types in your project
c = {"Product Backlog Item": B, "Task": Y, "Feature": P, "Epic": O}
COLOR_ENABLED = False


def color(text, color):
    return color + text + '\033[0m'


def bold(text):
    return '\033[1m' + text + '\033[0m'


def italic(text):
    return '\x1B[3m' + text + '\x1B[0m'


def underline(text):
    return '\033[4m' + text + '\033[0m'


def add_color(key, value):
    if COLOR_ENABLED:
        return f"{c.get(key, W)}{value}{W}"
    else:
        return str(value)


def process_children(work_item_details, elem, res, indent="\u2517\u2501 "):
    if "relations" not in elem:
        return

    for link in elem['relations']:
        if link['rel'] != "System.LinkTypes.Hierarchy-Forward":
            continue
        if link['url'] not in work_item_details:
            continue
        child = work_item_details.pop(link['url'])
        res.append(
            [
                indent + add_color(child["fields"]["System.WorkItemType"], child["id"]),
                indent + add_color(child["fields"]["System.WorkItemType"], child["fields"]["System.WorkItemType"]),
                indent + add_color(child["fields"]["System.WorkItemType"], child["fields"]["System.Title"]),
                add_color(child["fields"]["System.WorkItemType"], child["fields"]["System.IterationPath"])
            ])
        process_children(work_item_details, child, res, indent=f"  {indent}")


def list_ado_work_items(run_args):
    logger.debug(run_args)
    if os.environ.get("PAT_TOKEN") is None:
        logger.info("PAT_TOKEN must be set in the environment")
        return

    if run_args["all"]:
        area_path = None
    else:
        area_path = run_args['areaPath']

    found_items = get_source_work_items_from_wiql(organization=run_args['organization'],
                                                  project_name=run_args['project'],
                                                  wiql=build_wiql(area_path=area_path,
                                                                  assigned_to=run_args['username']))

    found_map = ({elem["url"]: elem["id"] for elem in found_items["workItems"]})
    ids = list(found_map.values())
    work_item_details = get_work_items_batch(organization=run_args['organization'],
                                             project_name=run_args['project'], source_ids=ids)

    if run_args.get("color", False):
        global COLOR_ENABLED
        COLOR_ENABLED = True

    res = []

    work_item_details = {elem["url"]: elem for elem in work_item_details}
    while work_item_details:
        elem = work_item_details.pop(list(work_item_details.keys())[0])
        res.append(
            [
                add_color(elem["fields"]["System.WorkItemType"], elem["id"]),
                add_color(elem["fields"]["System.WorkItemType"], elem["fields"]["System.WorkItemType"]),
                add_color(elem["fields"]["System.WorkItemType"], elem["fields"]["System.Title"]),
                add_color(elem["fields"]["System.WorkItemType"], elem["fields"]["System.IterationPath"])
            ])
        if run_args.get("hierarchy", False):
            process_children(work_item_details, elem, res)

    print(tabulate.tabulate(res, headers=["ID", "Type", "Title", "Iteration", "Tags", "State"],
                            tablefmt=run_args.get('tablefmt', "simple")))
    print(f"\n{len(res)} Work Items Found for {run_args['username']}")


def create_ado_work_items(run_args):
    logger.debug(run_args)
    if os.environ.get("PAT_TOKEN") is None:
        logger.info("PAT_TOKEN must be set in the environment")
        return

    work_item_create_body = [
        {
            "op": "add",
            "path": "/fields/System.AreaPath",
            "value": run_args['areaPath'],
        },
        {
            "op": "add",
            "path": "/fields/System.AssignedTo",
            "value": run_args['username'],
        },
        {
            "op": "add",
            "path": "/fields/System.Title",
            "value": run_args['title'],
        },
        {
            "op": "add",
            "path": "/fields/System.Description",
            "value": run_args['desc'],
        }
    ]

    if run_args['parent']:
        work_item_create_body.append({
            "op": "add",
            "path": "/relations/-",
            "value": {
                "rel": "System.LinkTypes.Hierarchy-Reverse",
                "url": f"https://dev.azure.com/{run_args['organization']}/{run_args['project']}/_apis/wit/workItems/{run_args['parent']}"
            },
        })

    if run_args.get("iteration", None) is not None:
        work_item_create_body.append({
            "op": "add",
            "path": "/fields/System.IterationPath",
            "value": run_args['iteration'],
        })

    res = create_source_work_item(organization=run_args['organization'],
                                  project_name=run_args['project'], work_item_type=run_args['wit'],
                                  work_item_create_body=work_item_create_body)

    if run_args.get("color", False):
        print(
            f"Created {add_color(res['fields']['System.WorkItemType'], res['id'])} {add_color(res['fields']['System.WorkItemType'], res['fields']['System.WorkItemType'])} {res['fields']['System.Title']}")
    else:
        print(f"Created {res['id']} {res['fields']['System.WorkItemType']} {res['fields']['System.Title']}")


def open_ado_work_item(run_args):
    open_url = f"https://dev.azure.com/{run_args['organization']}/{run_args['project']}/_workitems/edit/{run_args['ID']}"
    print(f"OPEN {run_args['ID']} {open_url}")
    if "browser" not in run_args:
        run_args["browser"] = "chrome"
    if run_args["system"] == "Windows":
        os.system(f"start {run_args['browser']} {open_url}")
    else:
        os.system(f"{run_args['browser']} {open_url} & disown")


def move_ado_work_item(run_args):
    logger.debug(run_args)
    if os.environ.get("PAT_TOKEN") is None:
        logger.info("PAT_TOKEN must be set in the environment")
        return

    work_item_update_body = [
        {
            "op": "add",
            "path": "/fields/System.State",
            "value": run_args['state'],
        }
    ]

    if run_args["comment"]:
        work_item_update_body.append({
            "op": "add",
            "path": "/fields/System.History",
            "value": run_args["comment"]
        })

    update_url = f"https://dev.azure.com/{run_args['organization']}/{run_args['project']}/_apis/wit/workitems/{run_args['ID']}"
    res = update_work_item(url=update_url, work_item_update_body=work_item_update_body)
    print(f"{res['id']} state set to {res['fields']['System.State']}")


def close_ado_work_item(run_args):
    # Alias for `ado move Done`
    move_ado_work_item(run_args)


def print_card(work_item):
    from bs4 import BeautifulSoup

    fields = work_item['fields']

    output = "\n" + tabulate.tabulate([
        [color(bold(italic('ID:')), B), fields['System.Id'], color(bold(italic('Type:')), B),
         fields['System.WorkItemType']],
        [color(bold(italic('State:')), B), fields['System.State'], color(bold(italic('Area:')), B),
         fields['System.AreaPath']],
        [color(bold(italic('AssignedTo:')), B), fields['System.AssignedTo']['uniqueName'],
         color(bold(italic('Iteration:')), B),
         fields['System.IterationPath']]
    ], tablefmt="plain")
    output += f"\n\n{color(bold(fields['System.Title']), Y)}\n"

    output += f"\n{color(underline(italic(bold('Description:'))), B)}"
    output += "\n" + BeautifulSoup(fields.get('System.Description', ''), features='html.parser').get_text(
        '\n').strip() + "\n"

    if 'Microsoft.VSTS.Common.AcceptanceCriteria' in fields:
        output += f"\n{color(underline(italic(bold('Acceptance Criteria:'))), B)}"
        output += "\n" + BeautifulSoup(fields.get('Microsoft.VSTS.Common.AcceptanceCriteria', ''),
                                       features='html.parser').get_text('\n').strip() + "\n"

    if 'System.CommentCount' in fields and fields['System.CommentCount'] == 0:
        print(output)
        return

    comment_json = get_comments(work_item['_links']['workItemComments']['href'])
    output += f"\n{color(underline(italic(bold('Comments:'))), B)}\n"
    comment_out = []

    for comment in comment_json['comments'][::-1]:
        comment_out.append([color(bold(comment['revisedBy']['uniqueName']), Y),
                            BeautifulSoup(comment.get('text', ''), features='html.parser').get_text('\n')])
    output += tabulate.tabulate(comment_out, tablefmt="plain")
    print(output)


def read_ado_work_item(run_args):
    work_items = get_work_items_batch(organization=run_args['organization'],
                                      project_name=run_args['project'], source_ids=[run_args['ID']])

    logger.debug(work_items)
    if len(work_items) == 0 or work_items[0] is None:
        logger.error(f"No Valid Work Item found for ID {run_args['ID']}")
        return

    if run_args.get("color", False):
        global COLOR_ENABLED
        COLOR_ENABLED = True

    if run_args.get("json"):
        print(work_items[0])
        return
    print_card(work_items[0])
