
from __future__ import print_function
import httplib2
import os
import sys

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apiclient import errors
from apiclient.discovery import build

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://mail.google.com'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def BuildService(credentials):
    """Build a Gmail service object.

    Args:
      credentials: OAuth 2.0 credentials.

    Returns:
      Gmail service object.
    """
    http = httplib2.Http()
    http = credentials.authorize(http)
    return build('gmail', 'v1', http=http)


def DeleteMessage(service, user_id, msg_id):
    try:
        response = service.users().messages().trash(userId=user_id, id=msg_id).execute()
        return response
    except errors.HttpError as error:
        print('An error occurred: %s' % error)


def DeleteMessagePerm(service, user_id, msg_id):
    try:
        response = service.users().messages().delete(
            userId=user_id, id=msg_id).execute()
        return response
    except errors.HttpError as error:
        print('An error occurred: %s' % error)


def ListMessagesWithLabels(service, user_id, label_ids=[]):
    """List all Messages of the user's mailbox with label_ids applied.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      label_ids: Only return Messages with these labelIds applied.

    Returns:
      List of Messages that have all required Labels applied. Note that the
      returned list contains Message IDs, you must use get with the
      appropriate id to get the details of a Message.
    """
    try:
        response = service.users().messages().list(userId=user_id,
                                                   labelIds=label_ids).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id,
                                                       labelIds=label_ids,
                                                       pageToken=page_token).execute()
            messages.extend(response['messages'])

        return messages
    except errors.HttpError as error:
        print('An error occurred: %s' % error)


def GetMessage(service, user_id, msg_id):
    """Get a Message with given ID.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      msg_id: The ID of the Message required.

    Returns:
      A Message.
    """
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()

        print('Message snippet: %s' % message['snippet'])

        return message
    except errors.HttpError as error:
        print('An error occurred: %s' % error)


def main():

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    while True:
        print("""
1. Delete all messages
2. Delete messages from label
3. Delete messages from specifed user
4. Empty trash
5. Empty spam
6. Exit
        """)
        try:
            choice = int(input('Choose an option: '))
            if choice == 1:
                messages = ListMessagesWithLabels(
                    service, 'me', 'INBOX')
                for message in messages:
                    delete = DeleteMessagePerm(service, 'me', message['id'])
            elif choice == 2:
                label_result = service.users().labels().list(userId='me').execute()
                labels = label_result.get('labels', [])
                for i, label in enumerate(labels):
                    print(str(i+1) + ': ' + label['name'])
                try:
                    label_choice = int(input('Choose label for deletion: '))
                except ValueError:
                    print('Invalid input! Try again')
                    continue
                messages = ListMessagesWithLabels(
                    service, 'me', labels[label_choice-1]['name'])
                for message in messages:
                    delete = DeleteMessage(service, 'me', message['id'])
            elif choice == 3:
                print("Delete messages from user")
            elif choice == 4:
                messages = ListMessagesWithLabels(
                    service, 'me', 'TRASH')
                for message in messages:
                    delete = DeleteMessagePerm(service, 'me', message['id'])
            elif choice == 5:
                messages = ListMessagesWithLabels(
                    service, 'me', 'SPAM')
                for message in messages:
                    delete = DeleteMessagePerm(service, 'me', message['id'])
            else:
                sys.exit(1)
        except ValueError:
            print('Invalid input! Try again')


if __name__ == '__main__':
    main()