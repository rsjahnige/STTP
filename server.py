# @author Ryan Jahnige
# This file contains a sample server implementation for STTP
#
# To run this code, type 'python3 server.py' at the command line
# The program will take care of the rest
# 
# Note that '0' is used to represent the public bulletin board and admin user

from socket import *
from datetime import datetime
from _thread import *
import threading
from collections import OrderedDict

# Used to keep track of when messages are posted
now = datetime.now()
timestamp = datetime.timestamp(now)

mutex_users = threading.Lock() # used when updating num_users
num_users = 0 # used to assign user id's

# Contains all current bulletin boards and their contents
bulletin_board = {}
bulletin_board['0'] = OrderedDict()
bulletin_board['0'][str(timestamp)] = ('0\f', "Greetings\f", "Welcome to the bulletin board\f")

# Maps group names to current members, first element in the array is the user that
# created the group
groups = {'0': ['0']}

# Used to store user timestamps in between sessions
users = {}

# Establish TCP connection
serverPort = 13037
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen(100)

# Inserts end of text character between fields and a end of transmission character
# at the end. Then finds the length of the transmission and completes the 4 way
# transaction
def sendResponse(connectionSocket, status, time, data):
	response = chr(3).join([status, str(time), data])
	response += chr(4)

	length = len(response)
	connectionSocket.send(str(length).encode())
	retval = connectionSocket.recv(1500).decode()

	if retval == "OK":
		connectionSocket.send(response.encode())

