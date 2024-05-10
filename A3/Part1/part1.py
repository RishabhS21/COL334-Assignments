import socket
import hashlib
import time

# Server details
server_host = "vayu.iitd.ac.in"
server_host="127.0.0.1"
server_port = 9801
start=time.time()
# Create a UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Define the timeout for receiving a response (in seconds)
timeout = 0.02
delta =0.001

mod=5

if server_port==9802:
    delta=0.002
    mod=5

t=[0]*mod
counter=0


def send_and_receive(request, expected_response_prefix, max_attempts=5):
    global counter
    attempts = 0
    while True:
        udp_socket.sendto(request.encode(), (server_host, server_port))
        u=0
        for i in range(mod):
            u+=t[i]
        udp_socket.settimeout(timeout+(u)*delta)
        try:
            response, _ = udp_socket.recvfrom(4096)
            response = response.decode()
            if response.startswith(expected_response_prefix):
                counter+=1
                return response
                
                
        except socket.timeout:
            print(f"Timeout: No response received for request. Retrying... (Attempt {attempts + 1})")
            attempts += 1
            t[counter%mod]=attempts



# Send the SendSize request to get the number of bytes to receive
send_size_request = "SendSize\nReset\n\n"
size_response = send_and_receive(send_size_request, "Size: ")

# Parse the Size response to get the number of bytes to receive
num_bytes = int(size_response.split(": ")[1])


print("Total size to be received : ",num_bytes)

# Create a buffer to store received data
data_buffer = [None] * (num_bytes // 1448 + 1)
offset_st=""
offset_rt=""

# Define the maximum number of bytes per request
max_bytes_per_request = 1448


def write_to_file():
    with open("data_for_graph.txt", "w") as file:
        file.write(offset_st)
        file.write("\n\n\n")
        file.write(offset_rt)


# Request and receive data in chunks
count=0
for offset in range(0, num_bytes, max_bytes_per_request):
    num_to_receive = min(max_bytes_per_request, num_bytes - offset)

    # Send the Offset and NumBytes request
    offset_request = f"Offset: {offset}\nNumBytes: {num_to_receive}\n\n"
    st=time.time()
    while True:

        offset_response = send_and_receive(offset_request, "Offset: ")

        # Parse the response
        received_offset = int(offset_response.split("\n")[0].split(": ")[1])
        received_num_bytes = int(offset_response.split("\nNumBytes: ")[1].split("\n")[0])
        received_data = offset_response.split("\n\n", 1)[1].encode()
        data_buffer[received_offset // 1448] = (received_offset, received_num_bytes, received_data)

        if(offset==received_offset):
            end=time.time()
            print(offset, " : ", int((end-start)*1000))
            if(count<10):
                offset_st+=(f"{int((st-start)*1000)} {offset}\n")
            if(count<10):
                offset_rt+=(f"{int((end-start)*1000)} {offset}\n")
            count+=1
            break



# Assemble the data in the correct order
assembled_data = bytearray(num_bytes)

for data in data_buffer:
    if(data is None):
        print("None type object")
        continue
    assembled_data[data[0]:data[0]+data[1]] = data[2]

# Calculate MD5 hash of the received data
md5_hash = hashlib.md5(assembled_data).hexdigest()

print(md5_hash)

# Submit the MD5 hash to the server
submit_request = f"Submit: [1@nothing]\nMD5: {md5_hash}\n\n"
udp_socket.sendto(submit_request.encode(), (server_host, server_port))

# Receive the Result response
result_response = send_and_receive(submit_request, "Result: ")

# Parse the Result response
if result_response.startswith("Result: "):

    result = result_response.split("\n")[0].split(": ")[1].strip()
    time_taken = float(result_response.split("\nTime: ")[1].split("\n")[0])
    penalty = float(result_response.split("\nPenalty: ")[1].split("\n")[0])
    print(f"Result: {result}")
    print(f"Time taken (ms): {time_taken}")
    print(f"Penalty: {penalty}")

else:
    print("Error: Failed to get the result from the server.")


write_to_file()

# Close the UDP socket
udp_socket.close()