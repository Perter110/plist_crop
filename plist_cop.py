# -*- coding: UTF-8 -*-
import xml.sax
import re
from PIL import Image
import os,io
import sys

class imgdata:
    def __init__(self) -> None:
        self.nowData = dict()
    
    def format(self):
        arg = re.findall(r'{{(\d*),(\d*)},{(\d*),(\d*)}}',self.nowData['frame'])
        self.startPos = [int(arg[0][0]),int(arg[0][1])]
        self.size = [int(arg[0][2]),int(arg[0][3])]
        self.rotated = self.nowData['rotated'] == 'true'
        arg = re.findall(r'{(\d*),(\d*)}',self.nowData['sourceSize'])
        self.sourceSize = [int(arg[0][0]),int(arg[0][1])]
        arg = re.findall(r'{(-?\d*),(-?\d*)}',self.nowData['offset'])
        self.offset = [int(arg[0][0]),int(arg[0][1])]

    def getBox(self):
        if self.rotated:
            return (self.startPos[0],self.startPos[1],self.startPos[0]+self.size[1],self.startPos[1]+self.size[0])
        else:
            return (self.startPos[0],self.startPos[1],self.startPos[0]+self.size[0],self.startPos[1]+self.size[1])

    def getRotate(self):
        if self.rotated:
            # return 0.5*math.pi
            return 90
        else:
            return 0


class plistCop(xml.sax.ContentHandler):
    def __init__(self) -> None:
        self.nowData = ""
        self.nowKeyType = ""
        self.nowReading = ""
        self.imgDatas = dict()
        self.bIsEnd = False

    def startElement(self,tag,attributes):
        # print("start, ",tag,attributes)
        self.nowKeyType = tag

    def endElement(self,tag):
        # print("end ,",tag)
        self.nowKeyType = ""
        if self.nowReading == 'rotated' and (tag == 'true' or tag == 'false') and self.imgDatas[self.nowData]:
            self.imgDatas[self.nowData].nowData.setdefault(self.nowReading,tag)
            self.nowReading = ''

    def characters(self,content):
        if not self.bIsEnd and re.match('.*.png',content):
            self.nowData = content
            self.imgDatas.setdefault(content,imgdata())
            # print("now img key,",content)
        elif content == 'frame':
            self.nowReading = 'frame'
        elif content == 'offset':
            self.nowReading = 'offset'
        elif content == 'rotated':
            self.nowReading = 'rotated'
        elif content == 'sourceSize':
            self.nowReading = 'sourceSize'
        elif content == 'metadata' or content == 'texture':
            self.nowData = ""
            self.nowReading = ""
            self.bIsEnd = True
        elif self.nowKeyType and self.nowReading and self.imgDatas[self.nowData]:
            self.imgDatas[self.nowData].nowData.setdefault(self.nowReading,content)
            self.nowReading = ''

def cop_image(sourceplist,sourcepng,todir):
    if not os.path.exists(sourcepng):
        return
    if not os.path.exists(sourceplist):
        return
    if not os.path.exists(todir):
        os.mkdir(todir)

    print('start to crop image',sourcepng)
    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)
    Handler = plistCop()
    parser.setContentHandler( Handler )
    
    parser.parse(sourceplist)

    img = Image.open(sourcepng)
    for items in Handler.imgDatas.items():
        items[1].format()

        savetoPath = os.path.join(todir,items[0])
        if items[1].rotated:
            img.crop(items[1].getBox()).transpose(Image.ROTATE_90).save(savetoPath,bitmap_format='png')
        else:
            img.crop(items[1].getBox()).save(savetoPath,bitmap_format='png')
        
    print('start to crop image finished')

def cop_dir(dir):
    if not os.path.exists(dir):
        print("没找到文件夹",dir)
        return
    
    for root,dir,file in os.walk(dir):
        for fileName in file:
            fullPath = os.path.join(root,fileName)
            if checkIsPlist(fullPath):
                split_arg = os.path.splitext(fileName)
                cropPlistIntoDir(fullPath,os.path.join(root,'.%s_PList.Dir'%split_arg[0]))


def cropPlistIntoDir(plistFile,toDir):
    if not os.path.exists(toDir):
        os.mkdir(toDir)
    arg_split = os.path.splitext(plistFile)
    
    cop_image(plistFile,arg_split[0]+'.png',toDir)

    # shutil.copyfile('./InfoConfig.xml',os.path.join(toDir,'InfoConfig.xml'))



def checkIsPlist(path):
    arg_split = os.path.splitext(path)
    if arg_split[1] != '.plist':
        return False

    with io.open(path,'r',encoding='utf-8') as file:
        data = file.read()
        res_A = re.findall('<key>frames</key>',data)
        res_B = re.findall('<key>metadata</key>',data)
        res_C = re.findall('<key>metadata</key>',data)
        if res_A and res_B and res_C:
            return True
    return False



if __name__ == "__main__":
    if os.path.isdir(sys.argv[1]):
        cop_dir(sys.argv[1])
    else:
        splitPath = os.path.splitdrive(sys.argv[1])
        split_arg = os.path.splitext(os.path.split(sys.argv[1])[1])
        cropPlistIntoDir(sys.argv[1],os.path.join(splitPath[0],'.%s_PList.Dir'%split_arg[0]))
    