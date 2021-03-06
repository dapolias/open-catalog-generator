#!/usr/bin/python
import json
import re
import sys
import datetime
import os
import shutil
import darpa_open_catalog as doc
import sunburst_graphics as graph
import catalog_filter as filter
import change_timeline as timeline
import catalog_search as lookup
from pprint import pprint

active_content_file = sys.argv[1]
license_content_file = sys.argv[2]
data_dir = sys.argv[3]
build_dir = sys.argv[4]
last_update_file = sys.argv[5]
darpa_links = sys.argv[6]
date = datetime.datetime.now()
formatted_date = date.strftime("%B") + " " + date.strftime("%d") + ", " + date.strftime("%Y")

print """
Active content file: %s
License directory: %s
Data directory: %s
Build directory: %s
Last Update file: %s
DARPA links: %s
Date: %s
""" % (active_content_file, license_content_file, data_dir, build_dir, last_update_file, darpa_links, date)

try:
  active_content = json.load(open(active_content_file))
except Exception, e:
  print "\nFAILED! JSON error in file %s" % active_content_file
  print " Details: %s" % str(e)
  sys.exit(1)

try:
  license_content = json.load(open(license_content_file))
except Exception, e:
  print "\nFAILED! JSON error in file %s" % license_content_file
  print " Details: %s" % str(e)
  sys.exit(1)

splash_page = doc.html_head()
splash_page += doc.catalog_program_script()
splash_page += doc.catalog_page_header("")
splash_page += doc.catalog_splash_content()
splash_page += doc.splash_table_header()

datavis_page = graph.sunburst_head()
datavis_page += graph.sunburst_script()
datavis_page += "<div id='vis_page'>" + graph.sunburst_html()

filter_page = filter.filter_head()
filter_page += filter.filter_script()
filter_page += filter.filter_html()

timeline_page = timeline.timeline_head()
timeline_page += timeline.timeline_script()
timeline_page += "<div id='timeline_page'>" + timeline.timeline_html() + "</div>"

lookup_page = lookup.search_head()
lookup_page += lookup.search_script()
lookup_page += lookup.search_html()

