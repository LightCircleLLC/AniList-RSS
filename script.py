import requests
import os
from jinja2 import Environment, FileSystemLoader
import datetime
import rss_py

root = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(root, 'templates')
env = Environment(loader=FileSystemLoader(templates_dir))

username = 'Reisbyfe'
link = 'https://github.com/LightCircleLLC/AniList-RSS'
perPage = 20

url = 'https://graphql.anilist.co'


def getUserID(name):
    query = '''
    query ($name: String) {
      User (name: $name) {
        id
      }
    }
    '''

    variables = {
        'name': name
    }

    response = requests.post(url, json={'query': query, 'variables': variables})

    # Check for HTTP errors
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code}")
        print(f"Response text: {response.text}")
        return None

    data = response.json()
    
        # Check if 'data' and 'User' are in the response
    if 'data' in data and 'User' in data['data']:
        return data
    else:
        print("Error: 'data' or 'User' not found in response")
        print(f"Response JSON: {data}")
        return None


def listActivity(userId, perPage):
    query = '''
    query ($userId: Int, $perPage: Int) {
      Page(page: 1, perPage:$perPage) {
        activities(userId: $userId, sort: ID_DESC) {
          ... on ListActivity {
            type
            createdAt
            progress
            status
            media {
              title {
                romaji
                english
                native
              }
              siteUrl
            }
          }
        }
      }
    }
    '''

    variables = {
        'userId': userId,
        'perPage': perPage
    }

    response = requests.post(url, json={'query': query, 'variables': variables})

    return (response.json())


def generate_feed(userActivity, media_type, feed_name, perPage):
    media_title = 'romaji'
    activities = []

    for activity in userActivity['data']['Page']['activities']:
        activity_type = activity.get('type')

        # Check if the activity type matches the specified media type
        if activity_type == media_type:

            # Construct title based on progress
            if not activity.get('progress'):
                title = f"{username} {activity.get('status')} {activity['media']['title'].get(media_title)}"
            else:
                title = f"{username} {activity.get('status')} {activity.get('progress')} of {activity['media']['title'].get(media_title)}"

            # Create item
            item = {
                'title': title,
                'pubDate': datetime.datetime.fromtimestamp(activity.get('createdAt'), tz=datetime.timezone.utc),
                'link': activity['media'].get('siteUrl')  # Access the siteUrl from the media object
            }
            activities.append(item)

    print(f"Found {len(activities)} activities.")  # Debug: Count of activities found

    # Define the output directory based on feed name
    folder_name = 'Anime Feeds' if feed_name == 'anime' else 'Manga Feeds'

    filename = f"anilist-{feed_name}-{perPage}.xml"
    filename_dir = os.path.join(folder_name, filename)

    # Make sure the directory exists
    os.makedirs(folder_name, exist_ok=True)

    print(f"Saving feed to: {filename_dir}")

    # Write the RSS feed to the file
    with open(filename_dir, "w") as fh:
        fh.write(
            rss_py.build(
                title=f"{username}'s {feed_name.capitalize()} Activity",
                link=link,  # Ensure 'link' variable is defined
                description=f"The unofficial AniList {feed_name} activity feed for {username}.",
                language="en-gb",
                lastBuildDate=datetime.datetime.now(datetime.timezone.utc),
                atomSelfLink=f"{link}{filename}",
                items=activities
            )
        )


# Get user ID
r = getUserID(username)
if r:
    userId = r.get('data').get('User').get('id')
    # Get user activity only if userId is successfully retrieved
    userActivity = listActivity(userId, perPage)

    # Generate separate feeds for anime and manga
    generate_feed(userActivity, 'ANIME_LIST', 'anime', perPage)
    generate_feed(userActivity, 'MANGA_LIST', 'manga', perPage)
else:
    print("Failed to retrieve user ID. Check the API response for details.")
    

# Get user activity
userActivity = listActivity(userId, perPage)

# Generate separate feeds for anime and manga
generate_feed(userActivity, 'ANIME_LIST', 'anime', perPage)
generate_feed(userActivity, 'MANGA_LIST', 'manga', perPage)
