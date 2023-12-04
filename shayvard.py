import jdatetime
from datetime import datetime
import requests
import base64
from bs4 import BeautifulSoup
import pathlib
from random import randint
from PIL import Image
import os
compimages=[]

# Function to check if a link has been scraped
def check_duplicate_links(link):
    with open('scraped_links.txt', 'r') as file:
        scraped_links = file.readlines()
        # Strip newline character from each line and check for the link
        scraped_links = [line.strip() for line in scraped_links]
        if link in scraped_links:
            return True
    return False

def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"File '{file_path}' has been successfully deleted.")
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    except PermissionError:
        print(f"You don't have permission to delete '{file_path}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

# define a function to compress pictures
def compress_image(input_image_path, output_image_path, quality=40):
    try:
        with Image.open(input_image_path) as img:
            img.save(output_image_path, quality=quality)
        print("Image compression successful!")
    except Exception as e:
        print(f"An error occurred: {e}")
# define a function to scrap and post to wordpress
def posttowordpress(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text ,'html.parser')
    # output = soup.select('time')
    # pdate = output[0]['datetime']
    # year = pdate[0:4]
    # month = pdate[5:6]
    # day = pdate[7:9]
    # gdate=jdatetime.date(int(year),int(month),int(day)).togregorian()
    today= datetime.today()
    # print(today , gdate , year,month,day)
    # print(str(today)[0:10])
    # if (str(today)[0:10] == gdate):
    title = soup.select_one('h1.post-tile')
    print(title.text)
    image = soup.select_one('div.feature-img img')
    src=image['src']
    alt=image['alt']
    mapping_table = str.maketrans({':': '-',' ': '-','.':'-'})
    todayf = str(today).translate(mapping_table)
    name = str(todayf)+'_'+str(randint(1000,9999))
    ext =  pathlib.Path(src).suffix
    fullname = name + ext
    with requests.get(src ,stream=True)as r:
        with open(fullname,'wb') as f:
            for img in r.iter_content(chunk_size=1024):
                f.write(img)
    # compress image to uplad to wordpress
    compimg = 'comp'+fullname
    compress_image(fullname,compimg)
    content = soup.select_one('div.entry-content')
    print(content.text)
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    base_url = 'http://localhost/wp/wp-json/wp/v2'
    user = 'mahdi'
    password = '81lx gbqU hHdB Q5Xy tIXR NBsp'

    creds = f"{user}:{password}"
    token = base64.b64encode(creds.encode()).decode('utf-8')
    headers = {"Authorization": f"Basic {token}"}
    media = {
        'file': (compimg, open(compimg, 'rb'), 'image/jpeg'),
        'caption': alt,
        'description': alt
    }

    mediaendpoint = f"{base_url}/media"
    image = requests.post(mediaendpoint, headers=headers, files=media)

    if image.status_code == 201:
        image_data = image.json()
        imageurl = image_data['guid']['rendered']
        print(f"Image uploaded successfully. URL: {imageurl}")
    else:
        print(f"Failed to upload image. Status code: {image.status_code}")
        print(image.text)  # Print the raw response for inspection
        imageurl = None  # Set image URL as None if upload fails
    # Post data
    post_data = {
        'date': now,
        'title': title.text,
        'content': f'<img src={imageurl} alt={alt}  > <br><article style="direction:rtl"> {content.text} <br> منبع: شایوردنیوز</article>',
        'status': 'publish'
    }
    # Endpoint for creating posts
    post_endpoint = f"{base_url}/posts"
    # Making the request
    response = requests.post(post_endpoint, headers=headers, json=post_data)
    print(token)
    if response.status_code == 201:
        print("Post created successfully!")
        delete_file(fullname)
        compimages.append(compimg)

    else:
        print(f"Failed to create post. Status code: {response.status_code}")

    try:
        print(response.json())
    except json.decoder.JSONDecodeError:
        print("Response is not in JSON format.")
        print(response.text)  # Print the raw response to inspect its format

searchurl='https://www.shayvardnews.com/?s=%D8%B1%D9%81%D8%B3%D9%86%D8%AC%D8%A7%D9%86'
response = requests.get(searchurl)
soup = BeautifulSoup(response.text ,'html.parser')
links=soup.select('div.bp-head h2 a')
for url in links:
    print(url['href']) 
    if not check_duplicate_links(url['href']):
        posttowordpress(url['href'])
        with open('scraped_links.txt', 'a') as file:
                file.write(url['href'] + '\n')
for img in compimages:
    delete_file(img)