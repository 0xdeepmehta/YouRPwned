import re
from requests_html import HTMLSession, HTML
import time
from datetime import datetime
from urllib.parse import quote
from lxml.etree import ParserError

session = HTMLSession()
class Profile:
    """
        Parse twitter profile and split informations into class as attribute.

        Attributes:
            - name
            - username
            - birthday
            - location
            - biography
            - website
            - profile_photo
            - banner_photo
            - likes_count
            - tweets_count
            - followers_count
            - following_count
            - is_verified
            - is_private
            - user_id
    """

    def __init__(self, username):
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": f"https://twitter.com/{username}",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8",
            "X-Twitter-Active-User": "yes",
            "X-Requested-With": "XMLHttpRequest",
            "Accept-Language": "en-US",
        }

        page = session.get(f"https://twitter.com/{username}", headers=headers)
        self.username = username
        self.__parse_profile(page)

    def __parse_profile(self, page):
        try:
            html = HTML(html=page.text, url="bunk", default_encoding="utf-8")
        except KeyError:
            raise ValueError(
                f'Oops! Either "{self.username}" does not exist or is private.'
            )
        except ParserError:
            pass

        try:
            self.is_private = html.find(".ProfileHeaderCard-badges .Icon--protected")[0]
            self.is_private = True
        except:
            self.is_private = False

        try:
            self.is_verified = html.find(".ProfileHeaderCard-badges .Icon--verified")[0]
            self.is_verified = True
        except:
            self.is_verified = False

        self.location = html.find(".ProfileHeaderCard-locationText")[0].text
        if not self.location:
            self.location = None

        self.birthday = html.find(".ProfileHeaderCard-birthdateText")[0].text
        if self.birthday:
            self.birthday = self.birthday.replace("Born ", "")
        else:
            self.birthday = None

        self.profile_photo = html.find(".ProfileAvatar-image")[0].attrs["src"]

        try:
            self.banner_photo = html.find(".ProfileCanopy-headerBg img")[0].attrs["src"]
        except KeyError:
            self.banner_photo = None

        page_title = html.find("title")[0].text
        self.name = page_title[: page_title.find("(")].strip()

        self.user_id = html.find(".ProfileNav")[0].attrs["data-user-id"]

        self.biography = html.find(".ProfileHeaderCard-bio")[0].text
        if not self.birthday:
            self.birthday = None

        self.website = html.find(".ProfileHeaderCard-urlText")[0].text
        if not self.website:
            self.website = None

        # get total tweets count if available
        try:
            q = html.find('li[class*="--tweets"] span[data-count]')[0].attrs["data-count"]
            self.tweets_count = int(q)
        except:
            self.tweets_count = None

        # get total following count if available
        try:
            q = html.find('li[class*="--following"] span[data-count]')[0].attrs["data-count"]
            self.following_count = int(q)
        except:
            self.following_count = None

        # get total follower count if available
        try:
            q = html.find('li[class*="--followers"] span[data-count]')[0].attrs["data-count"]
            self.followers_count = int(q)
        except:
            self.followers_count = None

        # get total like count if available
        try:
            q = html.find('li[class*="--favorites"] span[data-count]')[0].attrs["data-count"]
            self.likes_count = int(q)
        except:
            self.likes_count = None

    def to_dict(self):
        return dict(
            name=self.name,
            username=self.username,
            birthday=self.birthday,
            biography=self.biography,
            location=self.location,
            website=self.website,
            profile_photo=self.profile_photo,
            banner_photo=self.banner_photo,
            likes_count=self.likes_count,
            tweets_count=self.tweets_count,
            followers_count=self.followers_count,
            following_count=self.following_count,
            is_verified=self.is_verified,
            is_private=self.is_private,
            user_id=self.user_id
        )

    def __dir__(self):
        return [
            "name",
            "username",
            "birthday",
            "location",
            "biography",
            "website",
            "profile_photo",
            'banner_photo'
            "likes_count",
            "tweets_count",
            "followers_count",
            "following_count",
            "is_verified",
            "is_private",
            "user_id"
        ]

    def __repr__(self):
        return f"<profile {self.username}@twitter>"

