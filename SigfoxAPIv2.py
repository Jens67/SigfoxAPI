# Used for RESTful commands - GET & POST
import requests
import json
# For gmail to send logs
import smtplib
import ssl
# For Time date
import time

#v1:  sigfox_url = "https://backend.sigfox.com/api/callbacks/messages/error"
# https://api.sigfox.com/v2/groups/{id}/callbacks-not-delivered
# {id} = ? "Contract_Name"
# https://api.sigfox.com/v2/groups/contractID/callbacks-not-delivered
# where contractID = contract name Contract_Name
sigfox_url = "https://api.sigfox.com/v2/groups/contractID/callbacks-not-delivered"
username = "username"
password: str = "password"
authentication = (username, password)

# Time must be in milliseconds - according to Sigfox API
milli_seconds = int(round(time.time() * 1000))
# milli_seconds = 1546300800000 # 01/01/2019, 00:00:00.000

run_time = time.ctime()
end_reading_time_epoch = milli_seconds
end_reading_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(milli_seconds/1000))

# Start time = end time (run-time) - nr_days
# Will run API every 8 days, maybe daily
# nr_days = 60*60*24*days*1000 # in milliseconds
days = 2
records_retrieved = 0
nr_days = 60*60*24*days*1000  # in milliseconds
start_reading_time_epoch = milli_seconds - nr_days  # 8 days = 3600 x 24 x 8
start_reading_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime((milli_seconds-nr_days)/1000))

print('Nr of days: ', days)
print('Start reading: ', start_reading_time, '(', start_reading_time_epoch, ')')
print('End reading  : ', end_reading_time, '(', end_reading_time_epoch, ')')

parameters = {"since": start_reading_time_epoch, "before": end_reading_time_epoch}

response_messages_not_read = requests.get(url=sigfox_url, auth=authentication, params=parameters)

status_code = response_messages_not_read.status_code
print('status code - first read: ', status_code)

# in DICT format
result = response_messages_not_read.json()
# test code
print(result)
# end test code

for i in result["data"]:
    if i["callback"]["url"] == "http://check_destination_URL_is_correct":
        # Format must be: {"device":"{device}", "time":"{time}", "data":"{data}", "seqNumber":"{seqNumber}"}
        payload = i["callback"]["body"]
        # in JSON format
        json_result = json.dumps(payload)
        print(json_result)
        send_payload = requests.post("http://localhost:80_destination_URL/path", data=json_result)
        records_retrieved = records_retrieved + 1
        status_code1 = send_payload.status_code
        print(status_code1)

# count nr of pages
count = 0

if result["paging"]:
    while result["paging"]:
        try:
            next_page_url = result["paging"]["next"]
            next_page = result["paging"]
            print('next page (url): ', next_page_url)
            next_response_messages_not_read = requests.get(url=next_page_url, auth=authentication, params=parameters)
            result = next_response_messages_not_read.json()

            for i in result["data"]:
                if i["callback"]["url"] == "http://check_destination_URL_is_correct":
                    # Format must be: {"device":"{device}", "time":"{time}", "data":"{data}", "seqNumber":"{seqNumber}"}
                    payload = i["callback"]["body"]
                    # in JSON format
                    json_result = json.dumps(payload)
                    print(json_result)
                    send_payload = requests.post("http://localhost:80_destination_URL/path", data=json_result)
                    records_retrieved = records_retrieved + 1
                    status_code2 = send_payload.status_code
                    print(status_code2)

            next_page_url = result["paging"]["next"]
            # payload2 = json_result

            count = count + 1
        except KeyError:
            last_response_messages_not_read = requests.get(url=next_page_url, auth=authentication, params=parameters)
            last_result = last_response_messages_not_read.json()
            json_last_result = json.dumps(last_result)

            # in DICT format
            last_result = response_messages_not_read.json()

            for i in last_result["data"]:
                if i["callback"]["url"] == "http://check_destination_URL_is_correct":
                    # Format must be: {"device":"{device}", "time":"{time}", "data":"{data}", "seqNumber":"{seqNumber}"}
                    payload = i["callback"]["body"]
                    # in JSON format
                    json_last_result = json.dumps(payload)
                    print(json_last_result)
                    send_payload = requests.post("http://localhost:80_destination_URL/path", data=json_last_result)
                    records_retrieved = records_retrieved + 1
                    status_code3 = send_payload.status_code
                    print(status_code3)

            payload_last = json_last_result

            # send_payload = requests.post("http://check_destination_URL_is_correct", data=payload_last)
            # status_code3 = send_payload.status_code
            # print(status_code3)
            count = count + 1

print('API run completed at ', run_time)
print('Nr of pages: ', count)
print('Nr of records found:', records_retrieved)

# Email results
port = 587  # For starttls
smtp_server = "smtp.gmail.com"
sender_email = "sender_name@gmail.com"
receiver_email = "receiver_name@gmail.com"
# password = input("Type your password and press enter:")
password = "password"
# message = ("Number of unread messages: \n (100 messages per page, maybe less for last page):", NrOfPages)
msg1 = """\
Subject: Sigfox API status

Number of unread messages:  \n (100 messages per page, maybe less for last page): """
msg2 = str(count)
msg2a = '\n'
msg3 = ('API run completed at ', run_time)
msg3_str = str(msg3)
msg3a = '\n'
msg4 = start_reading_time
msg4a = '\n'
msg5 = end_reading_time
msg5a = '\n'
msg6 = 'Nr of days checked: '
msg7 = str(days)
msg7a = '\n'
msg7b = 'Status code: '
msg8 = str(status_code)
msg9 = '\n'
# msg10 = 'Nr of records found'
# msg11a = '\n'
# msg11 = str(status_code3)
msg12 = "Nr. of unread Records retrieved and inserted: "
msg13 = str(records_retrieved)

message = (msg1 + msg2 + msg2a + msg3_str + msg3a + msg4 + msg4a + msg5 + msg5a + msg6 + msg7 + msg7a + msg8 + msg9 + msg12 + msg13)
context = ssl.create_default_context()
with smtplib.SMTP(smtp_server, port) as server:
    server.ehlo()  # Can be omitted
    server.starttls(context=context)
    server.ehlo()  # Can be omitted
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message)

print('Results emailed')

# Iterate and extract required data from only our url
# This part must be uncommented - FROM here
# for i in result["data"]:
#   if i["callback"]["url"] == "http://check_destination_URL_is_correct":
#     payload = i["callback"]["body"]
# This part must be uncommented - TO here
#    print(payload)


# PUSH all messages (only required key:value pairs, also part of GET messages in [callback][body])
# not read by OUR web service
# Use Localhost if API hosted on endpoint or use same url if API is hosted elsewhere

# This next line must be uncommented
# requests.push('http://localhost:80_destination_URL/path',data = payload)
