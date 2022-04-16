# one-album-per-day

Simple python CLI tool that fetches the daily album from a 1001albumsgenerator.com project and populates a Spotify playlist with 
it.

The album changes daily and the spotify playlist always contains that daily album after running this tool.

Run this tool through a scheduler like cron to keep updating a playlist with the album of the day.


## Auth

To authenticate this app with spotify, an app registration at spotify is required. That can be setup
[here](https://developer.spotify.com/dashboard/applications).

As this app does not have a GUI, direct integration with oAuth 2.0 is a little tricky and might be done at a later point. So for
now, given an existing authorization, the refresh token is used to generate access tokens to spotify.

1. Generate an access token e.g. through Postman or a similar tool. Required scopes are `playlist-modify-private 
playlist-read-private ugc-image-upload`.
2. Copy the refresh token and use the function `pickle_refresh_token` to save the refresh token into the application folder
3. Given a valid configuration, the client ID and the client secret will be used with the refresh token to generate access tokens 
whenever the script is run


## Config

There are currently two ways to configure the tool.

1. Through CLI parameters. Run `python scripty.py -h` to see the parameters and use them to provide the required parameters
2. Through a config file `.conf` located in the script folder. The file has the following structure and the parameters have the 
same names as the CLI parameters:
```
[DEFAULT]
client_id=<client id>
client_secret=<client secret>
```
