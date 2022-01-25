## CurseForge Modpack Installer  
###### V2.2.1-beta
This command-line tool allows easy installation of CurseForge modpacks on Linux
systems. It installs each modpack in a semi-isolated environment, which prevents
them from modifying important settings and data in your main Minecraft installation.

This project is currently in beta and may be unstable. If you find a bug, please
help me out by posting an [issue](https://github.com/cdbbnnyCode/modpack-installer/issues)!



**V2.2 update info**: After updating to version 2.2, please run the `migrate.py`
script to create launcher profiles for your modpacks in your main `.minecraft`
directory. See the changelog below for details.

Minecraft Forge auto-installation should now work with all current versions of the installer.
If it does not work properly, please post an issue reporting the error as well as the version
of the installer.

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
  * If the installer fails to install the modloader automatically,
    delete the modpack directory out of `packs/`
    and run the program with the `--manual` flag:
    ```
    python installer.py --manual <modpack_name.zip>
    ```
    This will open the modloader's install GUI. Point it to your **main**
    `.minecraft` directory (should be default) and click 'Install Client'.
* To launch the modpack, simply load the Minecraft launcher normally. The modpack
  will appear as a new installation under the 'Installations' drop-down menu.
* To uninstall a modpack, simply delete its folder under the `packs/` directory
  and remove the installation from the Minecraft launcher. All of your saves, 
  resource packs, and shader packs will be retained and available in your other 
  modpacks.
  * Note that deleting the modpack does not automatically delete any mod files, as
    they are stored in a central `.modcache` directory. To clean up unused mods, run
    the `clean.py` script.

### How it Works
The installer script goes through several steps to install the modpack:
* First, it unzips the provided zip file into the `.packs` folder. The zip file
  contains a manifest file defining which version of Forge to use and a list of
  all of the mods in the pack, along with resource and configuration files.
* Next, it creates a `.minecraft` directory for the modpack, which is used to store
  the modpack data.
* Next, it runs [`forge_install.py`](/forge_install.py) to install Forge. This script downloads the
  requested version of the Forge installer and uses the [`ForgeHack.java`](/ForgeHack.java) program
  to bypass the install GUI and install directly to the user's *main* `.minecraft` folder.
  * The Fabric installer has command-line options to install the client directly, so `fabric_install.py`
    directly runs the installer.
* Next, it uses the [`mod_download.py`](/mod_download.py) script to download the required mods into
  the `.modcache` folder. The downloader script also generates a list of the mod
  jar files that are used by the modpack. The installer script then uses this
  list to create symbolic links to each mod. This reduces total disk usage when multiple
  modpacks use the same mod.
* Finally, the installer copies all of the folders in `overrides` from the unzipped
  modpack folder into the modpack's `.minecraft` folder.

#### The `clean.py` script
This script is intended to upgrade modpacks created with previous versions of the installer
as well as remove unused mods from the `.modcache` folder. Currently, it
* Deletes the `assets` folder from each existing modpack and links it into the `global`
  folder. This should improve download times when installing new modpacks as the assets
  (mainly language and sound files) do not need to be entirely re-downloaded for each install.
* Deletes any mods from the cache that aren't linked to by any modpacks.

#### The `migrate.py` script
This script creates launcher profiles for each existing installation in the user's *main* 
`.minecraft` directory. It also moves all Minecraft Forge/Fabric installations into the main
`.minecraft` directory. This allows all of the modpacks to be launched directly from the Minecraft 
launcher and eliminates issues related to launcher login and update files across multiple working 
directories.

### Limitations/Known Bugs
* This program only runs on Linux. (It might run on Mac, but I seriously doubt it.)
  As Windows/Mac users can use the official Curse client instead, these operating
  systems will not be supported by this tool.
* This tool always installs all mods, regardless of whether they are marked as
  required.
* The modpack's manifest format suggests that multiple mod loaders may be used
  in a single pack. I have not seen any modpacks that use this feature, so it
  is currently unsupported. If you do find a modpack that does this, please let
  me know by posting an issue.

### License
This project is licensed under the MIT license. See the LICENSE file for details.


### Changelog
#### v2.2.1-beta - 2022-01-25
* Fix `ForgeHack` to work with older installer versions (tested on latest major releases down to
  1.7.10).
* Automatically recompile the `ForgeHack` class file when its corresponding source file is updated.
* Fix a serious mod downloader bug where server errors would cause only the retried downloads to be
  linked correctly (#12).

#### v2.2-beta - 2022-01-10
* Move modloaders and launcher profiles to the main `.minecraft` folder.
  * This approach works better with recent versions of the launcher because of the way that they
    handle accounts and automatic updates.
  * All modpack-related data (mods, saves, options, config, etc.) is still kept isolated. Only the 
    modloader (which appears as a separate Minecraft version) and the launcher profile are migrated.
  * The `migrate.py` script is provided to move existing installations.
* Update `ForgeHack` so that it works for recent versions of the Forge installer.
* Fix mod downloader so that it handles server errors properly (#9).

#### v2.1-beta - 2021-07-24
* Migrate `assets` to a global directory
* Add `clean.py` script to migrate the `assets` folder in existing modpacks and remove
  unused mods.

#### v2.0-beta - 2021-07-10
* Fabric modloader support (#1)
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
