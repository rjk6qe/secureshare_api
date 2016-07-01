# secureshare_api

RESTFUL API created using Django Rest Framework

All URLs start with /api/v1/

###Reports

Supported Methods: GET, POST, PATCH, DELETE

####GET '/reports/<pk>'

GET Parameters: None
URL Parameters: pk

Requesting just /reports/ will return all reports visible to the user
Specifying pk will select a unique report, if it is visible to the user
