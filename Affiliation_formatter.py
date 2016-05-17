#!/nfs/team144/ds26/anaconda2/bin/python

'''
This script was written to create a formatted list of author affiliation list
for publications with too many authors.

Version: 1.0 Last modified: 2016.02.11
For comments and questions: ds26@sanger.ac.uk

Required fields of the input xlsx file:
"First name",
"Middle name" (Only initials without spaces),
"Last name"

Affiliation fields:
"Institute/Department/University",
"City/State",
"Post/Zip code",
"Country"

The affiliation fields can be repeated as many times as necessary. Other fields
in the xlsx table will not be considered.

Output formats:
Author names: [First name] [Middle name initials]. [Last name]^[affiliation_number]
Affiliation list: [affiliation_number]. [Institute/Department/University], [City/State] [Post/Zip Code], [Country]
'''

# importing libraries:
import argparse
import re
import os.path
import sys

parser = argparse.ArgumentParser()
input_options = parser.add_argument_group('Options')
input_options.add_argument("-i", "--input", help="Input xlsx file.", required=True)
input_options.add_argument("-o", "--output", help="Output html file.", required=False)

# Extracting command line parameters:
args = parser.parse_args()
inputFile = args.input
outputFile = ''

if args.output:
    outputFile = args.output
else:
    # Output file was not given, generated by the input filename:
    try:
        filename = re.search("/+(.+)\.xls", inputFile)
        outputFile = filename.groups()[0] + ".html"
    except:
        filename = re.search("(.+)\.xls", inputFile)
        outputFile = filename.groups()[0] + ".html"

# Print status update:
print "[Info] Input file: %s\n[Info] Output file: %s" %(inputFile, outputFile)

# Check if input file is exists:
if not os.path.isfile(inputFile):
    sys.exit("[Error] Input file (%s) does not exist.\n" % (inputFile))

# pandas is the only package that has to be loaded:
import pandas as pd

# Reading input xlsx file as a pandas dataframe:
try:
    df = pd.read_excel(inputFile)
except:
    sys.exit("[Error] Excel table could not be loaded! Check format.")


# Checking fields of the dataframe. If any of these will be missing, the script will terminate:
fields = df.columns.tolist()
if ((not 'First name' in  fields) or
        (not 'Middle Name' in  fields) or
        (not 'Last Name' in  fields)):
    sys.exit("[Error] Name fields are missing! 'First name', 'Middle Name' and 'Last Name' are required fields of the xlsx file!\n")

if ((not 'Institute/Department/University' in  fields) or
        (not 'City/State' in  fields) or
        (not 'Post/Zip code' in  fields) or
        (not 'Country' in  fields)):
    sys.exit("[Error] Affiliation fields are missing! 'Institute/Department/University', 'Post/Zip code', 'City/State' and 'Country' are required fields of the xlsx file!\n")

# Get maximum number of affiliations (based on field counts):
suffixes = ['']
for field in df.columns.tolist():
    try:
        match = re.search("Country(.+)", field)
        suffixes.append(match.groups()[0])
    except:
        continue
print "[Info] Maximum number of affiliations: %s" %(len(suffixes))
print "[INfo] Number of authors in the list: %s" %(len(df))

# At this point I have to delete all lines where none of the name fields are filled:
df = df.dropna(how='all', subset=["First name", "Middle Name", "Last Name"]).reindex()

# Defining a set of functions that will be used:
'''
List of functions to process and format author names and affiliations
They will be used in the apply functions.
'''

def get_full_name(row):
    '''
    A small function to generate full name of the authors.
    All first, middle and last names have to stripped to make sure there are not extra spaces added.

    <First name> <Middle name initials>. <Last name>

    '''

    full_name = ""
    try:
        first = row["First name"].strip()
        middle = row["Middle Name"]
        last = row["Last Name"].strip()

        if pd.isnull(middle):
            full_name = first+" "+last
        else:
            full_name = first.strip()
            for initial in middle.strip():
                full_name += " " +initial+"."
            full_name += " " +last
    except:
        try:
            full_name = row["First name"].strip()
        except:
            full_name = row["Last Name"].strip()
    return full_name

def get_affiliation_lists(row, suffixes):
    '''
    A small function to generate a list of affiliations.

    '<Department/Institute>, <Town/city> <Post code/Zip code>, <Country>'
    '''
    affiliation_list = []

    for suffix in suffixes:

        affiliation = ""

        inst = row['Institute/Department/University'+suffix]
        city = row['City/State'+suffix]
        postcode = row['Post/Zip code'+suffix]
        country = row['Country'+suffix]

        if not pd.isnull(inst):
            affiliation += inst.strip()
            if not pd.isnull(city):
                affiliation += ", " + city.strip()
            if not pd.isnull(postcode):
                affiliation += " " + str(postcode).strip()
            if not pd.isnull(country):
                affiliation += ", " + country.strip()

        if len(affiliation) > 0:
            affiliation_list.append(affiliation)

    return affiliation_list


## Generate formatted full-names:
df['full_name'] = df.apply(get_full_name, axis=1)

# Generate a list of formatted affiliations:
df['affiliation_total'] = df.apply(get_affiliation_lists, axis=1, args=([suffixes]))

# Combining authors and affiliations together:
names_numbers = []
affiliation_list = {}
affiliation_index = 0

for row in df.iterrows():
    numbers = []

    # checking if the given affiliation is already given
    for affiliation in row[1]["affiliation_total"]:
        try:
            numbers.append(affiliation_list[affiliation])
        except:
            affiliation_index += 1
            affiliation_list[affiliation] = affiliation_index
            numbers.append(affiliation_list[affiliation])
    names_numbers.append([row[1]['full_name'], numbers])

# Final datastructures:
names_numbers
affiliation_list

# Now we have to print out the affiliation list sorted for the dictionary value:
affiliation_list_sorted = sorted(affiliation_list, key=affiliation_list.get)

print "[Info] Formatting output... ",

# Now saving what we have:
html = '<!DOCTYPE html>\n<html>\n<body>\n<div></div>\n\n<div style="font-size: 16px; margin-left: 10px">'

# Looping through all authors:
for row in names_numbers:
    author = row[0]
    affiliation = row[1]
    html += author

    if len(affiliation) > 0:
        aff_string = ",".join(str(x) for x in sorted(affiliation))
        html += '<sup>%s</sup>, \n' % aff_string
    else:
        html += ', '

html += '</div>\n\n<div></div><div></div><div style="font-size: 12px; margin-left: 20px">\n\n<ol>'
# Now looping through all the affiliations and save them:
for index, affiliation in enumerate(affiliation_list_sorted):
    html += '\t<li>%s</li>\n' %(affiliation)

html += '</ol>\n<br>\n</body>\n</html>'

# Saving html data into file:
f = open(outputFile, 'w')
f.write(html.encode('utf8'))
f.close()

print " done."