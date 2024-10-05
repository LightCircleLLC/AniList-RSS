import requests
import os
from jinja2 import Environment, FileSystemLoader
import datetime
import rss_py

root = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(root, 'templates')
env = Environment(loader=FileSystemLoader(templates_dir))

username = "Reisonancia"
link = os.getenv('LINK', '')
perPage = os.getenv('PER_PAGE', 20)

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
    for activity in userActivity['data']['Page']['activities']:
        if activity.get('type') == media_type:
            if not activity.get('progress'):
                title = f"{username} {activity.get('status')} {activity['media']['title'].get(media_title)}"
            else:
                title = f"{username} {activity.get('status')} {activity.get('progress')} of {activity['media']['title'].get('romaji')}"
            item = {
                'title': title,
                'pubDate': datetime.datetime.fromtimestamp(activity.get('createdAt'), tz=datetime.timezone.utc),
                'link': activity.get('siteUrl')
            }
            activities.append(item)

    filename = f"anilist-{feed_name}-{perPage}.xml"
    filename_dir = os.path.join(root, 'feeds', filename)
    os.makedirs(os.path.dirname(filename_dir), exist_ok=True)
    print(link, filename)
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
