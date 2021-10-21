# Plex Continue Watching Helper
# Tracing the actually playing episodes and marks the next episode of the show as unwatched.
# Based on https://gist.github.com/brimur/c270deaded9e9cdcb764f163c0565311

import io
# import yaml package
try:
    from ruamel.yaml import YAML
except:
    print("No python module named 'ruamel' found.")
# import plexapi package for plex connection
try:
    from plexapi.server import PlexServer
    from plexapi.video import Episode
    from plexapi.exceptions import NotFound
except ImportError:
    print("No python module named 'plexapi' found.")

def ConnectPlex(plex_url: str, plex_token: str):
    print("\nConnecting to Plex server with admin account.\n")
    try:
        main_plex = PlexServer(plex_url, plex_token)
        return main_plex
    except Exception:
        print("Can not connect to Plex server.")  
        raise

def ConnectPlexUser(plex_url: str, plex_token: str, plex_username: str):
    print("\nConnecting to Plex server with user profile.\n")
    try:
        main_plex = PlexServer(plex_url, plex_token)
        main_account = main_plex.myPlexAccount()
        user_account = main_account.user(plex_username)
        user_plex = PlexServer(plex_url, user_account.get_token(main_plex.machineIdentifier))
        print("Plex User Token is: " + user_account.get_token(main_plex.machineIdentifier))
        return user_plex, user_account.get_token(main_plex.machineIdentifier)
    except Exception:
        print("Can not connect to Plex server.")  
        raise

def GetNextEpisode(show_title: str, season_number: int, episode_number: int):
    episodes = user_plex.library.section(plex_libraryname).get(show_title).episodes()
    try:
        index = next(i for i, ep in enumerate(episodes) if ep.seasonNumber == season_number and ep.episodeNumber == episode_number)
        return episodes[index + 1]
    except StopIteration:
        raise NotFound
    except IndexError:
        # already last episode
        pass

# main
print("-----------------------------\nPlex Continue Watching Helper\n-----------------------------")

# TODO: Main User case, get libraries automatically

# load yaml config
yaml = YAML(typ="safe")
yaml.default_flow_style = False
with open("config.yaml", "r") as config_file:
    config_yaml = yaml.load(config_file)
plex_url = config_yaml["plex"]["plex_url"]
plex_token = config_yaml["plex"]["plex_token"]
plex_libraryname = config_yaml["plex"]["plex_libraryname"]
plex_username = config_yaml["plex"]["plex_username"]
if "plex_user_token" in config_yaml["plex"]: plex_user_token = config_yaml["plex"]["plex_user_token"]
else: plex_user_token = 0

# connect to plex server
if plex_user_token:
    user_plex = PlexServer(plex_url, plex_user_token)
else:
    user_plex, plex_user_token = ConnectPlexUser(plex_url, plex_token, plex_username)
    config_yaml["plex"]["plex_user_token"] = str(plex_user_token)
    with io.open("config.yaml", "w", encoding="utf8") as config_file:
        yaml.dump(config_yaml, config_file)

print("Search for episodes in progress.")
series_library = user_plex.library.section(plex_libraryname)
search_results = series_library.search(filters={"inProgress": "True"}, libtype="episode")
for episode in search_results:
    if isinstance(episode, Episode):
        show_title = episode.grandparentTitle
        season_number = episode.parentIndex
        episode_number = episode.index
        print("Currently in Progress: " + str(show_title) + " - S" + str(season_number).zfill(2) + "E" + str(episode_number).zfill(2))
        next_episode = GetNextEpisode(show_title, int(season_number), int(episode_number))
        next_episode.markUnwatched()

print("Done!")