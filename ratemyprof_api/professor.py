
from typing import List, Dict, Optional, Any, Union

class Professor:
    def __init__(self, ratemyprof_id: int, first_name: str, last_name: str, num_of_ratings: int, overall_rating):
        """Initialize a Professor object.
        
        Args:
            ratemyprof_id: The RateMyProfessor ID of the professor
            first_name: The first name of the professor
            last_name: The last name of the professor
            num_of_ratings: The number of ratings for the professor
            overall_rating: The overall rating of the professor
        """
        self.ratemyprof_id = ratemyprof_id
        self.name = f"{first_name} {last_name}"
        self.first_name = first_name
        self.last_name = last_name
        self.num_of_ratings = num_of_ratings

        # Set overall rating to 0 if there are no ratings
        if self.num_of_ratings < 1:
            self.overall_rating = 0
        else:
            self.overall_rating = float(overall_rating) if overall_rating else 0
            
        # Additional fields that will be populated later
        self.department = ""
        self.would_take_again_percent = 0
        self.difficulty = 0
        self.ratings: List[Dict[str, Any]] = []
    
    def __str__(self) -> str:
        """Return a string representation of the professor."""
        return f"{self.name} (ID: {self.ratemyprof_id}, Rating: {self.overall_rating})"
    
    def __repr__(self) -> str:
        """Return a string representation of the professor."""
        return self.__str__()
