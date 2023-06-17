import pandas as pd
import json
import subprocess
import requests



#replace \s+h with ,h in vs code with regex enabled
with open("owners.txt", "r") as file:
    owners = [line.strip() for line in file if "," in line]

def find_owner(repo):
    # Read the owners.txt file

# Iterate over the lines and search for the repository URL
    for owner in owners:
        parts = owner.split(",")
        if len(parts) == 2:
            owner_email, stored_repo_url  = parts
            print(owner_email)
            print(f"18 {repo.strip()}")
            print(f"19 {stored_repo_url.strip()}")

            if repo.strip() == stored_repo_url.strip():
                print("we have found it")
                owner_email = owner_email.strip()
                print(owner_email)
                print(f"Owner of {repo.strip()}: {owner_email}")
                break
    
    else:
        owner_email="Unknown"
        print(f"Repository URL {repo} not found in the file.")
    return owner_email



def get_github_org_repolist(org_name, username, password):
    url = f"https://api.github.com/orgs/{org_name}/repos"
    response = requests.get(url, auth=(username, password))
    if response.status_code == 200:
        repos = response.json()
        repo_urls = [f"https://github.com/{org_name}/{repo['name']}" for repo in repos]
        return repo_urls
    else:
        print("Error retrieving repositories.")
        return []

# Example usage
org_name = "org_here"
username = "org_email"
password = "api_key"
repolist = get_github_org_repolist(org_name, username, password)


def getsecrets(repo):
    raw_text = subprocess.run(['trufflehog', 'git', '--json', repo], capture_output=True, text=True)
    output_list = []

    # Split the raw_text by newline character to separate each JSON
    json_strings = raw_text.stdout.split("\n")

    # Iterate over each JSON string
    for json_string in json_strings:
        # Skip any empty lines
        if json_string.strip() == "":
            continue
        
        # Parse the JSON string and add it to the list
        json_data = json.loads(json_string)
        print(json_data)
    
        output_list.append(json_data)

    # Extract the required data from each JSON
    data = []
    owner_email= find_owner(repo)
    for item in output_list:
        email = item['SourceMetadata']['Data']['Git']['email']
        repository = item['SourceMetadata']['Data']['Git']['repository']
        file = item['SourceMetadata']['Data']['Git']['file']
        commit = item['SourceMetadata']['Data']['Git']['commit']
        commit_url = f"{repository}/commit/{commit}"
        line_number = item['SourceMetadata']['Data']['Git']['line']
        secret_location =  f"{repository}/blob/{commit}/{file}#L{line_number}"
        timestamp = item['SourceMetadata']['Data']['Git']['timestamp']
        detector_name = item['DetectorName']
        Verified = item['Verified']
        Owner = owner_email
        raw = item['Raw']
        
        # Append the data as a list
        data.append([Owner, email, repository, file, commit_url, line_number, secret_location, timestamp, detector_name, Verified, raw])
    
    return data

repofile = open('repolist.txt','r')
repolist = repofile.readlines()


all_data = []

for repo in repolist:
    print(repo)
    data = getsecrets(repo.strip('\n'))
    #print(f"45 {data}")
    all_data.extend(data)
    #print(f" 47 {all_data}")

# Create a pandas DataFrame with the data
df = pd.DataFrame(all_data, columns=['Owner','email', 'repository', 'file', 'commit_url', 'line_number', 'secret_location' ,'timestamp', 'detector_name','Verified','Raw'])

# Save the DataFrame to an Excel file
df.to_excel('output.xlsx', index=False)