for program in active_content:
  program_name = program['Program Name']
  program_page_filename = program_name + ".html"
  program_page = doc.html_head()
  program_page += doc.catalog_program_script()
  program_page += doc.leaving_popup()
  program_image_file = ""
  software_columns = []
  pubs_columns = []
  data_columns = []
  examples_columns = []
  if program['Program File'] == "":
    print "ERROR: %s has no program details json file, can't continue.  Please fix this and restart the build." % program_name
    sys.exit(1)
  else:
    try:
      program_details = json.load(open(data_dir + program['Program File']))
    except Exception,e:
      print "\nFAILED! JSON error in file %s" % program['Program File']
      print " Details: %s" % str(e)
      sys.exit(1)
    if program['DARPA Office'] != "":
      try:
        office_details = json.load(open(data_dir + "01-DARPA-" + program['DARPA Office'] + ".json"))
      except Exception,e:
        print "\nFAILED! JSON error in file 01-DARPA-%s.json" % program['DARPA Office']
        print " Details: %s" % str(e)
        sys.exit(1)
      #print office_details
      program_page += doc.catalog_page_header("<a href='" + office_details['DARPA Link'] + "' class='programheader' style='color: #" + office_details['DARPA Office Color'] + ";'>" + office_details['DARPA Long Name'] + " (" + office_details['DARPA Office'] + ")</a>")
    if re.search('^http',program_details['Link']):
      program_page += "\n  <h2><a href='" + program_details['Link'] + "' class='programlink'>" + program_details['Long Name'] + "</a></h2>\n"
    else:
      program_page += "<h2>%s</h2>" % program_details['Long Name']

    program_page += "<div class='left-paragraph'><p>%s<p>" % program_details['Description']
    if program_details['Program Manager'] != "":
      if re.search('^http',program_details['Program Manager Link']):
        program_page += "<p>Program Manager: <a href='%s' class='programmanagerlink'>%s</a></p>" % (program_details['Program Manager Link'], program_details['Program Manager'])
      else:
        program_page += "<p>Program Manager: %s</p>" % program_details['Program Manager']

    if program_details['Program Manager Email'] != "":
      try:
        manager_email = doc.valid_email(program_details['Program Manager Email'], program_details['DARPA Program Name'])
        program_page += "<p>Contact: <a href='mailto:%s'>%s</a><p>" % (manager_email, manager_email)
      except Exception:
        raise
    program_page += "<p>The content below has been generated by organizations that are partially funded by DARPA; the views and conclusions contained therein are those of the authors and should not be interpreted as necessarily representing the official policies or endorsements, either expressed or implied, of DARPA or the U.S. Government.</p>"

	#if Software File has a value and it is not all whitespace
    if program['Software File'] and not program['Software File'].isspace():
      program_page += "<ul><li>The Software Table lists performers with one row per piece of software. Each piece of software has licensing information, a link to an external project page or contact information, and where possible a link to the code repository for the project.</li></ul>"
    if program['Pubs File'] and not program['Pubs File'].isspace():
      program_page += "<ul><li>The Publications Table contains author(s), title, and links to peer-reviewed articles related to specific DARPA programs.</li></ul>"
    if program['Data File'] and not program['Data File'].isspace():
      program_page += "<ul><li>The Data Set table includes a description and industry, as well as size indicators. Contact the program for access.</li></ul>"
    if program['Examples File'] and not program['Examples File'].isspace():
      program_page += "<ul><li>The Examples table includes a description and a link.</li></ul>"
    program_page += "<p>Report a problem: <a href=\"mailto:opencatalog@darpa.mil\">opencatalog@darpa.mil</a></p>"
    program_page += "<p>Last updated: %s</p></div>" % formatted_date
    if 'Image' in program_details.keys():
      if program_details['Image'] != "":
        program_page += "\n<div class='right-image'><img src=\"%s\"/></div>" % program_details['Image']
      program_image_file = program_details['Image']

    banner = ""
    program_link = "<a href='%s'>%s</a>" % (program_page_filename, program_details['DARPA Program Name'])
    if program['Banner'].upper() == "NEW":
      banner = "<div class='wrapper'><a href='%s'>%s</a><div class='ribbon-wrapper'><div class='ribbon-standard ribbon-red'>%s</div></div></div>"  % (program_page_filename, program_details['DARPA Program Name'], program['Banner'].upper())
    elif program['Banner'].upper() == "COMING SOON":
      banner = "<div class='wrapper'>%s<div class='ribbon-wrapper'><div class='ribbon-standard ribbon-blue'>%s</div></div></div>"  % (program_details['DARPA Program Name'], program['Banner'].upper())
    elif program['Banner'].upper() == "UPDATED":
      banner = "<div class='wrapper'><a href='%s'>%s</a><div class='ribbon-wrapper'><div class='ribbon-standard ribbon-green'>%s</div></div></div>"  % (program_page_filename, program_details['DARPA Program Name'], program['Banner'].upper())
    else:
     banner = "<a href='%s'>%s</a>" % (program_page_filename, program_details['DARPA Program Name'])
    splash_page += "<TR>\n <TD width=230> %s</TD>\n <TD width=70>%s</TD>\n <TD>%s</TD>\n</TR>" % (banner, program_details['DARPA Office'], program_details['Description'])
    software_columns = program_details['Display Software Columns']
    #print "program details: %s \n\r" % program_details
    pubs_columns = program_details['Display Pubs Columns']
    data_columns = program_details['Display Data Columns']
    #print program_details
    examples_columns = program_details['Display Examples Columns']

  # This creates a hashed array (dictionary) of teams that have publications. We use this to cross link to them from the software table. So far only XDATA program
  pubs_exist = {}
  if program['Pubs File'] != "" and program['Software File'] != "":
      pubs_file = open(data_dir + program['Pubs File'])
      try:
        pubs = json.load(pubs_file)
      except Exception,e:
        print "\nFAILED! JSON error in file %s" % program['Pubs File']
        print " Details: %s" % str(e)
        sys.exit(1)
      pubs_file.close()
      for pub in pubs:
        for team in pub['Program Teams']:
          pubs_exist[team] = 1


  #starts the tabs div for the Software and Publications tables
  search_tab = ""
  search_footer = ""
  program_page += "<div id='dialog'></div><div id='tabs' class='table-tabs'><ul>"
  if program['Software File'] != "":
    program_page += "<li><a href='#tabs0'>Software</a></li>"
    search_tab += "<div id='allSearch'><div id='tabs300'>"
    search_tab += "<div id='softwareSearch'><input class='search' placeholder='Search' id='search300' onkeyup='allSearch(this)'/>"
    search_tab += "<button class='clear_button' id='clear300'>Clear</button><div id='sftwrTable'><h2>Software</h2></div></div>"
  if program['Pubs File'] != "":
    program_page += "<li><a href='#tabs1'>Publications</a></li>"
    search_tab += "<div id='publicationsSearch'><div id='pubTable'><h2>Publications</h2></div></div>"
  if program['Data File'] != "":
    program_page += "<li><a href='#tabs2'>Data</a></li>"
    search_tab += "<div id='dataSearch'><div id='dataTable'><h2>Data</h2></div></div>"
  if program['Examples File'] != "":
    program_page += "<li><a href='#tabs3'>Examples</a></li>"
    search_tab += "<div id='examplesSearch'><div id='examplesTable'><h2>Examples</h2></div></div>"
  if program['Software File'] != "" and program['Pubs File'] != "":
    program_page += "<li><a href='#tabs300'>Search</a></li>"
  program_page += "</ul>"
  search_footer += "</div></div>"
  if search_tab != "":
    search_tab += search_footer


