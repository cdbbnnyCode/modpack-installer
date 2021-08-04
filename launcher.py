#!/bin/python3

import os
import subprocess
import sys
import requests
# from util import *
import magic # must be installed maybe: pip3 install magic-python
import json
import time
import shutil

# copied from util, made it a bit safer, could be copied to util.py
def download(url, dest):
    print("Downloading %s" % url)
    try:
        r = requests.get(url, headers = HEADER)
    except Exception as e:
        return e # it could throw a HTML error like 400 here as well

    print("Write file...")
    try:
        if not os.path.exists(os.path.dirname(dest)):
            os.mkdir(os.path.dirname(dest))
        with open(dest, 'wb') as f:
            f.write(r.content)
            f.close()
    except Exception as e:
        return f"Could not write to file '{dest}': {e}"
    
    return r.status_code

# create clear method + fallback if commands cls and clear doesn't exist on the machine
clearConsole = lambda: os.system('cls' if os.name in ('nt', 'dos') else 'clear')
try:
    clearConsole()
except:
    clearConsole = lambda: print("\n" * 100)

# handels colors and variable exchangees
# TODO: Maybe add support for non Ansi consoles (because the color codes are shwon, if the console doesn't support those)
class Format:
    # colors
    def format(text, *colors):
        returnText = ""
        for color in colors:
            returnText += color
        
        returnText += text + Format.RESET

        return returnText

    # Some Ansi Color Codes stolen from Blender Code
    # TODO: Add some more, if needed
    RESET = '\033[0m'
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    ORANGE = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    # changes variables in string trough replacements, ex:
    # Format.exchange("Hello &WORLD&", WORLD = "world!")
    # returns:
    # "Hello world!"
    def exchange(string, **replacements):
        splitString = string.split(VARSPARSER)
        formattedString = splitString
        i = 0
        for split in splitString:
            replace = ""
            if replacements.keys().__contains__(split):
                replace = replacements[split]
                formattedString[i] = replace
            i += 1
        return "".join(formattedString)

    # generates an underlined string
    def underlinedString(string):
        return string + "\n" + Format.underline(string)
    
    # maybe I need those two functions separated later
    def underline(string):
        underline = ""
        for s in string:
            underline += "-"
        return underline

# handles those beautiful menus
class MenuHelper:

    menuPoints = []
    cap = ""

    def __init__(self, caption):
        self.cap = caption
        self.menuPoints = []
    
    # adds an Item to the menu
    def addItem(self,text, function = quit, args = ""):
        self.menuPoints.append({
            'text': str(len(self.menuPoints) + 1) + ") " + Format.exchange(text, CAP=self.cap, NAME=text), 
            'func':function, 
            'args': Format.exchange(args, CAP=self.cap, NAME=text)
            })
    
    # adds an list to the menu
    def addItems(self, list, function, args = ""):
        for item in list:
            self.addItem(item, function, Format.exchange(args, CAP=self.cap, NAME=item))
        
    # shows the menu
    def show(self, error = ""):
        clearConsole()
        if len(self.menuPoints) == 1:
            self.do(0)

        # added this so there is a way to show errors in menus
        if error != "":
            print(Format.format(error, Format.RED))
        
        cap = self.cap
        print(Format.underlinedString(cap))

        for i in self.menuPoints:
            print(i["text"])
        
        # main part of function
        # it will count as 1, if only [return] pressed
        # it checks if entered object is a number and if the entered page does exist (-> function do()), so it should be pretty safe
        n = input()
        if n == "":
            n = 1
        try:
            n = int(n)
        except:
            self.show("Error! Please input only Numbers!")
        
        self.do(n - 1)

    # executes the function which is stored under the exact menu point in the menuPoints dict
    def do(self,n):
        if n < 0 or n >= len(self.menuPoints):
            self.show("Error! This page doesn't exist!")

        function = self.menuPoints[n]['func']
        argument = self.menuPoints[n]['args']
        functionExecutor(function, argument)
        
# this function is used to launch all functions. It gives better accurcy of describing the failure, if an function fails (name + error code).
# If this function would be build in the do-function, it would only display the last function called by an menu and not the recrusive calls of functions
def functionExecutor(function, argument):
    try:
        function(argument)
        print(str(function).split()[1] + '(' + str(argument) + ')')
    except Exception as e:
        quit(Format.format(f"Error in Code: Method \"{str(function).split()[1] + '(' + str(argument) + ')'}\" exited: {e}", Format.RED))

