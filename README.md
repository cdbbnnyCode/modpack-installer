## CurseForge Modpack Installer  
###### V1.0-beta
This is a small tool for Linux users to be able to install Minecraft modpacks
from CurseForge without the Twitch client. It generates isolated Minecraft
environments separate from your main .minecraft directory to avoid modifying
your default Minecraft installation.  
*DISCLAIMER: This tool has not been thoroughly tested! If you find a bug, please
help me out by posting an issue!*

### Requirements  
This program requires the Minecraft launcher, Python 3, NodeJS and Java (8 or
higher). The only dependency library is not automatically installed is Requests,
which can be installed with Pip (or your favorite method of installing Python
libraries):  
```
pip3 install --user requests
```
The Minecraft launcher must be in the PATH and named `minecraft-launcher`.
This is known to work in Arch Linux, but other distros may have Minecraft
installed differently.

### How to Use
* Download a modpack and move the zip file into this directory.
* Open a terminal in this directory and type:
  ```
  python installer.py <modpack_name.zip>
  ```
replacing `<modpack_name.zip>` with the name of the zip file you just downloaded.
* To launch Minecraft, `cd` to `packs/<modpack_name>` and run
  ```
  minecraft-launcher --workDir .
  ```
* To uninstall a modpack, simply delete its folder under the `packs/` directory.
  All of your saves, resource packs, and shader packs will be retained and
  available in your other modpacks.

### How it Works
The installer script goes through several steps to install the modpack:
* First, it unzips the modpack zip into the `.packs` folder. The zip file contains
  a manifest file defining which version of Forge to use and a list of all of the
  mods in the pack, along with resource and configuration files.
* Next, it creates a `.minecraft` folder for the modpack. It starts the launcher
  in order to create a `launcher_profiles.json` file, which is needed to install
  Forge. This step is skipped if a `.minecraft` folder already exists.
* Next, it runs `forge_install.py` to install Forge. This script downloads the
  requested version of the Forge installer and uses the `ForgeHack.java` program
  to bypass the install GUI and install directly to the `.minecraft` folder.
* Next, it uses the `mod_download.js` script to download the required mods into
  the `.modcache` folder. The downloader script also generates a list of the mod
  jar files that are used by the modpack. The installer script then uses this
  list to create symlinks to each mod. This reduces total disk usage when multiple
  modpacks use the same mod.
* Finally, the installer copies all of the folders in `overrides` from the unzipped
  modpack folder into the `.minecraft` folder.

### Limitations
* This tool has so far only been tested on one modpack (Sky Factory 4), and may
  not work with other modpacks.
* This tool only works with Minecraft Forge. Other mod loaders will probably never
  be supported.
* This tool always installs all mods, regardless of whether they are marked as
  required.
* Forge installation may fail when installing Forge for versions other than
  1.12.2. This is because the auto-installation hack only currently supports one
  version of the Forge installer binary. More versions (or an alternative
  installation method) will be added in the future.

### License
This project is licensed under the MIT license. See the LICENSE file for details.
