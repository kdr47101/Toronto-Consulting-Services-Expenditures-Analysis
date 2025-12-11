import requests
import os

def fetch_consulting_data():
    # Toronto Open Data is stored in a CKAN instance. It's APIs are documented here:
    # https://docs.ckan.org/en/latest/api/
    
    # To hit our API, you'll be making requests to:
    base_url = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
    
    # Datasets are called "packages". Each package can contain many "resources"
    # To retrieve the metadata for this package and its resources, use the package name in this page's URL:
    url = base_url + "/api/3/action/package_show"
    params = { "id": "consulting-services-expenditures"}
    package = requests.get(url, params = params).json()
    
    # Ensure the output directory exists
    output_dir = "data/raw"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # To get resource data:
    for idx, resource in enumerate(package["result"]["resources"]):
        
        # Filter for resources related to 2017 to 2024
        resource_name = resource["name"]
        if not any(str(year) in resource_name for year in range(2017, 2025)):
            continue

        print(f"Processing: {resource_name}")
        
        download_url = resource["url"]

        # To get metadata for non datastore_active resources:
        if not resource["datastore_active"]:
            url = base_url + "/api/3/action/resource_show?id=" + resource["id"]
            resource_metadata = requests.get(url).json()
            # From here, you can use the "url" attribute to download this file
            if resource_metadata.get("success"):
                download_url = resource_metadata["result"]["url"]
        
        # Download the file
        if download_url:
            try:
                response = requests.get(download_url)
                response.raise_for_status()
                
                # Construct a safe filename
                safe_name = "".join([c for c in resource_name if c.isalnum() or c in (' ', '-', '_')]).strip()
                if "." not in safe_name:
                    ext = resource.get("format", "csv").lower()
                    safe_name = f"{safe_name}.{ext}"
                
                file_path = os.path.join(output_dir, safe_name)
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"Downloaded to {file_path}")
            except Exception as e:
                print(f"Failed to download {resource_name}: {e}")

if __name__ == "__main__":
    fetch_consulting_data()