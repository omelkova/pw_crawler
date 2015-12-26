The 'setup/categories' and 'setup/categories_mashups' subfolders contains .csv files named by corresponding Web API's ans Mashup's categorys respectively in the programmableweb web site. Each .csv file contains a set of Web API's and Mashups accordingly to it's category. List of Web API's and Mashups can be re-crawled using the categories_catalog.py file, which is runnable python script. Before running the script it should be properly setted up by defining 3 global variables in the beggining of this file: 
* 'entity' variable can be set to 'service' or 'mashup' depending on which list the user is about to crawl, 
* the 'categories_source' variable indicate which file should be used as a list of categories to be crawled. Currently this variable points to 'categories_list/categories.csv' file which includes 471 categories. This file can be recreated using the 'categories_list/categories.py' script.
* and the 'output_folder' which indicates the place to save obtained lists in .csv format.
After the lists of Web API's or Mashups will be retrieved user can run pw_parser. This script consists of two files 'entity.py' and 'main.py' where the second one is runnable. 

