#!/usr/bin/env python

# Copyright 2013 Brett Kelly
# All rights reserved.

import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.type.ttypes as Types
import evernote.edam.error.ttypes as Errors

import time


## Determines to which Evernote host we're connecting
TESTING = True

def getEvernoteHost():
    host = 'sandbox' if TESTING else 'www'
    return 'https://%s.evernote.com' % host
    
def getUserStoreInstance():
	userStoreUri = "%s/edam/user" % getEvernoteHost()
	userStoreHttpClient = THttpClient.THttpClient(userStoreUri)
	userStoreProtocol = TBinaryProtocol.TBinaryProtocol(userStoreHttpClient)
	userStore = UserStore.Client(userStoreProtocol)
	print "Created UserStore.Client instance"
	return userStore

def getBusinessNoteStoreInstance(bNoteStoreUrl):
    "Create and return an instance of NoteStore.Client to interface with Business"
    bNoteStoreHttpClient = THttpClient.THttpClient(bNoteStoreUrl)
    bNoteStoreProtocol = TBinaryProtocol.TBinaryProtocol(bNoteStoreHttpClient)
    bNoteStore = NoteStore.Client(bNoteStoreUrl)
    return bNoteStore

def getNoteStoreInstance(authToken, userStore):
	try:
		noteStoreUrl = userStore.getNoteStoreUrl(authToken)
	except Errors.EDAMUserException, ue:
		print "Error: your dev token is probably wrong; double-check it."
		print ue
		return None

	noteStoreHttpClient = THttpClient.THttpClient(noteStoreUrl)
	noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
	noteStore = NoteStore.Client(noteStoreProtocol)
	print "Created NoteStore.Client instance"
	return noteStore

def authenticateToBusiness(authToken):
    "Authenticate with Evernote Business, return AuthenticationResult instance"
    try:
        bAuthResult = userStore.authenticateToBusiness(authToken)
    except Errors.EDAMUserException, e:
        print e
        return None
    except Errors.EDAMSystemException, e:
        print e
        return None

    return bAuthResult

def getNonEmptyUserInput(prompt):
	"Prompt the user for input, disallowing empty responses"
	uinput = raw_input(prompt)
	if uinput:
		return uinput
	print "This can't be empty. Try again."
	return getNonEmptyUserInput(prompt)

authToken = "" # bypass the dev token prompt by populating this variable.

if not authToken:
	authToken = getNonEmptyUserInput("Enter your dev token: ")

userStore = getUserStoreInstance()
try:
    noteStore = getNoteStoreInstance(authToken, userStore)
except Exception, e:
    print "Error getting NoteStore instance:"
    print type(e)
    print e
    raise SystemExit

##
# You now have a ready-to-use Evernote client. Kaboom.
##

# Retrieve the NoteStore URL for this user
ourUser = userStore.getUser(authToken)
noteStoreUrl = userStore.getNoteStoreUrl(authToken)

# Verify our user belongs to a business
if ourUser.accounting.businessId:
    # this user is part of a business
    print "Business %s" % ourUser.accounting.businessName
else:
    print "This user does not belong to a Business"
    raise SystemExit

# Authenticate to Evernote Business and grab the Business
# NoteStore URL
bAuthResult = authenticateToBusiness(authToken)
if bAuthResult:
    bNoteStoreUrl = bAuthResult.noteStoreUrl
    # Display the Business name if it's set (it may not be)
    if bAuthResult.user.accounting.businessName:
        print "You belong to the following Evernote Business: %s" % \
            bAuthResult.user.accounting.businessName
else:
    print "Error authenticating user to Evernote Business"
    raise SystemExit

# Retrieve the business auth token and use it to create
# an instance of Business NoteStore
bAuthToken = bAuthResult.authenticationToken
bNoteStore = getNoteStoreInstance(bAuthToken, userStore)

linkedNotebooks = noteStore.listLinkedNotebooks(authToken)
bizNotebooks = []
if len(linkedNotebooks):
    print "The following Business notebooks are accessible to this user:"
    for lnb in linkedNotebooks:
        # If the `businessId` member is set, this is a link to a 
        # Business notebook
        if hasattr(lnb, 'businessId'):
            bizNotebooks.append(lnb)
            print lnb.shareName
else:
    print "This account currently has no linked notebooks"

##
# Create a new Business notebook and link it to the
# current user's account.
##
# Create the local notebook object
newBizNotebook = Types.Notebook()
# Give it a name
newBizNotebook.name = getNonEmptyUserInput('Enter a notebook name: ')
# Create the notebook using the business NoteStore
try:
    newBizNotebook = bNoteStore.createNotebook(bAuthToken, newBizNotebook)
except Exception, e:
    print "Error creating Business Notebook:"
    print "Exception type: %s" % type(e)
    print e
    raise SystemExit

# First, get the SharedNotebook instance for the notebook we just made
# This is created automatically when the business notebook is created
# and gives the creator full access to the notebook
sharedBizNotebook = newBizNotebook.sharedNotebooks[0]
# Create a LinkedNotebook instance
linkedBizNotebook = Types.LinkedNotebook()
# Assign it the share key and name of our business notebook
linkedBizNotebook.shareKey = sharedBizNotebook.shareKey
linkedBizNotebook.shareName = newBizNotebook.name
# Assign the user who owns the notebook
linkedBizNotebook.username = bAuthResult.user.username
# Assign the shard where the notebook lives
linkedBizNotebook.shardId = bAuthResult.user.shardId
# Create the linked notebook using the *normal user* auth token
try:
    myLinkedBizNotebook = noteStore.createLinkedNotebook(authToken, linkedBizNotebook)
except Exception, e:
    print "Error creating LinkedNotebook:"
    print type(e)
    print e
    raise SystemExit
# If this worked, the new business notebook will now be available 
# to the creator in any Evernote app to which he/she is authenticated

##
# Authenticate to the shared notebook so we can add a note
##
# Using non-Business NoteStore and the LinkedNotebook instance
# from the previous step:
try:
    shareAuthResult = noteStore.authenticateToSharedNotebook(myLinkedBizNotebook.shareKey, authToken)
except Exception, e:
    print "Error authenticating to SharedNotebook"
    print type(e)
    print e
    raise SystemExit

# Capture authentication token for use in this instance
shareAuthToken = shareAuthResult.authenticationToken
# Get `Notebook` instance
try:
    sharedNotebook = bNoteStore.getSharedNotebookByAuth(shareAuthToken)
except Exception, e:
    print "Error getting SharedNotebook"
    print type(e)
    print e
    raise SystemExit
##
# Now, create a note in sharedNotebook (which we have access to)
##
myNote = Types.Note()
myNote.title = "I'm a test note!" 
userInput = getNonEmptyUserInput('Enter the note contents (keep it short!): ')
myNote.notebookGuid = newBizNotebook.guid
content = '<?xml version="1.0" encoding="UTF-8"?>'
content += '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
content += "<en-note>%s</en-note>" % userInput
myNote.content = content
# Create a new note in the business notebook
# if modifying an existing Note, call updateNote here
myNote = bNoteStore.createNote(bAuthToken, myNote)

print "Note created with GUID: %s" % myNote.guid
