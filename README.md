# ezIPSet v1.0.0

## Introduction
ezIPSet is a pure Python library that provides a convenient way to manage ipset rules. It allows you to interact with IPSet using Python code, making it easier to create, modify, and delete IPSet sets. This library includes all the functions existing in IPSet and works with protocols 6 and 7 of IPSet.

IPSet is an extension for IPTables and allows you to manipulate tens of thousands of rules. To check if you have this extension installed on your Linux distribution, type `ipset --version`. If you get an error, you can easily install it with the command below.

For available methods in `ipset`, please refer to the [https://ipset.netfilter.org/ipset.man.html](https://ipset.netfilter.org/ipset.man.html).

## Installation of ezIPSet Library

```shell
pip install ezIPSet
```

## Installation of ipset extension for iptables

> *Installing this extension has no impact on the operation of IPTables.*

For Ubuntu/Debian:
```shell
apt update
apt install ipset
```

For RedHat/CentOS/Amazon Linux:
```shell
yum install ipset
```

## Usage
Once you have installed ezIPSet, you can start using it in your Python code. Here's a basic example:

```python
Python 3.12.4 (main, Jun  8 2024, 18:29:57) [GCC 11.4.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from ezipset import ezIPSet
>>> import json
>>> ipset = ezIPSet(raise_on_errors=False)
>>> ipset.version
'7.15'
>>> ipset.protocol
7
>>> ipset.set_names
['']
>>> ipset.create_set('IPSET_EXAMPLE1',set_type='hash:net',family='inet',timeout=1200,with_comment=True)
True
>>> ipset.create_set('IPSET_EXAMPLE2',set_type='hash:net',family='inet',with_comment=True)
True
>>> ipset.set_names
['IPSET_EXAMPLE1', 'IPSET_EXAMPLE2']
>>> 
>>> ipset.add_entry('IPSET_EXAMPLE1',"1.2.3.4/32",timeout=600,comment='just a comment for 1.2.3.4/32',ignore_if_exists=True)
True
>>> ipset.add_entry('IPSET_EXAMPLE1',"4.5.6.0/24",comment='the 4.5.6.0/24 network')
True
>>> ipset.add_entry('IPSET_EXAMPLE2',"10.20.30.0/24",comment='internal network')
True
>>> 
>>> ipset.add_entry('IPSET_EXAMPLE1',"4.5.6.0/24",comment='the 4.5.6.0/24 network')
False
>>> ipset.last_command_output
"ipset v7.15: Element cannot be added to the set: it's already added"
>>> 
>>> example1 = ipset.get_set("IPSET_EXAMPLE1")
>>> ipset.last_command_elapsed_time
'0.002981348'
>>> print(example1)
{'name': 'IPSET_EXAMPLE1', 'type': 'hash:net', 'revision': 7, 'header': {'bucketsize': 12, 'comment': True, 'family': 'inet', 'hashsize': 1024, 'initval': '0xb433b7ea', 'maxelem': 65536, 'timeout': 1200}, 'header_orig_line': 'family inet hashsize 1024 maxelem 65536 timeout 1200 comment bucketsize 12 initval 0xb433b7ea', 'size_in_memory': 701, 'references': 0, 'number_of_entries': 2, 'members': {'1.2.3.4': {'timeout': 507, 'comment': 'just a comment for 1.2.3.4/32'}, '4.5.6.0/24': {'timeout': 1112, 'comment': 'the 4.5.6.0/24 network'}}}
>>> print(json.dumps(example1,indent=3,sort_keys=False))
{
   "name": "IPSET_EXAMPLE1",
   "type": "hash:net",
   "revision": 7,
   "header": {
      "bucketsize": 12,
      "comment": true,
      "family": "inet",
      "hashsize": 1024,
      "initval": "0xb433b7ea",
      "maxelem": 65536,
      "timeout": 1200
   },
   "header_orig_line": "family inet hashsize 1024 maxelem 65536 timeout 1200 comment bucketsize 12 initval 0xb433b7ea",
   "size_in_memory": 701,
   "references": 0,
   "number_of_entries": 2,
   "members": {
      "1.2.3.4": {
         "timeout": 507,
         "comment": "just a comment for 1.2.3.4/32"
      },
      "4.5.6.0/24": {
         "timeout": 1112,
         "comment": "the 4.5.6.0/24 network"
      }
   }
}
>>> 
>>> example2_header = ipset.get_set_header("IPSET_EXAMPLE2")
>>> print(json.dumps(example2_header,indent=3,sort_keys=False))
{
   "name": "IPSET_EXAMPLE2",
   "type": "hash:net",
   "revision": 7,
   "header": {
      "bucketsize": 12,
      "comment": true,
      "family": "inet",
      "hashsize": 1024,
      "initval": "0xd1ea7d18",
      "maxelem": 65536
   },
   "header_orig_line": "family inet hashsize 1024 maxelem 65536 comment bucketsize 12 initval 0xd1ea7d18",
   "size_in_memory": 553,
   "references": 0,
   "number_of_entries": 1
}
>>> 
>>> example2_members = ipset.get_set_members("IPSET_EXAMPLE2")
>>> print(json.dumps(example2_members,indent=3,sort_keys=False))
{
   "10.20.30.0/24": {
      "comment": "internal network"
   }
}
```
## Methods and Properties 

### The creation of the object

- ```def __init__(self, ipset_command:str='ipset', command_timeout:int=5, raise_on_errors:bool=True, debug:bool=False, **kwargs):```

    - `ipset_command`: If the operating system's ipset command has been renamed, then provide the new name here. The command specified here will be inserted at the beginning of every command line you execute.
    - `command_timeout`: self explanatory. You can change this value at any time by accessing the `command_timeout` property without having to create the object again. If you're working with multiple 50K rule sets, you may need to increase this to 10 seconds or more. In stress tests, everything ran in under 2~3 seconds.
    - `raise_on_errors`: This is a good option to avoid exceptions. If you prefer to handle exceptions by your own, set this option to `True`, otherwise keep it as `False` and the function returns will never raise an exception, it will always be `True` or `False`.
    - `debug`: In this option, the executed commands and the outputs are displayed with a highlighted color in case you need to resolve any atypical situation that may be occurring with the library. Before opening an issue, run with this flag as `True` to monitor the behavior. It is also possible to activate the debug flag without touching the code by exporting an environment variable like this: `export EZIPSET_DEBUG=1`

    With each command executed, 3 properties are populated automatically:

    - `set_names`: This is the current list of names of all existing ipset sets. You do not need to keep calling the get_set_names() function. This property changes every time you create, rename or destroy a set.
    - `last_command_elapsed_time`: Here the elapsed time of the last command executed is recorded, in case you need to keep track of the elapsed times and adjust the `command_timeout` property if necessary.
    - `last_command_output`: If you chose `raise_on_errors=False` and some command returned "False", access this property to see the error message that the IPSet returned.

    When manipulating many dictionaries and lists, you need to pay attention to the memory consumption of these variables. A sporadic call or two will not cause problems, but in an application that manages firewall rules hundreds or thousands of times per hour, this becomes a problem. With ezIPSet you can use it as a context and release all the memory used by the library as soon as you leave the context block. Example:

    ```
    with ezIPSet() as ipset:
        all_sets = ipset.get_all_sets()
        print(ipset.set_names)
    ```

### Methods

## ezIPSet Minimal Library

In the library directory you will find the `ezipset_min.py` file, which is a complete and minified version of the library with only 220 lines, which allows you to copy the code and include it in your application, avoiding a dependency : )

The minified version was made with [python-minifier](https://github.com/dflook/python-minifier)  and is obviously difficult to read, but it is completely functional and identical to the normal version. It is just an option.

## Contributing
If you find any issues or have suggestions for improvements, feel free to contribute to the ezIPSet project. 

## License
ezIPSet is licensed under the MIT License. See the [LICENSE](https://github.com/example/ezIPSet/blob/main/LICENSE) file for more information.

## Sugestions, feedbacks, bugs...

[Open an issue](https://github.com/rabuchaim/ezIPSet/issues) or e-mail me: ricardoabuchaim at gmail.com
