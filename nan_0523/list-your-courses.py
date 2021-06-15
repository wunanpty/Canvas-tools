#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./users-in-course.py course_id
#
# Output: XLSX spreadsheet with textual section names and URL to user's avatar
#
# --avatar flag include the avatar URLs
# -p or --picture flag include pictures
# -s or --size specification size the pictures (and enable pictures if not separately specified)
#
# with the option "-v" or "--verbose" you get lots of output - showing in detail the operations of the program
#
# Can also be called with an alternative configuration file:
# ./users-in-course.py --config config-test.json 11
#
# Example:
# ./users-in-course.py 11
#
# ./users-in-course.py --config config-test.json 6434
#
# ./users-in-course.py --config config-test.json --avatar 6434
# 
# documentation about using xlsxwriter to insert images can be found at:
#   John McNamara, "Example: Inserting images into a worksheet", web page, 10 November 2018, https://xlsxwriter.readthedocs.io/example_images.html
#
# G. Q. Maguire Jr.
#
# based on earlier users-in-course.py (that generated CSV files) and
#                  users-in-course-improved2.py (that included the images)
#
# 2019.01.04
#

import requests, time
import pprint
import optparse
import sys
import json

import datetime
import csv



# Use Python Pandas to create XLSX files
import pandas as pd

# for dealing with the image bytes
from io import StringIO, BytesIO

# Import urlopen() for either Python 2 or 3.
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

from PIL import Image

#############################
###### EDIT THIS STUFF ######
#############################

global baseUrl	# the base URL used for access to Canvas
global header	# the header for all HTML requests
global payload	# place to store additionally payload when needed for options to HTML requests


# Based upon the options to the program, initialize the variables used to access Canvas gia HTML requests
def initialize(options):
    global baseUrl, header, payload

    # styled based upon https://martin-thoma.com/configuration-files-in-python/
    if options.config_filename:
        config_file=options.config_filename
    else:
        config_file='config.json'

    try:
        with open(config_file) as json_data_file:
            configuration = json.load(json_data_file)
            access_token=configuration["canvas"]["access_token"]
            if options.containers:
                baseUrl="http://"+configuration["canvas"]["host"]+"/api/v1"
                print("using HTTP for the container environment")
            else:
                baseUrl="https://"+configuration["canvas"]["host"]+"/api/v1"

            header = {'Authorization' : 'Bearer ' + access_token}
            payload = {}
    except:
        print("Unable to open configuration file named {}".format(config_file))
        print("Please create a suitable configuration file, the default name is config.json")
        sys.exit()

# create the following dict to use as an associate directory about users
selected_user_data={}




def list_your_courses():
    courses_found_thus_far=[]
    # Use the Canvas API to get the list of all of your courses
    # GET /api/v1/courses

    url = baseUrl+'/courses'
    
    if Verbose_Flag:
        print("url: {}".format(url))

    r = requests.get(url, headers = header)
    
    if Verbose_Flag:
        print("result of getting courses: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        print("OK")
        page_response=r.json()

        for p_response in page_response:  
            courses_found_thus_far.append(p_response)

        # the following is needed when the reponse has been paginated
        # i.e., when the response is split into pieces - each returning only some of the list of modules
        # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500

        while r.links.get('next', False):
            r = requests.get(r.links['next']['url'], headers=header)  
            if Verbose_Flag:
                print("result of getting courses for a paginated response: {}".format(r.text))
            page_response = r.json()  
            for p_response in page_response:  
                courses_found_thus_far.append(p_response)

    return courses_found_thus_far


def main():
    global Verbose_Flag

    default_picture_size=128

    parser = optparse.OptionParser()

    parser.add_option('-v', '--verbose',
                      dest="verbose",
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout"
                      )
    parser.add_option("--config", dest="config_filename",
                      help="read configuration from FILE", metavar="FILE")
                      
    parser.add_option('-a', '--avatar',
                      dest="avatar",
                      default=False,
                      action="store_true",
                      help="include URL to avatar for each user"
                      )

    parser.add_option('-p', '--pictures',
                      dest="pictures",
                      default=False,
                      action="store_true",
                      help="Include pictures from user's avatars"
                      )

    parser.add_option("-s", "--size",
                      action="store",
                      dest="picture_size",
                      default=default_picture_size,
                      help="size of picture in pixels")



    parser.add_option('-C', '--containers',
                      dest="containers",
                      default=False,
                      action="store_true",
                      help="for the container enviroment in the virtual machine"
    )

    options, remainder = parser.parse_args()

    Verbose_Flag=options.verbose
    if Verbose_Flag:
        print("ARGV      : {}".format(sys.argv[1:]))
        print("VERBOSE   : {}".format(options.verbose))
        print("REMAINING : {}".format(remainder))
        print("Configuration file : {}".format(options.config_filename))

    Picture_Flag=options.pictures
    Picture_size=int(options.picture_size)
    # if a size is specified, but the picture option is not set, then set it automatically
    if Picture_Flag and Picture_size > 1:
        Picture_Flag=True
    else:
        Picture_Flag=False

    if Picture_Flag:         # you need to have the avatar URLs in order to make pictures, so enable them
        options.avatar=True

    initialize(options)

    if (len(remainder) < 1):
        print("Insuffient arguments - must provide course_id\n")
    else:
        course_id=remainder[0]
        time_diff_1 = []
        iteration = 100
            
            
        for x in range(iteration):
            time.sleep(1)
            
            before = datetime.datetime.now()
            courses=list_your_courses()
            after = datetime.datetime.now()
            
            time_diff_each = (after - before).total_seconds() * 1000
            time_diff_1.append(time_diff_each)
        
        
        filename2 = "BareMetal_courses_config_ite100_0525.csv"
        with open(filename2, 'w') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(time_diff_1)
            csvwriter.writerow(["iteration", iteration])
            
        
        #print("time_diff_1", time_diff_1)
        time_diff_mean_1 = sum(time_diff_1) / len(time_diff_1)
        print("list courses total time spent", time_diff_mean_1)
        

if __name__ == "__main__": main()

