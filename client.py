# @author Ryan Jahnige
# This file contains a sample client implementation for STTP
#
# To run this code, type 'python3 client.py' at the command line
# The program will take care of the rest
# 
# Note that this program does not user usernames and passwords to sign in,
# all users are identified by their server generated user ID

from socket import *
from datetime import datetime
import sys

serverName = input('Enter server ip: ')
#serverName = '10.0.0.233' # Can hard code the IP of the server if you like
serverPort = 13037

cookie = ''

timestamp = ''
status = ''
data = ''

# Establish TCP connection
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))

# This function controls all transactions between client and server except for the
# initial TCP handshake
def mainMenu():
    menuNum = ''
    while menuNum != '12':
    
        # Display main menu to user
        print("Main menu:")
        print("\t1. Get messages")
        print("\t2. Post message")
        print("\t3. Delete message")
        print("\t4. Create group")
        print("\t5. Remove group")
        print("\t6. Add members to group")
        print("\t7. Remove members from group")
        print("\t8. List your groups") #All groups the user is a member of
        print("\t9. List group members") #Can only list group members of groups you control
        print("\t10. List all subjects")
        print("\t11. Get number of messages")
        print("\t12. Exit")
        menuNum = input("Enter menu number: ")

        # Generate GET request to server
        if menuNum == '1':
            board = input("Enter group name ('0' for public): ")
            time = input("Enter 0 for all messages or 1 for new messages: ")
            if (time == '1'): time = timestamp
            search = input("Filter messages with ('0' for no filter): ")
        
            sendMessage(clientSocket, "GET", cookie, board, time, search)
            retval = clientSocket.recv(1500).decode()
            parseMessage(retval)

            if status == "OK":
                displayMessages(data, board, "GET")
            
        # Generate POST request to server
        elif menuNum == '2':
            board = input("Enter group name ('0' for public): ")
            header = input("Enter message header: ")
            body = input("Enter message body: ")
            message = header + '\f' + body
        
            sendMessage(clientSocket, "POST", cookie, board, timestamp, message)
            retval = clientSocket.recv(1500).decode()
            parseMessage(retval)

            if status == "REFRESH":
                sendMessage(clientSocket, "GET", cookie, board, timestamp, '0')
                retval = clientSocket.recv(1500).decode()
                parseMessage(retval)
                
                displayMessages(data, board, "GET")

        # Generate DELETE request to server
        elif menuNum == '3':
            board = input("Enter group to remove from ('0' for public): ")
            
            # List all message posted by the user
            sendMessage(clientSocket, "LIST", cookie, board, timestamp, 'MESSAGES')
            retval = clientSocket.recv(1500).decode()
            parseMessage(retval)

            if data != '':
                displayMessages(data, board, "LIST")

                messageID = input("Enter message id to remove: ")
                sendMessage(clientSocket, "DELETE", cookie, board, timestamp, messageID)
                retval = clientSocket.recv(1500).decode()
                parseMessage(retval)

            else:
                print("\nYou have not posted any messages to this group\n")
        
        # Generate ADD request to server
        elif menuNum == '4':
            board = input("Enter group name ('0' for public): ")

            members = ''
            user = input("Enter user cookie(or '0' when done): ")
            while user != '0':
                members += user + '\f'
                user = input("Enter user cookie(or '0' when done): ")

            if members == '': members = '0'  
                  
            sendMessage(clientSocket, "ADD", cookie, board, timestamp, members)
            retval = clientSocket.recv(1500).decode()
            parseMessage(retval)

        # Generate REMOVE request to server 
        elif menuNum =='5':        
            board = input("Enter group to remove: ")
            sendMessage(clientSocket, "REMOVE", cookie, board, timestamp, '0')
            retval = clientSocket.recv(1500).decode()
            parseMessage(retval)
            
        # Generate ADD users to group request to server
        elif menuNum == '6':
            board = input("Enter group name ('0' for public): ")

            members = ''
            user = input("Enter user cookie(or '0' when done): ")
            while user != '0':
                members += user + '\f'
                user = input("Enter user cookie(or '0' when done): ")

            if members != '':
                sendMessage(clientSocket, "ADD", cookie, board, timestamp, members)
                retval = clientSocket.recv(1500).decode()
                parseMessage(retval)

        # GEnerate REMOVE members from group request to server
        elif menuNum == '7':
            board = input("Enter group name: ")

            members = ''
            user = input("Enter user cookie(or '0' when done): ")
            while user != '0':
                members += user + '\f'
                user = input("Enter user cookie(or '0' when done): ")

            if members != '':
                sendMessage(clientSocket, "REMOVE", cookie, board, timestamp, members)
                retval = clientSocket.recv(1500).decode()
                parseMessage(retval)
          
        # Generate LIST all groups a user is  member of request to server
        elif menuNum == '8':
            print("\nYour groups: \n")
            sendMessage(clientSocket, "LIST", cookie, '0', timestamp, "GROUPS")
            retval = clientSocket.recv(1500).decode()
            parseMessage(retval)

            userGroup = data.partition('\f')
            while userGroup[1] != '':
                print("Name: ", userGroup[0])
                userGroup = userGroup[2].partition('\f')
                print("Owner: ", userGroup[0], '\n')
                userGroup = userGroup[2].partition('\f')

        # Generate LIST all members of a group request to server
        elif menuNum == '9':
            board = input("Enter group: ")
            sendMessage(clientSocket, "LIST", cookie, board, timestamp, "USERS")
            retval = clientSocket.recv(1500).decode()
            parseMessage(retval)
            
            i = 1
            user = data.partition('\f')
            print("Members:")
            while user[1] != '':
                print(i, ". ", user[0])
                user = user[2].partition('\f')
                i += 1

        # Generate LIST subjects request to server
        elif menuNum == '10':
            board = input("Enter group name ('0' for public): ")
            time = input("Enter '0' for all subjects and '1' for new subjects: ")
            
            if time == '1': time = timestamp
            sendMessage(clientSocket, "LIST", cookie, board, timestamp, time)
            retval = clientSocket.recv(1500).decode()
            parseMessage(retval)

            if data == '' and time == '0':
                print("\nNo subjects have been posted to '", board, "'\n")
            elif data == '' and time == '1':
                print("\nNo new subjects have been posted to '", board, "'\n")
            else:
                i = 1
                user = data.partition('\f')
                print("\nSubjects: ")
                while user[1] != '':
                    print(i, ". ", user[0])
                    user = user[2].partition('\f')
                    i += 1
                print()

        # Generate COUNT number of messages request to server
        elif menuNum == '11':
            board = input("Enter group name ('0' for public): ")
            time = input("Enter '0' for all messages and '1' for new messages: ")

            if time == '1': time = timestamp
            
            sendMessage(clientSocket, "COUNT", cookie, board, timestamp, time)
            retval = clientSocket.recv(1500).decode()
            parseMessage(retval)

            if time == '0':
                print("\nTotal messages posted to '", board, "': ", data, '\n')
            else:
                print("\nNew messages posted to '", board, "': ", data, '\n')
            
        # Generate EXIT request to server
        elif menuNum == '12':
            sendMessage(clientSocket, "EXIT", cookie, '0', timestamp, '0')
            retval = clientSocket.recv(1500).decode()
            parseMessage(retval)

        else:
            print("Invalid menu choice")

