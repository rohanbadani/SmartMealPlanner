import json
import os
import datatier
from configparser import ConfigParser

def lambda_handler(event, context):
    try:
        print("**STARTING**")
        print("**lambda: proj05_inventory_delete**")
        
        config_file = 'mealapp-config.ini'
        os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
        
        configur = ConfigParser()
        configur.read(config_file)

        rds_endpoint = configur.get('rds', 'endpoint')
        rds_portnum = int(configur.get('rds', 'port_number'))
        rds_username = configur.get('rds', 'user_name')
        rds_pwd = configur.get('rds', 'user_pwd')
        rds_dbname = configur.get('rds', 'db_name')

        print("**Opening connection**")
        dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)

        print("**Processing request body**")

        if "body" not in event:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing request body'})
            }
            
        body = json.loads(event['body'])  
        item_id = body.get('itemid')  
        if not item_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required parameter: id'})
            }

        print(f"**Deleting item: {item_id}**")

        sql = "DELETE FROM inventory WHERE type = %s"
        params = (item_id,)

        rows_affected = datatier.perform_action(dbConn, sql, params)  

        print(f"**Rows affected: {rows_affected}**")

        if rows_affected == 0:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Item not found'})
            }

        print(f"**Successfully deleted {item_id}**")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': f'Successfully deleted {item_id}'})
        }

    except FileNotFoundError as e:
        print(f"**ERROR: {e}**")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

    except Exception as err:
        print("**ERROR**", str(err))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(err)})
        }

    finally:
        if 'dbConn' in locals() and dbConn is not None:
            dbConn.close()
            print("**Database connection closed**")