###### SOFTWARE
  if program['Software File'] != "":
    program_page += "<div id='software'><div id='tabs0'>"
    program_page += "<input class='search' placeholder='Search' id='search0'/>"
    program_page += "<button class='clear_button' id='clear0'>Clear</button>"
    try:
      softwares = json.load(open(data_dir + program['Software File']))
    except Exception, e:
      print "\nFAILED! JSON error in file %s" % program['Software File']
      print " Details: %s" % str(e)
      sys.exit(1)
    program_page += doc.software_table_header(software_columns)
    for software in softwares:
      for column in software_columns:
        # Team
        if column == "Team":
          program_page += "<TR>\n  <TD class='%s'>" % column.lower()
          for team in software['Program Teams']:
            if team in pubs_exist:
              team += " <a href='#" + team + "' onclick='pubSearch(this)'>(publications)</a>"

            program_page += team + ", "
          program_page = program_page[:-2]
          program_page += "</TD>\n "
        # Software
        if column == "Project":
          # Debug
          #print " " + software['Software']
          elink = ""
          if 'External Link' in software.keys():
            elink = software['External Link']
          entry_title = ""
          if re.search('^http',elink) and elink != "":
            if darpa_links == "darpalinks":
              entry_title = "<a href='" + elink + "' class='external' target='_blank'>" + software['Software'] + "</a>"
            else:
              entry_title = "<a href='" + elink + "'>" + software['Software'] + "</a>"
          else:
            entry_title = software['Software']

          if program['Banner'].upper() != "NEW":
            entry_ribbon = doc.project_banner(software['Update Date'], software['New Date'], last_update_file, entry_title)
            program_page += "<TD width='202' class='" + column.lower() + "'>" + entry_ribbon + "</TD>"
          else:
            program_page += "<TD class='" + column.lower() + "'>" + entry_title + "</TD>"
        # Category
        if column == "Category":
          categories = ""
          if 'Categories' in software.keys():
            for category in software['Categories']:
              categories += category + ", "
            categories = categories[:-2]
          program_page += "  <TD class=" + column.lower() + ">" + categories + "</TD>\n"
        # Instructional Material
        if column == "Instructional Material":
          instructional_material = ""
          if 'Instructional Material' in software.keys():
            instructional_material = software['Instructional Material']
          if re.search('^http',instructional_material):
            if darpa_links == "darpalinks":
              program_page += "  <TD class='" + column.lower() + "'><a href='" + instructional_material + "' class='external' target='_blank'>Available </a></TD>\n"
            else:
              program_page += "  <TD class=" + column.lower() + "><a href='" + instructional_material + "'> Available </a></TD>\n"
          else:
            program_page += "  <TD class=" + column.lower() + ">" + instructional_material + "</TD>\n"
        # Code
        if column == "Code":
          clink = ""
          if 'Public Code Repo' in software.keys():
            if re.search('[^@]+@[^@]+\.[^@]+',software['Public Code Repo']): # regex to identify when it's an email address.
              try:
                code_email = doc.valid_email(software['Public Code Repo'], program_details['DARPA Program Name'])
                clink = "<a href='mailto:%s'>%s</a>" % (code_email, code_email)
              except Exception:
                raise
            elif re.search('^http',software['Public Code Repo']):
              codeurl = software['Public Code Repo']
              if darpa_links == "darpalinks":
                clink = "<a href=%s class='external' target='_blank'>%s</a>" % (codeurl, codeurl)
              else:
                clink = "<a href='%s'>%s</a>" % (codeurl, codeurl)
            else:
              clink = software['Public Code Repo']
          program_page += "  <TD class=" + column.lower() + "> " + clink + " </TD>\n"
        # Stats
        if column == "Stats":
          if 'Stats' in software.keys():
            if software['Stats'] != "":
              slink = software['Stats']
              program_page += "  <TD class=" + column.lower() + "> <a href='stats/" + slink + "/activity.html'>stats</a> </TD>\n"
            else:
              program_page += "  <TD class=" + column.lower() + "></TD>\n"
          else:
            program_page += "  <TD class=" + column.lower() + "></TD>\n"

        # Description
        if column == "Description":
          program_page += " <TD class=" + column.lower() + "> " + software['Description'] + " </TD>\n"
        # License
        if column == "License":
          licenses = software['License']
          license_html = "<TD class=%s>" % column.lower()
          for license_idx, license in enumerate(licenses):
            license_value_found = False
            for license_record in license_content:
              for short_nm in license_record['License Short Name']:
                if license == short_nm:
                  license_value_found = True
                  license_html += "<span onmouseover='licenseInfo(\"%s\", \"%s\", \"%s\", \"%s\", event)'>%s</span>" % (short_nm, license_record['License Long Name'].replace("'", ""), license_record['License Link'], license_record['License Description'].replace("'", ""), license)
                  if license_idx < len(licenses) - 1:
                    license_html += ", "
            if license_value_found == False:
              license_html += "<span>%s</span>" % license
              if license_idx < len(licenses) - 1:
                license_html += ", "
          program_page += license_html
          program_page += " </TD>\n </TR>\n"
    program_page += doc.table_footer()
    program_page += "</div></div>"


