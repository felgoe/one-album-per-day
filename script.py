# -*- coding: utf-8 -*-
"""
Created on Wed Apr 13 20:41:22 2022

@author: felgoe
"""

import requests
import base64
import pickle
import os
import logging
import argparse
import configparser

'''
Configuration parameters for the main script
'''
class Config:
	album_generator_project_name = None
	spotify_playlist_id = None
	spotify_client_id = None
	spotify_client_secret = None

'''
API service for 1001albumsgenerator.com
'''	
class album_generator_service:
	
	__album_generator_api_base_url = 'https://1001albumsgenerator.com/api/v1'
	
	def __init__(self):
		self.logger = logging.getLogger(self.__class__.__name__)
	
	# @static
	def get_album(self, project_name):
		self.logger.info('Getting album')
		projects_endpoint = "projects"
		url = "/".join([self.__album_generator_api_base_url, projects_endpoint, project_name])
		response = requests.get(url)
		
		if not response.ok:
			raise ValueError('Could not fetch album')
		
		return response.json()

'''
API service for Spotify
'''
class spotify_service:
	
	__api_base_url = 'https://api.spotify.com/v1'
	__access_token = None
	__refresh_token = None
	
	def __init__(self):
		self.logger = logging.getLogger(self.__class__.__name__)
	
	def set_access_token(self, token):
		self.__access_token = token
		
	def __get_access_token(self):
		if self.__access_token is None:
			raise ValueError('No access token set')
		
		return self.__access_token

	def set_refresh_token(self, token):
		self.__refresh_token = token

	def __get_refresh_token(self):
		if self.__refresh_token is None:
			raise ValueError('No refresh token set')
		
		return self.__refresh_token
	
	def acquire_spotify_access_token(self):
		raise NotImplementedError()
	
	'''
	Gets a new access token using the current refresh token and sets and return a new refresh token.
	'''
	def refresh_access_token(self, client_id, client_secret):
		self.logger.info('Refreshing access token')
		url = "https://accounts.spotify.com/api/token"
		
		payload='grant_type=refresh_token&refresh_token={}'.format(self.__get_refresh_token())
		byte_string = '{}:{}'.format(client_id, client_secret).encode()
		b64_encoded_client_id_and_secret = base64.b64encode(byte_string).decode('ascii')
		headers = {
		  'Authorization': 'Basic {}'.format(b64_encoded_client_id_and_secret),
		  'Content-Type': 'application/x-www-form-urlencoded'
		}
		
		response = requests.request("POST", url, headers=headers, data=payload)
		
		if not response.ok:
			raise ValueError('Unable to refresh access token, status: {}, message: {}'.format(
					response.status_code, response.json()))
		
		refresh_token = response.json()['refresh_token']
		self.set_refresh_token(refresh_token)
		self.set_access_token(response.json()['access_token'])
		
		return refresh_token

		
	def __execute_private_api_call(self, method, endpoint, body=None, additional_headers=None):
		url = '/'.join([self.__api_base_url, endpoint])
		headers = {
				'Authorization': 'Bearer ' + self.__get_access_token(),
				'accept': 'application/json'
		}
		if additional_headers is not None:
			headers.update(additional_headers)
		response = requests.request(method, url, headers=headers, json=body)
		
		if not response.ok:
			raise ValueError('Exception on spotify API call, status {}, message: {}'.format(
					response.status_code , response.json()))
		
		return response
	
	def get_playlist(self, id):
		self.logger.info('Getting playlist')
		playlists_endpoint = 'playlists'
		endpoint = '/'.join([playlists_endpoint, id])
		response = self.__execute_private_api_call('get', endpoint);
		
		return response.json()
	
	def remove_playlist_items(self, playlist_id, playlist_items):
		self.logger.info('Removing playlist items')
		endpoint = '/'.join(['playlists', playlist_id, 'tracks'])
		additional_headers = {
				'Content-Type': 'application/json'
		}
		body = {
				'tracks': [{'uri': item} for item in playlist_items]
		}
		response = self.__execute_private_api_call(
				'delete',
				endpoint,
				body=body,
				additional_headers=additional_headers
		);
		
		return response.json()
	
	def add_playlist_items(self, playlist_id, playlist_items):
		self.logger.info('Adding playlists items')
		endpoint = '/'.join(['playlists', playlist_id, 'tracks'])
		additional_headers = {
				'Content-Type': 'application/json'
		}
		body = {
				'uris': playlist_items
		}
		response = self.__execute_private_api_call(
				'post',
				endpoint,
				body=body,
				additional_headers=additional_headers
		);
		
		return response.json()
	
	def replace_playlist_contents(self, playlist_id, playlist_items):
		self.logger.info('Replacing playlist contents')
		endpoint = '/'.join(['playlists', playlist_id, 'tracks'])
		additional_headers = {
				'Content-Type': 'application/json'
		}
		body = {
				'uris': playlist_items
		}
		response = self.__execute_private_api_call(
				'put',
				endpoint,
				body=body,
				additional_headers=additional_headers
		);
		
		return response.json()
	
	def update_playlist_image(self, playlist_id, image):
		self.logger.info('Updating playlist image')
		endpoint = '/'.join([self.__api_base_url, 'playlists', playlist_id, 'images'])
		headers = {
				'Authorization': 'Bearer ' + self.__get_access_token(),
				'Content-Type': 'text/plain'
		}
		response = requests.request(
				'put',
				endpoint,
				headers=headers,
				data=image
		)
		
		if not response.ok:
			raise ValueError('Exception on spotify API call, status {}, message: {}'.format(
					response.status_code , response.json()))
	
	def get_album(self, id):
		self.logger.info('Getting album')
		endpoint = '/'.join(['albums', id])
		
		return self.__execute_private_api_call('get', endpoint).json()
	
	def update_playlist_description(self, playlist_id, text):
		self.logger.info('Updating playlist description')
		endpoint = '/'.join(['playlists', playlist_id])
		body = {
			'description': text	
		}
		self.__execute_private_api_call('put', endpoint, body=body)

