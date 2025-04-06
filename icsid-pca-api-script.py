#!/usr/bin/env python3
import requests
import json
import sys
import argparse
from typing import Dict, List, Any, Optional, Set, Tuple

def main():
    parser = argparse.ArgumentParser(description="Fetch and format ICSID & PCA case data")
    parser.add_argument("--api-key", required=True, help="API key for authentication")
    parser.add_argument("--case-id", type=int, help="Specific case ID to retrieve (defaults to first available)")
    parser.add_argument("--arbitrator", type=str, help="Search for arbitrator by name")
    args = parser.parse_args()
    
    # API configuration
    base_url = "https://api.jusmundi.com/stanford"
    headers = {
        "X-API-Key": args.api_key,
        "Accept": "application/json"
    }
    
    try:
        # If arbitrator name is provided, search for arbitrator and related cases
        if args.arbitrator:
            print(f"Searching for arbitrator: {args.arbitrator}")
            arbitrator_info, arbitrator_cases = search_arbitrator_with_cases(base_url, headers, args.arbitrator)
            
            if not arbitrator_info:
                print(f"No arbitrator found with name containing '{args.arbitrator}'")
                sys.exit(0)
                
            # Format and print the results
            print("\nArbitrator Information:")
            print(json.dumps(arbitrator_info, indent=2))
            
            print(f"\nCases involving {arbitrator_info.get('attributes', {}).get('name', 'this arbitrator')}:")
            for idx, case_info in enumerate(arbitrator_cases, 1):
                print(f"\nCase {idx}:")
                print(json.dumps(case_info, indent=2))
            
            print(f"\nTotal cases found: {len(arbitrator_cases)}")
            sys.exit(0)
        
        # Original functionality for specific case retrieval
        if args.case_id:
            case_id = args.case_id
            print(f"Fetching case ID: {case_id}")
            case = get_case_by_id(base_url, headers, case_id)
        else:
            print("Fetching first available case...")
            case = get_first_case(base_url, headers)
            case_id = int(case["id"])
            print(f"Using case ID: {case_id}")
        
        # Get case details
        print("Fetching case details...")
        case_parties = get_case_parties(base_url, headers, case_id)
        case_decisions = get_case_decisions(base_url, headers, case_id)
        
        # Get individuals from decisions
        print("Fetching individuals involved in decisions...")
        individuals = []
        for decision in case_decisions:
            decision_id = int(decision["id"])
            decision_individuals = get_decision_individuals(base_url, headers, decision_id)
            individuals.extend(decision_individuals)
        
        # Print formatted result
        print("case:")
        print(json.dumps(case))
        print("case_parties:")
        print(json.dumps(case_parties))
        print("case_decisions:")
        print(json.dumps(case_decisions))
        print("individuals:")
        print(json.dumps(individuals))
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def search_arbitrator_with_cases(base_url: str, headers: Dict[str, str], arbitrator_name: str) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Search for an arbitrator by name and return their information along with related cases.
    Returns a tuple of (arbitrator_info, related_cases).
    """
    # First, find decisions related to the arbitrator name
    url = f"{base_url}/decisions"
    params = {
        "search": arbitrator_name,
        "include": "cases",
        "count": 10  # Adjust as needed
    }
    
    try:
        print(f"Searching for decisions involving '{arbitrator_name}'...")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        decisions = data.get("data", [])
        included = data.get("included", [])
        
        # No decisions found
        if not decisions:
            return None, []
        
        # Collect unique case IDs from decision relationships
        case_ids = set()
        for decision in decisions:
            relationships = decision.get("relationships", {})
            case_data = relationships.get("cases", {}).get("data", [])
            for case_ref in case_data:
                if case_ref.get("id"):
                    case_ids.add(case_ref.get("id"))
        
        # Now for each decision, find the arbitrator
        arbitrator_info = None
        related_cases = []
        
        for decision in decisions:
            # Ensure decision is a dictionary
            if not isinstance(decision, dict):
                print(f"Warning: Expected decision to be a dictionary, got {type(decision)}")
                continue
                
            decision_id = decision.get("id")
            if not decision_id:
                continue
                
            # Get individuals involved in this decision
            individuals = get_decision_individuals(base_url, headers, int(decision_id))
            
            # Ensure individuals is a list
            if not isinstance(individuals, list):
                print(f"Warning: Expected individuals to be a list, got {type(individuals)}")
                continue
                
            # Look for arbitrators
            for individual in individuals:
                # Ensure individual is a dictionary
                if not isinstance(individual, dict):
                    print(f"Warning: Expected individual to be a dictionary, got {type(individual)}")
                    continue
                    
                attributes = individual.get("attributes", {})
                name = attributes.get("name", "")
                role = attributes.get("role", "").lower()
                
                # Check if this individual's name matches our search and they're an arbitrator
                if (arbitrator_name.lower() in name.lower() and 
                    any(r in role for r in ["arbitrator", "judge", "tribunal", "president"])):
                    arbitrator_info = individual
                    break
            
            if arbitrator_info:
                break
        
        # If we still haven't found a clear arbitrator, use the first individual that matches by name
        if not arbitrator_info:
            for decision in decisions:
                # Ensure decision is a dictionary
                if not isinstance(decision, dict):
                    continue
                    
                decision_id = decision.get("id")
                if not decision_id:
                    continue
                    
                individuals = get_decision_individuals(base_url, headers, int(decision_id))
                
                # Ensure individuals is a list
                if not isinstance(individuals, list):
                    continue
                    
                for individual in individuals:
                    # Ensure individual is a dictionary
                    if not isinstance(individual, dict):
                        continue
                        
                    attributes = individual.get("attributes", {})
                    name = attributes.get("name", "")
                    
                    if arbitrator_name.lower() in name.lower():
                        arbitrator_info = individual
                        break
                
                if arbitrator_info:
                    break
        
        # If we still haven't found the arbitrator, return empty results
        if not arbitrator_info:
            return None, []
        
        # For each case ID, get detailed information
        for case_id in case_ids:
            try:
                # Convert case_id to int if it's a string
                case_id_int = int(case_id) if isinstance(case_id, str) else case_id
                
                case_details = get_case_by_id(base_url, headers, case_id_int)
                parties = get_case_parties(base_url, headers, case_id_int)
                case_decisions = get_case_decisions(base_url, headers, case_id_int)
                
                # Ensure case_decisions is a list
                if not isinstance(case_decisions, list):
                    print(f"Warning: Expected case_decisions to be a list, got {type(case_decisions)}")
                    continue
                
                # Filter to only include decisions where our arbitrator is involved
                arbitrator_decisions = []
                for decision in case_decisions:
                    # Ensure decision is a dictionary
                    if not isinstance(decision, dict):
                        continue
                        
                    decision_id = decision.get("id")
                    if not decision_id:
                        continue
                    
                    # Convert decision_id to int if it's a string    
                    decision_id_int = int(decision_id) if isinstance(decision_id, str) else decision_id
                    
                    decision_individuals = get_decision_individuals(base_url, headers, decision_id_int)
                    
                    # Ensure decision_individuals is a list
                    if not isinstance(decision_individuals, list):
                        continue
                    
                    # Check if arbitrator is in this decision
                    arbitrator_in_decision = False
                    arbitrator_role_in_decision = None
                    
                    # Ensure arbitrator_info is a dictionary
                    if not isinstance(arbitrator_info, dict):
                        continue
                        
                    for individual in decision_individuals:
                        # Ensure individual is a dictionary
                        if not isinstance(individual, dict):
                            continue
                            
                        if individual.get("id") == arbitrator_info.get("id"):
                            arbitrator_in_decision = True
                            arbitrator_role_in_decision = individual.get("attributes", {}).get("role")
                            break
                    
                    if arbitrator_in_decision:
                        # Add arbitrator's role to the decision
                        decision_with_role = decision.copy()
                        if "arbitrator_role" not in decision_with_role:
                            decision_with_role["arbitrator_role"] = arbitrator_role_in_decision
                        arbitrator_decisions.append(decision_with_role)
                
                # Only include case if arbitrator is involved in at least one decision
                if arbitrator_decisions:
                    # Extract key case information
                    # Ensure case_details is a dictionary
                    if not isinstance(case_details, dict):
                        continue
                        
                    case_title = case_details.get("attributes", {}).get("title", "Untitled Case")
                    case_reference = case_details.get("attributes", {}).get("reference", "No Reference")
                    case_year = case_details.get("attributes", {}).get("year")
                    
                    # Get information about parties (claimant and respondent)
                    claimant = find_party_by_role(parties, "claimant")
                    respondent = find_party_by_role(parties, "respondent")
                    
                    claimant_name = get_attribute(claimant, "name", "Unknown Claimant")
                    respondent_name = get_attribute(respondent, "name", "Unknown Respondent")
                    
                    case_info = {
                        "id": case_id,
                        "title": case_title,
                        "reference": case_reference,
                        "year": case_year,
                        "claimant": claimant_name,
                        "respondent": respondent_name,
                        "full_case_details": case_details,
                        "parties": parties,
                        "arbitrator_decisions": arbitrator_decisions,
                    }
                    related_cases.append(case_info)
            except Exception as e:
                print(f"Warning: Error processing case {case_id}: {e}", file=sys.stderr)
        
        # Enhance arbitrator info with case count and other metadata
        if arbitrator_info and "attributes" in arbitrator_info:
            arbitrator_info["attributes"]["total_cases_found"] = len(related_cases)
            # Add additional arbitrator metadata if available
            
        return arbitrator_info, related_cases
    
    except Exception as e:
        print(f"Error searching for arbitrator: {e}", file=sys.stderr)
        return None, []

def get_case_by_id(base_url: str, headers: Dict[str, str], case_id: int) -> Dict[str, Any]:
    """Get a specific case by ID."""
    url = f"{base_url}/cases/{case_id}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    data = response.json().get("data")
    if not data:
        raise ValueError(f"Case with ID {case_id} not found")
    
    return data

def get_first_case(base_url: str, headers: Dict[str, str]) -> Dict[str, Any]:
    """Get the first available case."""
    url = f"{base_url}/cases"
    params = {"page": 1, "count": 1}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    data = response.json().get("data", [])
    if not data:
        raise ValueError("No cases found")
    
    return data[0]

def get_case_parties(base_url: str, headers: Dict[str, str], case_id: int) -> List[Dict[str, Any]]:
    """Get parties for a specific case."""
    url = f"{base_url}/cases/{case_id}/parties"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.json().get("data", [])

def get_case_decisions(base_url: str, headers: Dict[str, str], case_id: int) -> List[Dict[str, Any]]:
    """Get decisions for a specific case."""
    url = f"{base_url}/cases/{case_id}/decisions"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.json().get("data", [])

def get_decision_individuals(base_url: str, headers: Dict[str, str], decision_id: int) -> List[Dict[str, Any]]:
    """Get individuals associated with a specific decision."""
    url = f"{base_url}/decisions/{decision_id}/individuals"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse the JSON response
        response_json = response.json()
        
        # Ensure the response is a dictionary
        if not isinstance(response_json, dict):
            print(f"Warning: Expected response JSON to be a dictionary, got {type(response_json)}", file=sys.stderr)
            return []
            
        # Get the data field and ensure it's a list
        data = response_json.get("data", [])
        if not isinstance(data, list):
            print(f"Warning: Expected data to be a list, got {type(data)}", file=sys.stderr)
            return []
            
        return data
    except Exception as e:
        print(f"Warning: Could not fetch individuals for decision {decision_id}: {e}", file=sys.stderr)
        return []

def find_arbitrator(individuals: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Find an arbitrator among individuals."""
    for individual in individuals:
        role = get_attribute(individual, "role", "").lower()
        if any(r in role for r in ["arbitrator", "judge", "tribunal", "president"]):
            return individual
    return None

def find_party_by_role(parties: List[Dict[str, Any]], role_keyword: str) -> Optional[Dict[str, Any]]:
    """Find a party by a role keyword."""
    for party in parties:
        role = get_attribute(party, "role", "").lower()
        if role_keyword.lower() in role:
            return party
    return None

def get_attribute(obj: Optional[Dict[str, Any]], attr_name: str, default: Any = None) -> Any:
    """Safely get an attribute from object's attributes or return default."""
    if not obj:
        return default
    
    attributes = obj.get("attributes", {})
    return attributes.get(attr_name, default)

if __name__ == "__main__":
    main()