####### Publications
  if program['Pubs File'] != "":
    program_page += "<div id='publications'><div id='tabs1'>"
    program_page += "<input class='search' placeholder='Search' id='search1'/>"
    program_page += "<button class='clear_button' id='clear1'>Clear</button>"
    try:
      pubs = json.load(open(data_dir + program['Pubs File']))
    except Exception, e:
      print "\nFAILED! JSON error in file %s" % program['Pubs File']
      print " Details: %s" % str(e)
      sys.exit(1)
    program_page += doc.pubs_table_header(pubs_columns)
    for pub in pubs:
      # Debug
      #print "    " + pub['Title']
      for column in pubs_columns:
        # Team
        if column == "Team":
          program_page += "<TR>\n  <TD class='" + column.lower() + "'>"
          for team in pub['Program Teams']:
            program_page += team + "<a name='" + team + "'></a>, "
          program_page = program_page[:-2]
          program_page += "</TD>\n"
        # Title
        if column == "Title":
          program_page += "<TD class='" + column.lower() + "'>"
          entry_ribbon = ""
          if program['Banner'].upper() != "NEW":
            entry_ribbon = doc.project_banner(pub['Update Date'], pub['New Date'], last_update_file, pub['Title'])
          else:
            entry_ribbon = pub['Title']
          program_page +=  entry_ribbon + "</TD>"
        # Link
        if column == "Link":
          link = pub['Link']
          if re.search('^http',link) or re.search('^ftp',link):
            if darpa_links == "darpalinks":
              program_page += "  <TD class='" + column.lower() + "'><a href='" + link + "' class='external' target='_blank'>" + link + "</a></TD>\n"
            else:
              program_page += "  <TD class='" + column.lower() + "'><a href='" + link + "'>" + link + "</a></TD>\n"
          else:
            program_page += "  <TD class='" + column.lower() + "'>" + link + "</TD>\n"
          program_page += "</TR>\n"
    program_page += doc.table_footer()
    program_page += doc.pubs_table_footer() + "</div></div>"