################################################################################################################################################
# Here are the menu functions defined (such as quitting and launching instances)
################################################################################################################################################
def quit(message = "Bye!", clearCons = True):
    if clearCons:
        clearConsole()
    cleanUp(False, True)
    print(message)
    os._exit(1)

def launch(args):
    splitArgs = args.split(ARGSSEPARATOR)
    folder = splitArgs[1]
    if not os.path.exists(PACKSPATH + folder) or not os.path.exists(PACKSPATH + folder + "/.minecraft"):
        quit(Format.format(f"Error! The selected instance under '{folder}' doesn't exist or is broken. Try reset the instance!", Format.RED))
    if not os.path.exists(PACKSPATH + folder + "/.minecraft/mods"):
        print(Format.format("Warning: Your selected instance does not contain a mods-folder! If this is not desired, then try to reset this instance!", Format.ORANGE))
    cmd = Format.exchange(LAUNCHERCOMMAND.replace(" ", "!"), PathToInstance = PACKSPATH + folder)
    try:
        subprocess.Popen(cmd.replace('"', "").split("!"), close_fds=True, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print(Format.format(f"Start Launcher with command \'{cmd.replace('!', ' ')}\'. Press [return] to return to selection.", Format.CYAN))
        input()
        functionExecutor(main, args[0])
    except Exception as e:
        quit(Format.format(f"Error! Your minecraft client doesn't work (correctly). Try to start it manualy: \'{cmd.replace('!', ' ')}\'", Format.RED))

# The method gets launched with only download or local argument. 
# if the argument download is found, then it asks the user for name/id. Then it tries to find the pack with the courseforge API (in case of name it gets first 25 results and shows them in a list) The searchquerry gets downloaded to DOWNLOADPATH/tmp
# When one modpack is chosen (by the search result list), the method calls it self with an additional argument ("selectedPack" and the name of the pack)
# Then it loads the search query again (from local storage) and gets the id of selected pack. This is important, because now it is possible to get direct information of the pack. This direct information is downloaded to DOWNLOADPATH/tmp (gets rewritten)
# It lists all available versions (in some cases there are some missing, but thats not my fault, it's cursforges), from where the user can choose. The method calls itself again but this time with the additional argument "selectedVersion" and the Version name.
# This time it gets the downloadlink and downloads all the credentials (zip archive). The function calls itself again, but this time instead of "download" it's getting called with "local", "zip" and the path to the downloaded zip-file
# Now it executes the install.py script.
# If in installMenu "local install" is selected, then it calls the method install as well but only with the "local" argument. It asks for the path and calls itself with the additional argument "zip" and the path to the zip-file. This calls the install.py script (as well).
def install(args):
    splitArgs = args.split(ARGSSEPARATOR)
    if splitArgs.__contains__("download") and not splitArgs.__contains__("selectedPack"):
        cap = "Download a new instance from link"

        clearConsole()
        print(Format.underlinedString(cap))
        resp = 0
        search = ""
        url = ""
        while True:
            print("Please paste the name or the ID of Modpack (q to quit): ")
            search = input()
            if search == "q":
                main()
                quit(Format.format("Error! You shouldn't be here anymore! Check the main function! (Calling from install())", Format.BLUE))
            try:
                id = int(search)
                url = f"{BASEURL}{id}"
            except:
                name = search.replace(" ", "%20")
                url = f"{BASEURL}search?categoryId=0&gameId=432&gameVersion=&index=0&pageSize=15&searchFilter={name}&sectionId=4471&sort=0"
            
            resp = download(url, DOWNLOADPATH + "tmp")
            if resp != 200:
                print(Format.format(f"Error! Can't find a pack with thses credentials: {search}", Format.RED))
                if type(resp).__name__ == "int":
                    print(Format.format("HTML Error Code: " + str(resp), Format.ORANGE))
                else:
                    print(Format.format("Error Code: " + str(resp), Format.ORANGE))
            else:
                break

        with open(DOWNLOADPATH + "tmp", "rt") as jsonFile:
            data = json.load(jsonFile)
            if type(data).__name__ == "dict":
                data = [data]
                jsonFile.close()
                with open(DOWNLOADPATH + "tmp", "wt") as file:
                    file.write(json.dumps(data))
                    file.close()
            elif type(data).__name__ == "list":
                pass
            else:
                quit(Format.format(f"Error! The script can't read curseforges API. Please try {url} an verify, that the result is a json-type file (and not '{type(data).__name__})'", Format.RED))

        searchRes = {}
        for dataPart in data:
            searchRes.update({dataPart["name"]: dataPart["id"]})
        
        searchMenu = MenuHelper(f"Search Result for '{search}'")
        searchMenu.addItems(searchRes, install, argsParser(splitArgs[0], addArgs = [args, "selectedPack", "&NAME&"]))
        searchMenu.addItem("quit", cleanUp, "")
        searchMenu.show()
    
    elif splitArgs.__contains__("download") and splitArgs.__contains__("selectedPack") and not splitArgs.__contains__("selectedVersion"):
        clearConsole()
        modpackName = splitArgs[splitArgs.index("selectedPack") + 1]
        
        with open(DOWNLOADPATH + "tmp") as jsonFile:
            data = json.load(jsonFile)
            jsonFile.close()
        searchRes = {}
        for dataPart in data:
            searchRes.update({dataPart["name"]: (dataPart["id"], {})})
            for dataPartVersions in reversed(dataPart["latestFiles"]):
                searchRes[dataPart["name"]][1].update({dataPartVersions["displayName"]: dataPartVersions["downloadUrl"]})
        
        modpackId = searchRes[modpackName][0]

        print(f"Getting Modpack {modpackName} ({modpackId})...")
        url = f"{BASEURL}{modpackId}"

        versionMenu = MenuHelper(f"Select an Version for '{modpackName}'")
        versionMenu.addItems(searchRes[modpackName][1], install, argsParser(splitArgs[0], addArgs = [args, "selectedVersion", "&NAME&"]))
        versionMenu.addItem("quit", cleanUp, "")
        versionMenu.show()

    elif splitArgs.__contains__("download") and splitArgs.__contains__("selectedPack") and splitArgs.__contains__("selectedVersion"):
        modpackName = splitArgs[splitArgs.index("selectedPack") + 1]
        version = splitArgs[splitArgs.index("selectedVersion") + 1]

        with open(DOWNLOADPATH + "tmp") as jsonFile:
            data = json.load(jsonFile)
            jsonFile.close()
        searchRes = {}
        for dataPart in data:
            searchRes.update({dataPart["name"]: (dataPart["id"], {})})
            for dataPartVersions in reversed(dataPart["latestFiles"]):
                searchRes[dataPart["name"]][1].update({dataPartVersions["displayName"]: dataPartVersions["downloadUrl"]})
        url = searchRes[modpackName][1][version]

        modpackId = searchRes[modpackName][0]
        
        zipFile = DOWNLOADPATH + \
            Format.exchange(NEWINSTANCENAME, 
                ModpackName = modpackName, 
                ModpackId = modpackId, 
                DisplayModpackVersion = version, 
                NowTime = time.strftime("%H%M%S", time.localtime()), 
                NowDate = time.strftime("%d%m%y", time.localtime()), 
                NowDateUS = time.strftime("%m%d%y", time.localtime())
            ) + ".zip"
        resp = download(url, zipFile)

        if not os.path.exists(DOWNLOADPATH + ".packinfo"):
            open(DOWNLOADPATH + ".packinfo", "xt").close()
        with open(DOWNLOADPATH + ".packinfo", "wt") as packInfoFile:
            packInfoFile.writelines(json.dumps({"modpackId":modpackId, "modpackName": modpackName, "version": version, "downloadUrl": url}))
            packInfoFile.close()

        functionExecutor(install, argsParser(splitArgs[0], addArgs = ["local", "zip", zipFile]))
    
    elif splitArgs.__contains__("local") and not splitArgs.__contains__("zip"):
        cap = "Install a new instance from disk"

        clearConsole()
        print(Format.underlinedString(cap))

        while True:
            print("Please paste the path of your Zip-Archive (q to quit):")
            path = input()
            if path == "q":
                main()
                quit(Format.format("Error! You shouldn't be here anymore! Check the main function! (Calling from install())", Format.BLUE))
            
            print("Vaildating...")
            if not os.path.exists(path):
                print(Format.format(f"Error! Can't find '{path}'!", Format.RED))
                continue

            if magic.detect_from_filename(path).mime_type != "application/zip":
                print(Format.format(f"Error! Specified path '{path}' does not lead to an Zip-Archive!", Format.RED))
                print(Format.format(f"The specified path leads to mime type '{magic.detect_from_filename(path).mime_type}'!", Format.ORANGE))
                continue

            break
        
        print("Ok")
        functionExecutor(install, argsParser(splitArgs[0], addArgs = ["local", "zip", path]))

    elif splitArgs.__contains__("local") and splitArgs.__contains__("zip"):
        
        zipFile = splitArgs[splitArgs.index("zip") + 1]
        cmd = Format.exchange(INSTALLERCOMMAND, ZipFilePath = zipFile)
        
        clearConsole()
        print(f"Opening Installer with command '{cmd}'...")
        try:
            os.chdir(os.path.dirname(__file__))
            os.system(cmd)
            print(Format.format("Finished! Press [return] to return to menu!", Format.GREEN))
            input()
            os.replace(DOWNLOADPATH + ".packinfo", PACKSPATH + zipFile[:-4].split("/")[-1] + "/.packinfo")
            cleanUp()
        except Exception as e:
            print(e)
            cleanUp(False)
        quit(Format.format(f"Error in installer! Try running '{cmd}' in your console and check the output!", Format.RED), False)

def delete(args):
    splitArgs = args.split(ARGSSEPARATOR)
    instance = splitArgs[1]
    if not splitArgs.__contains__("delete"):
        deleteMenu = MenuHelper(f"Would you like to delete the instance '{instance}'? All data will be lost!")
        deleteMenu.addItem("No", main, splitArgs[0])
        deleteMenu.addItem("Yes", delete, argsParser(splitArgs[0], addArgs = [instance, "delete"]))
        deleteMenu.show()
    elif splitArgs.__contains__("delete"):
        print(f"Deleting instance '{instance}'...")
        shutil.rmtree(PACKSPATH + instance)
        print("Done!")
        time.sleep(1)
        if not splitArgs.__contains__("return"):
            main(argsParser(splitArgs[0].split(PATHSEPARATOR)[:-1]))

def reset(args):
    splitArgs = args.split(ARGSSEPARATOR)
    instance = splitArgs[1]
    if not splitArgs.__contains__("reset"):
        resetMenu = MenuHelper(f"Would you like to reset the instance '{instance}'? All data will be lost!")
        resetMenu.addItem("No", main, splitArgs[0])
        resetMenu.addItem("Yes", reset, argsParser(splitArgs[0], addArgs = [instance, "reset"]))
        resetMenu.show()
    elif splitArgs.__contains__("reset") and not splitArgs.__contains__("toDownload"):
        if not os.path.exists(PACKSPATH + instance + "/.packinfo"):
            notfoundMenu = MenuHelper(f"Packinfo file not found! How do you want to proceed?")
            notfoundMenu.addItem("delete instance and download it from search", reset, argsParser(splitArgs[0], addArgs = [instance, "reset", "toDownload"]))
            notfoundMenu.addItem("only delete", delete, argsParser(splitArgs[0], addArgs = [instance, "delete"]))
            notfoundMenu.addItem("abort", main, splitArgs[0])
            notfoundMenu.show()
        
        packInfo = {}
        with open(PACKSPATH + instance + "/.packinfo") as packInfoFile:
            packInfo = json.load(packInfoFile)
            packInfoFile.close()
        
        functionExecutor(delete, argsParser(splitArgs[0], addArgs = [instance, "delete", "return"]))
        
        zipFile = DOWNLOADPATH + f"{instance}.zip"
        resp = download(packInfo['downloadUrl'], zipFile)
        if resp != 200:
            quit(Format.format(f"Error! Can't download {zipFile} from '{url}': {resp}", Format.RED))
        
        with open(DOWNLOADPATH + ".packinfo", "wt") as packInfoFile:
            packInfoFile.writelines(json.dumps(packInfo))
            packInfoFile.close()
        
        functionExecutor(install, argsParser(splitArgs[0], addArgs = ["local", "zip", zipFile]))
    elif splitArgs.__contains__("reset") and splitArgs.__contains__("toDownload"):
        functionExecutor(delete, argsParser(splitArgs[0], addArgs = [instance, "delete", "return"]))
        functionExecutor(install, argsParser(splitArgs[0], addArgs = "download"))

def cleanUp(returnToMenu = True, fullCleanUp = False):
    print("Cleanup...")
    if CLEANUPFILES:
        try:
            shutil.rmtree(DOWNLOADPATH)
            if not fullCleanUp:
                os.mkdir(DOWNLOADPATH)
        except:
            pass
    if returnToMenu == False:
        return
    main("Home%install")

################################################################################################################################################
# this is the main function to manage the navigation
# separator constants:
PATHSEPARATOR = "%" # is used to get navigation path for example to serve the "back"-function
ARGSSEPARATOR = "|" # is used to seperate arguments for the functions. Could have used a dict or list instead of a string with separators, but oh well...
VARSPARSER = "&" # is used to signal an variable for MenuHelper (variable exchanger in Format.exchange())

# file save constants:
DOWNLOADPATH = os.path.dirname(__file__) + f"/.tmp/{time.time()}/" # path to temporarily download files
PACKSPATH = os.path.dirname(__file__) + "/packs/"
NEWINSTANCENAME = "&DisplayModpackVersion&" # available variables: ModpackName, ModpackId, DisplayModpackVersion, NowTime (Format: hhmmss), NowDateUS (Format: MMDDYY), NowDate (Format: DDMMYY) 
# TODO: more arguments (around line: 288)
# The Instance-Name gets transfered, if modpack is reset. Therefore if you use date and time vars it will NOT get updated (could be implemented, important credentials could be saved in .packinfo)

# download constants
BASEURL = "https://addons-ecs.forgesvc.net/api/v2/addon/" # curseforge API
AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36"
HEADER = {"User-Agent": AGENT}

# launch constants
INSTALLERCOMMAND = f'python3 {os.path.dirname(__file__)}/install.py "&ZipFilePath&" --manual' # command to call installer.py
LAUNCHERCOMMAND = 'minecraft-launcher --workDir "&PathToInstance&/.minecraft"' # command to call minecraft client

# misc
CLEANUPFILES = True
################################################################################################################################################
def main(path = "home"):
    splitPath = path.split(PATHSEPARATOR)

    if splitPath[-1] == "selector":
        selectorMenu = MenuHelper("Launch instances")
        selectorMenu.addItems([f for f in os.listdir(PACKSPATH) if not f.startswith('.')], main, argsParser(splitPath, addPath = "launch&NAME&"))
        selectorMenu.addItem("back", main, argsParser(splitPath[:-1]))
        selectorMenu.show()

    elif splitPath[-1][:6] == "launch":
        if len(splitPath[-1]) <= 6:
            quit(Format.format("Error in Code: No launch path in menu specified!", Format.RED))
        launchMenu = MenuHelper(splitPath[-1][6:])
        launchMenu.addItem("launch instance", launch, argsParser(splitPath, addArgs = "&CAP&"))
        launchMenu.addItem("reset instance", reset, argsParser(splitPath, addArgs = "&CAP&"))
        launchMenu.addItem("delete instance", delete, argsParser(splitPath, addArgs = "&CAP&"))
        launchMenu.addItem("back", main, argsParser(splitPath[:-1]))
        launchMenu.show()

    elif splitPath[-1] == "install":
        installMenu = MenuHelper("Install new instances")
        installMenu.addItem("over website download", install, argsParser(splitPath, addArgs = "download"))
        installMenu.addItem("over local package", install, argsParser(splitPath, addArgs = "local"))
        
        installMenu.addItem("back", main, argsParser(splitPath[:-1]))
        installMenu.show()

    else:
        mainMenu = MenuHelper("Launcher Tool for CurseForge Modpack Installer from cdbbnny")
        mainMenu.addItem("launch", main, argsParser(splitPath, addPath = "selector"))
        mainMenu.addItem("install",main, argsParser(splitPath, addPath = "install"))
        mainMenu.addItem("quit",quit, "Bye!")
        mainMenu.show()
    print(Format.format("You shouldn't be here!", Format.RED))

def argsParser(path, **additionalArguments):
    addPath = [] if not additionalArguments.__contains__("addPath") \
        else additionalArguments["addPath"] if type(additionalArguments["addPath"]).__name__ == "list" \
            else [additionalArguments["addPath"]]
    
    addArgs = [] if not additionalArguments.__contains__("addArgs") \
        else additionalArguments["addArgs"] if type(additionalArguments["addArgs"]).__name__ == "list" \
            else [additionalArguments["addArgs"]]
    
    path = path if type(path).__name__ == "list" else [path]

    return ARGSSEPARATOR.join([PATHSEPARATOR.join(path + addPath)] + addArgs)

################################################################################################################################################
if __name__ == "__main__":
    main()
