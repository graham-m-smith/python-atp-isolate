from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from azure.mgmt.automation import AutomationClient
import os
import datetime

#-----------------------------------------------------------------------------
# Get current lookup key value
#-----------------------------------------------------------------------------
def get_lookup_key(tc):

    try:
        record = tc.get_entity('atplookup', 'key')
    except HttpResponseError as err:
        lookup_key = None
        return lookup_key

    lookup_key = record['key']
    return lookup_key

#-----------------------------------------------------------------------------
# Get list of machines using current lookup key
#-----------------------------------------------------------------------------
def get_machines(tc, lookup_key):

    query = f"PartitionKey eq '{lookup_key}'"
    try:
        data = tc.query_entities(query)
    except HttpResponseError as err:
        data = None
    
    machines = []

    for record in data:
        machine = record['RowKey']
        machines.append(machine)

    return machines

#-----------------------------------------------------------------------------
# Execute runbook
#-----------------------------------------------------------------------------
def perform_action(machine, function):

    # Get settings from environment variables
    AA_SUBSCRIPTION_ID = os.environ.get('ATP_ISOLATE_AA_SUBSCRIPTION_ID', None)
    AA_RG = os.environ.get('ATP_ISOLATE_AA_RG', None)
    AA_NAME = os.environ.get('ATP_ISOLATE_AA_NAME', None)
    AA_RUNBOOK = os.environ.get('ATP_ISOLATE_AA_RUNBOOK', None)

    # Create automation client
    automation_client = AutomationClient(
        credential=DefaultAzureCredential(),
        subscription_id=AA_SUBSCRIPTION_ID
    )

    # Create unique job name
    now = datetime.datetime.now()
    timestamp = now.strftime('%d-%m-%Y-%H-%M-%S')
    job_name = f'{AA_RUNBOOK}-{timestamp}'

    # Create runbook job
    job = automation_client.job.create(
    AA_RG,
    AA_NAME,
    job_name,
    {
        "runbook": {
        "name": AA_RUNBOOK
        },
        "parameters": {
        "VM": machine,
        "ACTION": function
        },
        "run_on": ""
    }
    )

    return True
