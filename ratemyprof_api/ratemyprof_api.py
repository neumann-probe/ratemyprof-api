import requests
import json
import math
import csv
import os
import re
from typing import Dict, List, Optional, Any, Union

from .professor import Professor

class ProfessorNotFound(Exception):
    def __init__(self, search_argument, search_parameter: str = "Name"):
        # What the client is looking for. Ex: "Professor Pattis"
        self.search_argument = search_argument
        # The search criteria. Ex: Last Name
        self.search_parameter = search_parameter

    def __str__(self):
        return (
            f"Professor not found. "
            f"The search argument '{self.search_argument}' did not "
            f"match with any professor's {self.search_parameter}"
        )

class RateMyProfApi:
    def __init__(self, school_id: str = "1074", testing: bool = False):
        """Initialize the RateMyProfessor API.
        
        Args:
            school_id: The school ID from RateMyProfessor
            testing: If True, limit the number of professors fetched for testing
        """
        self.school_id = school_id
        self.base_url = "https://www.ratemyprofessors.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        
        # Create directory for school data if it doesn't exist
        if not os.path.exists(f"SchoolID_{self.school_id}"):
            os.mkdir(f"SchoolID_{self.school_id}")
        
        # Dictionary of professors indexed by their RMP ID
        self.professors = {}
        
        # School information
        self.school_name = None
        self.school_city = None
        self.school_state = None
        
        # Get school information
        self._get_school_info()
        
        # Scrape professors if not testing or if professors dict is empty
        if not testing or not self.professors:
            self.professors = self.scrape_professors(testing)

    def _get_school_info(self):
        """Get basic information about the school."""
        url = f"{self.base_url}/school/{self.school_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"Failed to get school info: {response.status_code}")
            return
        
        # Extract the Relay store data
        relay_data = self._extract_relay_data(response.text)
        if not relay_data:
            print("Failed to extract school data")
            return
        
        # Find the school node
        school_node_id = f"U2Nob29sLTQ0MA=="  # Base64 encoded "School-440"
        for key, value in relay_data.items():
            if key.startswith("U2Nob29s") and "__typename" in value and value["__typename"] == "School":
                self.school_name = value.get("name", "Unknown School")
                self.school_city = value.get("city", "Unknown City")
                self.school_state = value.get("state", "Unknown State")
                break

    def _extract_relay_data(self, html_content: str) -> Dict:
        """Extract the Relay store data from the HTML content."""
        match = re.search(r'window\.__RELAY_STORE__ = ({.*?});', html_content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                print("Failed to parse Relay store data")
        return {}

    def scrape_professors(self, testing: bool = False) -> Dict[int, Professor]:
        """Scrape professors from the school's page.
        
        Args:
            testing: If True, limit the number of professors fetched for testing
            
        Returns:
            Dictionary of Professor objects indexed by their RMP ID
        """
        professors = {}
        
        # Get the first page of professors
        url = f"{self.base_url}/search/professors/?q=*&sid={self.school_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"Failed to get professors: {response.status_code}")
            return professors
        
        # Extract the Relay store data
        relay_data = self._extract_relay_data(response.text)
        if not relay_data:
            print("Failed to extract professor data")
            return professors
        
        # Process the first page of professors
        professors.update(self._process_professor_search_data(relay_data))
        
        # If testing, return after processing the first page
        if testing:
            return professors
        
        # TODO: Implement pagination to get all professors
        # This would require making additional requests with the endCursor
        
        return professors

    def _process_professor_search_data(self, relay_data: Dict) -> Dict[int, Professor]:
        """Process the professor search data from the Relay store.
        
        Args:
            relay_data: The Relay store data
            
        Returns:
            Dictionary of Professor objects indexed by their RMP ID
        """
        professors = {}
        
        # Find the search results
        search_results = None
        for key, value in relay_data.items():
            if key.startswith("client:root:newSearch:teachers") and "__typename" in value and value["__typename"] == "TeacherSearchConnectionConnection":
                search_results = value
                break
        
        if not search_results or "edges" not in search_results:
            return professors
        
        # Process each professor in the search results
        for edge_ref in search_results["edges"].get("__refs", []):
            edge = relay_data.get(edge_ref)
            if not edge or "node" not in edge:
                continue
            
            node_ref = edge["node"].get("__ref")
            if not node_ref:
                continue
            
            prof_data = relay_data.get(node_ref)
            if not prof_data or "__typename" not in prof_data or prof_data["__typename"] != "Teacher":
                continue
            
            # Get the school data
            school_ref = prof_data.get("school", {}).get("__ref")
            school_data = relay_data.get(school_ref, {})
            
            # Create a Professor object
            prof_id = prof_data.get("legacyId")
            if not prof_id:
                continue
            
            first_name = prof_data.get("firstName", "")
            last_name = prof_data.get("lastName", "")
            num_ratings = prof_data.get("numRatings", 0)
            overall_rating = prof_data.get("avgRating", 0)
            
            professor = Professor(
                ratemyprof_id=prof_id,
                first_name=first_name,
                last_name=last_name,
                num_of_ratings=num_ratings,
                overall_rating=overall_rating
            )
            
            # Add additional information
            professor.department = prof_data.get("department", "")
            professor.would_take_again_percent = prof_data.get("wouldTakeAgainPercent", 0)
            professor.difficulty = prof_data.get("avgDifficulty", 0)
            
            professors[prof_id] = professor
        
        return professors

    def search_professor(self, query: str) -> List[Professor]:
        """Search for professors by name.
        
        Args:
            query: The search query (e.g., "John Smith")
            
        Returns:
            List of matching Professor objects
        """
        url = f"{self.base_url}/search/professors/?q={query.replace(' ', '%20')}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"Failed to search professors: {response.status_code}")
            return []
        
        # Extract the Relay store data
        relay_data = self._extract_relay_data(response.text)
        if not relay_data:
            print("Failed to extract search results")
            return []
        
        # Process the search results
        professors = self._process_professor_search_data(relay_data)
        
        # Convert to list and sort by name
        prof_list = list(professors.values())
        prof_list.sort(key=lambda p: p.name)
        
        return prof_list

    def get_professor_by_id(self, professor_id: int) -> Optional[Professor]:
        """Get a professor by their RMP ID.
        
        Args:
            professor_id: The RateMyProfessor ID of the professor
            
        Returns:
            Professor object if found, None otherwise
        """
        # Check if we already have this professor
        if professor_id in self.professors:
            return self.professors[professor_id]
        
        # Fetch the professor details
        url = f"{self.base_url}/professor/{professor_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"Failed to get professor: {response.status_code}")
            return None
        
        # Extract the Relay store data
        relay_data = self._extract_relay_data(response.text)
        if not relay_data:
            print("Failed to extract professor details")
            return None
        
        # Find the professor node
        prof_data = None
        for key, value in relay_data.items():
            if key.startswith("VGVhY2hlci0") and "__typename" in value and value["__typename"] == "Teacher":
                prof_data = value
                break
        
        if not prof_data:
            return None
        
        # Get the school data
        school_ref = prof_data.get("school", {}).get("__ref")
        school_data = relay_data.get(school_ref, {})
        
        # Create a Professor object
        prof_id = prof_data.get("legacyId")
        if not prof_id:
            return None
        
        first_name = prof_data.get("firstName", "")
        last_name = prof_data.get("lastName", "")
        num_ratings = prof_data.get("numRatings", 0)
        overall_rating = prof_data.get("avgRating", 0)
        
        professor = Professor(
            ratemyprof_id=prof_id,
            first_name=first_name,
            last_name=last_name,
            num_of_ratings=num_ratings,
            overall_rating=overall_rating
        )
        
        # Add additional information
        professor.department = prof_data.get("department", "")
        professor.would_take_again_percent = prof_data.get("wouldTakeAgainPercent", 0)
        professor.difficulty = prof_data.get("avgDifficulty", 0)
        
        # Add ratings
        professor.ratings = self._extract_ratings(relay_data, prof_data)
        
        # Add to professors dictionary
        self.professors[prof_id] = professor
        
        return professor

    def _extract_ratings(self, relay_data: Dict, prof_data: Dict) -> List[Dict]:
        """Extract ratings from the Relay store data.
        
        Args:
            relay_data: The Relay store data
            prof_data: The professor data
            
        Returns:
            List of rating dictionaries
        """
        ratings = []
        
        # Find the ratings connection
        ratings_ref = prof_data.get("ratings(first:20)", {}).get("__ref")
        if not ratings_ref:
            return ratings
        
        ratings_connection = relay_data.get(ratings_ref)
        if not ratings_connection or "edges" not in ratings_connection:
            return ratings
        
        # Process each rating
        for edge_ref in ratings_connection["edges"].get("__refs", []):
            edge = relay_data.get(edge_ref)
            if not edge or "node" not in edge:
                continue
            
            node_ref = edge["node"].get("__ref")
            if not node_ref:
                continue
            
            rating_data = relay_data.get(node_ref)
            if not rating_data or "__typename" not in rating_data or rating_data["__typename"] != "Rating":
                continue
            
            # Extract rating information
            rating = {
                "id": rating_data.get("legacyId"),
                "class": rating_data.get("class", ""),
                "comment": rating_data.get("comment", ""),
                "date": rating_data.get("date", ""),
                "helpful_rating": rating_data.get("helpfulRating", 0),
                "clarity_rating": rating_data.get("clarityRating", 0),
                "difficulty_rating": rating_data.get("difficultyRating", 0),
                "would_take_again": rating_data.get("wouldTakeAgain", 0),
                "grade": rating_data.get("grade", ""),
                "tags": rating_data.get("ratingTags", ""),
                "is_for_online_class": rating_data.get("isForOnlineClass", False),
            }
            
            ratings.append(rating)
        
        return ratings

    def get_professor_by_name(self, name: str) -> Optional[Professor]:
        """Get a professor by their name.
        
        Args:
            name: The name of the professor (e.g., "John Smith")
            
        Returns:
            Professor object if found, None otherwise
        """
        # Search for the professor
        professors = self.search_professor(name)
        
        if not professors:
            return None
        
        # Try to find an exact match
        name_parts = name.lower().split()
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = name_parts[-1]
            
            # Look for an exact match
            for prof in professors:
                if (prof.first_name.lower() == first_name and 
                    prof.last_name.lower() == last_name):
                    return self.get_professor_by_id(prof.ratemyprof_id)
        
        # If no exact match, return the first result
        return self.get_professor_by_id(professors[0].ratemyprof_id)

    def write_professors_to_csv(self):
        """Write all professors to a CSV file."""
        csv_columns = [
            "ratemyprof_id",
            "first_name",
            "last_name",
            "name",
            "department",
            "num_of_ratings",
            "overall_rating",
            "would_take_again_percent",
            "difficulty",
        ]
        
        csv_file = f"SchoolID_{self.school_id}/professors.csv"
        
        with open(csv_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            
            for professor in self.professors.values():
                writer.writerow({
                    "ratemyprof_id": professor.ratemyprof_id,
                    "first_name": professor.first_name,
                    "last_name": professor.last_name,
                    "name": professor.name,
                    "department": getattr(professor, "department", ""),
                    "num_of_ratings": professor.num_of_ratings,
                    "overall_rating": professor.overall_rating,
                    "would_take_again_percent": getattr(professor, "would_take_again_percent", 0),
                    "difficulty": getattr(professor, "difficulty", 0),
                })

    def write_ratings_to_csv(self, professor_id: int):
        """Write a professor's ratings to a CSV file.
        
        Args:
            professor_id: The RateMyProfessor ID of the professor
        """
        professor = self.get_professor_by_id(professor_id)
        if not professor or not hasattr(professor, "ratings") or not professor.ratings:
            print(f"No ratings found for professor {professor_id}")
            return
        
        csv_columns = [
            "id",
            "class",
            "comment",
            "date",
            "helpful_rating",
            "clarity_rating",
            "difficulty_rating",
            "would_take_again",
            "grade",
            "tags",
            "is_for_online_class",
        ]
        
        csv_file = f"SchoolID_{self.school_id}/TeacherID_{professor_id}.csv"
        
        with open(csv_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            
            for rating in professor.ratings:
                # Clean up the comment to remove newlines
                if "comment" in rating and rating["comment"]:
                    rating["comment"] = rating["comment"].replace("\n", " ").replace("\r", " ")
                writer.writerow(rating)


# Example usage
if __name__ == '__main__':
    # Initialize the API with Indiana University Bloomington
    rmp = RateMyProfApi("440")
    
    # Search for a professor
    professors = rmp.search_professor("Kristi DeBoeuf")
    if professors:
        print(f"Found {len(professors)} professors:")
        for prof in professors:
            print(f"- {prof.name} (ID: {prof.ratemyprof_id})")
            
        # Get details for the first professor
        professor = rmp.get_professor_by_id(professors[0].ratemyprof_id)
        if professor:
            print(f"\nProfessor: {professor.name}")
            print(f"Department: {professor.department}")
            print(f"Overall Rating: {professor.overall_rating}")
            print(f"Difficulty: {professor.difficulty}")
            print(f"Would Take Again: {professor.would_take_again_percent}%")
            print(f"Number of Ratings: {professor.num_of_ratings}")
            
            if hasattr(professor, "ratings") and professor.ratings:
                print(f"\nLatest Rating:")
                latest = professor.ratings[0]
                print(f"Class: {latest['class']}")
                print(f"Comment: {latest['comment']}")
                print(f"Date: {latest['date']}")
                print(f"Grade: {latest['grade']}")
