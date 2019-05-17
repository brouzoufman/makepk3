# makepk3

**it build the thing**

```text
usage: make.py [-h] [-d DIR] [-g OBJ] [-7] [-3] [-n] [-p] [-r] [name]

Compiles all ACS and GDCC code in your project, then stuffs it into a PK3.

positional arguments:
  name                name of your PK3 (default: directory name)

optional arguments:
  -h, --help          show this help message and exit
  -d DIR, --dir DIR   location of your project (default: "pk3")
  -g OBJ, --gdcc OBJ  name of GDCC object file (default: "gdcc")
  -7, --pk7           build a PK7 instead of a PK3
  -3, --pk3           build a PK3 even if building a PK7
  -n, --nobuild       build nothing, just compile code
  -p, --noprecompile  don't run any precompile module
  -r, --recompile     recompile all ACS/GDCC code
```

As of 2018.09.22, `makepk3` now handles filter/ directories properly, and will
compile ACS and GDCC code within them. If you want to `#include` files from the
non-filtered `acs/` directories, you'll have to go up the directory tree to do so.


## Dependencies

Windows shouldn't have any, besides Python itself (2 or 3 works). The required
programs are included in `bin_win/`.

Linux needs these:

- GDCC for GDCC and GD-ACS compilation ([https://github.com/DavidPH/GDCC](https://github.com/DavidPH/GDCC))
- ACC  for ACS compilation ([https://github.com/rheit/acc](https://github.com/rheit/acc))
- 7za  for packaging (check your distro's repositories for `p7zip` or `p7zip-full`)

Install them normally - as long as the above are on your PATH, makepk3 will find them.
Alternatively, you can put them in the following places:

- GDCC: `bin_usr/gdcc/`
- ACC:  `bin_usr/acc/`
- 7za:  `bin_usr/`

If GDCC is missing, `make.py` will not attempt to build anything in `pk3/gacs` or `pk3/gdcc`.

If ACC is missing, `make.py` will not attempt to build anything in `pk3/acs`.

If 7za is missing, `make.py` will not attempt to build a PK7.

## How to use it

Make sure your PK3's data is stored in a folder called `pk3`.

While in the directory containing `pk3/`, run `make.py`.

That's it.

Assuming no errors pop up, you should have a PK3 pop up in the directory you ran
it in, containing everything in the `pk3/` directory, with the ACS and GDCC
compiled up, ready to go.

The directory you run `make.py` in must have a `pk3/` directory, which holds the
contents of the PK3 you're making. If you're building ACS, GD-ACS, or GDCC
files, you must have a `pk3/acs` directory. Each compiler has its own directory:

- ACC:    `pk3/acs`
- GD-ACC: `pk3/gacs`
- GDCC:   `pk3/gdcc`

All the object files end up in `pk3/acs`, as that's the only directory ZDoom
looks for them in.

If you're running make.py through Windows Explorer or something (basically, not
through the command line), make a shortcut and change the working directory to
the one with `pk3/`. Or make a small batch script that runs the command while
in the right directory. Something along those lines. If you want to use any command
line options with the shortcut, put them in the Target box in the shortcut properties.

You do not need to copy this into the same directory that houses `pk3/`. Really,
you should leave makepk3's stuff in a directory of its own.


## Other stuff

- By default, makepk3 does not include `.ir` files in the output PK7. Get rid of
  the `-x!*.ir` argument in ARGS\_7ZIP if you don't want this.

- The reason GDCC-ACC only kicks in for `pk3/gacs` is because I want this to be
  more or less a drop-in replacement for my old packagepk3.py script (that never
  worked on any machine other than mine), and GDCC-ACC is stricter than ACC is -
  which is to say, it actually type-checks.
