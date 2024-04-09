import threading
import socket
from tkinter import *
from tkinter import simpledialog, messagebox, scrolledtext


class ChatClient:
    def __init__(self, master):
        # Initial setup: defines main window and establishes connection if a nickname is provided.
        self.window = master
        self.connected = False  # Initially not connected
        self.nickname = None
        self.get_nickname()
        if self.connected:  # Only setup GUI and socket if a nickname was provided
            self.active_chat = "All"  # To keep track of whom the user is currently chatting with
            self.setup_gui()  # Build the user interface
            self.setup_socket()  # Method to establish a network connection to the server.

    def get_nickname(self):
        # Requests a nickname from the user. Repeats until a valid nickname is entered or the user exits.
        while not self.nickname:
            self.nickname = simpledialog.askstring("Nickname", "Choose your nickname:", parent=self.window)
            if self.nickname is None:  # User cancelled the dialog
                if messagebox.askyesno("No Nickname", "You must choose a nickname to continue. Do you want to try again?"):
                    continue
                else:
                    messagebox.showinfo("Exiting", "The program will exit as no nickname was chosen.")
                    self.window.quit()  # Exit the application
                    return
            elif self.nickname.strip() == "":  # No actual text was entered
                messagebox.showwarning("Invalid Nickname", "Nickname cannot be empty. Please enter a nickname.")
                self.nickname = None  # Reset nickname and prompt again
            else:
                self.connected = True  # Nickname was provided, proceed to connect

    def setup_gui(self):
        # Constructs the GUI components for the chat application.
        self.window.title(f"Chat Room - {self.nickname}")

        # Setup for chat log, message entry, send button, and users list.
        # Includes functionality for sending messages and selecting chat recipients.

        # Additional disconnect button to allow user to leave the chat.

        # Left column for chat log
        self.chat_frame = Frame(self.window)
        self.chat_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 0))

        # Middle column for typing messages and sending them
        self.entry_frame = Frame(self.window)
        self.entry_frame.grid(row=1, column=0, sticky="ew")

        # Right column for users list
        self.users_frame = Frame(self.window, width=100)
        self.users_frame.grid(row=0, column=1, sticky="ns", padx=(0, 10))

        # Chat log as a scrolled text widget
        self.chat_log = scrolledtext.ScrolledText(self.chat_frame, state='disabled', height=20, width=50)
        self.chat_log.pack(fill=BOTH, expand=True)

        # Entry widget for messages
        self.msg_entry = Entry(self.entry_frame, width=50)
        self.msg_entry.pack(fill=BOTH, expand=True, side=LEFT)

        # Send button
        self.send_button = Button(self.entry_frame, text="Send", command=self.send_msg)
        self.send_button.pack(fill=BOTH, expand=True, side=RIGHT)

        # Label for users list
        self.lbl_users = Label(self.users_frame, text="Users")
        self.lbl_users.pack(anchor=N)

        # Add this in your setup_gui method
        self.disconnect_button = Button(self.entry_frame, text="Disconnect", command=self.disconnect)
        self.disconnect_button.pack(side=RIGHT)

        # Users list with an 'All' option for public messages
        self.users_list = Listbox(self.users_frame)
        self.users_list.pack(fill=BOTH, expand=True)
        self.users_list.insert(END, "All")  # Default option for public messages
        self.users_list.bind('<<ListboxSelect>>', self.select_user)

    # Establishes a socket connection to the server using user's nickname.
    def setup_socket(self): # Establishes a socket connection to the chat server
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(('127.0.0.1', 12435))
        self.client_socket.send(self.nickname.encode('ascii'))
        self.receive_thread = threading.Thread(target=self.receive_msg)
        self.receive_thread.start()

    # Sends the user's message to the server, either as a public or private message based on the active chat selection.
    def send_msg(self):
        message = self.msg_entry.get().strip()
        if message:
            if self.active_chat == "All":
                formatted_message = f"{self.nickname} to all: {message}"
                print(formatted_message)
            else:
                # 发送私聊消息时使用特定的格式
                formatted_message = f"[private]{self.nickname} to {self.active_chat}:{message}"
            self.client_socket.send(formatted_message.encode('ascii'))
            self.msg_entry.delete(0, END)

    # Receives messages from the server, updating the chat log or users list accordingly. Handles disconnection cleanly
    def receive_msg(self):
        while self.connected:
            try:
                if not self.connected:
                    # Exit the loop immediately if no longer connected
                    break
                message = self.client_socket.recv(1024).decode('ascii')
                # Check if the message is a nickname list
                if message.startswith('NICKLIST:'):
                    # Extract the nicknames and update the user list
                    nicknames = message[len('NICKLIST:'):].split(',')
                    self.update_user_list(nicknames)
                else:
                    # Display regular chat messages
                    self.chat_log.config(state='normal')
                    self.chat_log.insert(END, message + "\n")
                    self.chat_log.yview(END)
                    self.chat_log.config(state='disabled')
            except Exception as e:
                if self.connected:
                    print("An error occurred while connected:", e)
                else:
                    print("Disconnected.")
                    # Ensure the socket is closed even if an exception occurs
                try:
                    self.client_socket.close()
                except Exception as e:
                    print(f"Error closing socket after exception: {e}")
                break

    # Updates the GUI with the current list of online users, excluding the user's own nickname.
    def update_user_list(self, nicknames): #Updates the list of online users displayed in the GUI.
        # Clear the current list and add the 'All' option
        self.users_list.delete(0, END)
        self.users_list.insert(END, "All")
        # Add the new nicknames to the user list
        for nickname in nicknames:
            if nickname != self.nickname:  # Exclude the user's own nickname
                self.users_list.insert(END, nickname)

    # Updates the active chat based on the user's selection from the users list.
    def select_user(self, evt):
        selection = self.users_list.curselection()
        if selection:
            selected_index = selection[0]
            self.active_chat = self.users_list.get(selected_index)

    # Signals the server that the user is leaving, shuts down and closes the socket, and disables the GUI before exiting.
    def disconnect(self):
        self.connected = False  # Ensure no further recv calls

        try:
            self.client_socket.send("left".encode('ascii'))
        except Exception as e:
            print(f"Error sending disconnect message: {e}")

        try:
            self.client_socket.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print(f"Error shutting down socket: {e}")

        try:
            self.client_socket.close()
        except Exception as e:
            print(f"Error closing socket: {e}")

        self.send_button.config(state=DISABLED)
        self.msg_entry.config(state=DISABLED)
        self.window.destroy()


root = Tk()
root.geometry("600x400")
app = ChatClient(root)
root.mainloop()
