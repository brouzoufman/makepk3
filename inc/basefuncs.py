#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os

ISWINDOWS = sys.platform.startswith("win")

def printCommand(command):
    newCommand = []

    for i in command:
        if " " in i or "\t" in i:
            newCommand.append("\"" + i.replace("\\", "\\\\").replace("\"", "\\\"") + "\"")
        else:
            newCommand.append(i)

    return " ".join(newCommand)



def adjustBinaryName(name):
    if ISWINDOWS:
        return name.lower() + ".exe"

    return name



def getPathList():
    path = os.environ.get("PATH", "")

    if ISWINDOWS:
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



def compilationFiles(srcDir, objDir=None, srcExts=(".c",), hdrExts=(".h",), objExt=".o"):
    sources, headers, objects = [], [], []

    if ISWINDOWS:   adjustName = lambda x: x.lower()
    else:           adjustName = lambda x: x

    srcDir = os.path.realpath(srcDir)
    objDir = os.path.realpath(objDir or srcDir)

    if not os.path.isdir(srcDir):
        return ([], [], [])

    for dir, _, files in os.walk(srcDir):
        for file in files:
            adjName = adjustName(file)
            objName = adjName.rsplit(".", 1)[0] + objExt

            srcPath = os.path.join(dir, file)
            objPath = os.path.join(dir, objName).replace(srcDir, objDir, 1)

            for i in srcExts:
                if adjName.endswith(i):
                    sources.append(srcPath)
                    objects.append(objPath)

            for i in hdrExts:
                if adjName.endswith(i):
                    headers.append(srcPath)

    return (sources, headers, objects)


def toRecompile(sources, headers, objects):
    newestHeader = None
    oldestObject = None

    for h in headers:
        if not os.path.isfile(h): continue
        mtime = os.stat(h).st_mtime
        newestHeader = mtime if (newestHeader is None) else max(newestHeader, mtime)

    objectMtimes = {}

    for o in objects:
        if not os.path.isfile(o): continue
        mtime = os.stat(o).st_mtime
        oldestObject = mtime if (oldestObject is None) else min(oldestObject, mtime)

        objectMtimes[o] = mtime

    if not oldestObject or (newestHeader and newestHeader >= oldestObject):
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
