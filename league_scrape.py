import requests
from bs4 import BeautifulSoup
import wget
import os
import csv
import pandas as pd
from urllib.parse import urlparse, parse_qs
import re


def image_grab(url_link, resident_folder):
	'''
	grabs all the photos out of a wiki page for lol.fandom.com 
	creates a subfolder in the resident folder
	downloads all the pictures to the subfolder

	Params
	url_link- (str) in the form of https://lol.fandom.com/wiki/Babo
	resident_folder- (str) in the form of  'NA/'
	'''
	try:
		response = requests.get(
            url=url_link,
        )
	except requests.exceptions.ConnectionError:
		print(f"Connection Error for {url_link} in image_grab")
		return url_link
	if response.status_code != 200:
		print("BAD STATUS image")
		return url_link
	
	soup = BeautifulSoup(response.content, 'html.parser')

	#use this for file path later
	title = soup.find("span", class_="mw-page-title-main")
	if title is None:
		title = soup.find(id="firstHeading")
	title = title.string.strip()

	#might have to change this if youre a windows user
	path_str = "./" + resident_folder + title
	if not os.path.exists(path_str):
		# Create a new directory because it does not exist
		os.makedirs(path_str)

	#grab links
	gallery = soup.find("ul", {"class": "gallery mw-gallery-traditional"})
	if gallery is None:
		return

	#grab captions
	caption = gallery.find_all('p')
	captions = [p.text.strip() for p in caption]
	empty_caption = False
	if len(captions) == 0:
		 empty_caption = True

	gallery_links = gallery.find_all('a')

	img_list = []
	caption_list = []
	counter = 0
	for img_i in range(len(gallery_links)):
		url = gallery_links[img_i].get('href')

		# Check if the url is an image link
		if '.jpg' in url or '.png' in url or '.jpeg' in url:
			img_list.append(url)
			if not empty_caption:
				if len(captions)-1 < counter:
					caption_list.append(title)
				else:
					cap = captions[counter].replace("/", " ")
					caption_list.append(cap)
					counter += 1


	#gets a list of existing photos and removes them from the photo links
	existingPhotos = os.listdir(path_str)
	img_list_novel = []
	match_og_type = []
	for url in img_list:
		match = re.search(r'/([\w-]+\.(?:jpg|jpeg|png))/', url)
		if match is not None:
			filename = match.group(1)
			arr_url = url.split('/')
			for og in arr_url:
				if 'jpg' in og or '.jpeg' in og or '.png' in og:
					match_og_type.append(og.replace("_", " "))
			'''
			if '.jpg' in url:
				match_type.append('.jpg')
			if '.jpeg' in url:
				match_type.append('.jpeg')
			if '.png' in url:
				match_type.append('.png')
			'''
			if filename not in existingPhotos:
				img_list_novel.append(url)



	#iterate list and download images
	for i in range(len(img_list_novel)):
		if not empty_caption:
			res_path = path_str + "/" + caption_list[i] + " " + match_og_type[i]
		else:
			res_path = path_str
		wget.download(img_list_novel[i], out = res_path, bar=None)


def placements_grab(url_link, resident_folder):
	'''
	Grab the tournament results however how to organize
	Takes in a url_link that is a string.
	and resident_folder
	e.g. KR/
	'''
	try:
		response = requests.get(
            url=url_link,
        )
	except requests.exceptions.ConnectionError:
		print(f"Connection Error for {url_link} in placements_grab")
		return url_link
	if response.status_code != 200:
		print("BAD STATUS placement")
		return url_link
	
	soup = BeautifulSoup(response.content, 'html.parser')

	#use this for file path later
	title = soup.find("span", class_="mw-page-title-main")
	if title is None:
		title = soup.find(id="firstHeading")

	title = title.string.strip()

	dir_name = title.replace("/", "_").replace(" ","_")

	path_str = "./" + resident_folder + dir_name
	if not os.path.exists(path_str):
		# Create a new directory because it does not exist
		os.makedirs(path_str)

	file_str = path_str + "/"+ dir_name + ".csv"

	#if the .csv file already exists, rename it
	if os.path.isfile(file_str):
		renameNumber = 1
		newName = file_str[:-4] + str(renameNumber) + '.csv'
		while os.path.isfile(newName):
			renameNumber += 1
			newName = file_str[:-4] + str(renameNumber) + '.csv'
		os.rename(file_str, newName)

	placements = soup.find("table", {"class": "wikitable sortable hoverable-rows"}).find_all('tr')
	placements = placements[2:]
	placement_list = []
	for place in placements:
		cells = place.find_all('td')
		placement_list.append([cells[1].get_text(strip=True), cells[2].get_text(strip=True), cells[4].get_text(strip=True)])

	with open(file_str, "w", newline="") as f:
		writer = csv.writer(f)
		writer.writerows(placement_list)


