

##/upload -> will take in a qr code image and then add the necesarry input in.
#all qr codes will be in the format:
#ITEMNAME-DD-MM-YY-QUANITIY


import json
import requests
import base64
import pymysql
import configparser


def scan_QR(image_path):
    url = "https://api.qrserver.com/v1/read-qr-code/"
    with open(image_path, "rb") as image_file:
        files = {"files": image_file}
        response = requests.post(url, files=files)
    

    if response.status_code == 200:
        data = response.json()

        # The decoded text is found under data[0]['symbol'][0]['data'].
        qr_text = data[0]['symbol'][0]['data']
        return qr_text
    else:
        raise Exception("BAD SCAN!")


def parse_qr_text(text):
    #all qr codes will be in the format:
    #ITEMNAME-DD-MM-YY-QUANITIY

    parts = text.split('-')

    if len(parts) != 5:
        raise Exception("QR code format is incorrect")


    item_name, day, month, year, quantity = parts[0], parts[1], parts[2], parts[3], parts[4]

    return {
        "item_name": item_name,
        "expiration_date": f"20{year}-{month}-{day}",  
        "quantity": int(quantity)
    }


def lambda_handler(event, context):
    

    # Load config from mealappconfig.ini
    config = configparser.ConfigParser()
    config.read('mealappconfig.ini')

    # S3 configuration from [s3] section
    S3_BUCKET = config.get('s3', 'bucket_name')
    
    # RDS configuration from [rds] section
    DB_HOST = config.get('rds', 'endpoint')
    DB_PORT = config.getint('rds', 'port_number')
    DB_USER = config.get('rds', 'user_name')
    DB_PASSWORD = config.get('rds', 'user_pwd')
    DB_NAME = config.get('rds', 'db_name')

    try:

        # Determine if the body is base64-encoded directly or inside a JSON key "image"
        if event.get('isBase64Encoded', False):
            image_data = base64.b64decode(event['body'])
        else:
            data = json.loads(event['body'])
            if 'image' not in data:
                raise Exception("Missing 'image' field in request body")
            image_data = base64.b64decode(data['image'])

        # write the qr code to lambdas /tmp file
        tmp_image_path = '/tmp/upload.jpg'
        with open(tmp_image_path, 'wb') as f:
            f.write(image_data)

        
        qr_text = scan_QR(tmp_image_path)

        parsed_data = parse_qr_text(qr_text)

        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )

        try:
            with connection.cursor() as cursor:
                    insert_sql = """
                        INSERT INTO food_items (name, day, month, year, quanitity)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    # Split the expiration_date (YYYY-MM-DD) into its components:
                    exp_parts = parsed_data["expiration_date"].split("-")
                    year_val = exp_parts[0]
                    month_val = exp_parts[1]
                    day_val = exp_parts[2]
                    
                    cursor.execute(insert_sql, (parsed_data["item_name"], day_val, month_val, year_val, parsed_data["quantity"]))
                    connection.commit()
        finally:                       
            connection.close()
        

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Item successfully added",
                "item": parsed_data
            })
        }


    except Exception as e:
        logger.exception("Error processing the upload")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }