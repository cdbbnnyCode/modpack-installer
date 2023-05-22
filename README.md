## Modpack Installer  
###### V2.3.4

This command-line tool allows easy installation of CurseForge modpacks on Linux
systems. It installs each modpack in a semi-isolated environment, which prevents
them from modifying important settings and data in your main Minecraft installation.

This is a small project and may be unstable. If you find a bug, please
help me out by posting an [issue](https://github.com/cdbbnnyCode/modpack-installer/issues)!

**V2.3 update info**: Now uses the *official* CurseForge API. This has some major impacts:
* API requests are now authenticated with a key, and are now rate-limited on the client side
  to avoid excessive requests with this project's key.
  * **NOTE TO DEVELOPERS** - Forks and modifications of this project *must* use a new API key.
    See [here](https://support.curseforge.com/en/support/solutions/articles/9000208346-about-the-curseforge-api-and-how-to-apply-for-a-key) for details.
* Some mods now disallow 3rd-party distribution. These mods will be listed in the installer's output
  and must be downloaded manually from the CurseForge website. (Download URLs are provided directly).
  While this is tedious, it allows mod creators to always receive ad revenue from the download page.

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
* Modpacks can be launched directly from the official launcher; no third-party authentication required
* Supports installing to the Minecraft app from Flatpak
  * Uses 'sandbox mode' to ensure that the mods are placed inside the Flatpak sandbox environment
    where the game can still access them

### Requirements  
This program requires the Minecraft launcher, Python 3, and a JDK (8 or
higher). The only dependency library that is not automatically installed is Requests,
which can be installed with pip (or your favorite method of installing Python
libraries):  
```
pip3 install --user requests
```

### How to Use
* Download a modpack and move the zip file into this directory.
* Open a terminal in this directory and type:
  ```
  python install.py <modpack_name.zip>
  ```
  replacing `<modpack_name.zip>` with the name of the zip file you just downloaded.
  * If the installer fails to install the modloader automatically,
    delete the modpack directory out of `packs/`
    and run the program with the `--manual` flag:
    ```
    python install.py --manual <modpack_name.zip>
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
* You can use the `-b` flag in order to automatically open any modpacks
  that need to be installed manually. This will open them in your default
  browser using `webbrowser`.
* Use `python install.py -h` for a complete list of available commands

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

### Disclaimer
This project is not endorsed by or affiliated with CurseForge, Overwolf, or Microsoft in any way.
All product and company names are the registered trademarks of their original owners.

### Changelog
#### v2.3.4 - 2023-05-21
* Fixes a bug preventing the game from accessing mod files when launched via the Flatpak app
  ([#31](https://github.com/cdbbnnyCode/modpack-installer/issues/31))
  * Flatpak has a sandbox that blocks access to the filesystem outside `~/.var/app/<appname>/`
    unless explicitly specified otherwise. By default, the modpack installer creates a
    complete game directory and stores mods relative to itself (in `packs/` and `.modcache`,
    respectively).
  * This update adds a 'sandbox' mode that automatically enables if Flatpak is being used and
    moves modpack files closer to the main `.minecraft` location so that they exist within the
    Flatpak sandbox.
* Uses `shutil` instead of the deprecated `distutils` to recursively copy directories
  * ...except that `shutil.copytree` in Python versions before 3.8 does not support copying over
    existing directories, so those older versions will still use `distutils`.

#### v2.3.3 - 2023-05-08
* New features from community pull requests:
  * New `--open-browser` option will automatically open all of the manual download links in the
    browser (not recommended if there are many mods that need to be downloaded manually, as all
    of the links will be opened simultaneously)
    ([#28](https://github.com/cdbbnnyCode/modpack-installer/pull/28)).
  * Support for changing the user's `.minecraft` directory
    ([#15](https://github.com/cdbbnnyCode/modpack-installer/pull/15)). Automatically checks in the
    default location (`$HOME/.minecraft`) as well as the flatpak install location. Other locations
    can be chosen with the `--mcdir` option or by editing the `user_preferences.json` file.
* Fixes syntax error in v2.3.2
  * Original fix was force-pushed over the same commit but did not apply to the existing tag (my bad)
* Manual download URLs now point to `legacy.curseforge.com` instead of `www.curseforge.com`
  * It seems like the data is being moved from the legacy site to the new site, and some files only
    exist on the new site and not the old one. If any manual download links return a 404 error,
    try changing the URL to start with `www.curseforge.com`.

#### v2.3.2 - 2023-02-24
* Fix crash in the datapack detection logic when the modpack data has already been successfully
  installed. ([#26](https://github.com/cdbbnnyCode/modpack-installer/issues/26))

#### v2.3.1 - 2023-02-07
* Detect included datapacks (i.e. for Repurposed Structures) and install them to
  `.minecraft/datapacks`. Some modpacks will find datapacks at this location and will automatically
  include them in new worlds, but this is not vanilla behavior (AFAIK).
* [Forge] Read the Minecraft Forge download page to determine the file name rather than assuming that
  it follows a consistent pattern ([#25](https://github.com/cdbbnnyCode/modpack-installer/pull/25)).

#### v2.3.0 - 2022-07-06
* Use the officially documented CurseForge API
  * Add a project-specific API key from CurseForge; derived projects must use a different key!
  * Add experimental rate-limiting (3 JSON requests per second)
  * Request the user to manually download files that have the Project Distribution Toggle disabled.
    The script will directly import these files from the user's download directory.
* Fix the `status_bar()` function so that the status bar is right-aligned properly

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
