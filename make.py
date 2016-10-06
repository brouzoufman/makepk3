#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys, os
import subprocess
from collections import defaultdict

from inc.basefuncs import *

DIR_MINE = os.path.realpath(sys.argv[0]).rpartition(os.sep)[0]
DIR_CUR  = os.path.realpath(".")
DIR_PK3  = DIR_CUR + os.sep + "pk3"

# put your own project name in the quotes if you don't want to use dir name
# ditto for GDCC_TARGET
PROJECT_NAME = "" or os.path.basename(DIR_CUR)
GDCC_TARGET  = "bootymenu" or PROJECT_NAME
PK7_TARGET   = DIR_CUR + os.sep + PROJECT_NAME + ".pk7"

EXE_7ZIP         = findBinary("7za",          [DIR_MINE + os.sep + "bin_win"])
EXE_ACC          = findBinary("acc",          [DIR_MINE + os.sep + "bin_win/acc"])
EXE_GDCC_ACC     = findBinary("gdcc-acc",     [DIR_MINE + os.sep + "bin_win/gdcc"])
EXE_GDCC_CC      = findBinary("gdcc-cc",      [DIR_MINE + os.sep + "bin_win/gdcc"])
EXE_GDCC_LD      = findBinary("gdcc-ld",      [DIR_MINE + os.sep + "bin_win/gdcc"])
EXE_GDCC_MAKELIB = findBinary("gdcc-makelib", [DIR_MINE + os.sep + "bin_win/gdcc"])

ARGS_7ZIP      = ["-mx=9", "-x!*.ir"]

GDCC_CFLAGS    = ["--bc-target", "ZDoom"]
GDCC_LDFLAGS   = ["--bc-target", "ZDoom"]
GDCC_MLFLAGS   = ["--bc-target", "ZDoom"]
GDCC_ACCFLAGS  = []

GDCC_SRCDIR = DIR_PK3 + os.sep + "gdcc"
GACC_SRCDIR = DIR_PK3 + os.sep + "gacs"
ACC_SRCDIR  = DIR_PK3 + os.sep + "acs"

GDCC_SOURCES, GDCC_HEADERS, GDCC_OBJECTS = compilationFiles(GDCC_SRCDIR, objExt=".ir")
GACC_SOURCES, GACC_HEADERS, GACC_OBJECTS = compilationFiles(GACC_SRCDIR, srcExts=(".c", ".acs"))
ACC_SOURCES,  ACC_HEADERS,  ACC_OBJECTS  = compilationFiles(ACC_SRCDIR,  srcExts=(".c", ".acs"))

# extra step since zdoom only checks for .o files in acs/
GACC_OBJECTS = [i.replace(GACC_SRCDIR, ACC_SRCDIR) for i in GACC_OBJECTS]

GDCC_LIBS       = ["libGDCC", "libc"]
GDCC_LIBPATHS   = [GDCC_SRCDIR + os.sep + i + ".ir" for i in GDCC_LIBS]
GDCC_TARGETDIR  = DIR_PK3 + os.sep + "acs"
GDCC_TARGETPATH = GDCC_TARGETDIR + os.sep + GDCC_TARGET + ".o"




