#!/usr/bin/env python3
"""
Individual Finder - Search for individuals by name in ICSID & PCA cases API

This script allows users to search for individuals by name directly.
"""

import requests
import argparse
import sys
import json

def search_individual(api_key, name, output_file=None):
    """
    Search for an individual by name in the ICSID & PCA Cases API.
    
    Args:
        api_key (str): API key for authentication
        name (str): Name of the individual to search for
        output_file (str, optional): File to save results in JSON format
    """
    base_url = "https://api.jusmundi.com/stanford"
    headers = {
        "X-API-Key": api_key,
        "Accept": "application/json"
    }
    
    print(f"Searching for individual: '{name}'")
    
    # Search for decisions with individuals matching the name
    search_url = f"{base_url}/decisions"
    params = {
        "search": name,
        "fields": "individuals.name",  # Focus search on individual names
        "count": 10,
        "page": 1,
        "include": "individuals"  # Include individuals in the response
    }
    
    try:
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        search_data = response.json()
        
        # Extract unique individuals from included data
        individuals = {}
        
        if "included" in search_data:
            for item in search_data["included"]:
                if item["type"] == "individuals":
                    individual_id = item["id"]
                    individual_name = item["attributes"].get("name", "")
                    
                    # Case-insensitive substring match
                    if name.lower() in individual_name.lower():
                        # Get full individual details
                        individual_url = f"{base_url}/individuals/{individual_id}"
                        individual_response = requests.get(individual_url, headers=headers)
                        
                        if individual_response.status_code == 200:
                            individual_data = individual_response.json()
                            individuals[individual_id] = {
                                "id": individual_id,
                                "name": individual_name,
                                "details": individual_data.get("data", {}).get("attributes", {})
                            }
        
        # Display and return results
        if individuals:
            print(f"\nFound {len(individuals)} individual(s) matching '{name}':\n")
            
            for idx, (_, individual) in enumerate(individuals.items(), 1):
                print(f"Individual {idx}:")
                print(f"ID: {individual['id']}")
                print(f"Name: {individual['name']}")
                
                # Display additional details
                if individual['details']:
                    print("Details:")
                    for key, value in individual['details'].items():
                        if value:  # Only show non-empty values
                            print(f"  {key}: {value}")
                
                print("-" * 50)
            
            # Save to file if requested
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(list(individuals.values()), f, indent=2)
                print(f"Results saved to {output_file}")
                
        else:
            print(f"No individuals found matching '{name}'")
            
    except requests.RequestException as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Search for an individual by name in ICSID & PCA cases")
    parser.add_argument("--api-key", required=True, help="API Key for authentication")
    parser.add_argument("--name", required=True, help="Name of the individual to search for")
    parser.add_argument("--output", help="Output file to save results (JSON format)")
    
    args = parser.parse_args()
    
    search_individual(args.api_key, args.name, args.output)

if __name__ == "__main__":
    main()