from flask import Flask
from flask import render_template, redirect, url_for, flash
from azure.identity import DefaultAzureCredential
from azure.data.tables import TableServiceClient
from azure.core.credentials import AzureSasCredential
from functions import *
import os

# Get Settings from environment variables
SA_RG = os.environ.get('ATP_ISOLATE_SA_RG', None)
SA_ENDPOINT = os.environ.get('ATP_ISOLATE_SA_ENDPOINT', None)
SA_ATPLOOKUPKEY_TABLE_NAME = os.environ.get('ATP_ISOLATE_SA_ATPLOOKUPKEY_TABLE_NAME', None)
SA_ATPLOOKUPKEY_SAS_TOKEN = os.environ.get('ATP_ISOLATE_SA_ATPLOOKUPKEY_SAS_TOKEN', None)
SA_ATPLOOKUP_TABLE_NAME = os.environ.get('ATP_ISOLATE_SA_ATPLOOKUP_TABLE_NAME', None)
SA_ATPLOOKUP_SAS_TOKEN = os.environ.get('ATP_ISOLATE_SA_ATPLOOKUP_SAS_TOKEN', None)
FLASK_SECRET_KEY = os.environ.get('ATP_ISOLATE_FLASK_SECRET_KEY', None)

# Determine which credential method to use
if FLASK_SECRET_KEY == 'DEV':
    # Running on local development environment    
    atplookup_credential = AzureSasCredential(SA_ATPLOOKUP_SAS_TOKEN)
    atplookupkey_credential = AzureSasCredential(SA_ATPLOOKUPKEY_SAS_TOKEN)
else:
    # Running in Azure WebApp
    atplookup_credential = DefaultAzureCredential()
    atplookupkey_credential = DefaultAzureCredential()

# Initialize Azure Table Client
atplookup_tsc = TableServiceClient(endpoint=SA_ENDPOINT, credential=atplookup_credential)
atplookup_tc = atplookup_tsc.get_table_client(table_name=SA_ATPLOOKUP_TABLE_NAME)
atplookupkey_tsc = TableServiceClient(endpoint=SA_ENDPOINT, credential=atplookupkey_credential)
atplookupkey_tc = atplookupkey_tsc.get_table_client(table_name=SA_ATPLOOKUPKEY_TABLE_NAME)

# Initialize Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY

# Define Routes

# -----------------------------------------------------------------------------
# /list (default route) 
# -----------------------------------------------------------------------------
@app.route('/list')
@app.route('/')
def list():

    # Get current lookup key
    lookup_key = get_lookup_key(atplookupkey_tc)

    # Get list of machines
    machines = get_machines(atplookup_tc, lookup_key)

    # Display table
    return render_template('machine_list.html', machines=machines)

# -----------------------------------------------------------------------------
# /confirm/<machine>/<function>
# -----------------------------------------------------------------------------
@app.route('/confirm/<machine>/<function>')
def confirm(machine, function):
    return render_template('confirm_action.html', machine=machine, function=function)

# -----------------------------------------------------------------------------
# /startrunbook/<machine>/<function>  - Isolate specified machine from the network
# -----------------------------------------------------------------------------
@app.route('/startrunbook/<machine>/<function>')
def startrunbook(machine, function):
    job = perform_action(machine, function)
    flash(f'{function} initiated for {machine}')
    return redirect(url_for('list'))