def gdcc_buildObjects():
    if not GDCC_SOURCES: return False
    
    if EXE_GDCC_MAKELIB is None:
        raise EnvironmentError("gdcc-makelib was NOT FOUND")
        
    if EXE_GDCC_CC is None:
        raise EnvironmentError("gdcc-cc was NOT FOUND")
        
    mtime_ml   = os.stat(EXE_GDCC_MAKELIB).st_mtime
    mtime_cc   = os.stat(EXE_GDCC_CC).st_mtime
    checkMtime = max(mtime_ml, mtime_cc)
    
    libPaths     = {GDCC_LIBS[i]: GDCC_LIBPATHS[i] for i in range(len(GDCC_LIBS))}
    recompile    = toRecompile(GDCC_SOURCES, GDCC_HEADERS, GDCC_OBJECTS)
    libRecompile = {}
    
    for lib in libPaths:
        libPath = libPaths[lib]
        
        if not os.path.isfile(libPath):
            libRecompile[lib] = libPath
            continue
        
        mtime_lib = os.stat(libPath).st_mtime
        
        if checkMtime >= mtime_lib:
            libRecompile[lib] = libPath
            
    if not (recompile or libRecompile):
        return False
   
    for lib in libRecompile:
        libPath = libRecompile[lib]
        command = [EXE_GDCC_MAKELIB, "-c", lib, "-o", libPath] + GDCC_MLFLAGS
        print(printCommand(command))
        exitCode = subprocess.call(command)
        
        if exitCode != 0:
            raise RuntimeError("gdcc-makelib returned exit code " + str(exitCode))
    
    
    for src in recompile:
        obj = recompile[src]
        command = [EXE_GDCC_CC, "-c", src, "-o", obj] + GDCC_CFLAGS
        print(printCommand(command))
        exitCode = subprocess.call(command)
        
        if exitCode != 0:
            raise RuntimeError("gdcc-cc returned exit code " + str(exitCode))
    
    return True
    
def gdcc_linkObjects(builtAnything):
    if not GDCC_SOURCES: return False
    
    if EXE_GDCC_LD is None:
        raise EnvironmentError("gdcc-ld was NOT FOUND")
        
    objects = GDCC_OBJECTS + GDCC_LIBPATHS
    
    doBuild = True
    
    if os.path.isfile(GDCC_TARGETPATH):
        target_mtime = os.stat(GDCC_TARGETPATH).st_mtime
        
        for o in objects:
            if os.stat(o).st_mtime >= target_mtime:
                break
        else:
            doBuild = False
    
    if not doBuild: return False

    if os.path.isfile(GDCC_TARGETDIR):
        raise EnvironmentError("pk3/acs/ exists and is a file, can't write GDCC output")

    if not os.path.exists(GDCC_TARGETDIR):
        os.mkdir(GDCC_TARGETDIR)
    
    command = [EXE_GDCC_LD] + GDCC_LDFLAGS + objects + ["-o", GDCC_TARGETPATH]
    print(printCommand(command))
    exitCode = subprocess.call(command)
    
    return True


def acc_buildObjects():
    if not ACC_SOURCES: return False
    
    if EXE_ACC is None:
        raise EnvironmentError("acc was NOT FOUND")

    if os.path.isfile(ACC_SRCDIR):
        raise EnvironmentError("pk3/acs/ exists and is a file, can't output ACC output")

    if not os.path.exists(ACC_SRCDIR):
        os.mkdir(ACC_SRCDIR)
    
    recompile = toRecompile(ACC_SOURCES, ACC_HEADERS, ACC_OBJECTS)
    
    if len(recompile) == 0: return False
    
    for src in recompile:
        obj = recompile[src]
        command = [EXE_ACC, "-i", ACC_SRCDIR, src, obj]
        print(printCommand(command))
        exitCode = subprocess.call(command)
        
        if exitCode != 0:
            raise RuntimeError("acc returned exit code " + str(exitCode))
    
    return True


def gacc_buildObjects():
    if not GACC_SOURCES: return False
    
    if EXE_GDCC_ACC is None:
        raise EnvironmentError("gdcc-acc was NOT FOUND")

    if os.path.isfile(ACC_SRCDIR):
        raise EnvironmentError("pk3/acs/ exists and is a file, can't write GD-ACC ouput")

    if not os.path.exists(ACC_SRCDIR):
        os.mkdir(ACC_SRCDIR)
    
    recompile = toRecompile(GACC_SOURCES, GACC_HEADERS, GACC_OBJECTS)
    
    if len(recompile) == 0: return False
    
    for src in recompile:
        obj = recompile[src]
        command = [EXE_GDCC_ACC, "-i", GACC_SRCDIR, src, "-o", obj] + GDCC_ACCFLAGS
        print(printCommand(command))
        exitCode = subprocess.call(command)
        
        if exitCode != 0:
            raise RuntimeError("gdcc-acc returned exit code " + str(exitCode))
    
    return True
    
