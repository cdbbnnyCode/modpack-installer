## CurseForge Modpack Installer  
###### V2.1-beta
This is a small tool for Linux users to be able to install Minecraft modpacks
from CurseForge without the official client. It generates isolated Minecraft
environments separate from your main `.minecraft` directory to avoid modifying
your default Minecraft installation.  
This project is currently in beta and may be unstable. If you find a bug, please
help me out by posting an [issue](https://github.com/cdbbnnyCode/modpack-installer/issues)!

**V2.1 update info**: After updating to version 2.1, please run the `clean.py` script
to upgrade all of your existing modpacks.

### Features
* Simple command-line interface
* Supports Forge and Fabric modpacks
* Caches and re-uses mods across packs to save on bandwidth and drive usage

### Requirements  
This program requires the Minecraft launcher, Python 3, and a JDK (8 or
higher). The only dependency library is not automatically installed is Requests,
which can be installed with pip (or your favorite method of installing Python
libraries):  
```
pip3 install --user requests
```

### How to Use
* Download a modpack and move the zip file into this directory.
* Open a terminal in this directory and type:
  ```
  python installer.py <modpack_name.zip>
  ```
replacing `<modpack_name.zip>` with the name of the zip file you just downloaded.
  * If the installer fails to install the modloader (this is a known bug with
    Forge versions other than 1.12.2), delete the modpack directory out of `packs/`
    and run the program with the `--manual` flag:
    ```
    python installer.py --manual <modpack_name.zip>
    ```
    This will open the modloader's install GUI. Point it to the modpack's
    `.minecraft` directory and install the client there. Once that is finished,
    close the window and installation will continue normally.
* To launch Minecraft, `cd` to `packs/<modpack_name>` and run
  ```
  minecraft-launcher --workDir $(realpath .minecraft)
  ```
  If you are using a slightly older version of the Minecraft launcher (i.e. if
  the above command doesn't work), use
  ```
  minecraft-launcher --workDir .
  ```
* To uninstall a modpack, simply delete its folder under the `packs/` directory.
  All of your saves, resource packs, and shader packs will be retained and
  available in your other modpacks.
  * Note that deleting the modpack does not automatically delete any mod files, as
    they are stored in a central `.modcache` directory. To clean up unused mods, run
    the `clean.py` script.

### How it Works (for Forge modpacks)
The installer script goes through several steps to install the modpack:
* First, it unzips the provided zip file into the `.packs` folder. The zip file
  contains a manifest file defining which version of Forge to use and a list of
  all of the mods in the pack, along with resource and configuration files.
* Next, it creates a `.minecraft` directory for the modpack and generates a
  dummy `launcher_profiles.json` file, which is subsequently used when installing
  Forge.
* Next, it runs [`forge_install.py`](/forge_install.py) to install Forge. This script downloads the
  requested version of the Forge installer and uses the [`ForgeHack.java`](/ForgeHack.java) program
  to bypass the install GUI and install directly to the `.minecraft` folder.
Next, it uses the [`mod_download.py`](/mod_download.py) script to download the required mods into
  the `.modcache` folder. The downloader script also generates a list of the mod
  jar files that are used by the modpack. The installer script then uses this
  list to create symbolic links to each mod. This reduces total disk usage when multiple
  modpacks use the same mod.
* Finally, the installer copies all of the folders in `overrides` from the unzipped
  modpack folder into the `.minecraft` folder.

#### The `clean.py` script
This script is intended to upgrade modpacks created with previous versions of the installer
as well as remove unused mods from the `.modcache` folder. Currently, it
* Deletes the `assets` folder from each existing modpack and links it into the `global`
  folder. This should improve download times when installing new modpacks as the assets
  (mainly language and sound files) do not need to be entirely re-downloaded for each install.
* Deletes any mods from the cache that aren't linked to by any modpacks.

### Limitations/Known Bugs
* This program only runs on Linux. (It might run on Mac, but I seriously doubt it.)
  As Windows/Mac users can use the official Curse client instead, these operating
  systems will not be supported by this tool.
* This tool always installs all mods, regardless of whether they are marked as
  required.
* Forge installation may fail when installing Forge for versions other than
  1.12.2. This is because the auto-installation hack only currently supports one
  version of the Forge installer binary. Compatibility with other Forge installers
  will likely be added in the future.
* The modpack's manifest format suggests that multiple mod loaders may be used
  in a single pack. I have not seen any modpacks that use this feature, so it
  is currently unsupported. If you do find a modpack that does this, please let
  me know by posting an issue.

### License
This project is licensed under the MIT license. See the LICENSE file for details.


### Changelog
#### v2.1-beta - 2021-07-24
* Migrate `assets` to a global directory
* Add `clean.py` script to migrate the `assets` folder in existing modpacks and remove
  unused mods.

#### v2.0-beta - 2021-07-10
* Fabric modloader support
* Add `--manual` option to open the modloader installer GUI when automatic installation
  fails
* Generate a `launcher-profiles.json` file automatically instead of using the Minecraft
  launcher to generate it
* Clean up code

#### v1.1-beta - 2020-04-25
* Rewrite mod downloader in Python
* Extract resource packs (included in the manifest's mod list) into the resourcepacks
  directory
* Ensure that files and directories are both copied properly from the modpack's overrides

#### v1.0-beta - 2020-04-25
Initial version--uses NodeJS script to fetch mod files
