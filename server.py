import socket, threading

# Global variable that mantain client's connections
connections = []

def handle_user_connection(connection: socket.socket, address: str) -> None:
    '''
        Get user connection in order to keep receiving their messages and
        sent to others users/connections.
    '''

    # log the user entering the server
    print(str(f'{address[0]}:{address[1]}') + " has joined the server.")

    # create a blank nickname variable:
    nickname = ''

    while True:
        try:
            # Get client message
            msg = connection.recv(1024)

            # If no message is received, there is a chance that connection has ended
            # so in this case, we need to close connection and remove it from connections list.
            if msg:
                # first assign the sender ip to a variable
                sender = str(f'{address[0]}:{address[1]}')

                # [[COMMAND]] debug commands
                if msg.decode()=='!connections':
                    for each in connections:
                        print("\n" + str(each))
                    continue

                if msg.decode()=='!connection':
                    print(connection)
                    continue

                # [[COMMAND]] recognize when the sender wants to create a nickname for themselves
                if msg.decode().split(" ")[0]=='!name': 
                    try:
                        nickname = str(msg.decode().split(" ")[1])
                    except Exception:
                        # catch if no input passed in, telling sender to reformat command.
                        connection.send(str('Please check your command syntax. The command usage is "!name [args]", where [args] is a string.').encode())
                    continue

                # [[COMMAND]] creates a command that when run closes connections to other users
                def find_ip(socket_address):
                    ip = str(socket_address).split("raddr=('")[1].split("', ")[0] #this gets the ip address
                    port = str(socket_address).split("raddr=('")[1].split("', ")[1].split(")")[0] #this gets the port number
                    full_address = ip + ":" + port #this puts the two together in readable form ie 127.0.0.1:1111
                    return full_address

                if msg.decode().split(" ")[0]=='!kick':
                    try:
                        arg = str(msg.decode().split(" ")[1]) #if this fails, that means nothing was passed in as an argument
                        if arg == 'all': #if the argument is "all", kick all other users
                            print("\nall\n")
                            broadcast("You have been kicked from the server.", connection) #first tell the users they have been kicked
                            for kicked in connections[:]:
                                full_address = find_ip(kicked)
                                if kicked != connection:                            
                                    print(full_address + " has been kicked from the server.")
                                    remove_connection(kicked)
                        else:
                            found=0
                            for kicked in connections[:]:
                                full_address = find_ip(kicked)
                                if full_address == arg:
                                    print(full_address + " has been kicked from the server.")
                                    kicked.send(str("You have been kicked from the server.").encode())
                                    remove_connection(kicked)
                                    found=1
                                    break
                            if found == 0:
                                connection.send(str("No such user was found.").encode())
                    except Exception:
                        # catch if no input passed in, telling sender to reformat command.
                        connection.send(str('Please check your command syntax. The command usage is "!kick [args]", where [args] is a string. [args] can be a username, or "all" to kick off all other users.').encode())
                    continue

                
                # Build message format and broadcast to users connected on server
                if connection in connections:
                    # Log message sent by user
                    print(sender + f' - {msg.decode()}')

                    if nickname:
                        msg_to_send = "\t" + f'From {nickname} - {msg.decode()}'
                    else:
                        msg_to_send = "\t" + f'From {address[0]}:{address[1]} - {msg.decode()}'    
                    broadcast(msg_to_send, connection)

            # Close connection if no message was sent
            else:
                remove_connection(connection)
                break

        except Exception as e:
            print(f'Error to handle user connection: {e}')
            remove_connection(connection)
            break


def broadcast(message: str, connection: socket.socket) -> None:
    '''
        Broadcast message to all users connected to the server
    '''

    # Iterate on connections in order to send message to all client's connected
    for client_conn in connections:
        # Check if isn't the connection of who's send
        if client_conn != connection:
            try:
                # Sending message to client connection
                client_conn.send(message.encode())

            # if it fails, there is a chance of socket has died
            except Exception as e:
                print('Error broadcasting message: {e}')
                remove_connection(client_conn)


def remove_connection(conn: socket.socket) -> None:
    '''
        Remove specified connection from connections list
    '''

    # Check if connection exists on connections list
    if conn in connections:
        # Close socket connection and remove connection from connections list
        conn.close()
        connections.remove(conn)


def server() -> None:
    '''
        Main process that receive client's connections and start a new thread
        to handle their messages
    '''

    LISTENING_PORT = 12000
    
    try:
        # Create server and specifying that it can only handle 4 connections by time!
        socket_instance = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_instance.bind(('', LISTENING_PORT))
        socket_instance.listen(4)

        print('Server running!')
        
        while True:

            # Accept client connection
            socket_connection, address = socket_instance.accept()
            # Add client connection to connections list
            connections.append(socket_connection)
            # Start a new thread to handle client connection and receive it's messages
            # in order to send to others connections
            threading.Thread(target=handle_user_connection, args=[socket_connection, address]).start()

    except Exception as e:
        print(f'An error has occurred when instancing socket: {e}')
    finally:
        # In case of any problem we clean all connections and close the server connection
        if len(connections) > 0:
            for conn in connections:
                remove_connection(conn)

        socket_instance.close()


if __name__ == "__main__":
    server()