def getTweets(query, pages=25):
    print(f"{query}")
    """Gets tweets for a given user, via the Twitter frontend API."""
    after_part = (
        f"include_available_features=1&include_entities=1&include_new_items_bar=true"
    )
    if query.startswith("#"):
        query = quote(query)
        print(query)
        url = f"https://twitter.com/i/search/timeline?f=tweets&vertical=default&q={query}&src=tyah&reset_error_state=false&"
    else:
        url = f"https://twitter.com/i/profiles/show/{query}/timeline/tweets?"
    url += after_part

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": f"https://twitter.com/{query}",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8",
        "X-Twitter-Active-User": "yes",
        "X-Requested-With": "XMLHttpRequest",
        "Accept-Language": "en-US",
    }

    def gen_tweets(pages):
        request = session.get(url + '&max_position', headers=headers)
        print(request)

        while pages > 0:
            try:
                json_response = request.json()
                html = HTML(
                    html=json_response["items_html"], url="bunk", default_encoding="utf-8"
                )
            except KeyError:
                raise ValueError(
                    f'Oops! Either "{query}" does not exist or is private.'
                )
            except ParserError:
                break

            comma = ","
            dot = "."
            tweets = []
            for tweet, profile in zip(
                html.find(".stream-item"), html.find(".js-profile-popup-actionable")
            ):
                # 10~11 html elements have `.stream-item` class and also their `data-item-type` is `tweet`
                # but their content doesn't look like a tweet's content
                try:
                    text = tweet.find(".tweet-text")[0].full_text
                except IndexError:  # issue #50
                    continue


                tweet_id = tweet.attrs["data-item-id"]

                tweet_url = profile.attrs["data-permalink-path"]

                username = profile.attrs["data-screen-name"]

                user_id = profile.attrs["data-user-id"]

                is_pinned = bool(tweet.find("div.pinned"))

                time = datetime.fromtimestamp(
                    int(tweet.find("._timestamp")[0].attrs["data-time-ms"]) / 1000.0
                )

                interactions = [x.text for x in tweet.find(".ProfileTweet-actionCount")]

                replies = int(
                    interactions[0].split(" ")[0].replace(comma, "").replace(dot, "")
                    or interactions[3]
                )

                retweets = int(
                    interactions[1].split(" ")[0].replace(comma, "").replace(dot, "")
                    or interactions[4]
                    or interactions[5]
                )

                likes = int(
                    interactions[2].split(" ")[0].replace(comma, "").replace(dot, "")
                    or interactions[6]
                    or interactions[7]
                )

                hashtags = [
                    hashtag_node.full_text
                    for hashtag_node in tweet.find(".twitter-hashtag")
                ]

                urls = [
                    url_node.attrs["data-expanded-url"]
                    for url_node in (
                        tweet.find("a.twitter-timeline-link:not(.u-hidden)") +
                        tweet.find("[class='js-tweet-text-container'] a[data-expanded-url]")
                    )
                ]
                urls = list(set(urls)) # delete duplicated elements

                photos = [
                    photo_node.attrs["data-image-url"]
                    for photo_node in tweet.find(".AdaptiveMedia-photoContainer")
                ]

                is_retweet = (
                    True
                    if tweet.find(".js-stream-tweet")[0].attrs.get(
                        "data-retweet-id", None
                    )
                    else False
                )

                videos = []
                video_nodes = tweet.find(".PlayableMedia-player")
                for node in video_nodes:
                    styles = node.attrs["style"].split()
                    for style in styles:
                        if style.startswith("background"):
                            tmp = style.split("/")[-1]
                            video_id = (
                                tmp[: tmp.index(".jpg")]
                                if ".jpg" in tmp
                                else tmp[: tmp.index(".png")]
                                if ".png" in tmp
                                else None
                            )
                            videos.append({"id": video_id})

                tweets.append(
                    {
                        "tweetId": tweet_id,
                        "tweetUrl": tweet_url,
                        "username": username,
                        "userId": user_id,
                        "isRetweet": is_retweet,
                        "isPinned": is_pinned,
                        "time": time,
                        "text": text,
                        "replies": replies,
                        "retweets": retweets,
                        "likes": likes,
                        "entries": {
                            "hashtags": hashtags,
                            "urls": urls,
                            "photos": photos,
                            "videos": videos,
                        },
                    }
                )

            last_tweet = html.find(".stream-item")[-1].attrs["data-item-id"]
            print("last tweet", last_tweet)

            for tweet in tweets:
                tweet["text"] = re.sub(r"(\S)http", "\g<1> http", tweet["text"], 1)
                tweet["text"] = re.sub(
                    r"(\S)pic\.twitter", "\g<1> pic.twitter", tweet["text"], 1
                )
                print(tweet)
                yield tweet

            request = session.get(url, params={"max_position": json_response['min_position']}, headers=headers)
            pages += -1

    yield from gen_tweets(pages)


if __name__ == "__main__":
    print("Welcome ! Finally You care Abut Your *Privacy*")
    pwnedName = input("Enter your Twitter User Name (e.g \" MIPwned \") ")
    print(f"Let's See how much \"Twitter\" Know about you =>",end="")
    profile = Profile(pwnedName)
    print(profile.to_dict())
    print("\n Know Explore your tweets")
    time.sleep(2)
    tweets=getTweets(pwnedName, pages=1) 
    for tweet in tweets:
        print(tweet)
