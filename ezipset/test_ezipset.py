#!/usr/bin/env python3
import unittest, time
from ezipset import ezIPSet

try:
    ipset = ezIPSet()
except Exception as ERR:
    raise Exception(f"Failed to initialize the class ezIPSet()")

ipset_to_test = ["ipset_unittest_1","ipset_unittest_2","ipset_unittest_3"]

class Test_ezIPSet(unittest.TestCase):
    def test_01_ipset_version(self):
        self.assertTrue(isinstance(ipset.protocol,int))
    def test_02_ipset_protocol(self):
        self.assertTrue(isinstance(ipset.version,str))
    def test_03_ipset_protocol_greater_equal_6(self):
        self.assertGreaterEqual(ipset.protocol,6)
    def test_04_ipset_create(self):
        for set_name in ipset_to_test:
            self.assertTrue(ipset.create_set(set_name,"hash:ip",timeout=2,ignore_if_exists=True))
    def test_05_ipset_rename(self):
        for set_name in ipset_to_test:
            self.assertTrue(ipset.rename_set(set_name,f"{set_name}_renamed"))            
    def test_06_ipset_add(self):
        for set_name in ipset_to_test:
            self.assertTrue(ipset.add_entry(set_name+"_renamed","1.2.3.4"))
            self.assertTrue(ipset.add_entry(set_name+"_renamed","5.6.7.8"))
            self.assertTrue(ipset.add_entry(set_name+"_renamed","9.10.11.12"))
            self.assertTrue(ipset.add_entry(set_name+"_renamed","13.14.15.16"))
            self.assertTrue(ipset.add_entry(set_name+"_renamed","17.18.19.20"))
    def test_07_del_entry(self):
        self.assertTrue(ipset.del_entry(ipset_to_test[0]+"_renamed","1.2.3.4"))
        self.assertTrue(ipset.del_entry(ipset_to_test[0]+"_renamed","5.6.7.8"))
    def test_08_swap_set(self):
        self.assertTrue(ipset.swap_set(ipset_to_test[0]+"_renamed",ipset_to_test[1]+"_renamed"))
    def test_09_get_members(self):
        self.assertEqual(len(ipset.get_set_members(ipset_to_test[0]+"_renamed")),5)
        self.assertEqual(len(ipset.get_set_members(ipset_to_test[1]+"_renamed")),3)
    def test_10_test_timeout_2_seconds(self):
        time.sleep(2)
        self.assertEqual(len(ipset.get_set_members(ipset_to_test[0]+"_renamed")),0)
        self.assertEqual(len(ipset.get_set_members(ipset_to_test[1]+"_renamed")),0)
    def test_11_flush_set(self):
        for set_name in ipset_to_test:
            self.assertTrue(ipset.flush_set(set_name+"_renamed"))
    def test_12_ipset_destroy(self):
        for set_name in ipset_to_test:
            self.assertTrue(ipset.destroy_set(set_name+"_renamed"))

if __name__ == '__main__':
    unittest.main(verbosity=2)