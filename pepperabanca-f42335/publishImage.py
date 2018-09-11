#!/usr/bin/env python
# -*- coding: utf-8 -*-

from temboo.Library.Twitter.Tweets import UpdateWithMedia
from temboo.core.session import TembooSession
from argparse import ArgumentParser
 
# ArgumentParser con una descripción de la aplicación 
parser = ArgumentParser(description='%(prog)s is an ArgumentParser demo')
 
# Argumento posicional. Los argumentos posicionales son obligatorios.
parser.add_argument('arg1')
parser.add_argument('arg2')

args = parser.parse_args()


# Create a session with your Temboo account details
session = TembooSession("alvarorobotronica", "myFirstApp", "9UGNDGB8sa9Z6Lpm0odgb3MCn08vCu2m")

# Instantiate the Choreo
updateWithMediaChoreo = UpdateWithMedia(session)

# Get an InputSet object for the Choreo
updateWithMediaInputs = updateWithMediaChoreo.new_input_set()

# Set credential to use for execution
updateWithMediaInputs.set_credential('empathytool')

# Set the Choreo inputs
import base64
with open("/var/www/apps/"+args.arg2+"/html/images/local-image.jpg", "rb") as image_file:
            foto = base64.b64encode(image_file.read())
updateWithMediaInputs.set_StatusUpdate(args.arg1)
updateWithMediaInputs.set_MediaContent(foto)


# Execute the Choreo
updateWithMediaResults = updateWithMediaChoreo.execute_with_results(updateWithMediaInputs)

# Print the Choreo outputs
print("Limit: " + updateWithMediaResults.get_Limit())
print("Remaining: " + updateWithMediaResults.get_Remaining())
print("Reset: " + updateWithMediaResults.get_Reset())
print("Response: " + updateWithMediaResults.get_Response())