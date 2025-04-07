import os
import json
from openai import OpenAI
import time
from datetime import datetime

class ArbitratorInfoCollector:
    def __init__(self, api_key=None):
        """Initialize the information collector with OpenAI API key."""
        # Use provided API key or get from environment variable
        self.api_key = ""
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Either pass it directly or set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        
    def collect_information(self, arbitrator_data, detailed=True):
        """
        Collect comprehensive information about the arbitrator without making severity judgments.
        
        Args:
            arbitrator_data (dict): Dictionary containing arbitrator information
                                   including at minimum their name
            detailed (bool): Whether to collect highly detailed information
        
        Returns:
            dict: Comprehensive information about the arbitrator
        """
        # Extract basic info from the data
        name = arbitrator_data.get('name')
        if not name:
            raise ValueError("Arbitrator name is required")
            
        # Construct a thorough prompt for information gathering
        system_prompt = """
        You are an expert legal researcher specializing in gathering comprehensive information about arbitrators.
        Your task is to provide EXTENSIVE, DETAILED information that could be relevant to conflict of interest analysis,
        without making any judgments about severity or relevance. Include ALL potentially relevant information.
        
        Explore thoroughly and report on:
        
        1. Professional background:
           - Current and previous employers, positions, and duration
           - Law firms or organizations they've been affiliated with
           - Client relationships throughout their career
           - Notable cases and rulings with specific details
           - Professional reputation and any controversies
        
        2. Financial interests:
           - Known investments, shareholdings, board positions
           - Financial relationships with companies or organizations
           - Compensation from speaking engagements, consulting, etc.
           - Real estate or property holdings if publicly known
        
        3. Personal connections:
           - Family members in relevant industries or positions
           - Known friendships or relationships with key figures
           - Social circles and elite membership organizations
           - University connections and alumni networks
        
        4. Publications, speeches and public positions:
           - Academic papers, books, and their positions
           - Public statements on relevant topics
           - Quotes in media that reveal potential biases or views
           - Conference presentations and their content
        
        5. Institutional affiliations:
           - Professional memberships
           - Non-profit board positions
           - Political affiliations or donations
           - Religious affiliations if publicly known
        
        6. Geographic and cultural considerations:
           - Regional biases or connections
           - Cultural factors that could influence decision-making
           - International connections or experiences
        
        7. Digital presence:
           - Social media activity and statements
           - Online forums or communities
           - Digital footprint analysis
        
        Be extremely detailed and comprehensive. Include EVERYTHING you find, even if it seems minor.
        DO NOT filter information based on perceived relevance - include all data points.
        """
        
        # Construct the user message with arbitrator info
        user_message = f"Please gather ALL available information about this arbitrator that could be relevant to conflict of interest analysis. Be extremely thorough and include EVERYTHING:\n\n{json.dumps(arbitrator_data, indent=2)}"
        
        try:
            # Call the OpenAI API with higher token limit for more detailed response
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using a capable model for analysis
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,  # Higher temperature for more creative and comprehensive exploration
                max_tokens=4000 if detailed else 2000  # Higher token limit for detailed responses
            )
            
            # Parse the response
            information = response.choices[0].message.content
            
            # Store the raw information
            raw_data = {
                "timestamp": datetime.now().isoformat(),
                "arbitrator_name": name,
                "raw_information": information
            }
            
            return raw_data
            
        except Exception as e:
            return {"error": str(e)}
    
    def web_research(self, arbitrator_data, research_depth="extensive"):
        """
        Conduct extensive web research on the arbitrator to gather all possible information.
        Uses OpenAI's browsing capability for comprehensive data collection.
        
        Args:
            arbitrator_data (dict): Dictionary containing arbitrator information
            research_depth (str): Level of research depth ("basic", "standard", "extensive")
        
        Returns:
            dict: Comprehensive information from web sources
        """
        name = arbitrator_data.get('name')
        if not name:
            raise ValueError("Arbitrator name is required")
        
        # Additional context from arbitrator_data
        context = ""
        for key, value in arbitrator_data.items():
            if key != "name":
                context += f"\n- {key}: {value}"
        
        # Configure research depth
        tokens = {"basic": 2000, "standard": 3500, "extensive": 5000}
        max_tokens = tokens.get(research_depth, 3500)
        
        # Construct the prompt with instructions for exhaustive research
        system_prompt = """
        You are an expert legal researcher with expertise in gathering information about arbitrators.
        Your task is to conduct EXHAUSTIVE web research and provide ALL information you can find about
        the arbitrator. Do not filter or judge the information - include EVERYTHING that could potentially
        be relevant to a conflict of interest analysis.
        
        Use web browsing to search for and report on:
        1. Their complete professional history and connections
        2. All known business relationships and affiliations
        3. Financial interests of any kind
        4. Personal relationships and connections
        5. All published work, speeches, and public statements
        6. Media mentions and appearances
        7. Social media presence and activity
        8. Professional reputation and any controversies
        9. Political activities or donations
        10. Membership in organizations, clubs, or associations
        
        For EVERY piece of information you find, include:
        - The specific information in detail
        - The exact source (URL, publication, etc.)
        - The date of the information if available
        
        DO NOT summarize or condense information. Include ALL raw data you find during your research.
        Be methodical and thorough in your search approach. Use multiple search queries to find different
        types of information.
        """
        
        try:
            # Call the OpenAI API with the browsing capability for extensive research
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",  # Ensure this is a model with browsing capability
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Conduct exhaustive research on arbitrator: {name}{context}\n\nFind ALL possible information. Do not filter or judge relevance - include EVERYTHING. Be methodical and thorough."}
                ],
                temperature=0.7,  # Higher temperature for more creative research
                max_tokens=max_tokens,
                tools=[{"type": "browsing"}]  # Enable browsing capability
            )
            
            # Store the raw findings with metadata
            findings = {
                "timestamp": datetime.now().isoformat(),
                "arbitrator_name": name,
                "research_depth": research_depth,
                "raw_findings": response.choices[0].message.content,
                "metadata": {
                    "model": "gpt-4-turbo-preview",
                    "temperature": 0.7,
                    "max_tokens": max_tokens
                }
            }
            
            # Organize the findings into categories (optional second call)
            categories_response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an assistant that organizes raw research findings into categories while preserving ALL details. Do not summarize or omit any information."},
                    {"role": "user", "content": f"Organize these raw findings into categories while preserving ALL details and information:\n\n{response.choices[0].message.content}"}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            findings["categorized_findings"] = categories_response.choices[0].message.content
            
            return findings
            
        except Exception as e:
            return {"error": str(e), "details": "This functionality requires a model with browsing capability."}

    def search_across_entities(self, arbitrator_data, entities_list):
        """
        Search for connections between the arbitrator and a list of entities (companies, people, etc.)
        
        Args:
            arbitrator_data (dict): Dictionary containing arbitrator information
            entities_list (list): List of entities to check for connections
            
        Returns:
            dict: All found connections between arbitrator and entities
        """
        name = arbitrator_data.get('name')
        if not name:
            raise ValueError("Arbitrator name is required")
            
        # Format entities list
        entities_formatted = "\n".join([f"- {entity}" for entity in entities_list])
        
        system_prompt = """
        You are an expert in finding connections between people and organizations. Your task is to identify
        ANY possible connection between the arbitrator and the provided list of entities. Report EVERY 
        possible connection you can find or infer, no matter how minor or indirect.
        
        For EACH entity, report:
        1. Direct connections (employment, board membership, etc.)
        2. Indirect connections (mutual connections, organizations, alumni status)
        3. Possible interactions (events, conferences, publications)
        4. Any other potential linkages
        
        Include EVERYTHING, even tenuous or speculative connections. Your goal is to be exhaustive, not selective.
        """
        
        try:
            # Call the OpenAI API with browsing to find connections
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Find ALL possible connections between arbitrator {name} and the following entities:\n\n{entities_formatted}\n\nBe exhaustive and report EVERYTHING you find, including sources."}
                ],
                temperature=0.5,
                max_tokens=4000,
                tools=[{"type": "browsing"}]
            )
            
            # Store the connection information
            connections = {
                "timestamp": datetime.now().isoformat(),
                "arbitrator_name": name,
                "entities_searched": entities_list,
                "connections_found": response.choices[0].message.content
            }
            
            return connections
            
        except Exception as e:
            return {"error": str(e)}

    def save_to_file(self, data, filename=None):
        """
        Save collected information to a JSON file.
        
        Args:
            data (dict): The data to save
            filename (str): Optional filename, defaults to arbitrator name and timestamp
            
        Returns:
            str: Path to the saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            arbitrator = data.get("arbitrator_name", "arbitrator").replace(" ", "_")
            filename = f"{arbitrator}_{timestamp}.json"
            
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        return filename


# Example usage
if __name__ == "__main__":
    # Example arbitrator data - can be minimal or extensive as available
    arbitrator_data = {
        "name": "Charles Poncet",
        "title": "Arbitrator",
        "location": "Switzerland"
    }
    
    # Example list of entities to check for connections
    entities_list = [
            
    ]
    
    # Initialize the collector
    collector = ArbitratorInfoCollector()
    
    # Basic information collection
    print("Collecting basic information...")
    basic_info = collector.collect_information(arbitrator_data, detailed=False)
    collector.save_to_file(basic_info, "basic_info.json")
    
    # Extensive web research
    print("Conducting web research...")
    web_info = collector.web_research(arbitrator_data, research_depth="extensive")
    collector.save_to_file(web_info, "web_research.json")
    
    # Connection search
    print("Searching for entity connections...")
    connections = collector.search_across_entities(arbitrator_data, entities_list)
    collector.save_to_file(connections, "entity_connections.json")
    
    # Combine all information into a master file
    master_data = {
        "timestamp": datetime.now().isoformat(),
        "arbitrator_data": arbitrator_data,
        "basic_information": basic_info,
        "web_research": web_info,
        "entity_connections": connections
    }
    
    master_file = collector.save_to_file(master_data, f"{arbitrator_data['name'].replace(' ', '_')}_master_data.json")
    print(f"All data collected and saved to {master_file}")