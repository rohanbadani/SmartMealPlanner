import json
import os
import datetime
import boto3
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

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

        sendgrid_apikey = configur.get('sendgrid', 'api_key')

        print("**Opening DB connection**")
        dbConn = datatier.get_dbConn(rds_endpoint,
                                     rds_portnum,
                                     rds_username,
                                     rds_pwd,
                                     rds_dbname)

        #ses_client = boto3.client('ses')  

        input_data = json.loads(event['body'])
        recipient_email = input_data.get("email")

        today = datetime.date.today()
        three_days = today + datetime.timedelta(days=3)

        sql = "SELECT name, quantity, day, month, year FROM inventory;"
        items = datatier.retrieve_all_rows(dbConn, sql)

        if not items:
            print("**No items found in inventory**")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No items in inventory'})
            }

        expiring_items = []
        for row in items:
            item_type = row[0]
            item_qty  = row[1]
            item_day  = row[2]
            item_mon  = row[3]
            item_yr   = row[4]

            try:
                exp_date = datetime.date(item_yr, item_mon, item_day)
            except ValueError:
                print(f"**Skipping invalid date {item_yr}-{item_mon}-{item_day} for '{item_type}'**")
                continue

            if exp_date <= three_days:
                expiring_items.append({
                    'name': item_type,
                    'quantity': item_qty,
                    'expires': exp_date
                })

        if expiring_items:
            
        
            subject = "Expiration Alert: Items Expiring in 3 Days"
            body_lines = [
                "The following items expire soon:",
                ""
            ]
            for item in expiring_items:
                expires_str = item['expires'].strftime("%m/%d/%Y")
                body_lines.append(f"- {item['name']} (qty: {item['quantity']}), expires on {expires_str}")

            body_text = "\n".join(body_lines)

            message = Mail(
                from_email="jackcarroll2027@u.northwestern.edu",  # This sender email must be verified in SendGrid
                to_emails=recipient_email,
                subject=subject,
                plain_text_content=body_text
            )

            # Send the email via SendGrid
            sg = SendGridAPIClient(sendgrid_apikey)
            response = sg.send(message)
            print("**Email sent via SendGrid**:", response.status_code)

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
