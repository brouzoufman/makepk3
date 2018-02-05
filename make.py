#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys, os
import subprocess
from collections import defaultdict

from inc.basefuncs import *

DIR_MINE = os.path.realpath(sys.argv[0]).rpartition(os.sep)[0]
DIR_CUR  = os.path.realpath(".")
DIR_PK3  = os.path.join(DIR_CUR, "pk3")

PRECOMPILE_PATH = os.path.join(DIR_CUR, "precompile.py")

if os.path.isfile(PRECOMPILE_PATH):
    print("loading pre-compile module at \"" + PRECOMPILE_PATH + "\"")
    sys.path.insert(0, DIR_CUR)
    import precompile
    sys.path.pop(0)

# put your own project name in the quotes if you don't want to use dir name
# ditto for GDCC_TARGET
PROJECT_NAME = "" or os.path.basename(DIR_CUR)
GDCC_TARGET  = PROJECT_NAME
PK7_TARGET   = os.path.join(DIR_CUR, PROJECT_NAME + ".pk3")

EXE_7ZIP         = findBinary("7za",          [os.path.join(DIR_MINE, "bin_win")])
EXE_ACC          = findBinary("acc",          [os.path.join(DIR_MINE, "bin_win/acc")])
EXE_GDCC_ACC     = findBinary("gdcc-acc",     [os.path.join(DIR_MINE, "bin_win/gdcc")])
EXE_GDCC_CC      = findBinary("gdcc-cc",      [os.path.join(DIR_MINE, "bin_win/gdcc")])
EXE_GDCC_LD      = findBinary("gdcc-ld",      [os.path.join(DIR_MINE, "bin_win/gdcc")])
EXE_GDCC_MAKELIB = findBinary("gdcc-makelib", [os.path.join(DIR_MINE, "bin_win/gdcc")])

ARGS_7ZIP      = ["-mx=9", "-x!*.ir", "-x!*.dbs", "-x!*.backup*", "-x!*.bak", "-x!desktop.ini", "-tzip"]

GDCC_CFLAGS    = ["--bc-target", "ZDoom", "--warn-all"]
GDCC_LDFLAGS   = ["--bc-target", "ZDoom"]
GDCC_MLFLAGS   = ["--bc-target", "ZDoom"]
GDCC_ACCFLAGS  = []

GDCC_SRCDIR = os.path.join(DIR_PK3, "gdcc")
GACC_SRCDIR = os.path.join(DIR_PK3, "gacs")
ACC_SRCDIR  = os.path.join(DIR_PK3, "acs")

GDCC_LIBS       = ["libGDCC", "libc"]
GDCC_LIBPATHS   = [os.path.join(GDCC_SRCDIR, i + ".ir") for i in GDCC_LIBS]
GDCC_TARGETPATH = os.path.join(DIR_PK3, "acs", GDCC_TARGET + ".o")



def gdcc_buildObjects(src, hdr, obj):
    mtime_makelib   = os.stat(EXE_GDCC_MAKELIB).st_mtime
    mtime_cc        = os.stat(EXE_GDCC_CC).st_mtime
    checkMtime      = max(mtime_makelib, mtime_cc)

    libPaths     = {lib: path for lib, path in zip(GDCC_LIBS, GDCC_LIBPATHS)}
    recompile    = toRecompile(src, hdr, obj)
    libRecompile = {}

    # update libraries if nonexistent, or GDCC updated
    for lib, libPath in libPaths.items():
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



def gdcc_linkObjects(obj, target, builtAnything):
    objects   = obj + GDCC_LIBPATHS
    targetDir = os.path.dirname(target)

    doBuild = False

    if os.path.isfile(target):
        target_mtime = os.stat(GDCC_TARGETPATH).st_mtime

        for o in objects:
            if os.stat(o).st_mtime >= target_mtime:
                doBuild = True
                break

    else:
        doBuild = True

    if not doBuild: return False

    if os.path.isfile(targetDir):
        raise EnvironmentError("target dir \"{}\" exists and is a file\n - can't write GDCC output".format(targetDir))

    if not os.path.exists(targetDir):
        os.mkdir(targetDir)

    command = [EXE_GDCC_LD] + GDCC_LDFLAGS + objects + ["-o", GDCC_TARGETPATH]
    print(printCommand(command))
    exitCode = subprocess.call(command)

    if exitCode != 0:
        raise RuntimeError("gdcc-ld returned exit code " + str(exitCode))

    return True



