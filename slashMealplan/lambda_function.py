import json
import os
import datatier
from configparser import ConfigParser
import requests

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
            name = item[0]
            quantity = item[1]
            day = item[2]
            month = item[3]
            year = item[4]
            prompt += f"{name}: {quantity} units, expires on {year}-{month}-{day}\n"

        print("Constructed prompt:")
        print(prompt)


        # Retrieve the OpenAI API key from config file
        openai_api_key = configur.get('openai', 'key')
        
        # Set up the request to the OpenAI API using the text-davinci-003 model.
        openai_url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
        }
        data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300,
            "temperature": 0.7,
            "n": 1
        }

        response = requests.post(openai_url, headers=headers, json=data)
        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code}, {response.text}")
        
        res = response.json()
        meal_plan_text = res["choices"][0]["message"]["content"].strip() if "choices" in res and res["choices"] else "No meal plan generated"


        print(meal_plan_text)

        return {
            "statusCode": 200,
            "body": json.dumps({"meal_plan": meal_plan_text})
        }



    except Exception as err:
        print("**ERROR**")
        print(str(err))
        
        return {
        'statusCode': 500,
        'body': json.dumps(str(err))
        }