# Format messages recieved from the server and print them to the users terminal    
def displayMessages(data, group, action):
    print("\nGroup: ", group, '\n')
    message = data.partition('\f')

    if message[2] == '':
        print(data, '\n')
    
    while message[2] != '':    
        print("\nUser: ", message[0])
        message = message[2].partition('\f')
        print("Header: ", message[0])
        message = message[2].partition('\f')
        print("Body: ", message[0])
        message = message[2].partition('\f')
        
        if action == "GET":
            tempTime = datetime.fromtimestamp(float(message[0]))
            print("Time posted: ", tempTime, '\n')
        else:
            print("Message ID: ", message[0], '\n')

        message = message[2].partition('\f')
        
# Formats request to server then sends the request
def sendMessage(clientSocket, action, id, group, time, data):
    message = chr(3).join([action, id, group, time, data])
    message += chr(4)
    clientSocket.send(message.encode())

# Completes the 4 way transaction initiated by sendMessage() and parses the servers response
def parseMessage(retval):
    global timestamp
    global status
    global data

    val = "OK"
    length = int(retval)
    clientSocket.send(val.encode())
    message = clientSocket.recv(length).decode()

    fields = message.partition(chr(3))
    status = fields[0]
    
    fields = fields[2].partition(chr(3))
    timestamp = fields[0]
    
    fields = fields[2].partition(chr(4))
    data = fields[0]

    if status == "ERROR":
        print("\nError: ", data, '\n')

