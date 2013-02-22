#!/usr/bin/env python

# Copyright 2013 Brett Kelly
# All rights reserved.

import evernote.edam.type.ttypes as Types
from evernote.api.client import EvernoteClient


## Determines to which Evernote host we're connecting
TESTING = True

# bypass the dev token prompt by populating this variable.
auth_token = ""


def get_non_empty_user_input(prompt):
    "Prompt the user for input, disallowing empty responses"
    uinput = raw_input(prompt)
    if uinput:
        return uinput
    print "This can't be empty. Try again."
    return get_non_empty_user_input(prompt)


if not auth_token:
    auth_token = get_non_empty_user_input("Enter your dev token: ")

client = EvernoteClient(token=auth_token, sandbox=TESTING)
try:
    note_store = client.get_note_store()
except Exception, e:
    print "Error getting NoteStore instance:"
    print type(e)
    print e
    raise SystemExit

##
# You now have a ready-to-use Evernote client. Kaboom.
##

# Verify our user belongs to a business
user_store = client.get_user_store()
our_user = user_store.getUser()
if our_user.accounting.businessId:
    # this user is part of a business
    print "Business %s" % our_user.accounting.businessName
else:
    print "This user does not belong to a Business"
    raise SystemExit

# Authenticate to Evernote Business and get Business User
try:
    biz_auth_result = user_store.authenticateToBusiness()
    biz_user = biz_auth_result.user
    # Display the Business name if it's set (it may not be)
    if biz_user.accounting.businessName:
        print "You belong to the following Evernote Business: %s" % \
            biz_user.accounting.businessName
except Exception, e:
    print "Error authenticating user to Evernote Business"
    print type(e)
    print e
    raise SystemExit

linked_notebooks = note_store.listLinkedNotebooks()
biz_notebooks = []
if len(linked_notebooks):
    print "The following Business notebooks are accessible to this user:"
    for lnb in linked_notebooks:
        # If the `businessId` member is set, this is a link to a
        # Business notebook
        if hasattr(lnb, 'businessId'):
            biz_notebooks.append(lnb)
            print lnb.shareName
else:
    print "This account currently has no linked notebooks"

##
# Create a new Business notebook and link it to the
# current user's account.
##
# Create an instance of Business NoteStore
biz_note_store = client.get_business_note_store()
# Create the local notebook object
new_biz_notebook = Types.Notebook()
# Give it a name
new_biz_notebook.name = get_non_empty_user_input('Enter a notebook name: ')
# Create the notebook using the business NoteStore
try:
    new_biz_notebook = biz_note_store.createNotebook(new_biz_notebook)
except Exception, e:
    print "Error creating Business Notebook:"
    print "Exception type: %s" % type(e)
    print e
    raise SystemExit

# First, get the SharedNotebook instance for the notebook we just made
# This is created automatically when the business notebook is created
# and gives the creator full access to the notebook
shared_biz_notebook = new_biz_notebook.sharedNotebooks[0]
# Create a LinkedNotebook instance
linked_biz_notebook = Types.LinkedNotebook()
# Assign it the share key and name of our business notebook
linked_biz_notebook.shareKey = shared_biz_notebook.shareKey
linked_biz_notebook.shareName = new_biz_notebook.name
# Assign the user who owns the notebook
linked_biz_notebook.username = biz_user.username
# Assign the shard where the notebook lives
linked_biz_notebook.shardId = biz_user.shardId

# Create the linked notebook using the *normal user* NoteStore
try:
    my_linked_biz_notebook = \
        note_store.createLinkedNotebook(linked_biz_notebook)
except Exception, e:
    print "Error creating LinkedNotebook:"
    print type(e)
    print e
    raise SystemExit
# If this worked, the new business notebook will now be available
# to the creator in any Evernote app to which he/she is authenticated

##
# Now, create a note in Business Notebook (which we have access to)
##
my_note = Types.Note()
my_note.title = "I'm a test note!"
user_input = \
    get_non_empty_user_input('Enter the note contents (keep it short!): ')
my_note.notebookGuid = new_biz_notebook.guid
my_note.content = '<?xml version="1.0" encoding="UTF-8"?>\
    <!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">\
    <en-note>%s</en-note>' % user_input
# Create a new note in the business notebook
# if modifying an existing Note, call updateNote here
my_note = biz_note_store.createNote(my_note)

print "Note created with GUID: %s" % my_note.guid
