import socket
import hashlib
import time
# import matplotlib.pyplot as plt
# Server details
# server_host = "10.17.7.134"
server_host = "127.0.0.1"
server_port = 9801
start=time.time()
# datas to plot graphs
'''
time_record = []
squished = []
squished_time = []
total_squish = 0
cwnd_record = []
requested_data = []
requeted_time = []
received_data_ = []
received_time = []
'''

# Create a UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Define the timeout for receiving a response (in seconds)
timeout = 0.02

def send_and_receive(request, expected_response_prefix):

    while True:
        udp_socket.sendto(request.encode(), (server_host, server_port))
        udp_socket.settimeout(timeout)
        try:
            response, _ = udp_socket.recvfrom(4096)
            response = response.decode()

            if response.startswith(expected_response_prefix):
                return response
            
        except socket.timeout:
            print(f"Timeout: No response received for request. Retrying...")
    
def findSize():
    request="SendSize\nReset\n\n"
    expected_response_prefix="Size: "
    response=send_and_receive(request,expected_response_prefix)
    return int(response.split(": ")[1])


# the number of bytes to receive
num_bytes = findSize()
print("Total size to be received : ",num_bytes)

# Create a buffer to store received data
data_buffer = [None] * (num_bytes // 1448 + 1)

All_offset=[]

# Define the maximum number of bytes per request
max_bytes_per_request = 1448


def SendRequest(cwnd,ai_factor,mi_factor):
    global total_squish
    requested_offset=set([])
    n=len(All_offset)
    count=min(int(cwnd),n)

    for i in range(count):

        num_to_receive=min(max_bytes_per_request,num_bytes-(All_offset[-1]))
        offset_request = f"Offset: {All_offset[-1]}\nNumBytes: {num_to_receive}\n\n"
        udp_socket.sendto(offset_request.encode(), (server_host, server_port))

        requested_offset.add(All_offset[-1])

        # requested_data.append(All_offset[-1])
        # requeted_time.append(time.time() - start)
        
        All_offset.pop()

    udp_socket.settimeout(timeout)
    responses=[]

    while True:
        time.sleep(0.004)
        if(count==0):
            cwnd=cwnd+(1/cwnd)
            break
        try:
            response, _ = udp_socket.recvfrom(4096)
            response = response.decode()
            if "Squished" in response:
                total_squish+=1
            # squished.append(total_squish)
            # squished_time.append(time.time() - start)

            if response.startswith("Offset: "):
                count-=1
                responses.append(response)

        except socket.timeout:

            cwnd=cwnd*mi_factor
            break

    for offset_response in responses:

        received_offset = int(offset_response.split("\n")[0].split(": ")[1])
        received_num_bytes = int(offset_response.split("\nNumBytes: ")[1].split("\n")[0])
        received_data = offset_response.split("\n\n", 1)[1].encode()

        requested_offset.discard(received_offset)
        data_buffer[received_offset // 1448] = (received_offset, received_num_bytes, received_data)
        # received_data_.append(received_offset)
        # received_time.append(time.time() - start)

    for off in requested_offset:
        All_offset.append(off)


    return cwnd


def RunAIMD():
    # Request and receive data in chunks
    mincwnd=1
    cwnd=1.0
    ai_factor=1
    mi_factor=0.5
    
    for offset in range(0, num_bytes, max_bytes_per_request):
        All_offset.append(offset)

    while len(All_offset):
        response=SendRequest(cwnd,ai_factor,mi_factor)
        cwnd=max(mincwnd,response)
        # cwnd_record.append(cwnd)
        # time_record.append(time.time()-start)


def CheckResult():
    # Assemble the data in the correct order
    assembled_data = bytearray(num_bytes)

    for data in data_buffer:
        if(data is None):
            print("Data is None")
            continue
        assembled_data[data[0]:data[0]+data[1]] = data[2]

    # Calculate MD5 hash of the received data
    md5_hash = hashlib.md5(assembled_data).hexdigest()

    # Submit the MD5 hash to the server
    submit_request = f"Submit: [2021CS10915_2021CS10103@nothing]\nMD5: {md5_hash}\n\n"

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

    udp_socket.close()

RunAIMD()
CheckResult()

# code for plots

# plt.plot(requeted_time, requested_data, label='Requested Offset', marker='o')
# plt.plot(received_time, received_data_, label='Received Offset', marker='x')
# plt.plot(time_record, cwnd_record, label = 'Burst Size', marker = 'o')
# plt.plot(squished_time, squished, label='No. of Squish', marker='x')
# plt.xlabel('Time')
# plt.ylabel('No. of Squish')
# plt.title('No. of times Squished over time')
# plt.legend()
# plt.show()