# Create user session
try: 
    user_info = open("bulletin_user.txt", "r+")
except FileNotFoundError:
    temp = ''
    while temp != '1' and temp != '0':
        temp = input("Enter '0' to create user or '1' to sign in: ")
    
    # Generate NEW user request to server
    if temp == '0':
        sendMessage(clientSocket, "NEW", '0', '0', '0', '0')
        retval = clientSocket.recv(1500).decode()
        parseMessage(retval)

    # Generate LOAD user request to server
    elif temp == '1':
        userName = input("Enter user ID: ")
        
        sendMessage(clientSocket, "LOAD", '0', '0', '0', userName)
        retval = clientSocket.recv(1500).decode()
        parseMessage(retval)
        
        if status == "ERROR":
            sendMessage(clientSocket, "EXIT", '0', '0', '0', '0')
            retval = clientSocket.recv(1500).decode()
            parseMessage(retval)
            
            clientSocket.close()
            sys.exit()

    cookie = data
    
# User already has an application specific file saved in the users file system
else:
    cookie = user_info.readline().rstrip()

    if cookie == "False":
        temp = ''
        while temp != '1' and temp != '0':
            temp = input("Enter '0' to create user or '1' to sign in: ")
    
            if temp == '0':
                sendMessage(clientSocket, "NEW", '0', '0', '0', '0')
                retval = clientSocket.recv(1500).decode()
                parseMessage(retval)
                
            elif temp == '1':
                userName = input("Enter user ID: ")
        
                sendMessage(clientSocket, "LOAD", '0', '0', '0', userName)
                retval = clientSocket.recv(1500).decode()
                parseMessage(retval)
        
                if status == "ERROR":
                    sendMessage(clientSocket, "EXIT", '0', '0', '0', '0')
                    retval = clientSocket.recv(1500).decode()
                    parseMessage(retval)
                    
                    clientSocket.close()
                    sys.exit()

            cookie = data
    else:
        timestamp = user_info.readline().rstrip()

    user_info.close()
# User session has beed created
    
# Start by loading all new messages on public bulletin board
sendMessage(clientSocket, "GET", cookie, '0', timestamp, '0')
retval = clientSocket.recv(1500).decode()
parseMessage(retval)

if status == "OK":
    displayMessages(data, '0', "GET")
else:
    sendMessage(clientSocket, "EXIT", '0', '0', '0', '0')
    retval = clientSocket.recv(1500).decode()
    parseMessage(retval)

    print("Server has been restarted, delete bulletin_user.txt")
    
    clientSocket.close()
    sys.exit()

mainMenu()

# Exit
temp_choice = input("Sign off ('y' or 'n'): ")

if temp_choice == 'y':
    print("Your user ID is: ", cookie, "\nTo sign back on you will need to remember this value.")
    
    user_info = open("bulletin_user.txt", "w")
    user_info.write("False\n")

    user_info.close()
    
else:
    user_info = open("bulletin_user.txt", "w")
    user_info.write(cookie + '\n')
    user_info.write(timestamp + '\n')

    user_info.close()


clientSocket.close()
