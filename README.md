# secureshare_api

####RESTFUL API created using Django Rest Framework

##Users `/users/`


##Reports `/reports/<pk>`

###Supported Methods: GET, POST, PATCH, DELETE

####GET

#####GET Parameters: None
#####URL Parameters: pk

Requesting just /reports/ will return all reports visible to the user

Specifying pk will select a unique report, if it is visible to the user

####POST

#####POST Parameters: 
  Type: multipart
  data: {'name':string, 'short_description':string, 'long_description':string,'private':boolean,'encrypted':list of booleans (boolean for each file)}
  file: file or list of files

  Responses: 201 on creation, 400 on invalid data or failed encrypted
