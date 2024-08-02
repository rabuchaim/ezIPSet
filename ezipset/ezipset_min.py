"""ezIPSet Minified v1.0.0 - A pure Python library to manage ipset rules"""
##─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
import os,re,tempfile,subprocess,random,string,gzip,shlex,time,datetime as dt
from typing import Union,Literal
class ezIPSetError(Exception):
	def __init__(self,message):self.message='\x1b[38;2;255;99;71m'+str(message)+'\x1b[0m';super().__init__(self.message)
	def __str__(self):return self.message
	def __repr__(self):return self.message
class ezIPSet:
	__appname__='ezIPSet';__version__='1.0.0';VALID_SET_TYPES={'bitmap:ip':['counters','comment','skbinfo'],'bitmap:ip,mac':['counters','comment','skbinfo'],'bitmap:port':['counters','comment','skbinfo'],'hash:ip':['counters','comment','forceadd','skbinfo','bucketsize'],'hash:ip,mac':['bucketsize'],'hash:ip,mark':['forceadd','skbinfo','bucketsize'],'hash:ip,port':['counters','comment','forceadd','skbinfo','bucketsize'],'hash:ip,port,ip':['counters','comment','forceadd','skbinfo','bucketsize'],'hash:ip,port,net':['nomatch','counters','comment','forceadd','skbinfo','bucketsize'],'hash:mac':['bucketsize'],'hash:net':['nomatch','counters','comment','forceadd','skbinfo','bucketsize'],'hash:net,iface':['nomatch','counters','comment','forceadd','skbinfo','bucketsize','wildcard'],'hash:net,net':['forceadd','skbinfo','bucketsize'],'hash:net,port':['nomatch','counters','comment','forceadd','skbinfo','bucketsize'],'hash:net,port,net':['forceadd','skbinfo','bucketsize'],'list:set':['counters','comment','skbinfo']}
	def __init__(self,ipset_command='ipset',command_timeout=5,raise_on_errors=True,debug=False,**kwargs):
		" Initializes an instance of the ezIPSet class. Check `man ipset` for more information.\n\n        Usage example:\n        ```python\n        from ezipset import ezIPSet\n        with ezIPSet() as ipset:\n            print(ipset.get_ipset_version())\n        ```\n            \n        Args:\n            - ipset_command (str): The command to execute IPSet. Defaults to 'ipset'.\n            - command_timeout (int): The timeout value for IPSet commands in seconds. Defaults to 5.\n            - raise_on_errors (bool): Whether to raise an exception on IPSet errors. Defaults to True.\n            - debug (bool): Whether to enable debug mode. Defaults to False.\n        "
		if not debug:
			debug=bool(os.environ.get('EZIPSET_DEBUG','')!='')
			if not debug:self._debug=self.__debug_empty
		self.ipset_command=ipset_command;self.command_timeout=command_timeout;self.raise_on_errors=raise_on_errors;self.__decimal_places=kwargs.get('elapsed_decimal_places',9);self.last_command_elapsed_time='0.'+'0'*self.__decimal_places;self.get_ipset_version();self.get_set_names();self.__IPSET_RE_LIST_MEMBERS=re.compile('.*Members:\n(.*|$)',re.DOTALL)
		if self.protocol==7:self.__IPSET_RE_LIST_TERSE=re.compile('Name:\\s(.*?)\nType:\\s(.*?)\nRevision:\\s(.*?)\nHeader:\\s(.*?)\nSize in memory:\\s(.*?)\nReferences:\\s(.*?)\nNumber of entries:\\s(.*?)\n',re.DOTALL)
		elif self.protocol==6:self.__IPSET_RE_LIST_TERSE=re.compile('Name:\\s(.*?)\\sType:\\s(.*?)\\sRevision:\\s(.*?)\\sHeader:\\s(.*?)\\sSize in memory:\\s(.*?)\\sReferences:\\s(.*?)\\s',re.DOTALL)
		else:
			if self.raise_on_errors:raise ezIPSetError(f"Unknown protocol - {self.get_ipset_version()}")
			print(f"Cannot start ezIPSet() - Unknown protocol - {self.get_ipset_version()}")
	def __enter__(self):'Returns the instance of the ezIPSet class.';return self
	def __exit__(self,type,value,traceback):'Closes the instance of the ezIPSet class.'
	@property
	def version(self):'Returns the version of IPSet\n        \n        Just call: `ipset().version`';return self.__version
	@property
	def protocol(self):'Returns the protocol version of IPSet\n        \n        Just call: `ipset().protocol`';return int(self.__protocol)
	@property
	def set_names(self):'Returns a list with all IPSet set names.\n        \n        Just call: `ipset().set_names`';return self.__set_names
	def __debug_empty(self,message):...
	def _debug(self,message):print(f"[38;2;0;255;0m{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [DEBUG]: {str(message)}[0m")
	def __run_command(self,command_to_run,command_timeout=5,raise_on_errors=False,update_elapsed_time=True):
		'Runs an ipset command line and returns a list with 2 values: [(True|False),(output|error)] and\n        save the elapsed time in the property `last_command_elapsed_time` (a string formatted with 9 decimal places).\n        \n        Returns: [bool(return_code == 0), result:str] \n        '
		try:start_time=time.monotonic();cmd2run=shlex.split(f"{self.ipset_command} {command_to_run}");self._debug(f"Running command: {cmd2run}");process=subprocess.Popen(cmd2run,universal_newlines=True,shell=False,stderr=subprocess.PIPE,stdout=subprocess.PIPE,stdin=subprocess.PIPE);result,error=process.communicate(timeout=command_timeout)
		except subprocess.TimeoutExpired:
			process.kill()
			if raise_on_errors:raise ezIPSetError(f"Command timeout ({str(cmd2run)})")from None
		except FileNotFoundError:
			if raise_on_errors:raise ezIPSetError(f"File not found ({str(cmd2run)})")from None
		try:
			if process.returncode!=0:result=error
			if update_elapsed_time:self.last_command_elapsed_time=f"%.{self.__decimal_places}f"%(time.monotonic()-start_time)
			self.last_command_output=result.strip();self._debug(self.last_command_output);return[process.returncode==0,self.last_command_output]
		finally:del result,error
	def __update_set_names(self):
		'Internal function to update set names and don´t update the elapsed time of last command.\n        Used after any other function that modifies/create/destroy/restore a set.';result,output=self.__run_command('list -name',update_elapsed_time=False)
		if not result:self.__set_names.clear()
		self.__set_names=output.split('\n')
	def get_ezipset_version(self):' Returns the version of the ezIPSet library.';return f"{self.__version__}"
	def get_ipset_version(self):
		'Returns the current version of IPSet. This function will always raise an error if failed.\n        \n        Or you can call the properties: `ipset().version` or `ipset().protocol`\n        ';result,output=self.__run_command('--version')
		if not result:self.__version='0.0';self.__protocol='0';raise ezIPSetError(f"Failed to get ipset --version. Check if the 'ipset' extension is correctly installed.")
		else:self.__version,self.__protocol=output.split(',');_,self.__version=self.__version.split('v');_,self.__protocol=self.__protocol.split(': ');return output
	def save(self,to_file=None,gzipped=False,compression_level=9,overwrite_if_exists=False)->Union[str,bool]:
		"Saves the current IPSet rules to a file or returns the output.\n\n        Args:\n            - to_file (str, optional): The file path to save the IPSet rules. If None, it will return the output.\n            - gzipped (bool, optional): Whether to gzip the output file. Defaults to False.\n            - compression_level (int, optional): The compression level for gzip. Defaults to 9.\n            - overwrite_if_exists (bool, optional): Overwrite if the 'to_file' already exists. Defaults to False.\n\n        Returns:\n            - Union[str, bool]: If `to_file` is None, it returns the output. Otherwise, it returns True if the save operation is successful, False otherwise.\n\n        Raises:\n            - ezIPSetError: If the save operation fails and `raise_on_errors` is True.\n        "
		if to_file is not None:
			if not overwrite_if_exists and os.path.isfile(to_file):
				if self.raise_on_errors:raise ezIPSetError(f"File already exists ({str(to_file)})")
				return False
		result,output=self.__run_command('save')
		if result:
			if to_file is not None:
				gzipped=True if to_file.endswith('.gz')else gzipped;to_file=to_file+'.gz'if gzipped and not to_file.endswith('.gz')else to_file
				try:
					with gzip.GzipFile(filename=to_file,mode='wb',compresslevel=compression_level)if gzipped else open(to_file,'w')as f:f.write(output.encode()if gzipped else output);return True
				except Exception as ERR:
					if self.raise_on_errors:raise ezIPSetError(f"Failed to save ipset rules to file ({str(to_file)}) {str(ERR)}")from None
					return False
			return output
		elif self.raise_on_errors:raise ezIPSetError(f"Failed to save ipset rules")from None
	def restore(self,file_to_restore,skip_create_sets=False,skip_add_entries=False,ignore_if_exists=False):
		"Restores the IPSet rules from a file.\n\n        Args:\n            - file_to_restore (str): The path of the file to restore the IPSet rules from.\n            - skip_create_sets (bool, optional): Whether to skip the 'create' commands in the file. Defaults to False.\n            - skip_add_entries (bool, optional): Whether to skip the 'add' commands in the file. Defaults to False.\n            - ignore_if_exists (bool, optional): Whether to ignore if the IPSet already exists. Defaults to False.\n\n        Returns:\n            - bool: True if the IPSet rules are successfully restored, False otherwise.\n        "
		if not os.path.isfile(file_to_restore):
			if self.raise_on_errors:raise ezIPSetError(f"Cannot access/locate the specified file '{file_to_restore}'")
			return False
		try:
			if file_to_restore.endswith('.gz'):
				with gzip.open(file_to_restore,'r')as f:textfile=f.readlines()
				textfile=[item.strip().decode()for item in textfile]
			else:
				with open(file_to_restore,'r')as f:textfile=f.readlines()
				textfile=[item.strip()for item in textfile]
		except Exception as ERR:
			if self.raise_on_errors:raise ezIPSetError(f"Failed to read the file {file_to_restore} - {str(ERR)}")from None
			return False
		if skip_create_sets:textfile=[item for item in textfile if not item.startswith('create ')]
		if skip_add_entries:textfile=[item for item in textfile if not item.startswith('add ')]
		if(skip_add_entries or skip_create_sets)or file_to_restore.endswith('.gz'):
			random_text=''.join(random.choice(string.ascii_lowercase)for _ in range(6));new_file_to_restore=os.path.join(tempfile.gettempdir(),'ipset_restore_file-'+random_text)
			with open(new_file_to_restore,'w')as f:f.writelines('\n'.join(textfile))
		result,output=self.__run_command(f"restore {'-exist'if ignore_if_exists else''} -file {new_file_to_restore}")
		try:
			if not result:
				if self.raise_on_errors:raise ezIPSetError(f"Failed to restore file {str(file_to_restore)} {output}")from None
				return False
			return True
		finally:self.__update_set_names();os.remove(new_file_to_restore)
	def destroy_set(self,setname_to_destroy):
		'Destroys an IPSet set.\n\n        Args:\n            - setname_to_destroy (str): The name of the IPSet set to destroy.\n\n        Returns:\n            - bool: True if the IPSet set is successfully destroyed, False otherwise.\n        ';result,output=self.__run_command(f"destroy {setname_to_destroy}")
		try:
			if not result:
				if self.raise_on_errors:raise ezIPSetError(f"Failed to destroy ipset set ({str(setname_to_destroy)}) {output}")from None
				return False
			return True
		finally:self.__update_set_names()
	def destroy_all(self):
		'Destroys ALL sets.\n\n        Returns:\n            - bool: True if successfully destroyed all, False otherwise.\n        ';start_time=time.monotonic();ipset_list=self.get_set_names()
		for ipset_name in ipset_list:
			if self.destroy_set(ipset_name):self.set_names.pop(self.set_names.index(ipset_name))
		self.last_command_elapsed_time=f"%.{self.__decimal_places}f"%(time.monotonic()-start_time);return True
	def rename_set(self,old_setname,new_setname):
		'Renames an IPSet set. \n\n        Args:\n            - old_setname (str): The current name of the IPSet set.\n            - new_setname (str): The new name of the IPSet set.\n\n        Returns:\n            - bool: True if the IPSet set is successfully renamed, False otherwise.\n        ';result,output=self.__run_command(f"rename {old_setname} {new_setname}")
		if not result:
			if self.raise_on_errors:raise ezIPSetError(f"Failed to rename ipset set ({str(old_setname)} to {str(new_setname)}) {output}")from None
			return False
		self.__update_set_names();return True
	def swap_set(self,setname_from,setname_to):
		'Swaps two IPSet sets. \n\n        Args:\n            - setname_from (str): The first IPSet set name.\n            - setname_to (str): The second IPSet set name.\n\n        Returns:\n            - bool: True if the IPSet sets are successfully swapped, False otherwise.\n        ';result,output=self.__run_command(f"swap {setname_from} {setname_to}")
		if not result:
			if self.raise_on_errors:raise ezIPSetError(f"Failed to swap ipset sets ({str(setname_from)} and {str(setname_to)}) {output}")from None
			return False
		return True
	def flush_set(self,setname):
		'Flushes an IPSet set.\n\n        Args:\n            - setname (str): The name of the IPSet set to flush.\n\n        Returns:\n            - bool: True if the IPSet set is successfully flushed, False otherwise.\n        ';result,output=self.__run_command(f"flush {setname}")
		if not result:
			if self.raise_on_errors:raise ezIPSetError(f"Failed to flush ipset set ({str(setname)}) {output}")from None
			return False
		return True
	def flush_all(self,ignore_errors=False):
		'Flushes all IPSet sets.\n\n        Args:\n            - ignore_errors (bool, optional): Whether to ignore errors. Defaults to False.\n\n        Returns:\n            - bool: True if all IPSet sets are successfully flushed, False otherwise.\n        ';result,output=self.__run_command('flush')
		if not result:
			if self.raise_on_errors and not ignore_errors:raise ezIPSetError(f"Failed to flush all ipset sets {output}")from None
			return False
		return True
	def get_all_sets(self,with_members=True,sorted=False):
		'Returns a list with all IPSet information as a dict (with headers and with members).\n\n        Args:\n            - with_members (bool, optional): Whether to include the members of the set. Defaults to True.\n\n        Returns:\n            - list: A list with dictionaries with all information of the IPSet set.        \n        ';return_list=[];start_time=time.monotonic();set_names=self.get_set_names()
		for set_name in set_names:return_list.append(self.get_set(set_name,with_members=with_members,sorted=sorted))
		self.last_command_elapsed_time=f"%.{self.__decimal_places}f"%(time.monotonic()-start_time);return return_list
	def get_set_names(self):
		'Returns a list with all IPSet set names.';result,output=self.__run_command('list -name')
		if not result:
			if self.raise_on_errors:raise ezIPSetError(f"Failed to list ipset set names {output}")from None
			return[]
		self.__set_names=output.split('\n');return self.__set_names
	def get_set(self,setname,with_members=True,sorted=False):
		'Returns a dictionary with all information of an IPSet set.\n\n        Args:\n            - setname (str): The name of the IPSet set.\n            - with_members (bool, optional): Whether to include the members of the set. Defaults to True.\n\n        Returns:\n            - dict: A dictionary with all information of the IPSet set.\n        ';start_time=time.monotonic();set_header=self.get_set_header(setname)
		if with_members:set_members=self.get_set_members(setname,sorted=sorted);set_header.update({'members':set_members.copy()});set_members.clear();del set_members
		self.last_command_elapsed_time=f"%.{self.__decimal_places}f"%(time.monotonic()-start_time);return set_header
	def get_set_header(self,setname):
		'Returns a dictionary with the header information of an IPSet set.\n\n        Args:\n            - setname (str): The name of the IPSet set.\n\n        Returns:\n            - dict: A dictionary with the header information of the IPSet set.\n        ';start_time=time.monotonic();result,output=self.__run_command(f"list {setname} -terse")
		if not result:
			if self.raise_on_errors:raise ezIPSetError(f"Failed to list ipset set headers ({str(setname)}) {output}")from None
			return{}
		name,type,revision,header,size_in_memory,references,number_of_entries=self.__IPSET_RE_LIST_TERSE.search(output+'\n').groups();header_dict={};header_orig_line=header;header=shlex.split(header);params_to_pop=['comment','counters','skbinfo']
		for param in params_to_pop:
			if param in header:header_dict[param]=True;header.pop(header.index(param))
		for i in range(0,len(header),2):
			param_key=header[i];param_value=header[i+1]
			if str(param_value).isdigit():param_value=int(param_value)
			header_dict[param_key]=param_value
		header_dict=dict(sorted(header_dict.items(),key=lambda x:x[0]));self.last_command_elapsed_time=f"%.{self.__decimal_places}f"%(time.monotonic()-start_time);return{'name':name,'type':type,'revision':int(revision),'header':header_dict,'header_orig_line':header_orig_line,'size_in_memory':int(size_in_memory),'references':int(references),'number_of_entries':int(number_of_entries)}
	def get_set_members(self,setname,sorted=False):
		'Returns a list with all members of an IPSet set.\n\n        Args:\n            - setname (str): The name of the IPSet set.\n\n        Returns:\n            - list: A list with all members of the IPSet set.\n        ';start_time=time.monotonic();members_dict={};result,output=self.__run_command(f"list {setname} {'-sorted'if sorted else''}")
		if not result:
			if self.raise_on_errors:raise ezIPSetError(f"Failed to list ipset set members ({str(setname)}) {output}")from None
			return{}
		members_list=self.__IPSET_RE_LIST_MEMBERS.search(output+'\n').group(1).strip().split('\n');members_list=[shlex.split(item.replace('\\"','\\ "'),comments=True)for item in members_list if item!='']
		if len(members_list)>0:
			for item in members_list:
				key=item[0];params=item[1:];param_dict={}
				for i in range(0,len(params),2):
					param_key=params[i];param_value=params[i+1]
					if str(param_value).isdigit():param_value=int(param_value)
					param_dict[param_key]=param_value
				members_dict[key]=param_dict
		members_list.clear();del members_list;self.last_command_elapsed_time=f"%.{self.__decimal_places}f"%(time.monotonic()-start_time);return members_dict
	def add_entry(self,set_name,entry,timeout=None,comment=None,packets=None,bytes=None,skbmark=None,skbprio=None,skbqueue=None,ignore_if_exists=False):
		'\n        Add an entry to the specified set.\n\n        Args:\n            - set_name (str): The name of the set to add the entry to.\n            - entry (str): The entry to be added.\n            - ignore_if_exists (bool, optional): Whether to ignore if the entry already exists. Defaults to False.\n            \n            Others parameters (if applicable):\n            \n            - timeout (int, optional): The timeout value for the entry in seconds. Defaults to None.\n            - comment (str, optional): A comment for the entry. Note: IPSet does not accept double quotes in comments (even with escapes). Defaults to None.\n            - packets (int, optional): The number of packets associated with the entry. Defaults to None.\n            - bytes (int, optional): The number of bytes associated with the entry. Defaults to None.\n            - skbmark (str, optional): The skbmark value for the entry (ex: 0x1111/0xff00ffff). Defaults to None.\n            - skbprio (str, optional): The skbprio value for the entry (ex: 1:10). Defaults to None.\n            - skbqueue (int, optional): The skbqueue value for the entry (ex: 10). Defaults to None.\n            \n        Returns:\n            - bool: True if the entry was successfully added, False otherwise.\n        ';start_time=time.monotonic();add_command_line=f"add {set_name} {entry} "
		if timeout is not None:add_command_line+=f"timeout {str(int(timeout))} "
		if comment is not None:add_command_line+=f'comment "{comment}" '
		if packets is not None:add_command_line+=f"packets {str(int(packets))} "
		if bytes is not None:add_command_line+=f"bytes {str(int(bytes))} "
		if skbmark is not None:add_command_line+=f"skbmark {skbmark} "
		if skbprio is not None:add_command_line+=f"skbprio {skbprio} "
		if skbqueue is not None:add_command_line+=f"skbqueue {str(int(skbqueue))} "
		add_command_line+=f"{'-exist'if ignore_if_exists else''}";result,output=self.__run_command(add_command_line)
		if not result:
			if self.raise_on_errors:raise ezIPSetError(f"Failed to add entry to ipset set ({str(set_name)}) {output}")from None
			return False
		self.last_command_elapsed_time=f"%.{self.__decimal_places}f"%(time.monotonic()-start_time);return True
	def test_entry(self,set_name,entry,raise_on_test_failed=False):
		'Tests if an entry is in the specified set.\n\n        Args:\n            - set_name (str): The name of the set to test the entry in.\n            - entry (str): The entry to test.\n            - raise_on_test_failed (bool, optional): Whether to raise an exception if the test fails. Defaults to False. \n                                              This override the `raise_on_errors` property.\n        \n        Returns:\n            - bool: True if the entry is in the set, False otherwise.\n        ';result,output=self.__run_command(f"test {set_name} {entry}")
		if not result:
			if self.raise_on_errors and raise_on_test_failed:raise ezIPSetError(f"{output}")from None
			return False
		return True
	def del_entry(self,set_name,entry,ignore_if_not_exists=False,raise_if_not_exists=False):
		'Deletes an entry from the specified set.\n\n        Args:\n            - set_name (str): The name of the set to delete the entry from.\n            - entry (str): The entry to delete.\n            - ignore_if_not_exists (bool, optional): Whether to ignore if the entry does not exist. Defaults to False.\n            - raise_if_not_exists (bool, optional): Whether to raise an exception if the entry does not exist. Defaults to False. \n                                                    This override the `raise_on_errors` property.\n\n        Returns:\n            - bool: True if the entry was successfully deleted, False otherwise.\n        ';result,output=self.__run_command(f"del {set_name} {entry} {'-exist'if ignore_if_not_exists else''}")
		if not result:
			if self.raise_on_errors and raise_if_not_exists:raise ezIPSetError(f"Failed to delete {entry} from set ({str(set_name)}) {output}")from None
			return False
		return True
	def create_set(self,set_name,set_type:Literal['bitmap:ip','bitmap:ip,mac','bitmap:port','hash:ip','hash:ip,mac','hash:ip,mark','hash:ip,port','hash:ip,port,ip','hash:ip,port,net','hash:mac','hash:net','hash:net,iface','hash:net,net','hash:net,port','hash:net,port,net','list:set'],family:Literal['inet','inet6']='inet',timeout=None,with_comment=False,with_counters=False,with_skbinfo=False,nomatch=False,forceadd=False,wildcard=False,hashsize=None,maxelem=None,bucketsize=None,ignore_if_exists=False):
		"Creates an IPSet set. See `man ipset` for more information about the parameters.\n\n        Args:\n            - set_name (str): The name of the set to create.\n            - set_type (str): The type of the set to create.\n            - family (str, optional): The family of the set ('inet' for IPv4 or 'inet6' for IPv6). Defaults to 'inet'.\n            - timeout (int, optional): The timeout value (like a time to live) for the set in seconds. Defaults to None.\n            - with_comment (bool, optional): Whether to include a comment in the set. Defaults to False.\n            - with_counters (bool, optional): Whether to include a counter (packets and bytes) in the set. Defaults to False.\n            - with_skbinfo (bool, optional): Whether to include skbinfo (skbmark, skbprio, skbqueue) in the set. Defaults to False.\n            - nomatch (bool, optional): Whether to create a nomatch set. Defaults to False.\n            - forceadd (bool, optional): Whether to force the add operation. Defaults to False.\n            - wildcard (bool, optional): Whether to create a wildcard set. Defaults to False.\n            - hashsize (int, optional): The hash size of the set. Defaults to None.\n            - maxelem (int, optional): The maximum number of elements in the set. Defaults to None. \n            - bucketsize (int, optional): The bucket size of the set. Defaults to None.\n            - ignore_if_exists (bool, optional): Whether to ignore if the set already exists. Defaults to False.\n            \n        Returns:\n            - bool: True if the set was successfully created, False otherwise.\n        ";start_time=time.monotonic()
		if set_type not in list(self.VALID_SET_TYPES.keys()):
			self.last_command_elapsed_time=f"%.{self.__decimal_places}f"%(time.monotonic()-start_time)
			if self.raise_on_errors:raise ezIPSetError(f"Invalid set type ({str(set_type)}). Valid values are: "+str(list(self.VALID_SET_TYPES.keys())).replace("', '","','")[1:-1]+'.')
			return False
		if family not in['inet','inet6']:
			self.last_command_elapsed_time=f"%.{self.__decimal_places}f"%(time.monotonic()-start_time)
			if self.raise_on_errors:raise ezIPSetError(f"Invalid 'family' ({str(family)}). Valid 'family' values are 'inet' or 'inet6'")
			return False
		create_command_line=f"{'family '+family+' 'if family is not None else''}{'timeout '+str(int(timeout))+' 'if timeout is not None else''}{'hashsize '+str(int(hashsize))+' 'if hashsize is not None else''}{'maxelem '+str(int(maxelem))+' 'if maxelem is not None else''}{'bucketsize '+str(int(bucketsize))+' 'if bucketsize is not None else''}{'comment 'if with_comment else''}{'counters 'if with_counters else''}{'skbinfo 'if with_skbinfo else''}{'nomatch 'if nomatch else''}{'forceadd 'if forceadd else''}{'wildcard 'if wildcard else''}";result,output=self.__run_command(f"create {set_name} {set_type} {create_command_line} {'-exist'if ignore_if_exists else''}")
		if not result:
			if self.raise_on_errors:raise ezIPSetError(f"Failed to create ipset set ({str(set_name)}) {output}")from None
			return False
		self.__update_set_names();return True
##─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────