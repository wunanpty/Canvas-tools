#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -*- mode: python; python-indent-offset: 4 -*-
#
# ./insert_teachers_grading_standard.py course_id
#
# Generate a "grading standard" scale with the names of teachers as the "grades".
# Note that if the grading scale is already present, it does nothing unless the "-f" (force) flag is set.
# In the latter case it adds the grading scale.
#
# Note that this only creates a COURSE LEVEL grading scale. 
#
# G. Q. Maguire Jr.
#
# 2021.01.24
#
# Test with
#  ./insert_teachers_grading_standard.py -v 11 
#  ./insert_teachers_grading_standard.py -v --config config-test.json 11
# 
# based on earlier program insert_teachers_grading_standards.py
#

import csv, requests, time
import optparse
import sys
import json


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
            baseUrl="https://"+configuration["canvas"]["host"]+"/api/v1"
            
            header = {'Authorization' : 'Bearer ' + access_token}
            payload = {}
    except:
        print("Unable to open configuration file named {}".format(config_file))
        print("Please create a suitable configuration file, the default name is config.json")
        sys.exit()


##############################################################################
## ONLY update the code below if you are experimenting with other API calls ##
##############################################################################

def users_in_course(course_id):
    user_found_thus_far=[]
    # Use the Canvas API to get the list of users enrolled in this course
    #GET /api/v1/courses/:course_id/enrollments

    url = "{0}/courses/{1}/enrollments".format(baseUrl,course_id)
    if Verbose_Flag:
        print("url: {}".format(url))

    extra_parameters={'per_page': '100'}
    r = requests.get(url, params=extra_parameters, headers = header)
    if Verbose_Flag:
        print("result of getting enrollments: {}".format(r.text))

    if r.status_code == requests.codes.ok:
        page_response=r.json()

        for p_response in page_response:  
            user_found_thus_far.append(p_response)

        # the following is needed when the reponse has been paginated
        # i.e., when the response is split into pieces - each returning only some of the list of modules
        # see "Handling Pagination" - Discussion created by tyler.clair@usu.edu on Apr 27, 2015, https://community.canvaslms.com/thread/1500
        while r.links.get('next', False):
            r = requests.get(r.links['next']['url'], headers=header)  
            page_response = r.json()  
            for p_response in page_response:  
                user_found_thus_far.append(p_response)
    return user_found_thus_far

def get_course_info(course_id):
    global Verbose_Flag
    # Use the Canvas API to get a grading standard
    #GET /api/v1/courses/:id
    url = "{0}/courses/{1}".format(baseUrl, course_id)

    if Verbose_Flag:
        print("url: " + url)

    r = requests.get(url, headers = header)
    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    return None

def create_grading_standard(id, name, scale):
    global Verbose_Flag
    # Use the Canvas API to create an grading standard
    # POST /api/v1/courses/:course_id/grading_standards

    # Request Parameters:
    #Parameter		        Type	Description
    # title	Required	string	 The title for the Grading Standard.
    # grading_scheme_entry[][name]	Required	string	The name for an entry value within a GradingStandard that describes the range of the value e.g. A-
    # grading_scheme_entry[][value]	Required	integer	 -The value for the name of the entry within a GradingStandard. The entry represents the lower bound of the range for the entry. This range includes the value up to the next entry in the GradingStandard, or 100 if there is no upper bound. The lowest value will have a lower bound range of 0. e.g. 93

    url = "{0}/courses/{1}/grading_standards".format(baseUrl, id)

    if Verbose_Flag:
        print("url: {}".format(url))

    payload={'title': name,
             'grading_scheme_entry': scale
            }
    
    if Verbose_Flag:
        print("payload={0}".format(payload))

    r = requests.post(url, headers = header, json=payload)
    if r.status_code == requests.codes.ok:
        page_response=r.json()
        print("inserted grading standard")
        return True
    print("r.status_code={0}".format(r.status_code))
    return False

def get_grading_standards(id):
    global Verbose_Flag
    # Use the Canvas API to get a grading standard
    # GET /api/v1/courses/:course_id/grading_standards

    # Request Parameters:
    #Parameter		        Type	Description
    url = "{0}/courses/{1}/grading_standards".format(baseUrl, id)

    if Verbose_Flag:
        print("url: " + url)

    r = requests.get(url, headers = header)
    if r.status_code == requests.codes.ok:
        page_response=r.json()
        return page_response
    return None


