#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys, os
import subprocess
from collections import defaultdict

from inc.basefuncs import *

DIR_MINE = os.path.realpath(sys.argv[0]).rpartition(os.sep)[0]

EXE_7ZIP         = findBinary("7za",          [os.path.join(DIR_MINE, "bin_win")])
EXE_ACC          = findBinary("acc",          [os.path.join(DIR_MINE, "bin_win/acc")])
EXE_GDCC_ACC     = findBinary("gdcc-acc",     [os.path.join(DIR_MINE, "bin_win/gdcc")])
EXE_GDCC_CC      = findBinary("gdcc-cc",      [os.path.join(DIR_MINE, "bin_win/gdcc")])
EXE_GDCC_LD      = findBinary("gdcc-ld",      [os.path.join(DIR_MINE, "bin_win/gdcc")])
EXE_GDCC_MAKELIB = findBinary("gdcc-makelib", [os.path.join(DIR_MINE, "bin_win/gdcc")])

ARGS_7ZIP_COMMON = ["-mx=9", "-x!*.ir", "-x!*.dbs", "-x!*.backup*", "-x!*.bak", "-x!desktop.ini"]
ARGS_7ZIP_PK3    = ARGS_7ZIP_COMMON + ["-tzip"]
ARGS_7ZIP_PK7    = ARGS_7ZIP_COMMON + ["-t7z"]

GDCC_CFLAGS    = ["--bc-target", "ZDoom", "--warn-all"]
GDCC_LDFLAGS   = ["--bc-target", "ZDoom"]
GDCC_MLFLAGS   = ["--bc-target", "ZDoom"]
GDCC_ACCFLAGS  = []

DIRNAME_GDCC = "gdcc"
DIRNAME_GACC = "gacs"
DIRNAME_ACC  = "acs"

GDCC_LIBS   = ["libGDCC", "libc"]


def gdcc_buildObjects(src, hdr, obj, libs):
    mtime_makelib   = os.stat(EXE_GDCC_MAKELIB).st_mtime
    mtime_cc        = os.stat(EXE_GDCC_CC).st_mtime
    checkMtime      = max(mtime_makelib, mtime_cc)

    recompile    = toRecompile(src, hdr, obj)
    libRecompile = {}

    # update libraries if nonexistent, or GDCC updated
    for lib, libPath in libs:
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



def gdcc_linkObjects(objects, target):
    targetDir = os.path.dirname(target)

    doBuild = False

    if os.path.isfile(target):
        target_mtime = os.stat(target).st_mtime

        for o in objects:
            if os.stat(o).st_mtime >= target_mtime:
                doBuild = True
                break

    else:
        doBuild = True

    if not doBuild: return False

    if not os.path.isdir(targetDir):
        if os.path.isfile(targetDir):
            raise EnvironmentError("target dir \"{}\" exists and is a file".format(targetDir))

        print("creating directory \"{}\"".format(targetDir))
        os.makedirs(targetDir, exist_ok=True)

    command = [EXE_GDCC_LD] + GDCC_LDFLAGS + objects + ["-o", target]
    print(printCommand(command))
    exitCode = subprocess.call(command)

    if exitCode != 0:
        raise RuntimeError("gdcc-ld returned exit code " + str(exitCode))

    return True



def acc_buildObjects(src, hdr, obj, exe=EXE_ACC):
    recompile = toRecompile(src, hdr, obj)
    if len(recompile) == 0: return False

    for src in recompile:
        obj    = recompile[src]

        srcDir = os.path.dirname(src)
        objDir = os.path.dirname(obj)

        if not os.path.isdir(objDir):
            if os.path.isfile(objDir):
                raise EnvironmentError("target dir \"{}\" exists and is a file".format(objDir))

            print("creating directory \"{}\"".format(objDir))
            os.makedirs(objDir, exist_ok=True)

        command = [exe, "-i", srcDir, src, obj]
        print(printCommand(command))
        exitCode = subprocess.call(command)

        if exitCode != 0:
            exeName = os.path.splitext(os.path.basename(exe))[0]
            raise RuntimeError(exeName + " returned exit code " + str(exitCode))

    return True


