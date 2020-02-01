from log_into_wiki import login


class CronTasks(object):
	"""Handles scheduling cron tasks that run based on sites' revisions and/or logs
	
	Initialize with number of minutes and set of wikis to create lists for, then
	run the tasks that you want run with run_logs or run_revs.
	Does NOT support running code that requires seeing both - in cases like that, separate
	the functionality into 2 separate functions.
	The set of wikis you run each individual task on will often be a subset of the total
	set of wikis, so re-specify that for each function defined.
	Use one file per interval because that's convenient for cron scheduling.
	"""
	def __init__(self, interval=1, wikis=None):
		self.all_wikis = wikis
		self.all_sites = {}
		self.all_revs = {}
		self.all_logs = {}
		for wiki in self.all_wikis:
			site = login('me', wiki)
			revs_gen = site.recentchanges_by_interval(interval)
			revs = [_ for _ in revs_gen]
			logs = site.logs_by_interval(interval)
			self.all_sites[wiki] = site
			self.all_revs[wiki] = revs
			self.all_logs[wiki] = logs
	
	def run_logs(self, fn, wikis, **kwargs):
		self._run_data(fn, wikis, self.all_logs, **kwargs)
	
	def run_revs(self, fn, wikis, **kwargs):
		self._run_data(fn, wikis, self.all_revs, **kwargs)
	
	def _run_data(self, fn, wikis, data, **kwargs):
		if wikis is None:
			return
		for wiki in wikis:
			try:
				fn(self.all_sites[wiki], data[wiki], **kwargs)
			except Exception as e:
				print(e)
				pass
