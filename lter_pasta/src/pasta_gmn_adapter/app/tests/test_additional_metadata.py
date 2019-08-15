#!/usr/bin/env python

import xml.etree.ElementTree as ET

ns = {
  'eml': 'eml://ecoinformatics.org/eml-2.1.1',
}


def main():
  eml_str = open('knb-lter-nin-19-1.eml', 'r').read()

  tree = ET.ElementTree(ET.fromstring(eml_str))
  # tree = ET.parse('knb-lter-nin-19-1.eml')
  root = tree.getroot()

  # print(root.findall("./eml:eml/additionalMetadata[2]/metadata[1]", ns))
  replicationPolicy_list = root.findall(
    "additionalMetadata/metadata/replicationPolicy", ns
  )

  if len(replicationPolicy_list):
    ET.register_namespace(
      'd1v1', "http://ns.dataone.org/service/types/v1"
    ) #some name
    replication_policy = replicationPolicy_list[0]
    replication_policy.tag = '{http://ns.dataone.org/service/types/v1}' + replication_policy.tag



if __name__ == '__main__':
  main()
