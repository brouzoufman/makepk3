#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os

def printCommand(command):
    newCommand = []

    for i in command:
        if " " in i or "\t" in i:
            newCommand.append("\"" + i.replace("\\", "\\\\").replace("\"", "\\\"") + "\"")
        else:
            newCommand.append(i)

    return " ".join(newCommand)

def adjustBinaryName(name):
    if sys.platform.startswith("win"):
        return name.lower() + ".exe"
    
    return name

def getPathList():
    path = os.environ.get("PATH", "")
    
    if sys.platform.startswith("win"):
        return path.split(";")
    
    return path.split(":")

def findBinary(binaryName, extraPath=None):
    path = []
    if extraPath: path.extend(extraPath)
    path.extend(getPathList())
    
    adjustedName = adjustBinaryName(binaryName)
    
    for dir in path:
        realdir   = os.path.realpath(dir)
        checkpath = realdir + os.sep + adjustedName
        
        if os.path.isfile(checkpath) and os.access(checkpath, os.X_OK):
            return checkpath
    
    return None

def compilationFiles(srcDir, srcExts=(".c",), hdrExts=(".h",), objExt=".o"):
    sources = []
    headers = []
    objects = []
    
    if sys.platform.startswith("win"):
        adjustName = lambda x: x.lower()
    else:
        adjustName = lambda x: x
    
    srcDir = os.path.realpath(srcDir)
    
    if not os.path.isdir(srcDir):
        return ([], [], [])
    
    for dir, _, files in os.walk(srcDir):
        for file in files:
            afile = adjustName(file)
            pfile = dir + os.sep + file
            
            for i in srcExts:
                if afile.endswith(i):
                    sources.append(pfile)
                    objects.append(objExt.join(pfile.rsplit(i, 1)))
            
            for i in hdrExts:
                if afile.endswith(i):  headers.append(pfile)
    
    return (sources, headers, objects)

def toRecompile(sources, headers, objects):
    latestHeaderMod = -1
    latestObjectMod = -1
    
    for h in headers:
        if not os.path.isfile(h): continue
        mtime = os.stat(h).st_mtime
        latestHeaderMod = max(latestHeaderMod, mtime)
    
    objectMtimes = {}
    
    for o in objects:
        if not os.path.isfile(o): continue
        mtime = os.stat(o).st_mtime
        latestObjectMod = max(latestObjectMod, mtime)
        
        objectMtimes[o] = mtime
    
    if latestHeaderMod >= latestObjectMod:
        return {sources[i]: objects[i] for i in range(len(sources))}
    
    
    ret = {}
    
    for i, c in enumerate(sources):
        if not os.path.isfile(c): continue
        
        o = objects[i]
        if not os.path.isfile(o):
            ret[c] = o
            continue
        
        c_mtime = os.stat(c).st_mtime
        o_mtime = objectMtimes[o]
        
        if c_mtime >= o_mtime: ret[c] = o
    
    return ret
