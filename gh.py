import pandas as pd
import json
import subprocess
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


#replace \s+h with ,h in vs code with regex enabled
with open("owners.txt", "r") as file:
    owners = [line.strip() for line in file if "," in line]

def find_owner(repo):

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
    repo_urls = []
    page = 1
    per_page = 100  # Adjust per_page value as needed

    while True:
        response = requests.get(url, auth=(username, password), params={"page": page, "per_page": per_page})
        if response.status_code == 200:
            repos = response.json()
            if len(repos) == 0:
                break

            repo_urls.extend([f"https://github.com/{org_name}/{repo['name']}" for repo in repos])
            page += 1
        else:
            print("Error retrieving repositories.")
            return []

    return repo_urls

# Example usage
org_name = "orgname"
username = "mmajeed@company.com"
password = "ghp_aoqj2eB1SSv************"
repolist = get_github_org_repolist(org_name, username, password)
print(f"here is  {repolist}")
print(len(repolist))
for rep in repolist:
    print(rep)


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
        characters_to_mask = len(raw) // 2
        masked_raw = raw[:-characters_to_mask] + '*' * characters_to_mask
        
        # Append the data as a list
        data.append([Owner, email, repository, file, commit_url, line_number, secret_location, timestamp, detector_name, Verified, raw, masked_raw])
    
    return data

# repofile = open('repolist.txt','r')
# repolist = repofile.readlines()


all_data = []

max_threads = 10

# Create a thread pool
with ThreadPoolExecutor(max_workers=max_threads) as executor:
    # Submit each repository URL for processing
    futures = [executor.submit(getsecrets, repo.strip('\n')) for repo in repolist]

    # Retrieve the results from the completed futures
    for future in as_completed(futures):
        data = future.result()
        all_data.extend(data)

# Create a pandas DataFrame with the data
df = pd.DataFrame(all_data, columns=['Owner', 'Offender', 'Repository', 'File_Location', 'Commit_URL', 'Line_Number',
                                     'Secret_Location', 'TimeStamp', 'Detector_Name', 'Verified', 'Raw', 'Masked_Raw'])

# Save the DataFrame to an Excel file
df.to_excel('output.xlsx', index=False)
