import json
import os
import datetime
import boto3

from configparser import ConfigParser
import datatier

def lambda_handler(event, context):
    try:
        print("**STARTING**")
        print("**lambda: proj05_notify**")
        
        config_file = 'mealapp-config.ini'
        os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
        
        configur = ConfigParser()
        configur.read(config_file)

        rds_endpoint = configur.get('rds', 'endpoint')
        rds_portnum  = int(configur.get('rds', 'port_number'))
        rds_username = configur.get('rds', 'user_name')
        rds_pwd      = configur.get('rds', 'user_pwd')
        rds_dbname   = configur.get('rds', 'db_name')

        print("**Opening DB connection**")
        dbConn = datatier.get_dbConn(rds_endpoint,
                                     rds_portnum,
                                     rds_username,
                                     rds_pwd,
                                     rds_dbname)

        ses_client = boto3.client('ses')  

        today = datetime.date.today()
        three_days = today + datetime.timedelta(days=3)

        sql = "SELECT type, quantity, day, month, year FROM inventory;"
        items = datatier.perform_query(dbConn, sql)

        if not items:
            print("**No items found in inventory**")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No items in inventory'})
            }

        expiring_items = []
        for row in items:
            item_type = row['type']
            item_qty  = row['quantity']
            item_day  = row['day']
            item_mon  = row['month']
            item_yr   = row['year']

            try:
                exp_date = datetime.date(item_yr, item_mon, item_day)
            except ValueError:
                print(f"**Skipping invalid date {item_yr}-{item_mon}-{item_day} for '{item_type}'**")
                continue

            if exp_date == three_days:
                expiring_items.append({
                    'type': item_type,
                    'quantity': item_qty,
                    'expires': exp_date
                })

        if expiring_items:
            recipient_email = configur.get('notifications', 'recipient_email', fallback=None)
        
            subject = "Expiration Alert: Items Expiring in 3 Days"
            body_lines = [
                "The following items expire soon:",
                ""
            ]
            for item in expiring_items:
                expires_str = item['expires'].strftime("%m/%d/%Y")
                body_lines.append(f"- {item['type']} (qty: {item['quantity']}), expires on {expires_str}")

            body_text = "\n".join(body_lines)

            response = ses_client.send_email(
                Source=recipient_email,  
                Destination={
                    'ToAddresses': [recipient_email]  
                },
                Message={
                    'Subject': {'Data': subject},
                    'Body': {
                        'Text': {'Data': body_text}
                    }
                }
            )
            print("**Email sent**:", response.get('MessageId'))
        else:
            print("**No items expiring in 3 days, no email sent**")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Checked for 3 day expiring items.',
                'num_expiring': len(expiring_items)
            })
        }

    except Exception as err:
        print("**ERROR**")
        print(str(err))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(err)})
        }

    finally:
        if 'dbConn' in locals() and dbConn is not None:
            dbConn.close()
            print("**Database connection closed**")