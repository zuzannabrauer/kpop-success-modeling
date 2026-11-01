import requests
import re
import csv
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

girl_groups_list_url = 'https://kprofiles.com/k-pop-girl-groups/'
boy_groups_list_url = 'https://kprofiles.com/k-pop-boy-groups/'


def get_groups_profiles_links(list_url):
    response = requests.get(list_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    content = soup.select_one('.entry-content')

    profiles_links = []
    for link in content.select('a[href]'):
        url = urljoin(list_url, link['href'])
        parsed_url = urlparse(url)
        if 'profile' in parsed_url.path and url not in profiles_links:
            profiles_links.append(url)
    return profiles_links


IDOL_FIELDS = (
        'Group', 'Stage Name', 'Birth Name', 'Real Name', 'English Name', 'Korean Name',
        'Chinese Name', 'Former Stage Names', 'Birthday', 'Position(s)',
        'Zodiac Sign', 'Chinese Zodiac Sign', 'Height', 'Official Height',
        'Weight', 'Blood Type', 'MBTI Type', 'Nationality',
        'Representative Symbol', 'Representative Color', 'Representative Animal',
        'Representative Number', 'Representative Emoji', 'Sub-Unit',
    )


def get_idols_details(group_profile_link):
    response = requests.get(group_profile_link)
    soup = BeautifulSoup(response.content, 'html.parser')
    content = soup.select_one('.entry-content')
    group_name = re.split(r'\s+Members?\s+Profile', soup.select_one('h1').get_text(strip = True), flags = re.IGNORECASE)[0]

    idols_details = []
    fields = IDOL_FIELDS
    aliases = {
        'Former Stage Name': 'Former Stage Names',
        'Birthdate': 'Birthday',
        'MBIT Type': 'MBTI Type',
        'Position': 'Position(s)',
    }

    def split_combined_value(value):
        for index, character in enumerate(value):
            if character == '/':
                return value[:index].strip() or 'N/A', value[index + 1:].strip() or 'N/A'
        return value, value

    current_idol = None
    for paragraph in content.find_all('p'):
        paragraph_has_name = False
        for line_break in paragraph.find_all('br'):
            line_break.replace_with('\n')
        for line in paragraph.get_text().splitlines():
            label, separator, value = line.partition(':')
            if not separator:
                continue
            field = re.sub(r'\s+', ' ', label).strip()
            field = aliases.get(field, field)
            value = value.strip() or 'N/A'
            if field in {'Stage Name', 'Stage / Birth Name'} or (
                not paragraph_has_name and 'Name' in field
            ):
                current_idol = dict.fromkeys(fields, 'N/A')
                current_idol['Group'] = group_name
                idols_details.append(current_idol)
            if 'Name' in field:
                paragraph_has_name = True
            if current_idol is None:
                continue
            if field == 'Stage / Birth Name':
                current_idol['Stage Name'], current_idol['Birth Name'] = split_combined_value(value)
            elif field == 'Official Height / Real Height':
                current_idol['Official Height'], current_idol['Height'] = split_combined_value(value)
            elif field in fields:
                current_idol[field] = value

    return idols_details


idols_details = []
girl_group_profile_links = get_groups_profiles_links(girl_groups_list_url)
boy_group_profile_links = get_groups_profiles_links(boy_groups_list_url)

for group_link in girl_group_profile_links + boy_group_profile_links:
    group_idols = get_idols_details(group_link)
    idols_details.extend(group_idols)

output_file = open("kpop_idols_data.csv", 'w', newline = '', encoding = 'utf-8-sig')
writer = csv.DictWriter(output_file, fieldnames = IDOL_FIELDS)
writer.writeheader()
for idol in idols_details:
        writer.writerow(idol)
