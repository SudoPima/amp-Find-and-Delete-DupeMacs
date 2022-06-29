from collections import namedtuple
import configparser
import json
import csv
import requests
import datetime




def process_response_json(response_json, parsing_container):
    '''Process the decoded JSON blob from /v1/computers API Endpoint
    '''

    def process_guid_json(guid_json, parsing_container=parsing_container):
        '''Process the individual GUID entry
        '''
        connector_guid = guid_json.get('connector_guid')
        hostname = guid_json.get('hostname')
        last_seen = guid_json.get('last_seen')

        network_addresses = guid_json.get('network_addresses')

        parsing_container.setdefault(hostname, {'macs':[], 'mac_guids':{}, 'guid_last_seen':{}})
        parsing_container[hostname]['guid_last_seen'][connector_guid] = last_seen

        for network_interface in network_addresses:
            mac = network_interface.get('mac')
            # ip = network_interface.get('ip')
            # ipv6 = network_interface.get('ipv6')

            parsing_container[hostname]['macs'].append(mac)
            parsing_container[hostname]['mac_guids'].setdefault(mac, set())
            parsing_container[hostname]['mac_guids'][mac].add(connector_guid)

    for guid_entry in response_json['data']:
        if 'network_addresses' in guid_entry:
            process_guid_json(guid_entry)

def authenticate_and_process_requests():
    """
    """
    client_id = input("Enter the Client ID: ")
    api_key = input("Enter the API Key: ")

    parsed_computers = {}

    # Instantiate requestions session object
    amp_session = requests.session()
    amp_session.auth = (client_id, api_key)

    # URL to query AMP
    computers_url = 'https://api.amp.cisco.com/v1/computers'

    # Query the API
    response_json = get(amp_session, computers_url)

    # Print the total number of GUIDs found
    total_guids = response_json['metadata']['results']['total']
    print('GUIDs found in environment: {}'.format(total_guids))

    # Process the returned JSON
    process_response_json(response_json, parsed_computers)

    # Check if there are more pages and repeat
    while 'next' in response_json['metadata']['links']:
        next_url = response_json['metadata']['links']['next']
        response_json = get(amp_session, next_url)
        index = response_json['metadata']['results']['index']
        print('Processing index: {}'.format(index))
        process_response_json(response_json, parsed_computers)

    return parsed_computers

def analyze_parsed_computers(parsed_data, duplicate_container):
    ''' Analyzes the parsed_computers container and looks at how many times each MAC Address
        appears for a given hostname. If the same MAC appears more than once the host is
        added to  the duplicate_computers container.
    '''
    for hostname, data in parsed_data.items():
        macs = data['macs']
        for mac in macs:
            if macs.count(mac) > 1:
                for guid in data['mac_guids'][mac]:
                    host_tuple = namedtuple('host_tuple', ['hostname', 'guid', 'last_seen'])
                    last_seen = parsed_data[hostname]['guid_last_seen'][guid]
                    duplicate_container.add(host_tuple(hostname, guid, last_seen))

def format_duplicate_container(duplicate_container):
    ''' Processes the duplicate_computers container and formats the output based on hostname
        Returns a dictionary that can be saved to disk as JSON
    '''
    hosts = {}

    for host_tuple in sorted(duplicate_container):
        hostname = host_tuple.hostname
        guid = host_tuple.guid
        last_seen = host_tuple.last_seen
        hosts.setdefault(hostname, {})
        hosts[hostname][last_seen] = guid
    return hosts

def print_duplicate_output(formatted_duplicate_container):
    '''Process formatted_duplicate_computers and print duplicate stats by host name
    '''
    print('Hosts with duplicate GUIDs found: {}'.format(len(formatted_duplicate_container)))
    for host, dupes in formatted_duplicate_container.items():
        print('\n{} has {} duplicates'.format(host, len(dupes)))
        for last_seen, guid  in dupes.items():
            print('  {} - {}'.format(last_seen, guid))

def write_duplicate_json(formatted_duplicate_container):
    '''Write formatted_duplicate_computers to disk as JSON
    '''
    with open('duplicate_hosts.json', 'w') as file:
        file.write(json.dumps(formatted_duplicate_container))

"""
def write_parsed_computers(parsed_data):
    ''' Converts the Set of unique MAC Addresses in the parsed_computers container
        Without this conversion it can not be written to disk as JSON
        Writes parsed computers to disk as JSON
    '''
    for _, data in parsed_data.items():
        for key, _ in data['mac_guids'].items():
            data['mac_guids'][key] = list(data['mac_guids'][key])

    with open('parsed_computers.json', 'w') as file:
        file.write(json.dumps(parsed_data))
"""

def extract_target_guids(hosts):
    """ Iterate through the hosts and target the duplicates that have the 
        oldest last_seen times.
    """
    # for storing the guids of the oldest duplicates
    target_guids = []

    for host, data in hosts.items():
        # Store the times stamps for every guid in the host
        time_stamps = []
        # safe measure, ensures only getting objects with duplicates
        if (len(data) > 1):
            for last_seen, guid in sorted(data.items()):
                # add timestamp to list
                time_stamps.append(last_seen)
            # remove the largest time stamp, eveything else will be deleted
            time_stamps.remove(max(time_stamps))
            for i in time_stamps:
                # add the guids for the corresponding time stamp to our target list
                target_guids.append(hosts[host][i])

    return target_guids

def delete_dupe_guids(session, computers_url, guid_list):
    """ Iterate through  the target list of duplicate computers and
        delte them by connector_guid
    """
    for guid in guid_list:
        url = computers_url + '{}'.format(guid)
        response = session.delete(url)
        response_json = response.json()

        if response.status_code == 200 and response_json['data']['deleted']:
            print('Succesfully deleted {}'.format(guid))
        else:
            print('Something went wrong deleting: {}'.format(guid))         

def get(session, url):
    '''HTTP GET the URL and return the decoded JSON
    '''
    response = session.get(url)
    response_json = response.json()
    return response_json

def main():
    '''The main logic of the script
    '''

    # Containers for data
    parsed_computers = {}
    duplicate_computers = set()
    target_guids = []

    # iterate through parsed computers and find duplicate macs
    parsed_computers = authenticate_and_process_requests()
    analyze_parsed_computers(parsed_computers, duplicate_computers)

    # Clean up the duplicate objects
    hosts = format_duplicate_container(duplicate_computers)
    # display all hosts that have duplicates in the environment
    # display hosts: last_seen time stamp and Connector_GUID
    print_duplicate_output(hosts)
    
    # iterate through the cleaned up objects and extract the oldest objects connector guids for deletion
    target_guids = extract_target_guids(hosts)
    for i in target_guids:
        print(i)
    # Iterates through the guid list and deletes the computers
    #delete_dupe_guids(amp_session, computers_url, target_guids)


if __name__ == "__main__":
    main()