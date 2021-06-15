#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./users-in-course_page.py course_id
#
# Output: CSV file with time spent on each List enrollments API call
#
# Can be called with an alternative configuration file:
# ./users-in-course_page.py --config config-test.json 11
#
# Example:
# ./users-in-course_page.py --containers 1
#
# Nan Wu
#
# based on G. Q. Maguire Jr. 's file https://github.com/wunanpty/Canvas-tools/blob/master/users-in-course.py
#
# 2021.05.10
#

import requests, time
import optparse
import sys
import json
import datetime
import csv

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


#To store data
time_diff_page=[]
response_each_page=[]
time_diff_page.append("time_diff_page")
response_each_page.append("response_each_page")


def users_in_course_page(course_id):
    user_found_thus_far=[]
    # Use the Canvas API to get the list of users enrolled in this course
    # GET /api/v1/courses/:course_id/enrollments

    url = "{0}/courses/{1}/enrollments".format(baseUrl,course_id)
    extra_parameters={'per_page': '40'}
    
    before = datetime.datetime.now()
    r = requests.get(url, params=extra_parameters, headers = header)
    after = datetime.datetime.now()
    time_diff_page_each = (after - before).total_seconds() * 1000
    time_diff_page.append(time_diff_page_each)
    
    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            user_found_thus_far.append(p_response)
        response_each_page.append(len(page_response))
        
        # count the number of paginated response for API: 
        # GET /api/v1/courses/:course_id/enrollments
        global paginated_count
        paginated_count = 0
        
        while r.links.get('next', False):
            paginated_count = paginated_count + 1
            before = datetime.datetime.now()
            r = requests.get(r.links['next']['url'], headers=header)
            after = datetime.datetime.now()
            time_diff_page_each = (after - before).total_seconds() * 1000
            time_diff_page.append(time_diff_page_each)
            page_response = r.json()  
            for p_response in page_response:  
                user_found_thus_far.append(p_response)
            response_each_page.append(len(page_response))
    return user_found_thus_far


def main():

    parser = optparse.OptionParser()

    parser.add_option("--config", dest="config_filename",
                      help="read configuration from FILE", metavar="FILE")

    parser.add_option('-C', '--containers',
                      dest="containers",
                      default=False,
                      action="store_true",
                      help="for the container enviroment in the virtual machine"
    )

    options, remainder = parser.parse_args()

    initialize(options)

    if (len(remainder) < 1):
        print("Insuffient arguments - must provide course_id\n")
    else:
        course_id=remainder[0]
        time_diff_total=[]
        time_diff_total.append("time_diff_total")
        iteration = 2
        
        for x in range(iteration):
            time.sleep(0.2)
            a = datetime.datetime.now()
            users=users_in_course_page(course_id)
            b = datetime.datetime.now()
            time_diff_total_each = (b - a).total_seconds() * 1000
            time_diff_total.append(time_diff_total_each)
            
        
        #Write to a csv file
        filename = "BareMetal_baseline_50users_perpage40_sleep200ms_ite_2_redis.csv"
        with open(filename, 'w') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(time_diff_page)
            csvwriter.writerow(response_each_page)
            csvwriter.writerow(["paginated_count", paginated_count])
            csvwriter.writerow(["iteration", iteration])
            csvwriter.writerow(time_diff_total)
            
        

if __name__ == "__main__": main()