def pickle_refresh_token(token):
	logger.info('Pickling refresh token')
	with open('.refresh_token.pkl', 'wb') as file:
		pickle.dump(token, file)

def load_config():
	parser = argparse.ArgumentParser()
	parser.add_argument('--client_id', help='Spotify client id')
	parser.add_argument('--client_secret', help='Spotify client secret')
	parser.add_argument('--playlist_id', help='Spotify playlist id')
	parser.add_argument('--project_name', help='Album generator project name')
	parser.add_argument('--conf', help='Use .conf file for configuration', action='store_const', default=False, const=True)
	
	args = parser.parse_args()
	
	if args.conf:
		config = load_config_file()
	else:
		config = load_arguments(args)
	
	return config
		
def load_config_file():
	parser = configparser.ConfigParser()
	parser.read('.conf')
	config = Config()
	config.spotify_client_id = parser['DEFAULT']['client_id']
	config.spotify_client_secret = parser['DEFAULT']['client_secret']
	config.spotify_playlist_id = parser['DEFAULT']['playlist_id']
	config.album_generator_project_name = parser['DEFAULT']['project_name']
	
	return config

def load_arguments(args):
	assert args.client_id and args.client_secret and args.playlist_id and args.project_name
	config = Config()
	config.spotify_client_id = args.client_id
	config.spotify_client_secret = args.client_secret
	config.spotify_playlist_id = args.playlist_id
	config.album_generator_project_name = args.project_name
	
	return config
	
# Script
if __name__ == '__main__':
	directory = os.path.dirname(os.path.abspath(__file__))
	os.chdir(directory)
	
	logging.basicConfig(filename='service.log', level='INFO', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	logger = logging.getLogger(__name__)
	logger.info('Started run, working directory: ' + directory)
	
	config = load_config()
	
	try:
		new_album = album_generator_service().get_album(config.album_generator_project_name)
		spotify_album_id = new_album['currentAlbum']['spotifyId']
		image_url = new_album['currentAlbum']['images'][1]['url']
		b64_encoded_album_cover = base64.b64encode(requests.get(image_url).content).decode('ascii')
		
		with open('.refresh_token.pkl', 'rb') as file:
			refresh_token = pickle.load(file)
		
		spot = spotify_service()
		spot.set_refresh_token(refresh_token)
		refresh_token = spot.refresh_access_token(config.spotify_client_id, config.spotify_client_secret)
		pickle_refresh_token(refresh_token)
		
		spot.update_playlist_image(config.spotify_playlist_id, b64_encoded_album_cover)
		album = spot.get_album(spotify_album_id)
		track_ids = [track['uri'] for track in album['tracks']['items']]
		spot.replace_playlist_contents(config.spotify_playlist_id, track_ids)
		desc = 'Album of the day: {} - {}'.format(new_album['currentAlbum']['artist'], new_album['currentAlbum']['name'])
		spot.update_playlist_description(config.spotify_playlist_id, desc)
	except Exception as e:
		logger.error(e)