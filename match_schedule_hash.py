import mwparserfromhell
from river_mwclient import *

ERROR_LOCATION = 'MatchSchedule Ordering Errors'
ERROR_TEAMS_TEXT = 'Team 1 - {}; Team 2: {}'

def get_append_hash(hash, res):
	tl = mwparserfromhell.nodes.Template(name='MSHash')
	tl.add('hash', hash)
	tl.add('team1', res['Team1'])
	tl.add('team2', res['Team2'])
	return str(tl)

def verify_hash(template, team1, team2):
	team1_old = template.get('team1').value.strip()
	team2_old = template.get('team2').value.strip()
	if team1_old != 'TBD' and team1_old != team1:
		return False
	if team2_old != 'TBD' and team2_old != team2:
		return False
	return True

def get_hash_template(ms_hash, wikitext):
	for template in wikitext.filter_templates():
		if template.has('hash') and template.get('hash').value.strip() == ms_hash:
			return template
	return None
	
def get_error_text(res, tl):
	match_info = 'Tab - {}; initialorder: {}'.format(res['Tab'], res['Order'])
	original = ERROR_TEAMS_TEXT.format(tl.get('team1').value.strip(), tl.get('team2').value.strip())
	new = ERROR_TEAMS_TEXT.format(res['Team1'], res['Team2'])
	return 'Match Info: {}\n<br>Originally: {}\n<br>Now: {}<br>'.format(match_info, original, new)

def check_page(site: GamepediaSite, page_name):
	response = site.api('cargoquery', tables = 'MatchSchedule',
					  fields = 'InitialN_MatchInTab=Order, Team1, Team2, Tab, InitialPageAndTab',
					  where = '_pageName="%s"' % page_name
					  )
	result = response['cargoquery']
	hash_location = site.pages[page_name + '/Hash']
	text = hash_location.text()
	wikitext = mwparserfromhell.parse(text)
	hashes_to_add = []
	for res in result:
		data = res['title']
		if data['InitialPageAndTab'] != '':
			ms_hash = data['InitialPageAndTab'].split('_')[1] + '_' + data['Order']
		else:
			ms_hash = data['Tab'] + '_' + data['Order']
		hash_template = get_hash_template(ms_hash, wikitext)
		if not hash_template:
			hashes_to_add.append(get_append_hash(ms_hash, data))
		elif not verify_hash(hash_template, data['Team1'], data['Team2']):
			site.error_content(title=page_name, text=get_error_text(data, hash_template))
			hash_template.add('team1', data['Team1'])
			hash_template.add('team2', data['Team2'])
		else: # There could be a TBD that we need to replace
			hash_template.add('team1', data['Team1'])
			hash_template.add('team2', data['Team2'])
	if str(wikitext) != '':
		hashes_to_add.insert(0, str(wikitext))
	new_text = '\n'.join(hashes_to_add)
	if text != new_text:
		hash_location.save(new_text)

def run(site, revs):
	done = {}
	for rev in revs:
		title = rev['title']
		if title in done:
			continue
		done[title] = True
		if title.startswith('Data:'):
			check_page(site, title)
	site.report_all_errors(ERROR_LOCATION)

if __name__ == '__main__':
	site = login('me', 'lol')
	run(site, site.recentchanges_by_interval(200))