def getPrecompiler(dir="."):
    dir = os.path.abspath(dir)
    precompilePath = os.path.join(dir, "precompile.py")
    precompile = None
    
    if os.path.isfile(precompilePath):
        print("loading pre-compile module at \"" + precompilePath + "\"")
        sys.path.insert(0, dir)
        import precompile
        sys.path.pop(0)
    
    return precompile



def buildSources(basedir, gdccName, precompile=False):
    if precompile:
        precompiler = getPrecompiler()
        
        if precompiler:
            print("pre-compiling")
            precompiler.precompile()
        else:
            print("nothing to do for pre-compiling")
    
    else:
        print("pre-compiling disabled")
    
    dirGDCC = os.path.join(basedir, DIRNAME_GDCC)
    dirGACC = os.path.join(basedir, DIRNAME_GACC)
    dirACC  = os.path.join(basedir, DIRNAME_ACC)
    
    srcGDCC, hdrGDCC, objGDCC = compilationFiles(dirGDCC,         objExt=".ir")
    srcGACC, hdrGACC, objGACC = compilationFiles(dirGACC, dirACC, srcExts=(".c", ".acs"))
    srcACC,  hdrACC,  objACC  = compilationFiles(dirACC,          srcExts=(".c", ".acs"))
    
    targetGDCC = os.path.join(dirACC, gdccName + ".o")

    canDoGDCC = bool(EXE_GDCC_CC and EXE_GDCC_MAKELIB and EXE_GDCC_LD)
    canDoGACC = bool(EXE_GDCC_ACC)
    canDoACC  = bool(EXE_ACC)

    doGDCC = bool(srcGDCC and canDoGDCC)
    doGACC = bool(srcGACC and canDoGACC)
    doACC  = bool(srcACC  and canDoACC)

    try:
        # check for overlapping object files
        allOutFiles = defaultdict(list)

        if doGDCC:
            allOutFiles[targetGDCC].append("GDCC target")

        if doGACC:
            for n, (src, obj) in enumerate(zip(srcGACC, objGACC)):
                allOutFiles[obj].append(src)

        if doACC:
            for n, (src, obj) in enumerate(zip(srcACC, objACC)):
                allOutFiles[obj].append(src)

        overlapFiles = []

        for obj in sorted(allOutFiles):
            sources = allOutFiles[obj]

            if len(sources) > 1:
                overlapFiles.append((obj, sorted(sources)))

        if overlapFiles:
            errorMsg = ["following files would be written to multiple times"]

            for obj, srcs in overlapFiles:
                errorMsg.append(" - {} [{}]".format(i, ", ".join(srcs)))

            raise RuntimeError("\n".join(errorMsg))


        # compile

        if doGDCC:
            libGDCC     = [(i, os.path.join(dirGDCC, i + ".ir")) for i in GDCC_LIBS]
            linkObjects = [i[1] for i in libGDCC] + objGDCC
    
            builtAnything  = gdcc_buildObjects(srcGDCC, hdrGDCC, objGDCC, libGDCC)
            linkedAnything = gdcc_linkObjects(linkObjects, targetGDCC)

            if (builtAnything or linkedAnything):   print()
            else:                                   print("GDCC files up to date")

        elif canDoGDCC: print("nothing to do for GDCC")
        else: print("any of (gdcc-cc, gdcc-makelib, gdcc-ld) missing, cannot compile for GDCC", file=sys.stderr)
        
        
        if doGACC:
            builtAnything = acc_buildObjects(srcGACC, hdrGACC, objGACC, exe=EXE_GDCC_ACC)

            if builtAnything:   print()
            else:               print("GD-ACC files up to date")

        elif canDoGACC: print("nothing to do for GD-ACC")
        else: print("gdcc-acc missing, cannot compile for GD-ACC", file=sys.stderr)
      

        if doACC:
            builtAnything = acc_buildObjects(srcACC, hdrACC, objACC)
            
            if builtAnything:   print()
            else:               print("ACC files up to date")

        elif canDoACC: print("nothing to do for ACC")
        else: print("acc missing, cannot compile for ACC", file=sys.stderr)


    except RuntimeError as e:
        print("\nEnded prematurely: " + str(e), file=sys.stderr)
        return False

    except EnvironmentError as e:
        print("\nCan't continue compiling: " + str(e), file=sys.stderr)
        return False

    else:
        return True


