import requests
import os
from jinja2 import Environment, FileSystemLoader
import datetime
import rss_py

root = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(root, 'templates')
env = Environment(loader=FileSystemLoader(templates_dir))

username = 'Reisonancia'
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

    return (response.json())


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
            }
            siteUrl
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
    
    # Debug: Print the userActivity structure
    print("User Activity Structure:", userActivity)

    for activity in userActivity['data']['Page']['activities']:
        print(f"Checking activity type: {activity.get('type')}")  # Debug: Print activity type

        if activity.get('type') == media_type:
            # Construct title based on progress
            if not activity.get('progress'):
                title = f"{username} {activity.get('status')} {activity['media']['title'].get(media_title)}"
            else:
                title = f"{username} {activity.get('status')} {activity.get('progress')} of {activity['media']['title'].get(media_title)}"
                
            # Create item
            item = {
                'title': title,
                'pubDate': datetime.datetime.fromtimestamp(activity.get('createdAt'), tz=datetime.timezone.utc),
                'link': activity.get('siteUrl')
            }
            activities.append(item)

    print(f"Found {len(activities)} activities.")  # Debug: Count of activities found

    # Define the output directory based on feed name
    if feed_name == 'anime':
        folder_name = 'Anime Feeds'
    elif feed_name == 'manga':
        folder_name = 'Manga Feeds'
    else:
        raise ValueError("Invalid feed name")

    filename = f"anilist-{feed_name}-{perPage}.xml"
    # Set filename_dir to point to the correct folders directly
    filename_dir = os.path.join(folder_name, filename)
    
    # Make sure the directory exists
    os.makedirs(folder_name, exist_ok=True)
    
    print(f"Saving feed to: {filename_dir}")
    
    # Write the RSS feed to the file
    with open(filename_dir, "w") as fh:
        fh.write(
            rss_py.build(
                title=f"{username}'s {feed_name.capitalize()} Activity",
                link=link,
                description=f"The unofficial AniList {feed_name} activity feed for {username}.",
                language="en-gb",
                lastBuildDate=datetime.datetime.now(datetime.timezone.utc),
                atomSelfLink=f"{link}{filename}",
                items=activities
            )
        )


# Get user ID
r = getUserID(username)
userId = r.get('data').get('User').get('id')

# Get user activity
userActivity = listActivity(userId, perPage)

# Generate separate feeds for anime and manga
generate_feed(userActivity, 'ANIME', 'anime', perPage)
generate_feed(userActivity, 'MANGA', 'manga', perPage)


#New code to check for other things
def check_user_activity(activities, activity_type):
    # Initialize a list to hold the filtered activities
    filtered_activities = []

    for activity in activities:
        if activity.get('type') == activity_type:
            media_title = activity['media']['title']['romaji']
            site_url = activity['siteUrl']
            # Check for progress and status, if applicable
            progress = activity.get('progress', 'N/A')
            status = activity['status']
            created_at = datetime.fromtimestamp(activity['createdAt']).isoformat()

            # Add the activity to the list
            filtered_activities.append({
                'title': media_title,
                'url': site_url,
                'progress': progress,
                'status': status,
                'created_at': created_at,
            })

    return filtered_activities

def save_activities_to_xml(activities, filename):
    root = ET.Element('activities')
    for activity in activities:
        activity_element = ET.SubElement(root, 'activity')
        for key, value in activity.items():
            child = ET.SubElement(activity_element, key)
            child.text = str(value)

    tree = ET.ElementTree(root)
    tree.write(filename, encoding='utf-8', xml_declaration=True)

# Assuming you've defined your activity retrieval logic
user_activity = get_user_activity()  # Function to fetch user activity
activities = user_activity['data']['Page']['activities']

# Check for anime activities
anime_activities = check_user_activity(activities, 'ANIME_LIST')
if anime_activities:
    print(f"Found {len(anime_activities)} anime activities.")
    save_activities_to_xml(anime_activities, 'Anime Feeds/anilist-anime.xml')
else:
    print("No anime activities found.")

# Check for manga activities
manga_activities = check_user_activity(activities, 'MANGA_LIST')
if manga_activities:
    print(f"Found {len(manga_activities)} manga activities.")
    save_activities_to_xml(manga_activities, 'Anime Feeds/anilist-manga.xml')
else:
    print("No manga activities found.")