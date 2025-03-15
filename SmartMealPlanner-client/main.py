#
# Client-side python app for Smart Meal Planner, which is calling
# a set of lambda functions in AWS through API Gateway.
# The overall purpose of the app is to track the items in a user's
# fridge and keep track of those items to provide recipe suggestions
# and notify users when items are about to expire.
#
# Authors:
#   << Rohan Badani >>
#
#   Prof. Joe Hummel (initial template)
#   Northwestern University
#   CS 310
#

import requests
import json

import uuid
import pathlib
import logging
import sys
import os
import base64
import time

from configparser import ConfigParser
from getpass import getpass

############################################################
#
# classes
#
class Item:

  def __init__(self, row):
    self.name = row[0]
    self.quantity = row[1]
    self.day = row[2]
    self.month = row[3]
    self.year = row[4]
    


###################################################################
#
# web_service_get
#
# When calling servers on a network, calls can randomly fail. 
# The better approach is to repeat at least N times (typically 
# N=3), and then give up after N tries.
#
def web_service_get(url):
  """
  Submits a GET request to a web service at most 3 times, since 
  web services can fail to respond e.g. to heavy user or internet 
  traffic. If the web service responds with status code 200, 400 
  or 500, we consider this a valid response and return the response.
  Otherwise we try again, at most 3 times. After 3 attempts the 
  function returns with the last response.
  
  Parameters
  ----------
  url: url for calling the web service
  
  Returns
  -------
  response received from web service
  """

  try:
    retries = 0
    
    while True:
      response = requests.get(url)
        
      if response.status_code in [200, 400, 480, 481, 482, 500]:
        #
        # we consider this a successful call and response
        #
        break;

      #
      # failed, try again?
      #
      retries = retries + 1
      if retries < 3:
        # try at most 3 times
        time.sleep(retries)
        continue
          
      #
      # if get here, we tried 3 times, we give up:
      #
      break

    return response

  except Exception as e:
    print("**ERROR**")
    logging.error("web_service_get() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return None
    

############################################################
#
# prompt
#
def prompt():
  """
  Prompts the user and returns the command number

  Parameters
  ----------
  None

  Returns
  -------
  Command number entered by user (0, 1, 2, ...)
  """
  try:
      print()
      print(">> Enter a command:")
      print("   0 => end")
      print("   1 => upload to inventory")
      print("   2 => see inventory")
      print("   3 => delete from inventory")
      print("   4 => get a meal plan")
      print("   5 => get an email notification about which items are expiring within 3 days")

      cmd = input()

      if cmd == "":
        cmd = -1
      elif not cmd.isnumeric():
        cmd = -1
      else:
        cmd = int(cmd)

      return cmd

  except Exception as e:
      print("**ERROR")
      print("**ERROR: invalid input")
      print("**ERROR")
      return -1



############################################################
#
# notify
#
def notify(baseurl):
    """
    Notifies the user which items are expiring within the next 3 days

    Parameters
    ----------
    baseurl: baseurl for web service

    Returns
    -------
    nothing
    """

    try:
        #
        # call the web service:
        #
        api = '/notify'
        url = baseurl + api

        # res = requests.get(url)
        res = web_service_get(url)

        #
        # let's look at what we got back:
        #
        if res.status_code == 200: #success
            pass
        else:
            # failed:
            print("**ERROR: failed with status code:", res.status_code)
            print("url: " + url)
            if res.status_code == 500:
                # we'll have an error message
                body = res.json()
                print("Error message:", body)
            #
            return
        body = res.json()
        print(body)
        #
        return

    except Exception as e:
        logging.error("**ERROR: notify() failed:")
        logging.error("url: " + url)
        logging.error(e)
        return



############################################################
#
# mealplan
#
def mealplan(baseurl):
    """
    Generates a meal plan based on the user's inventory

    Parameters
    ----------
    baseurl: baseurl for web service

    Returns
    -------
    nothing
    """

    try:
        #
        # call the web service:
        #
        api = '/mealplan'
        url = baseurl + api

        # res = requests.get(url)
        res = web_service_get(url)

        #
        # let's look at what we got back:
        #
        if res.status_code == 200: #success
            pass
        else:
            # failed:
            print("**ERROR: failed with status code:", res.status_code)
            print("url: " + url)
            if res.status_code == 500:
                # we'll have an error message
                body = res.json()
                print("Error message:", body)
            #
            return

        #
        # deserialize and extract users:
        #
        body = res.json()
        meal_plan_text = body.get("meal_plan", "No meal plan found.")
        print(meal_plan_text)

        #
        return

    except Exception as e:
        logging.error("**ERROR: mealplan() failed:")
        logging.error("url: " + url)
        logging.error(e)
        return




############################################################
#
# delete
#
def delete(baseurl):
  """
  User inputs an item name and an amount of that item they consumed. This will then be updated in the table.

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """

  try:
    #
    # call the web service:
    #
    api = "/inventory"
    url = baseurl + api

    print("Enter an item name>")
    name = input()
    print("Enter the quantity that you consumed>")
    quantity = input()

    quantity = int(quantity)
    payload = {"name": name, "quantity": quantity}
    headers = {"Content-Type": "application/json"}

    res = requests.post(url, json=payload, headers=headers)


    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      print("Inventory updated successfully")
    elif res.status_code == 400: # no such user
      body = res.json()
      print(body)
      return
    else:
      # failed:
      print("**ERROR: failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return

  except Exception as e:
    logging.error("**ERROR: delete() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return



############################################################
#
# inventory
#
def inventory(baseurl):
    """
    Gets the items in the inventory and prints them out for the user to see

    Parameters
    ----------
    baseurl: baseurl for web service

    Returns
    -------
    nothing
    """

    try:
        #
        # call the web service:
        #
        api = '/inventory'
        url = baseurl + api

        # res = requests.get(url)
        res = web_service_get(url)

        #
        # let's look at what we got back:
        #
        if res.status_code == 200: #success
            pass
        else:
            # failed:
            print("**ERROR: failed with status code:", res.status_code)
            print("url: " + url)
            if res.status_code == 500:
                # we'll have an error message
                body = res.json()
                print("Error message:", body)
            #
            return

        #
        # deserialize and extract users:
        #
        body = res.json()

        #
        # let's map each row into a User object:
        #
        items = []
        for row in body:
            item = Item(row)
            items.append(item)
        #
        # Now we can think OOP:
        #
        if len(items) == 0:
            print("no items...")
            return

        for item in items:
            print(item.name)
            print(" quantity: ", item.quantity)
            print(f" expiration date: {item.month}/{item.day}/{item.year}")
        #
        return

    except Exception as e:
        logging.error("**ERROR: inventory() failed:")
        logging.error("url: " + url)
        logging.error(e)
        return


############################################################
#
# upload
#
def upload(baseurl):
  """
  Prompts the user for a local filename 
  and uploads that asset (JPG) to S3 for processing. 

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """
  try:
    api = '/upload'
    url = baseurl + api
    print("Enter Image filename>")
    local_filename = input()

    if not pathlib.Path(local_filename).is_file():
      print("Image file '", local_filename, "' does not exist...")
      return
 
    #
    # build the data packet:
    #
    infile = open(local_filename, "rb")
    bytes = infile.read()
    infile.close()

    #
    # now encode the jpg as base64. Note b64encode returns
    # a bytes object, not a string. So then we have to convert
    # (decode) the bytes -> string, and then we can serialize
    # the string as JSON for upload to server:
    #
    data = base64.b64encode(bytes)
    datastr = data.decode("utf-8")
    
    payload = {"image": datastr}
    headers = {"Content-Type": "application/json"}
    res = requests.post(url, json=payload, headers=headers)


    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      pass
    elif res.status_code == 400: # no such user
      body = res.json()
      print(body)
      return
    else:
      # failed:
      print("**ERROR: failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return

    body = res.json()
    item_data = body.get('item', {})

    # need to get name, expiration date, quantity to print to user
    item_name = item_data.get('item_name', 'Unknown')
    date = item_data.get('expiration_date', 'Unknown')
    quantity = item_data.get('quantity', 'Unknown')

    print(f"Added {item_name} to inventory with quantity: {quantity} and expiration date: {date}")
    return

  except Exception as e:
    logging.error("**ERROR: upload() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return




############################################################
#
# check_url
#
def check_url(baseurl):
  """
  Performs some checks on the given url, which is read from a config file.
  Returns updated url if it needs to be modified.

  Parameters
  ----------
  baseurl: url for a web service

  Returns
  -------
  same url or an updated version if it contains an error
  """

  #
  # make sure baseurl does not end with /, if so remove:
  #
  if len(baseurl) < 16:
    print("**ERROR: baseurl '", baseurl, "' is not nearly long enough...")
    sys.exit(0)

  if baseurl == "https://YOUR_GATEWAY_API.amazonaws.com":
    print("**ERROR: update config file with your gateway endpoint")
    sys.exit(0)

  if baseurl.startswith("http:"):
    print("**ERROR: your URL starts with 'http', it should start with 'https'")
    sys.exit(0)

  lastchar = baseurl[len(baseurl) - 1]
  if lastchar == "/":
    baseurl = baseurl[:-1]
    
  return baseurl
  

############################################################
# main
#
try:
  print('** Welcome to BenfordApp with Authentication **')
  print()

  # eliminate traceback so we just get error message:
  sys.tracebacklimit = 0

  #
  # we have one config file:
  # 
  #    1. client's API endpoint
  #
  #
  config_file = 'client-config.ini'

  print("First, enter name of config file to use...")
  print("Press ENTER to use default, or")
  print("enter config file name>")
  s = input()

  if s == "":  # use default
    pass  # already set
  else:
    config_file = s

  #
  # does config file exist?
  #
  if not pathlib.Path(config_file).is_file():
    print("**ERROR: config file '", config_file, "' does not exist, exiting")
    sys.exit(0)

  #
  # setup base URL to web service:
  #
  configur = ConfigParser()
  configur.read(config_file)
  baseurl = configur.get('client', 'webservice')
  
  baseurl = check_url(baseurl)

  #
  # main processing loop:
  #
  cmd = prompt()

  while cmd != 0:
    #
    if cmd == 1:
      upload(baseurl)
    elif cmd == 2:
      inventory(baseurl)
    elif cmd == 3:
      delete(baseurl)
    elif cmd == 4:
      mealplan(baseurl)
    elif cmd == 5:
      notify(baseurl)
    else:
      print("** Unknown command, try again...")
    #
    cmd = prompt()

  #
  # done
  #
  print()
  print('** done **')
  sys.exit(0)

except Exception as e:
  logging.error("**ERROR: main() failed:")
  logging.error(e)
  sys.exit(0)
