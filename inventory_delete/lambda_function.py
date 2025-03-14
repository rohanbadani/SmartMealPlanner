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
        item_name = body.get('name')  
        remove_quantity = body.get('quantity')
        if not item_name or not remove_quantity:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required parameter'})
            }

        select_sql = "SELECT quantity FROM inventory WHERE name = %s"
        select_params = (item_name,)

        result = datatier.perform_query(dbConn, select_sql, select_params)

        if not result:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'Item "{item_name}" not found'})
            }
        
        current_quantity = result[0]['quantity']
        print(f"**Current quantity of {item_name}: {current_quantity}**")

        new_quantity = current_quantity - remove_quantity
    
        if new_quantity <= 0:
            delete_sql = "DELETE FROM inventory WHERE name = %s"
            delete_params = (item_name,)

            rows_affected = datatier.perform_action(dbConn, delete_sql, delete_params)
            if rows_affected == 0:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': f'Could not delete "{item_name}". Item not found.'})
                }
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Delete.'
                })
            }

        else:
            update_sql = "UPDATE inventory SET quantity = %s WHERE name = %s"
            update_params = (new_quantity, item_name)

            rows_affected = datatier.perform_action(dbConn, update_sql, update_params)
            print(f"**Rows affected by update: {rows_affected}**")

            if rows_affected == 0:
                return {
                    'statusCode': 404,
                    'body': json.dumps({
                        'error': f'Unable to update. "{item_name}" was not found.'
                    })
                }

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Successfully removed {remove_quantity} from "{item_name}".',
                    'new_quantity': new_quantity
                })
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