import logging
import requests
import os
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

APPLICATION_JSON_HEADERS = {
    "Accept": "application/json",
    "Content-Typ": "application/json",
}
APPLICATION_JSON_PATCH_HEADERS = {
    "Accept": "application/json-patch+json",
    "Content-Type": "application/json-patch+json",
}

DEFAULT_ADO_PARAMS = {"api-version": "5.0-preview"}

BATCH_MAXIMUM = 200


def build_wiql(area_path: str, assigned_to: str) -> dict:
    """
    Wiql String Builder Helper
    :param area_path: The Area Path to Search for Work Items
    :param assigned_to: Email of user
    :return: Dict with wiql Payload
    """
    wiql = "Select [System.Id], [System.Title], [System.State] From WorkItems Where"

    wiql += f' [System.AssignedTo] == "{assigned_to}"'

    if area_path is not None:
        wiql += f'AND [System.AreaPath] == "{area_path}"'

    wiql += f' AND [System.State] <> "Done"'
    wiql += f' AND [System.State] <> "Removed"'
    return {"query": wiql}


def get_azure_devops_work_item(work_item_url: str):
    """
    Fetches a Work Items Details the from Azure DevOps work_item_url passed
    :param work_item_url: The url of the work item to fetch details from
    :return:
    """
    # Param to return full work item details
    # https://docs.microsoft.com/en-us/rest/api/azure/devops/wit/work%20items/get%20work%20item
    request_params = {"$expand": "ALL"}

    resp = requests.request(
        method="GET",
        url=work_item_url,
        headers=APPLICATION_JSON_HEADERS,
        auth=HTTPBasicAuth("", os.environ["PAT_TOKEN"]),
        params={**DEFAULT_ADO_PARAMS, **request_params},
    )

    resp.raise_for_status()
    return resp.json()


def get_work_items_batch(organization: str, project_name: str, source_ids: list):
    """
    Get Work Item Details matching the source_ids passed
    The ids are processed in batches of max size 200
    :param project_name:
    :param organization:
    :param source_ids:
    :return: A List containing all work item details for every workitem.id=id in source_ids
    """
    if len(source_ids) < 1:
        logger.error("get_source_work_item_details called on empty source_ids list")
        return []

    chunks = [
        source_ids[i: i + BATCH_MAXIMUM]
        for i in range(0, len(source_ids), BATCH_MAXIMUM)
    ]

    work_item_details = []
    for chunk in chunks:
        work_item_details_json = __get_work_items_batch(organization=organization,
                                                        project_name=project_name, batch_ids=chunk)
        if work_item_details_json["count"] < 1:
            logger.error(f"No values found for work item chunk. Check usage. \n:{chunk}")
            logger.debug(work_item_details_json)
            raise UserWarning(f"No values found for work item chunk. Check usage. \n:{chunk}")
        work_item_details += work_item_details_json["value"]
    return work_item_details


def __get_work_items_batch(organization: str, project_name: str, batch_ids: list):
    """
    Get Work Item Details matching the source_ids passed
    The ids are processed in batches of max size 200
    :param project_name:
    :param organization:
    :param batch_ids:
    :return:
    """
    if len(batch_ids) > BATCH_MAXIMUM:
        err_string = (
            f"Maximum batch size of {BATCH_MAXIMUM} Exceeded.\nReceived Batch size of {len(batch_ids)}. "
            f"Reduce list size"
        )
        logger.error(err_string)
        raise ValueError(err_string)
    get_work_items_batch_url = f"https://dev.azure.com/{organization}/{project_name}/_apis/wit/workitemsbatch"

    body = {"ids": batch_ids, "$expand": "All", "errorPolicy": "Omit"}
    res = requests.request(
        method="POST",
        url=get_work_items_batch_url,
        auth=HTTPBasicAuth("", os.environ["PAT_TOKEN"]),
        json=body,
        params=DEFAULT_ADO_PARAMS,
        headers=APPLICATION_JSON_HEADERS,
    )
    res.raise_for_status()
    return res.json()


def get_source_work_items_from_wiql(organization: str, project_name: str, wiql: dict):
    """
    Runs a WIQL request against the source defined in the job instance and using all the filters defined for the job
    :param wiql: Json wiql query
    :param project_name:
    :param organization:
    :return: Response from WIQL Restapi Endpoint.
    """
    wiql_url = f"https://dev.azure.com/{organization}/{project_name}/_apis/wit/wiql"

    resp = requests.request(
        method="POST",
        url=wiql_url,
        auth=HTTPBasicAuth("", os.environ["PAT_TOKEN"]),
        json=wiql,
        params=DEFAULT_ADO_PARAMS,
        headers=APPLICATION_JSON_HEADERS,
    )
    resp.raise_for_status()
    if resp.status_code != 200:
        raise ConnectionError(
            f"get_source_work_items_from_wiql expected a HTTP 200 but received a HTTP {resp.status_code}")
    return resp.json()


def create_source_work_item(organization: str, project_name: str, work_item_type: str, work_item_create_body):
    creation_url = f"https://dev.azure.com/{organization}/{project_name}/_apis/wit" \
                   f"/workitems/${work_item_type}"

    res = requests.request(
        method="POST",
        url=creation_url,
        auth=HTTPBasicAuth("", os.environ["PAT_TOKEN"]),
        json=work_item_create_body,
        params=DEFAULT_ADO_PARAMS,
        headers=APPLICATION_JSON_PATCH_HEADERS,
    )

    res.raise_for_status()
    # Add the created work item into the relationship map. Lookup required for hierarchy creation
    return res.json()


def update_work_item(url: str, work_item_update_body):
    res = requests.request(
        method="PATCH",
        url=url,
        auth=HTTPBasicAuth("", os.environ["PAT_TOKEN"]),
        json=work_item_update_body,
        params=DEFAULT_ADO_PARAMS,
        headers=APPLICATION_JSON_PATCH_HEADERS,
    )

    res.raise_for_status()
    # Add the created work item into the relationship map. Lookup required for hierarchy creation
    return res.json()


def get_comments(comment_url: str):
    """
    Runs a WIQL request against the source defined in the job instance and using all the filters defined for the job
    :return: Comments jsons.
    """

    resp = requests.request(
        method="GET",
        url=comment_url,
        auth=HTTPBasicAuth("", os.environ["PAT_TOKEN"]),
        params=DEFAULT_ADO_PARAMS,
        headers=APPLICATION_JSON_HEADERS,
    )
    resp.raise_for_status()
    return resp.json()