def acc_buildObjects(src, hdr, obj):
    recompile = toRecompile(src, hdr, obj)
    if len(recompile) == 0: return False

    for src in recompile:
        obj    = recompile[src]

        srcDir = os.path.dirname(src)
        objDir = os.path.dirname(obj)

        if not os.path.isdir(objDir):
            print("mkdir -p {}".format(printCommand([objDir])))
            os.makedirs(objDir, exist_ok=True)

        command = [EXE_ACC, "-i", srcDir, src, obj]
        print(printCommand(command))
        exitCode = subprocess.call(command)

        if exitCode != 0:
            raise RuntimeError("acc returned exit code " + str(exitCode))

    return True



def gacc_buildObjects(src, hdr, obj):
    recompile = toRecompile(src, hdr, obj)
    if len(recompile) == 0: return False

    for src in recompile:
        obj    = recompile[src]

        srcDir = os.path.dirname(src)
        objDir = os.path.dirname(obj)

        if not os.path.isdir(objDir):
            print("mkdir -p {}".format(printCommand([objDir])))
            os.makedirs(objDir, exist_ok=True)

        command = [EXE_GDCC_ACC, "-i", srcDir, src, obj]
        print(printCommand(command))
        exitCode = subprocess.call(command)

        if exitCode != 0:
            raise RuntimeError("gdcc-acc returned exit code " + str(exitCode))

    return True



def make():
    if "precompile" in globals():
        print("pre-compiling")
        precompile.precompile()
    else:
        print("nothing to do for pre-compiling")

    srcGDCC, hdrGDCC, objGDCC = compilationFiles(GDCC_SRCDIR,             objExt=".ir")
    srcGACC, hdrGACC, objGACC = compilationFiles(GACC_SRCDIR, ACC_SRCDIR, srcExts=(".c", ".acs"))
    srcACC,  hdrACC,  objACC  = compilationFiles(ACC_SRCDIR,              srcExts=(".c", ".acs"))

    canDoGDCC = bool(EXE_GDCC_CC and EXE_GDCC_MAKELIB and EXE_GDCC_LD)
    canDoGACC = bool(EXE_GDCC_ACC)
    canDoACC  = bool(EXE_ACC)

    doGDCC = bool(srcGDCC and canDoGDCC)
    doGACC = bool(srcGACC and canDoGACC)
    doACC  = bool(srcACC  and canDoACC)

    print()

    try:
        # check for overlapping object files
        allOutFiles = defaultdict(list)

        if doGDCC:
            allOutFiles[GDCC_TARGETPATH].append("GDCC target")

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
            builtAnything  = gdcc_buildObjects(srcGDCC, hdrGDCC, objGDCC)
            linkedAnything = gdcc_linkObjects(objGDCC, GDCC_TARGETPATH, builtAnything)

            if not (builtAnything or linkedAnything):
                print("GDCC files up to date")

        elif canDoGDCC: print("nothing to do for GDCC")
        else: print("any of (gdcc-cc, gdcc-makelib, gdcc-ld) missing, cannot compile for GDCC")

        print()

        if doGACC:
            builtAnything = gacc_buildObjects(srcGACC, hdrGACC, objGACC)

            if not builtAnything:
                print("GD-ACC files up to date")

        elif canDoGACC: print("nothing to do for GD-ACC")
        else: print("gdcc-acc missing, cannot compile for GD-ACC")

        print()

        if doACC:
            builtAnything = acc_buildObjects(srcACC, hdrACC, objACC)
            if not builtAnything: print("ACC files up to date")

        elif canDoACC: print("nothing to do for ACC")
        else: print("acc missing, cannot compile for ACC")


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
    if sys.version_info[0] == 2:    inputFunc = raw_input
    else:                           inputFunc = input

    def done(exitCode=0):
        if sys.platform.startswith("win"): inputFunc(" -- hit enter to exit -- ")
        sys.exit(exitCode)


    if not os.path.isdir(DIR_PK3):
        print("no pk3/ directory, aborting", file=sys.stderr)
        done(1)

    couldCompile = make()

    if couldCompile:
        print("")
        package()
        done()
    else:
        done(2)
