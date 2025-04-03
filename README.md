# Rate My Professor API

Bare bones Python API for scraping and searching Rate My Professor data from all professors of a single university. This API can be used to search for professors, get their ratings, and export the data to CSV files.

## Getting Started

Initialize the API with the corresponding Rate My Professor university ID.

```python
from ratemyprof_api.ratemyprof_api import RateMyProfApi

# Initialize with Indiana University Bloomington
iu_bloomington = RateMyProfApi("440")

# Initialize with MIT
mit = RateMyProfApi("580")
```

The university ID can be found in the URL of the university's Rate My Professor page:
```
https://www.ratemyprofessors.com/school/440  # Indiana University Bloomington
https://www.ratemyprofessors.com/school/580  # MIT
```

## Features

### Search for Professors

```python
# Search for a professor by name
professors = iu_bloomington.search_professor("Kristi DeBoeuf")

# Print the search results
for prof in professors:
    print(f"{prof.name} (ID: {prof.ratemyprof_id})")
```

### Get Professor Details

```python
# Get a professor by ID
professor = iu_bloomington.get_professor_by_id(2255935)

# Get a professor by name (returns the first match)
professor = iu_bloomington.get_professor_by_name("Kristi DeBoeuf")

# Print professor details
print(f"Professor: {professor.name}")
print(f"Department: {professor.department}")
print(f"Overall Rating: {professor.overall_rating}")
print(f"Difficulty: {professor.difficulty}")
print(f"Would Take Again: {professor.would_take_again_percent}%")
print(f"Number of Ratings: {professor.num_of_ratings}")
```

### Access Ratings

```python
# Get a professor's ratings
professor = iu_bloomington.get_professor_by_id(2255935)

# Print the first rating
if professor.ratings:
    rating = professor.ratings[0]
    print(f"Class: {rating['class']}")
    print(f"Comment: {rating['comment']}")
    print(f"Date: {rating['date']}")
    print(f"Grade: {rating['grade']}")
```

### Export Data to CSV

```python
# Export all professors to CSV
iu_bloomington.write_professors_to_csv()

# Export a professor's ratings to CSV
iu_bloomington.write_ratings_to_csv(2255935)
```

## Professor Object

The `Professor` class represents a professor with the following attributes:

- `ratemyprof_id`: The Rate My Professor ID of the professor
- `name`: The full name of the professor
- `first_name`: The first name of the professor
- `last_name`: The last name of the professor
- `department`: The department of the professor
- `num_of_ratings`: The number of ratings for the professor
- `overall_rating`: The overall rating of the professor
- `would_take_again_percent`: The percentage of students who would take the professor again
- `difficulty`: The difficulty rating of the professor
- `ratings`: A list of rating dictionaries

## Rating Dictionary

Each rating is represented as a dictionary with the following keys:

- `id`: The ID of the rating
- `class`: The class code for the rating
- `comment`: The comment left by the student
- `date`: The date the rating was posted
- `helpful_rating`: The helpfulness rating (1-5)
- `clarity_rating`: The clarity rating (1-5)
- `difficulty_rating`: The difficulty rating (1-5)
- `would_take_again`: Whether the student would take the professor again (1 = yes, 0 = no)
- `grade`: The grade the student received
- `tags`: Tags associated with the rating
- `is_for_online_class`: Whether the class was online

## Acknowledgments

This project is based on [tisuela/ratemyprof-api](https://github.com/tisuela/ratemyprof-api), which provided the initial inspiration. The codebase has been completely rewritten to work with the current version of RateMyProfessor's website and expanded with additional features.
