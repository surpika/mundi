#!/usr/bin/env python3
"""
Arbitrator Case Finder - Search for arbitrators and their cases in ICSID & PCA API

This script allows users to search for arbitrators by name and find the first 10 cases they were involved in.
"""

import requests
import argparse
import sys
import json
import io
import locale

def search_arbitrator_cases(api_key, name, output_file=None):
    """
    Search for an arbitrator by name and find up to 10 of their cases.
    
    Args:
        api_key (str): API key for authentication
        name (str): Name of the arbitrator to search for
        output_file (str, optional): File to save results in JSON format
    """
    base_url = "https://api.jusmundi.com/stanford"
    headers = {
        "X-API-Key": api_key,
        "Accept": "application/json"
    }
    
    print(f"Searching for individual: '{name}'")
    
    # Step 1: Search for decisions with individuals matching the name
    search_url = f"{base_url}/decisions"
    params = {
        "search": name,
        "fields": "individuals.name",  # Focus search on individual names
        "count": 10,
        "page": 1,
        "include": "individuals"  # Include individuals in the response
    }
    
    try:
        # Find matching individuals
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        search_data = response.json()
        
        # Extract individuals matching the name
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
                                "details": individual_data.get("data", {}).get("attributes", {}),
                                "cases": []
                            }
        
        if not individuals:
            print(f"No individuals found matching '{name}'")
            return
            
        # Step 2: For each individual, find up to 10 decisions they're involved in
        for individual_id, individual in individuals.items():
            print(f"\nFinding cases for: {individual['name']} (ID: {individual_id})")
            
            # Get decisions (paginated)
            page = 1
            case_ids = set()  # Use set to avoid duplicates
            max_cases = 10    # Limit to 10 cases per arbitrator
            
            while len(case_ids) < max_cases:
                decisions_url = f"{base_url}/decisions"
                params = {
                    "search": individual["name"],
                    "fields": "individuals.name",
                    "include": "cases",  # Include case information
                    "page": page,
                    "count": 10
                }
                
                decisions_response = requests.get(decisions_url, headers=headers, params=params)
                
                if decisions_response.status_code != 200:
                    break
                    
                decisions_data = decisions_response.json()
                decisions = decisions_data.get("data", [])
                
                if not decisions:
                    break
                
                # Extract case IDs from included data
                if "included" in decisions_data:
                    for item in decisions_data["included"]:
                        if item["type"] == "cases":
                            case_ids.add(item["id"])

                            print(f"Found case: {item['id']}", flush=True)

                            # Break once we have 10 cases
                            if len(case_ids) >= max_cases:
                                break
                
                # Check if we have enough cases or if there are more pages
                if len(case_ids) >= max_cases or page >= decisions_data.get("meta", {}).get("totalPages", 0):
                    break
                    
                page += 1
            
            # Step 3: Get details for each case (limited to 10)
            for i, case_id in enumerate(list(case_ids)[:max_cases]):
                case_url = f"{base_url}/cases/{case_id}"
                case_response = requests.get(case_url, headers=headers)
                
                if case_response.status_code == 200:
                    case_data = case_response.json().get("data", {})
                    case_attributes = case_data.get("attributes", {})
                    
                    individual["cases"].append({
                        "id": case_id,
                        "title": case_attributes.get("title", "Untitled Case"),
                        "reference": case_attributes.get("reference", ""),
                        "status": case_attributes.get("status", ""),
                        "startDate": case_attributes.get("startDate", ""),
                        "endDate": case_attributes.get("endDate", ""),
                        "organization": case_attributes.get("organization", "")
                    })
        
        # Step 4: Display and return results
        for idx, (_, individual) in enumerate(individuals.items(), 1):
            print(f"\nArbitrator {idx}:")
            print(f"ID: {individual['id']}")
            print(f"Name: {individual['name']}")
            
            # Display individual details
            if individual['details']:
                print("Details:")
                for key, value in individual['details'].items():
                    if value:  # Only show non-empty values
                        print(f"  {key}: {value}")
            
            # Display cases
            cases = individual.get("cases", [])
            if cases:
                print(f"\nInvolved in {len(cases)} case(s) (Limited to first 10):")
                for i, case in enumerate(cases, 1):
                    print(f"\nCase {i}:")
                    print(f"  Title: {case['title']}")
                    print(f"  ID: {case['id']}")
                    if case["reference"]:
                        print(f"  Reference: {case['reference']}")
                    if case["organization"]:
                        print(f"  Organization: {case['organization']}")
                    if case["status"]:
                        print(f"  Status: {case['status']}")
                    if case["startDate"]:
                        print(f"  Start Date: {case['startDate']}")
                    if case["endDate"]:
                        print(f"  End Date: {case['endDate']}")
            else:
                print("\nNo cases found for this individual")
            
            print("-" * 60)
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(list(individuals.values()), f, indent=2)
            print(f"Results saved to {output_file}")
            
    except requests.RequestException as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

def main():
    # Fix potential encoding issues by setting stdout to use UTF-8
    # This handles special characters in names and text content
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    parser = argparse.ArgumentParser(description="Search for arbitrators and their cases in ICSID & PCA API")
    parser.add_argument("--api-key", required=True, help="API Key for authentication")
    parser.add_argument("--name", required=True, help="Name of the arbitrator to search for")
    parser.add_argument("--output", help="Output file to save results (JSON format)")
    
    args = parser.parse_args()
    
    search_arbitrator_cases(args.api_key, args.name, args.output)

if __name__ == "__main__":
    main()