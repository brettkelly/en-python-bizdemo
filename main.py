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

EN_HOST = "sandbox.evernote.com"
EN_URL = "https://%s" % EN_HOST

def getUserStoreInstance(authToken):
	userStoreUri = "%s/edam/user" % EN_URL
	userStoreHttpClient = THttpClient.THttpClient(userStoreUri)
	userStoreProtocol = TBinaryProtocol.TBinaryProtocol(userStoreHttpClient)
	userStore = UserStore.Client(userStoreProtocol)
	print "Created UserStore.Client instance"
	return userStore

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

userStore = getUserStoreInstance(authToken)
noteStore = getNoteStoreInstance(authToken, userStore)

##
# You now have a ready-to-use Evernote client. Kaboom.
##


