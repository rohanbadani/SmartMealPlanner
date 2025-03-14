import json
import os
import boto3
import datatier
from configparser import ConfigParser

def lambda_handler(event, context):
    try:
        print("**STARTING /mealplan Lambda**")
        print("**lambda: proj05_mealplan**")
        
        # Load configuration
        config_file = 'mealapp-config.ini'
        os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
        
        configur = ConfigParser()
        configur.read(config_file)
        
        rds_endpoint = configur.get('rds', 'endpoint')
        rds_portnum = int(configur.get('rds', 'port_number'))
        rds_username = configur.get('rds', 'user_name')
        rds_pwd = configur.get('rds', 'user_pwd')
        rds_dbname = configur.get('rds', 'db_name')
        
        print("**Opening DB connection**")
        dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)


        # Retrieve inventory from the database
        sql = "SELECT * FROM inventory ORDER BY name"
        inventory_rows = datatier.retrieve_all_rows(dbConn, sql)
        print("**Inventory retrieved**")
        for row in inventory_rows:
            print(row)

        
        prompt = "Generate a healthy meal plan and efficent meal plan that uses every item from the following " \
        "inventory, do not use anything not on the list."


        for item in inventory_rows:
            # Assume each item is a dict with keys: 'name', 'expiration_date', and 'quantity'
            prompt += f"{item.get('name')}: {item.get('quantity')} units, expires on {item.get('expiration_date')}\n"

        print("Constructed prompt:")
        print(prompt)



    except:
        raise Exception()