# The function is responsible for all transmissions sent between the server and client 
# aside from the initial TCP handshake
def user_thread(connectionSocket):
	action = ''
	id = ''
	group = ''
	time = ''
	data = ''

	def validateRequest():
        # Check if client request corresponds to an existing group
		if group not in groups.keys():
			sendResponse(connectionSocket, "ERROR", time, "Group does not exist")
        
        # Ensure that a user is a member of any group the would like to perform an action in
        elif id not in groups[group]:
			if group == '0':
				sendResponse(connectionSocket, "ERROR", time, "User does not exist")
			else:
				sendResponse(connectionSocket, "ERROR", time, "Not a member of this group")
		else:
			return True

		return False

	while action != "EXIT":
		message = connectionSocket.recv(1500).decode()

		# Parse message
		fields = message.partition(chr(3))
		action = fields[0]
		fields = fields[2].partition(chr(3))
		id = fields[0]
		fields = fields[2].partition(chr(3))
		group = fields[0]
		fields = fields[2].partition(chr(3))
		time = fields[0]
		fields = fields[2].partition(chr(4))
		data = fields[0]

		if action == "NEW":
			global num_users

			mutex_users.acquire()
			num_users += 1
			mutex_users.release()

			groups['0'].append(str(num_users))
			users[num_users] = timestamp
			sendResponse(connectionSocket, "OK", timestamp, str(num_users))

		elif action == "LOAD":
			if data not in groups['0'] or data == '0':
				sendResponse(connectionSocket, "ERROR", '0', "User does not exist") 
			else:
				time = users[data]
				sendResponse(connectionSocket, "OK", time, data)

		elif action == "GET":
			if (validateRequest()):
				response_data = ''
				searchFlag = False
				for key, value in bulletin_board[group].items():
					flag = True

					# Get all and get new require that data = '0'
					if data != '0':
						searchFlag = True
						flag = False
						# Get all messages with a specific subject line
						if data in value[1]:
							flag = True

					if flag and time <= key:
						response_data += value[0]
						response_data += value[1]
						response_data += value[2]
						response_data += key + '\f'

				#end for loop

				if not searchFlag:
					nnow = datetime.now()
					time = datetime.timestamp(nnow)
					if len(response_data) == 0:
						response_data = "No new posts"
				elif len(response_data) == 0:
					response_data = "No posts match your search criteria"

				sendResponse(connectionSocket, "OK", time, response_data)

		elif action == "POST":
			if (validateRequest()):
				id += '\f'
				message = data.partition('\f')

				nnow = datetime.now()
				ntimestamp = str(datetime.timestamp(nnow))

				bulletin_board[group][ntimestamp] = (id, message[0] + '\f', message[2] + '\f')
				sendResponse(connectionSocket, "REFRESH", time, '0')

		elif action == "LIST":
			if (validateRequest()):
				response_data = ''
                
                # List all groups a user is a member of
				if data == "GROUPS":
					for key, value in groups.items():
						if id in value:
							response_data += key + '\f'
							response_data += value[0] + '\f'

                # List all users within a specified group
				elif data == "USERS":
					for user in groups[group]:
						response_data += user + '\f'
                        
                 # List all messages posted by a user in a specific group
				elif data == "MESSAGES":
					for key, value in bulletin_board[group].items():
						userID = value[0].strip('\f')
						if id == userID:
							response_data += value[0]
							response_data += value[1]
							response_data += value[2]
							response_data += key + '\f'
                            
                # List all subjects posted to a group within specified time period
				else:
					for key, value in bulletin_board[group].items():
						if data <= key:
							response_data += value[1]

				sendResponse(connectionSocket, "OK", time, response_data)

		elif action == "DELETE":
			if validateRequest():
                # Message does not exist
				if data not in bulletin_board[group].keys():
					sendResponse(connectionSocket, "ERROR", time, "Invalid message ID")
				else:
					userID = bulletin_board[group][data][0].strip('\f')
                    
                    # Message was not posted by the user making the request
					if userID != id:
						sendResponse(connectionSocket, "ERROR", time, "Invalid message ID")
                        
                    # Remove message from the group
					else:
						del bulletin_board[group][data]
						sendResponse(connectionSocket, "OK", time, '0')

		elif action == "ADD":
        
            # Add new group to bulletin board
			if group not in groups.keys():
				groups[group] = [id]
				bulletin_board[group] = OrderedDict()

                # Add members to new group
				if data != '0':
					user = data.partition('\f')
					while user[0] != '':
						if user[0] not in groups['0']:
							sendResponse(connectionSocket, "ERROR", time, "User does not exist")
						else:
							groups[group].append(user[0])

						user = user[2].partition('\f')

				sendResponse(connectionSocket, "OK", time, '0')
             
            # Add user to an existing group
			else:
                # Ensure the user making the request is the one that created the group
				if id != groups[group][0]:
					sendResponse(connectionSocket, "ERROR", time, "Connot add members to this group")
				else:
                    # Invalid request
					if data == '0':
						sendResponse(connectionSocket, "ERROR", time, "Group already exists, try a different name")
					else:
						user = data.partition('\f')
						while user[0] != '':
							if user[0] not in groups['0']:
								sendResponse(connectionSocket, "ERROR", time, "User " + user[0] +" does not exist")
							else:
								groups[group].append(user[0])

							user = user[2].partition('\f')

						sendResponse(connectionSocket, "OK", time, '0')

		elif action == "REMOVE":
			if (validateRequest()):
            
                # Ensure the user making the request is the one that created the group
				if id != groups[group][0]:
					sendResponse(connectionSocket, "ERROR", time, "Cannot delete this group")
				else:
                    # Remove group
					if data == '0':
						del groups[group]
						del bulletin_board[group]
                        
                    # Remove member from group
					else:
						user = data.partition('\f')
						while user[0] != '':
							if user[0] not in groups[group]:
								sendResponse(connectionSocket, "ERROR", time, "User" + user[0] + " does not exist")
							else:
								groups[group].remove(user[0])
								user = user[2].partition('\f')

					sendResponse(connectionSocket, "OK", time, '0')


		elif action == "COUNT":
			if validateRequest():
				count = 0
				for key in bulletin_board[group].keys():
					if data <= key:
						count += 1

				sendResponse(connectionSocket, "OK", time, str(count))

		elif action == "EXIT":
			if id != '0':
				users[id] = time
			sendResponse(connectionSocket, "OK", time, '0')

		else:
			sendResponse(connectionSocket, "ERROR", time, "Invalid request")

	connectionSocket.close()

while True:
	connectionSocket, addr = serverSocket.accept()
	start_new_thread(user_thread, (connectionSocket,))