def grab_all_players(url_link):
	'''
	takes in url_link of each region and collects all url of each player to feed in
	Should output
	Returns 2 lists, first one is list of names and the second is list of urls
	'''
	#append since the stuff from the table is limited
	wiki_url = "https://lol.fandom.com"
	response = requests.get(
		url=url_link,
	)
	if response.status_code != 200:
		print("BAD STATUS grab players")
		return
	soup = BeautifulSoup(response.content, 'html.parser')

	url_list = []
	name_list = []

	url_table = soup.find("table", {"class": "cargoTable sortable"}).find_all('td', {"class": "field_ID"})
	for urls in url_table:
		name_list.append(urls.find('a').get_text())
		url_list.append(wiki_url + urls.find('a')["href"])

	assert len(url_list) == len(name_list)
	return name_list, url_list


def append_error(error_message, error_file):
    with open(error_file, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([error_message])



def scrapePlayersFromURL(url, folder):

	_, player_urls = grab_all_players(url)

	counter = 1
	for player_url in player_urls:
		print(str(round(counter/len(player_urls)*100, ndigits=2)) + "% done: " + player_url)
		
		response_placement = placements_grab(player_url+"/Tournament_Results", folder)
		if response_placement is not None:
			append_error(response_placement, './placement_errors.csv')
		
		response_image = image_grab(player_url, folder)
		if response_image is not None:
			append_error(response_image, './image_errors.csv')

		counter += 1
	return



def main():

	folders = ['NA/', 'CN/', "KR/"]
	#folders = ['CN/', "KR/"]

	urls = ['https://lol.fandom.com/wiki/North_American_Players', 'https://lol.fandom.com/wiki/Chinese_Players', 'https://lol.fandom.com/wiki/Korean_Players']
	#urls = [ 'https://lol.fandom.com/wiki/Chinese_Players', 'https://lol.fandom.com/wiki/Korean_Players']
	for (folder, url) in zip(folders, urls):
		
		activePlayersUrl = url
		freeAgentUrl = url + '/Free_Agents'
		retiredPlayersUrl = url + '/Retired'

		print("now processing: " + folder[:-1] + ' active players')
		scrapePlayersFromURL(activePlayersUrl, folder)
		
		print("now processing: " + folder[:-1] + ' free agents')
		scrapePlayersFromURL(freeAgentUrl, folder)
		
		print("now processing: " + folder[:-1] + ' retired players')
		scrapePlayersFromURL(retiredPlayersUrl, folder)


	#special case to process EU
	url = 'https://lol.fandom.com/wiki/EMEA_Players'
	urls = [url, url+'/Free_Agents', url+'/Free_Agents/N-S', url+'/Free_Agents/G-M', url + '/Free_Agents/T-Z']

	for urlEU in urls:
		scrapePlayersFromURL(urlEU, 'EU/')


if __name__ == "__main__":
    main()
	#image_grab('https://lol.fandom.com/wiki/Tuesday_(Jean-Sébastien_Thery)', 'Test/')
	#scrapePlayersFromURL('https://lol.fandom.com/wiki/Diamond_(David_Bérubé)', 'KR/')