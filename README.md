# makepk3

**it actually makes pk7s but who gives a shit seriously now**


## Dependencies

Windows shouldn't have any, besides Python itself (2 or 3 works). The required
programs are included in `bin_win/`.

Linux needs these:

- GDCC ([https://github.com/DavidPH/GDCC](https://github.com/DavidPH/GDCC))
- ACC  ([https://github.com/rheit/acc](https://github.com/rheit/acc))
- 7za  (check your distro's repositories for `p7zip`)

Install them normally - as long as the above are on your PATH, makepk3 will
find them.

## How to use it

Run `make.py`. That's it. Assuming no errors pop up

The directory you run `make.py` in must have a `pk3/` directory, which holds the
contents of the PK3 you're making. If you're building ACS, GD-ACS, or GDCC
files, you must have a `pk3/acs` directory. Each compiler has its own directory:

- ACC:    `pk3/acs`
- GD-ACC: `pk3/gacs`
- GDCC:   `pk3/gdcc`

All the object files end up in `pk3/acs`, as that's the only directory ZDoom
looks for them in.

If you want to change the name of the generated PK3 or GDCC target file, either
change the name of the directory your project is in, or hardcode it into the
`PROJECT_NAME`/`GDCC_TARGET`/`PK7_TARGET` variable (`make.py`, line 18/19/20).

You do not need to copy this into the same folder that houses `pk3/`. Really, you
should leave makepk3's stuff in a directory of its own.


## Other stuff

- By default, makepk3 does not include `.ir` files in the output PK7. Get rid of
  the `-x!*.ir` argument in ARGS_7ZIP if you don't want this.
