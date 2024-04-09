import threading
import socket
import errno

# Set up the server to listen on localhost and a specified port
host = '127.0.0.1'
port = 12435

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

# Lists to keep track of clients and their nicknames
clients = []
nicknames = []

# Accepts new client connections
def receive():
    while True:
        # Accepting new connection
        client, address = server.accept()
        print(f"Connected with {str(address)}")

        # Request and receive the new client's nickname
        nickname = client.recv(1024).decode('ascii')

        # Add the client and their nickname to the respective lists
        nicknames.append(nickname)
        clients.append(client)

        print(f'Nickname of the new client is {nickname}!')
        broadcast(f'{nickname} joined the chat!'.encode('ascii'))

        # Send the updated list of nicknames to all clients


        # Start handling the client in a new thread
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

        send_nicknames_list()

# Broadcasts a message to all clients
def broadcast(message):
    for client in clients:
        try:
            client.send(message)
        except:
            print("error")
            clients.remove(client)

# Sends a private message from one client to another
def send_private_message(sender_nickname, receiver_nickname, message):
    # Ensure both sender and receiver are connected
    if receiver_nickname in nicknames:
        receiver_index = nicknames.index(receiver_nickname)
        receiver_client = clients[receiver_index]
    if sender_nickname in nicknames:
        sender_index = nicknames.index(sender_nickname)
        sender_client = clients[sender_index]
        try:
            receiver_client.send(f"[Private]{sender_nickname} to {receiver_nickname}: {message}".encode('ascii'))
            sender_client.send(f"[Private]{sender_nickname} to {receiver_nickname}: {message}".encode('ascii'))

        except socket.error as e:
            # Handle specific socket errors, such as connection reset
            if isinstance(e.args, tuple) and e[0] == errno.ECONNRESET:
                print(f"{receiver_nickname} has disconnected.")

            # Close the connection and update the client lists
                receiver_client.close()
                clients.remove(receiver_client)
                nicknames.remove(receiver_nickname)
    else:
        # Notify the sender if the receiver is not found or offline
        sender_index = nicknames.index(sender_nickname)
        sender_client = clients[sender_index]
        sender_client.send(f"User {receiver_nickname} not found or offline.".encode('ascii'))

# Handles a connected client message(three types)
def handle(client):
    while True:
        try:
            message = client.recv(1024).decode('ascii')

            index = clients.index(client)
            nickname = nicknames[index]

            # Handling a client leaving the chat
            if message == "left":
                client.close()
                clients.remove(client)
                nicknames.pop(index)
                broadcast(f"{nickname} has left the chat.".encode('ascii'))
                print(f"Disconnected with {nickname}")
                send_nicknames_list()
                break

            # # Handling a private message
            if message.startswith("[private]"):
                # Remove the "[private]" tag and then split the remaining part
                stripped_message = message[len("[private]"):].strip()
                sender_nickname, rest = stripped_message.split(" to ", 1)
                receiver_nickname, actual_message = rest.split(":", 1)
                send_private_message(sender_nickname.strip(), receiver_nickname.strip(), actual_message.strip())
            else:
                # Broadcast any public message
                broadcast(message.encode('ascii'))

        # Handle potential disconnections or socket errors
        except socket.error as e:
            if isinstance(e.args, tuple) and e[0] == errno.ECONNRESET:
                print(f"{receiver_nickname} has disconnected.")

            # Client has disconnected
            index = clients.index(client)
            nickname = nicknames[index]
            broadcast(f'{nickname} left the chat!'.encode('ascii'))

            # Remove the client and their nickname
            clients.remove(client)
            nicknames.remove(nickname)
            client.close()

            # Notify all clients about the updated list of users
            send_nicknames_list()

            break


# Sends an updated list of nicknames to all clients
def send_nicknames_list():
    nicknames_message = 'NICKLIST:' + ','.join(nicknames)
    broadcast(nicknames_message.encode('ascii'))


print("Server is listening...")
receive()