def make():
    try:
        allOutFiles        = defaultdict(int)
        allOutFiles_byWhat = defaultdict(list)
        
        if EXE_GDCC_CC and EXE_GDCC_MAKELIB and EXE_GDCC_LD:
            if GDCC_SOURCES:
                allOutFiles[GDCC_TARGETPATH] += 1
                allOutFiles_byWhat[GDCC_TARGETPATH].append("GDCC target")
        
        if EXE_GDCC_ACC:
            for n, i in enumerate(GACC_OBJECTS):
                allOutFiles[i] += 1
                allOutFiles_byWhat[i].append(GACC_SOURCES[n])
        
        if EXE_ACC:
            for n, i in enumerate(ACC_OBJECTS):
                allOutFiles[i] += 1
                allOutFiles_byWhat[i].append(ACC_SOURCES[n])
        
        overlapFiles = []
        
        for i in sorted(allOutFiles):
            refcount = allOutFiles[i]
            if refcount > 1: overlapFiles.append(i)
        
        if overlapFiles:
            errorMsg = ["following files would be written to multiple times"]
            
            for i in overlapFiles:
                errorMsg.append(" - {} [{}]".format(i, ", ".join(allOutFiles_byWhat[i])))
            
            raise RuntimeError("\n".join(errorMsg))
        
        
        if GDCC_SOURCES:
            if EXE_GDCC_CC and EXE_GDCC_MAKELIB and EXE_GDCC_LD:
                builtAnything  = gdcc_buildObjects()
                linkedAnything = gdcc_linkObjects(builtAnything)
                
                if not (builtAnything or linkedAnything):
                    print("GDCC files up to date")

            else:
                print("any of (gdcc-cc, gdcc-makelib, gdcc-ld) missing, cannot compile for GDCC")

        else:
            print("nothing to do for GDCC")
        
        print("")
        
        if GACC_SOURCES:
            if EXE_GDCC_ACC:
                builtAnything = gacc_buildObjects()
                
                if not builtAnything:
                    print("GD-ACC files up to date")

            else:
                print("gdcc-acc missing, cannot compile for GD-ACC")

        else:
            print("nothing to do for GD-ACC")
        
        print("")
        
        if ACC_SOURCES:
            if EXE_ACC:
                builtAnything = acc_buildObjects()
                
                if not builtAnything:
                    print("ACC files up to date")

            else:
                print("acc missing, cannot compile for ACC")

        else:
            print("nothing to do for ACC")
            
    except RuntimeError as e:
        print("\nEnded prematurely: " + str(e))
        return False
        
    except EnvironmentError as e:
        print("\nCan't continue compiling: " + str(e))
        return False
    
    else:
        return True

def package():
    if not EXE_7ZIP:
        print("\n7za not found, packaging aborted")
        return False

    if os.path.isfile(PK7_TARGET):
        os.remove(PK7_TARGET)
    
    print("cd " + DIR_PK3)
    os.chdir(DIR_PK3)
    command = [EXE_7ZIP, "a", PK7_TARGET, ".", "-r"] + ARGS_7ZIP
    print(printCommand(command))
    exitcode = subprocess.call(command)

    if exitcode == 0:
        print("\nFinal package is at " + PK7_TARGET)
    else:
        raise RuntimeError("packaging failed")

    return True


if __name__ == "__main__":
    if sys.version_info[0] == 2:
        inputFunc = raw_input
    else:
        inputFunc = input

    if not os.path.isdir(DIR_PK3):
        print("no pk3/ directory, aborting", file=sys.stderr)
        if sys.platform.startswith("win"): inputFunc(" -- hit enter to exit -- ")
        sys.exit(1)

    couldCompile = make()
    
    if couldCompile:
        print("")
        package()
        if sys.platform.startswith("win"): inputFunc(" -- hit enter to exit -- ")
    else:
        if sys.platform.startswith("win"): inputFunc(" -- hit enter to exit -- ")
        sys.exit(2)
