# Copyright 2019 - The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# Minimal dependency script to query a set of
# publically available emulator and system image zip files.
import multiprocessing
import os
import sys
import urlfetch
import xml.etree.ElementTree as ET
SYSIMG_REPOS = [
    'https://dl.google.com/android/repository/sys-img/android/sys-img2-1.xml',
    'https://dl.google.com/android/repository/sys-img/google_apis/sys-img2-1.xml',
    'https://dl.google.com/android/repository/sys-img/google_apis_playstore/sys-img2-1.xml'
]
EMU_REPOS = [
    'https://dl.google.com/android/repository/repository2-1.xml',
]
CHANNEL_MAPPING = {
    "channel-0" : "stable",
    "channel-1" : "beta",
    "channel-2" : "dev",
    "channel-3" : "canary",
}
API_LETTER_MAPPING = {
    "10" : "G",
    "15" : "I",
    "16" : "J",
    "17" : "J",
    "18" : "J",
    "19" : "K",
    "21" : "L",
    "22" : "L",
    "23" : "M",
    "24" : "N",
    "25" : "N",
    "26" : "O",
    "27" : "O",
    "28" : "P",
    "29" : "Q",
}
class SysImgInfo(object):
    def __init__(self, pkg):
        details = pkg.find('type-details')
        self.api = details.find('api-level').text
        codename = details.find('codename')
        if codename is None:
            if self.api in API_LETTER_MAPPING:
                self.letter = API_LETTER_MAPPING[self.api]
            else:
                self.letter = "_"
        else:
            self.letter = codename.text
        self.tag = details.find('tag').find('id').text
        if self.tag == 'default':
            self.tag = 'android'
        self.abi = details.find('abi').text
        self.zip = pkg.find('.//url').text
        self.url = 'https://dl.google.com/android/repository/sys-img/%s/%s' % (
            self.tag, self.zip)
class EmuInfo(object):
    def __init__(self, pkg):
        rev = pkg.find('revision')
        rev_major = rev.find('major').text
        rev_minor = rev.find('minor').text
        rev_micro = rev.find('micro').text
        archives = pkg.find('archives')
        channel = pkg.find('channelRef')
        self.channel = CHANNEL_MAPPING[channel.attrib['ref']]
        self.version = "%s.%s.%s" % (rev_major, rev_minor, rev_micro)
        self.urls = {}
        for archive in archives:
            url = archive.find('.//url').text
            hostos = archive.find('host-os').text
            self.urls[hostos] = "https://dl.google.com/android/repository/%s" % url
def get_images_info():
    """Gets all the publicly available system images from the Android Image Repos.
         Returns a list of AndroidSystemImages that were found.
      """
    xml = []
    for url in SYSIMG_REPOS:
        response = urlfetch.get(url)
        if response.status == 200:
            xml.append(response.content)
    xml = [ET.fromstring(x).findall('remotePackage') for x in xml]
    # Flatten the list of lists into a system image objects.
    infos = [SysImgInfo(item) for sublist in xml for item in sublist]
    # Filter only for x86_64 images (TODO: allow other types)
    x64_images = filter(lambda info: info.abi == "x86_64", infos)
    return x64_images
def get_emus_info():
    """Gets all the publicly available system images from the Android Image Repos.
         Returns a list of AndroidSystemImages that were found.
      """
    xml = []
    for url in EMU_REPOS:
        response = urlfetch.get(url)
        if response.status == 200:
            xml.append(response.content)
    xml = [filter(lambda p: "emulator" == p.attrib["path"], \
                  ET.fromstring(x).findall('remotePackage')) for x in xml]
    # Flatten the list of lists into a system image objects.
    infos = [EmuInfo(item) for sublist in xml for item in sublist]
    return infos
img_infos = get_images_info()
emu_infos = get_emus_info()
for img_info in img_infos:
    print "SYSIMG", img_info.tag, img_info.api, img_info.letter, img_info.abi, img_info.url
for emu_info in emu_infos:
    for (hostos, url) in emu_info.urls.items():
        print "EMU", emu_info.channel, emu_info.version, hostos, url