import pymysql
import json

#database connection
connection = pymysql.connect(host="localhost", user="root", passwd="root", database="indoor_navigation_logs",  autocommit=True)
cursor = connection.cursor()
# Query for creating table
insertSql = """INSERT INTO indoor_logs
(`scenario_num`,
`point_num`,
`device_name`,
`rssi`,
`tx_power`)
VALUES(%s,%s,%s,%s,%s)"""

def lambda_handler(event, context):
    print event['body']['param']
    input_data = json.load(event['body']['param'])
    cursor.execute(insertSql, (input_data['scenario_num'], input_data['point_num'], 
        input_data['device_name'], input_data['rssi'], input_data['tx_power']))
    connection.close()
    response = {}
    response_body = {"success"}
    response['headers'] = {}

    response['statusCode'] = 200

    response['body'] = json.dumps(response_body)
    return response