def main():
    global Verbose_Flag
    global Use_local_time_for_output_flag
    global Force_appointment_flag

    Use_local_time_for_output_flag=True

    parser = optparse.OptionParser()

    parser.add_option('-v', '--verbose',
                      dest="verbose",
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout"
                    )


    parser.add_option('-f', '--force',
                      dest="force",
                      default=False,
                      action="store_true",
                      help="Replace existing grading scheme"
                      )

    parser.add_option('-t', '--testing',
                      dest="testing",
                      default=False,
                      action="store_true",
                      help="execute test code"
                      )

    parser.add_option("--config", dest="config_filename",
                      help="read configuration from FILE", metavar="FILE")



    options, remainder = parser.parse_args()

    Verbose_Flag=options.verbose
    Force_Flag=options.force

    if Verbose_Flag:
        print('ARGV      :', sys.argv[1:])
        print('VERBOSE   :', options.verbose)
        print('REMAINING :', remainder)
        print("Configuration file : {}".format(options.config_filename))

    if (len(remainder) < 1):
        print("Insuffient arguments - must provide course_id\n")
        return

    initialize(options)

    course_id=remainder[0]

    users=users_in_course(course_id)

    teachers=list()
    for u in users:
        if u['type'] == 'TeacherEnrollment':
            teachers.append(u)

    teacher_names_sortable=list()
    for u in teachers:
        user_data=u.get('user', False)
        if user_data:
            sortable_name=user_data.get('sortable_name', False)
            if sortable_name:
                if sortable_name in teacher_names_sortable:
                    continue
                else:
                    teacher_names_sortable.append(sortable_name)
    
    if Verbose_Flag:
        print("teacher_names_sortable={0}".format(teacher_names_sortable))

    teacher_names_sortable_sorted=list()
    if len(teacher_names_sortable) > 0:
        teacher_names_sortable_sorted=sorted(teacher_names_sortable)
        print("teacher_names_sortable_sorted={0}".format(teacher_names_sortable_sorted))

    if len(teacher_names_sortable_sorted)  < 1:
        print("No teacher, nothing to do")
        return

    course_info=get_course_info(course_id)
    if not course_info:
        print("course information not found: {}}".format(course_info))
        return

    if Verbose_Flag:
        print("course_info={}".format(course_info))

    if (len(remainder) > 1):
        course_code=remainder[1]
    else:
        course_code=course_info.get('course_code', False)

    if not course_code:
        print("No course code found: {}}".format(course_code))
        return
        
    if Verbose_Flag:
        print("course_code={}".format(course_code))

    canvas_grading_standards=dict()
    available_grading_standards=get_grading_standards(course_id)
    if available_grading_standards:
        for s in available_grading_standards:
            old_id=canvas_grading_standards.get(s['title'], None)
            if old_id and s['id'] < old_id: # use only the highest numbered instance of each scale
                continue
            else:
                canvas_grading_standards[s['title']]=s['id']
                if Verbose_Flag:
                    print("title={0} for id={1}".format(s['title'], s['id']))

    if Verbose_Flag:
        print("canvas_grading_standards={}".format(canvas_grading_standards))

    potential_grading_standard_id=canvas_grading_standards.get(course_code, None)

    if Force_Flag or (not potential_grading_standard_id):
        name=course_code
        scale=[]
        number_of_teachers=len(teacher_names_sortable_sorted)
        print("number_of_teachers={}".format(number_of_teachers))
        index=0
        for e in teacher_names_sortable_sorted:
            i=number_of_teachers-index
            d=dict()
            d['name']=e
            d['value'] =(float(i)/float(number_of_teachers))*100.0
            scale.append(d)
            index=index+1

        # testing shows that this was the smallest value other than zero that could be inserted as a value
        scale.append({'name': 'other - see comments', 'value': 0.01})

        scale.append({'name': 'none assigned', 'value': 0.0})
        if Verbose_Flag:
            print("scale={}".format(scale))

        status=create_grading_standard(course_id, name, scale)
        print("status={0}".format(status))
        if Verbose_Flag and status:
            print("Created new grading scale: {}".format(name))

if __name__ == "__main__": main()