def make(pk3dir, gdccName, precompile=True):
    pk3dir = os.path.abspath(pk3dir)
    
    buildDirs = [pk3dir]
    
    filterDir = os.path.join(pk3dir, "filter")
    
    if os.path.isdir(filterDir):
        for filter in os.listdir(filterDir):
            path = os.path.join(filterDir, filter)
            if os.path.isdir(path):
                buildDirs.append(path)
    
    
    for dir in buildDirs:
        print("\n ---- building files in \"{}\" ---- \n".format(dir))
        built = buildSources(dir, gdccName, precompile)
        precompile = False # only precompile once
        
        if not built: return False
    
    return True


def package(projectdir, projectname, pk7=False, builddir=None):
    builddir   = os.path.abspath(builddir or ".")
    projectdir = os.path.abspath(projectdir)
    curdir     = os.getcwd()
    
    pk3name    = projectname + "." + ("pk7" if pk7 else "pk3")
    pk3path    = os.path.join(builddir, pk3name)
    
    print("\n ---- packaging up \"{}\" ---- \n".format(pk3name))
    
    if not EXE_7ZIP:
        print("\n7za not found, packaging aborted")
        return False

    if os.path.isfile(pk3path):
        os.remove(pk3path)

    print("going to \"{}\"".format(projectdir))
    os.chdir(projectdir)
    
    print("compiling \"{}\"".format(pk3name))
    extraArgs = ARGS_7ZIP_PK7 if pk7 else ARGS_7ZIP_PK3
    command = [EXE_7ZIP, "a", pk3path, ".", "-r"] + extraArgs
    print(printCommand(command))
    
    with open(os.devnull, 'w') as shutup:
        exitcode = subprocess.call(command, stdout=shutup, stderr=shutup)
    
    os.chdir(curdir)

    if exitcode == 0:
        print("\nDone, package is at " + pk3path)
    else:
        raise RuntimeError("packaging failed")

    return True



if __name__ == "__main__":
    import argparse
    
    if sys.version_info[0] == 2:    inputFunc = raw_input
    else:                           inputFunc = input

    def done(exitCode=0):
        if sys.platform.startswith("win"): inputFunc("\n -- hit enter to exit -- ")
        sys.exit(exitCode)

    # do the or check in case some crazy fucker is running in /
    dirname = os.path.basename(os.getcwd()) or "yourproject"

    parser = argparse.ArgumentParser(prog="make.py", description="Compiles all ACS and GDCC code in your project, then stuffs it into a PK3.")
    parser.add_argument("name",                 type=str, default=dirname, nargs="?",  help="name of your PK3 (default: \"{}\")".format(dirname))
    parser.add_argument("-d", "--dir",          type=str, default="pk3",               help="location of your project (default: \"pk3\")")
    parser.add_argument("-g", "--gdcc",         type=str, default="gdcc", dest="obj",  help="name of GDCC object file (default: \"gdcc\")")
    parser.add_argument("-7", "--pk7",          action="store_true",      dest="pk7",  help="build a PK7 instead of a PK3")
    parser.add_argument("-3", "--pk3",          action="store_true",      dest="pk3",  help="build a PK3 even if building a PK7")
    parser.add_argument("-n", "--nobuild",      action="store_true",                   help="build nothing, just compile code")
    parser.add_argument("-p", "--noprecompile", action="store_false",     dest="pre",  help="don't run any precompile module")
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.dir):
        print("\"{}\" is not a directory, aborting".format(args.dir), file=sys.stderr)
        done(1)

    couldCompile = make(args.dir, args.obj, precompile=args.pre)

    if couldCompile and not args.nobuild:
        if (not args.pk7) or args.pk3: package(args.dir, args.name, pk7=False)
        if args.pk7: package(args.dir, args.name, pk7=True)
        done()
    else:
        done(2)