###### DATA
  if program['Data File'] != "":
    program_page += "<div id='dataset'><div id='tabs2'>"
    program_page += "<input class='search' placeholder='Search' id='search2'/>"
    program_page += "<button class='clear_button' id='clear2'>Clear</button>"
    try:
      data = json.load(open(data_dir + program['Data File']))
    except Exception, e:
      print "\nFAILED! JSON error in file %s" % program['Data File']
      print " Details: %s" % str(e)
      sys.exit(1)
    program_page += doc.data_table_header(data_columns)
    for datum in data:
      for column in data_columns:
	    # Industry
        if column == "Industry":
          industries = ""
          if 'Industry' in datum.keys():
            for industry in datum['Industry']:
              industries += industry + ", "
            industries = industries[:-2]
          program_page += "<TR>\n <TD class=" + column.lower() + ">" + industries + "</TD>\n"
        # Name
        if column == "Name":
          program_page += "<TD class='" + column.lower() + "'>"
          entry_ribbon = ""
          if program['Banner'].upper() != "NEW":
            entry_ribbon = doc.project_banner(datum['Update Date'], datum['New Date'], last_update_file, datum['Data Set Name'])
          else:
            entry_ribbon = datum['Data Set Name']
          program_page +=  entry_ribbon + "</TD>"
        # Description
        if column == "Description":
          program_page += " <TD class=" + column.lower() + "> " + datum['Description'] + " </TD>\n"
        # Total Rows
        if column == "Total Rows":
          program_page += " <TD class=" + column.lower() + "> " + datum['Number of Rows'] + " </TD>\n"
		# Total Columns
        if column == "Total Columns":
          program_page += " <TD class=" + column.lower() + "> " + datum['Number of Columns'] + " </TD>\n"
          program_page += "</TR>\n"
    program_page += doc.table_footer()
    program_page += "</div></div>"
    #print program_page

###### EXAMPLES

  if program['Examples File'] != "":
    program_page += "<div id='examples'><div id='tabs3'>"
    program_page += "<input class='search' placeholder='Search' id='search3'/>"
    program_page += "<button class='clear_button' id='clear3'>Clear</button>"
    try:
      examples = json.load(open(data_dir + program['Examples File']))
    except Exception, e:
      print "\nFAILED! JSON error in file %s" % program['Examples File']
      print " Details: %s" % str(e)
      sys.exit(1)

    program_page += doc.examples_table_header(examples_columns)
    for example in examples:
      for column in examples_columns:
        # Application Name
        if column == "Name":
          program_page += " <TR>\n <TD class=" + column.lower() + "> " + example['Application Name'] + " </TD>\n"
        # Team
        if column == "Team":
          program_page += "<TD class='" + column.lower() + "'>"
          for team in example['Teams']:
            program_page += team + "<a name='" + team + "'></a>, "
          program_page = program_page[:-2]
          program_page += "</TD>\n"
        # Description
        if column == "Description":
          program_page += " <TD class=" + column.lower() + "> " + example['Description'] + " </TD>\n"
        # Instructional Material
        if column == "Instructional Material":
          program_page += " <TD class=" + column.lower() + "> " + example['Instructional Material'] + " </TD>\n"
        # Link
        if column == "Link":
          program_page += " <TD class=" + column.lower() + "> " + example['Link'] + " </TD>\n"
          program_page += "</TR>\n"
    program_page += doc.table_footer()
    program_page += "</div></div>"
    #print program_page

###### Add search tab only if software and publications tab exists
  if program['Software File'] != "" and program['Pubs File'] != "":
    program_page += search_tab
  program_page += "</div><br>\n"
  program_page += doc.catalog_page_footer()

  if program['Banner'].upper() != "COMING SOON":
    #print "Writing to %s" % build_dir + '/' + program_page_filename
    program_outfile = open(build_dir + '/' + program_page_filename, 'w')
    print program_page_filename
    program_outfile.write(program_page.encode('utf-8'))
    if program_image_file != "":
      shutil.copy(data_dir + program_image_file, build_dir)

splash_page += doc.splash_table_footer()
splash_page += doc.leaving_popup()
splash_page += doc.catalog_page_footer()
doc.write_file(splash_page, build_dir + '/index.html')

datavis_page += doc.catalog_page_footer()
doc.write_file(datavis_page, build_dir + '/data_vis.html')

filter_page += doc.catalog_page_footer()
doc.write_file(filter_page, build_dir + '/catalog_filter.html')

timeline_page += doc.catalog_page_footer()
doc.write_file(timeline_page, build_dir + '/change_timeline.html')

lookup_page += doc.catalog_page_footer()
doc.write_file(lookup_page, build_dir + '/catalog_search.html')
