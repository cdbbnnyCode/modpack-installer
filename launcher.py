#!/bin/python3

import os
import subprocess
import sys
import requests
# from util import *
import json
import time
import shutil
import argparse

import install as installScript

# copied from util, made it a bit safer, could be copied to util.py
def download(url, dest):
    print("Downloading %s" % url)
    try:
        r = requests.get(url, headers = HEADER)
    except (requests.exceptions) as e:
        return 404 # it could return a HTML error like 400 or 404 here as well
    print("Write file...")
    try:
        with open(dest, 'wb') as f:
            f.write(r.content)
    except IOError as e:
        return f"Could not write to file '{dest}': {e}"
    
    return r.status_code

# create clear method + fallback if commands cls and clear doesn't exist on the machine
def clearConsole():
    os.system('cls' if os.name in ('nt', 'dos') else 'clear')

try:
    clearConsole()
except OSError:
    def clearConsole(): 
        print("\n" * 100)

def addDicts(dict1, *dict2):
    tempDict = dict1
    for dict in dict2:
        tempDict.update(dict)
    
    return tempDict



# handels colors and variable exchangees
# TODO: Maybe add support for non Ansi consoles (because the color codes are shwon, if the console doesn't support those)
class Format:
    # colors
    @staticmethod
    def format(text, *colors):
        returnText = ""
        if not NOCOLORS:
            for color in colors:
                returnText += color
            
            returnText += text + Format.RESET
        else:
            returnText = text

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

    # generates an underlined string
    @staticmethod
    def underlinedString(string):
        return string + "\n" + Format.underline(string)
    
    # maybe I need those two functions separated later
    @staticmethod
    def underline(string):
        return "-" * len(string)

# handles those beautiful menus
class MenuHelper:

    menuPoints = []
    cap = ""

    def __init__(self, caption):
        self.cap = caption
        self.menuPoints = []
    
    # adds an Item to the menu
    def addItem(self,text, function = quit, args = {}):
        argsItem = {}
        for key in args:
            if type(args[key]).__name__ == "str":
                argsItem[key] = args[key].format(CAP=self.cap, NAME=text)
            else:
                argsItem[key] = args[key]
        self.menuPoints.append({
            'text': str(len(self.menuPoints) + 1) + ") " + text.format(CAP=self.cap, NAME=text), 
            'func':function, 
            'args': argsItem
            })
    
    # adds an list to the menu
    def addItems(self, list, function, args = {}):
        for item in list:
            self.addItem(item, function, args)
        
    # shows the menu
    def show(self, error = ""):
        clearConsole()

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
        except ValueError:
            self.show("Error! Please input only Numbers!")
        
        self.do(n - 1)

    # executes the function which is stored under the exact menu point in the menuPoints dict
    def do(self,n):
        if n < 0 or n >= len(self.menuPoints):
            self.show("Error! This page doesn't exist!")

        function = self.menuPoints[n]['func']
        argument = self.menuPoints[n]['args']
        function(argument)

################################################################################################################################################
# Here are the menu functions defined (such as quitting and launching instances)
################################################################################################################################################
def quit(args):
    if not "message" in args:
        args["message"] = "Bye!"
    if (not "clearConsole" in args) or ("clearConsole" in args and args["clearConsole"] == True):
        clearConsole()
    cleanUp({"returnToMenu": False, "fullCleanUp": True})
    print(args["message"])
    os._exit(1)

def launch(args):
    folder = args['instance']
    if not os.path.exists(PACKSPATH + folder) or not os.path.exists(PACKSPATH + folder + "/.minecraft"):
        quit({"message": Format.format(f"Error! The selected instance under '{folder}' doesn't exist or is broken. Try reset the instance!", Format.RED)})
    if not os.path.exists(PACKSPATH + folder + "/.minecraft/mods"):
        print(Format.format("Warning: Your selected instance does not contain a mods-folder! If this is not desired, then try to reset this instance!", Format.ORANGE))
    cmd = LAUNCHERCOMMAND.replace(" ", "!").format(PathToInstance = PACKSPATH + folder)
    try:
        subprocess.Popen(cmd.replace('"', "").split("!"), close_fds=True, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print(Format.format(f"Start Launcher with command \'{cmd.replace('!', ' ')}\'. Press [return] to return to selection.", Format.CYAN))
        input()
        main({"path" : args['path']})
    except OSError as e:
        quit({"message": Format.format(f"Error! Your minecraft client doesn't work (correctly). Try to start it manualy: \'{cmd.replace('!', ' ')}\'", Format.RED)})

# The method gets launched with only download or local argument. 
# if the argument download is found, then it asks the user for name/id. Then it tries to find the pack with the courseforge API (in case of name it gets first 25 results and shows them in a list) The searchquerry gets downloaded to DOWNLOADPATH/tmp
# When one modpack is chosen (by the search result list), the method calls it self with an additional argument ("selectedPack" and the name of the pack)
# Then it loads the search query again (from local storage) and gets the id of selected pack. This is important, because now it is possible to get direct information of the pack. This direct information is downloaded to DOWNLOADPATH/tmp (gets rewritten)
# It lists all available versions (in some cases there are some missing, but thats not my fault, it's cursforges), from where the user can choose. The method calls itself again but this time with the additional argument "selectedVersion" and the Version name.
# This time it gets the downloadlink and downloads all the credentials (zip archive). The function calls itself again, but this time instead of "download" it's getting called with "local", "zip" and the path to the downloaded zip-file
# Now it executes the install.py script.
# If in installMenu "local install" is selected, then it calls the method install as well but only with the "local" argument. It asks for the path and calls itself with the additional argument "zip" and the path to the zip-file. This calls the install.py script (as well).
def install(args):
    if not "source" in args:
        quit({"message": Format.format(f"Error! Arguments for install-function are incorrect: {args['path']}", Format.RED)})

    if args["source"] == "web" and not "selectedPackName" in args and not "selectedPack" in args:
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
                quit({"message": Format.format("Error! You shouldn't be here anymore! Check the main function! (Calling from install())", Format.BLUE)})
            try:
                id = int(search)
                install(addDicts(args, {"selectedPack": f"{id}"}))
                break
            except ValueError:
                name = search.replace(" ", "%20")
                url = f"{BASEURL}search?categoryId=0&gameId=432&gameVersion=&index=0&pageSize=15&searchFilter={name}&sectionId=4471&sort=0"
            
            if not os.path.exists(os.path.dirname(DOWNLOADPATH + "tmp")):
                os.mkdir(os.path.dirname(DOWNLOADPATH + "tmp"))
            
            resp = download(url, DOWNLOADPATH + "tmp")
            if resp != 200:
                print(Format.format(f"Error! Can't find a pack with these credentials: {search}", Format.RED))
                if type(resp).__name__ == "int":
                    print(Format.format("HTML Error Code: " + str(resp), Format.ORANGE))
                else:
                    print(Format.format("Error Code: " + str(resp), Format.ORANGE))
            else:
                break

        with open(DOWNLOADPATH + "tmp", "rt") as jsonFile:
            data = json.load(jsonFile)
        
        if not type(data).__name__ == "list":
            quit({"message": Format.format(f"Error! The script can't read curseforges API. Please try {url} an verify, that the result is a json-type file (and not '{type(data).__name__})'", Format.RED)})
                
        searchRes = {}
        for dataPart in data:
            searchRes.update({dataPart["name"]: dataPart["id"]})
        
        searchMenu = MenuHelper(f"Search Result for '{search}'")
        searchMenu.addItems(searchRes, install, addDicts(args, {"selectedPackName": "{NAME}"}))
        searchMenu.addItem("quit", cleanUp)
        searchMenu.show()
    
    elif args["source"] == "web" and "selectedPackName" in args and not "selectedPack" in args and not "selectedVersionName" in args:
        with open(DOWNLOADPATH + "tmp", "rt") as jsonFile:
            data = json.load(jsonFile)

        searchRes = {}
        for dataPart in data:
            searchRes.update({dataPart["name"]: dataPart["id"]})
        install(addDicts(args, {"selectedPack": searchRes[args["selectedPackName"]]}))

    elif args["source"] == "web" and "selectedPack" in args and not "selectedVersionName" in args:
        clearConsole()
        modpackId = args["selectedPack"]
        
        if not os.path.exists(os.path.dirname(DOWNLOADPATH + "tmp")):
                os.mkdir(os.path.dirname(DOWNLOADPATH + "tmp"))

        resp = download(BASEURL + str(modpackId), DOWNLOADPATH + "tmp")
        if resp != 200:
            print(Format.format(f"Error! Can't find a pack with this ID: {modpackId}", Format.RED))
            if type(resp).__name__ == "int":
                print(Format.format("HTML Error Code: " + str(resp), Format.ORANGE))
            else:
                print(Format.format("Error Code: " + str(resp), Format.ORANGE))
            print("Press [return] to go back to search!")
            input()
            install({"path": args["path"], "source": "web"})        

        with open(DOWNLOADPATH + "tmp") as jsonFile:
            data = json.load(jsonFile)
        
        packInfoSearch = {}
        packInfoSearch["modpackName"] = data["name"]
        packInfoSearch["modpackId"] = data["id"]
        packInfoSearch["latestFiles"] = {}
        for latestFile in reversed(data["latestFiles"]):
            index = 0
            modloader = "Forge"
            for i in range(len(latestFile["sortableGameVersion"])): # important, because curseforge mixes versions
                if latestFile["sortableGameVersion"][i]["gameVersionName"].find(".") > -1:
                    index = i
                elif latestFile["sortableGameVersion"][i]["gameVersionName"].find("Fabric") > -1:
                    modloader = "Fabric"
            packInfoSearch["latestFiles"][latestFile["displayName"]] = {
                "versionId": latestFile["id"], 
                "downloadUrl": latestFile["downloadUrl"], 
                "minecraftVersionName": latestFile["sortableGameVersion"][index]["gameVersionName"],
                "modloader": modloader}
        
        modpackName = packInfoSearch["modpackName"]

        versionMenu = MenuHelper(f"Select an Version for '{modpackName}'")
        versionMenu.addItems(packInfoSearch["latestFiles"], install, addDicts(args, {"selectedVersionName": "{NAME}", "packInfoSearch": packInfoSearch}))
        versionMenu.addItem("quit", cleanUp)
        versionMenu.show()

    elif args["source"] == "web" and "selectedPack" in args and "selectedVersionName" in args:
        modpackName = args["selectedPack"]
        version = args["selectedVersionName"]
        packInfoSearch = args["packInfoSearch"]
        modpackId = packInfoSearch["modpackId"]
        
        packInfoSearch["selectedVersion"] = packInfoSearch["latestFiles"][args["selectedVersionName"]]
        packInfoSearch["selectedVersion"]["versionName"] = args["selectedVersionName"]
        
        zipFile = DOWNLOADPATH + \
            NEWINSTANCENAME.format(
                ModpackName = modpackName, 
                ModpackId = modpackId, 
                ModpackVersionName = packInfoSearch["selectedVersion"]["versionName"], 
                MinecraftVersionName = packInfoSearch["selectedVersion"]["minecraftVersionName"],
                ModpackVersionId = packInfoSearch["selectedVersion"]["versionId"],
                Modloader = packInfoSearch["selectedVersion"]["modloader"],
                NowTime = time.strftime("%H%M%S", time.localtime()), 
                NowDate = time.strftime("%d%m%y", time.localtime()), 
                NowDateUS = time.strftime("%m%d%y", time.localtime())
            ).replace(".zip","") + ".zip"
        if not os.path.exists(os.path.dirname(zipFile)):
            os.mkdir(os.path.dirname(zipFile))
        url = packInfoSearch["selectedVersion"]["downloadUrl"]
        resp = download(url, zipFile)

        if not os.path.exists(DOWNLOADPATH + ".packinfo"):
            open(DOWNLOADPATH + ".packinfo", "xt").close()
        with open(DOWNLOADPATH + ".packinfo", "wt") as packInfoFile:
            packInfoFile.writelines(json.dumps(packInfoSearch))

        install({"path": args["path"], "source": "local", "zip": zipFile})
    
    elif args["source"] == "local" and not "zip" in args:
        cap = "Install a new instance from disk"

        clearConsole()
        print(Format.underlinedString(cap))

        while True:
            print("Please paste the path of your Zip-Archive (q to quit):")
            path = input()
            if path == "q":
                main()
            
            print("Vaildating...")
            if not os.path.exists(path):
                print(Format.format(f"Error! Can't find '{path}'!", Format.RED))
                continue

            if not path.endswith('.zip'):
                print(Format.format(f"Error! Specified path '{path}' does not lead to an Zip-Archive!", Format.RED))
                continue

            break
        
        print("Ok")
        install(args["path"].update({"source": "local", "zip": path}))

    elif args["source"] == "local" and "zip" in args:
        
        zipFile = args["zip"]

        with open(DOWNLOADPATH + ".packinfo") as packInfoFile:
            packInfo = json.load(packInfoFile)
        
        minecraftVersionName = packInfo["selectedVersion"]["minecraftVersionName"]
        modloader = packInfo["selectedVersion"]["modloader"]

        versionNumberString = ""
        for i in range(0, 3): # a mc version consits out of 3 numbers
            if len(minecraftVersionName.split(".")) > i: # I don't really know, how curseforge handels 1.8 (1.8 or 1.8.0). Therefore I am going safe and check, if it has that much numbers. If not, just place "000"
                versionNumberString += minecraftVersionName.split(".")[i].zfill(3)
            else:
                versionNumberString += "000"
        versionNumber = int(versionNumberString)
        print()
        if AUTOMATICVERSION[modloader]["only"].__contains__(versionNumber) or (len(AUTOMATICVERSION[modloader]["only"]) == 0 and \
            versionNumber <= AUTOMATICVERSION[modloader]["max"] and \
            versionNumber >= AUTOMATICVERSION[modloader]["min"] and \
            not AUTOMATICVERSION[modloader]["not"].__contains__(versionNumber)):
            manual = False
        else:
            manual = True
        
        clearConsole()
        print(f"Opening Installer: Zipfile = {zipFile}, manual = {manual}")
        try:
            os.chdir(os.path.dirname(__file__))
            installScript.main(zipFile, manual)
            print(Format.format("Finished! Press [return] to return to menu!", Format.GREEN))
            input()
            os.replace(DOWNLOADPATH + ".packinfo", PACKSPATH + zipFile[:-4].split("/")[-1] + "/.packinfo")
            cleanUp()
        except Exception as e: # I think I should leave it here
            cleanUp({"returnToMenu": False})
            cmd = "\'python3 " + os.path.dirname(__file__) + "install.py \"" + zipFile + "\" --manual\'" if manual else "\"\'"
            print(Format.format(f"Error in installer! Try running {cmd} in your console and check the output!", Format.RED))
            quit({"message": Format.format("Errorcode: " + str(e), Format.ORANGE), "clearConsole": False})
        
def delete(args):
    instance = args["instance"]
    if not "confirmed" in args:
        deleteMenu = MenuHelper(f"Would you like to delete the instance '{instance}'? All data will be lost!")
        deleteMenu.addItem("No", main, {"path": args["path"]})
        deleteMenu.addItem("Yes", delete, {"path": args["path"],"instance": instance, "confirmed": True})
        deleteMenu.show()
    elif "confirmed" in args and args["confirmed"]:
        print(f"Deleting instance '{instance}'...")
        shutil.rmtree(PACKSPATH + instance)
        print("Done!")
        time.sleep(1)
        if (not "return" in args) or ("return" in args and args["return"] == False):
            main()

def reset(args):
    instance = args["instance"]
    if not "confirmed" in args:
        resetMenu = MenuHelper(f"Would you like to reset the instance '{instance}'? All data will be lost!")
        resetMenu.addItem("No", main, {"path": args["path"]})
        resetMenu.addItem("Yes", reset, {"path": args["path"], "instance": instance, "confirmed": True})
        resetMenu.show()
    elif "confirmed" in args and args["confirmed"] == True and not "toDownload" in args:
        if not os.path.exists(PACKSPATH + instance + "/.packinfo"):
            notfoundMenu = MenuHelper(f"Packinfo file not found! How do you want to proceed?")
            notfoundMenu.addItem("delete instance and download it from search", reset, {"path": args["path"], "instance": instance, "confirmed": True, "toDownload": True})
            notfoundMenu.addItem("only delete", delete, {"path": args["path"]})
            notfoundMenu.addItem("abort", main, {"path": args["path"]})
            notfoundMenu.show()
        
        packInfo = {}
        with open(PACKSPATH + instance + "/.packinfo") as packInfoFile:
            packInfo = json.load(packInfoFile)
        
        delete({"path": args["path"], "instance": instance, "confirmed": True, "return": True})
        
        zipFile = DOWNLOADPATH + f"{instance}.zip"
        resp = download(packInfo["selectedVersion"]['downloadUrl'], zipFile)
        if resp != 200:
            quit({"message": Format.format(f"Error! Can't download {zipFile} from \'{packInfo['selectedVersion']['downloadUrl']}\': {resp}", Format.RED)})
        
        with open(DOWNLOADPATH + ".packinfo", "wt") as packInfoFile:
            packInfoFile.writelines(json.dumps(packInfo))
        
        install({"path": args["path"], "source": "local", "zip": zipFile})
    elif "confirmed" in args and args["confirmed"] == True and "toDownload" in args and args["toDownload"] == True:
        delete({"path": args["path"], "instance": instance, "mode": "delete", "return": True})
        install({"path": args["path"], "source": "download"})

def cleanUp(args = {}):
    
    if not "path" in args:
        args["path"] = "home"
    if not "returnToMenu" in args:
        args["returnToMenu"] = True
    if not "fullCleanUp" in args:
        args["fullCleanUp"] = False
    print("Cleanup...")
    if CLEANUPFILES:
        try:
            shutil.rmtree(DOWNLOADPATH)
            if not args["fullCleanUp"]:
                os.mkdir(DOWNLOADPATH)
        except (shutil.Error, FileNotFoundError):
            pass
    if args["returnToMenu"] == False:
        return
    main({"path": args["path"]})

################################################################################################################################################
# this is the main function to manage the navigation
# separator constants:
PATHSEPARATOR = "%" # is used to get navigation path for example to serve the "back"-function

# file save constants:
DOWNLOADPATH = f"/tmp/mcmodpackinstaller/" # path to temporarily download files
PACKSPATH = os.path.dirname(__file__) + "/packs/"
NEWINSTANCENAME = "{ModpackVersionName}" # 
# available variables: ModpackName, ModpackId, ModpackVersionName, MinecraftVersionName, ModpackVersionId, Modloader, NowTime (Format: hhmmss), NowDateUS (Format: MMDDYY), NowDate (Format: DDMMYY) 
# TODO: more arguments (around line: 288)
# The Instance-Name gets transfered, if modpack is reset. Therefore if you use date and time vars it will NOT get updated (could be implemented, important credentials could be saved in .packinfo)

# download constants
BASEURL = "https://addons-ecs.forgesvc.net/api/v2/addon/" # curseforge API
AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36"
HEADER = {"User-Agent": AGENT}

# launch constants
AUTOMATICVERSION = {"Forge": {"min": 00000000, "max": 100100100, "not": [], "only": [1012002]}, "Fabric": {"min": 00000000, "max": 100100100, "not": [], "only": []}} # seems a bit overkill, but now it can be precisely determined, wich version is supported.
    # it uses a special formating: Minecraft version aaa.bbb.ccc = aaabbbccc, 1.12.2 -> 001012002 or 1012002
    # if not/only is empty, it will be ignored
    # min/max specifies min/max version, wich could be automatically installed
    # every version is supported: {"min": 00000000, "max": 100100100, "not": [], "only": []}
    # only 1.12.2 is supported: {"min": 00000000, "max": 100100100, "not": [], "only": [1012002]}
    # version 1.12 - 1.12.2 is supported: {"min": 1012000, "max": 1012002, "not": [], "only": []}
LAUNCHERCOMMAND = 'minecraft-launcher --workDir "{PathToInstance}/.minecraft"' # command to call minecraft client

# misc
CLEANUPFILES = True
NOCOLORS = None # None = listen to command line argument, default False; False/True overwrites command line argument
################################################################################################################################################
def main(args = {}):
    if not "path" in args:
        args["path"] = "home"
    splitPath = args["path"].split(PATHSEPARATOR)

    if splitPath[-1] == "selector":
        selectorMenu = MenuHelper("Launch instances")
        selectorMenu.addItems([f for f in os.listdir(PACKSPATH) if not f.startswith('.')], main, {"path": args["path"] + PATHSEPARATOR + "launch{NAME}"})
        selectorMenu.addItem("back", main, {"path": PATHSEPARATOR.join(splitPath[:-1])})
        selectorMenu.show()

    elif splitPath[-1][:6] == "launch":
        if len(splitPath[-1]) <= 6:
            quit({"message": Format.format("Error in Code: No launch path in menu specified!", Format.RED)})
        launchMenu = MenuHelper(splitPath[-1][6:])
        launchMenu.addItem("launch instance", launch, {"path": args["path"], "instance": "{CAP}"})
        launchMenu.addItem("reset instance", reset, {"path": args["path"], "instance": "{CAP}"})
        launchMenu.addItem("delete instance", delete, {"path": args["path"], "instance": "{CAP}"})
        launchMenu.addItem("back", main, {"path": PATHSEPARATOR.join(splitPath[:-1])})
        launchMenu.show()

    elif splitPath[-1] == "install":
        installMenu = MenuHelper("Install new instances")
        installMenu.addItem("over website download", install, {"path": args["path"], "source": "web"})
        installMenu.addItem("over local package", install, {"path": args["path"], "source": "local"})
        installMenu.addItem("back", main, {"path": PATHSEPARATOR.join(splitPath[:-1])})
        installMenu.show()

    else:
        mainMenu = MenuHelper("Launcher Tool for CurseForge Modpack Installer from cdbbnny")
        mainMenu.addItem("launch", main, {"path": args["path"] + PATHSEPARATOR + "selector"})
        mainMenu.addItem("install",main, {"path": args["path"] + PATHSEPARATOR + "install"})
        mainMenu.addItem("quit",quit)
        mainMenu.show()
    print(Format.format("You shouldn't be here!", Format.RED))

################################################################################################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-nc", "--no-colors", "--no-colours",help="Deactivate colorful output" ,action='store_const', const=True, default=False)
    commandlineArgs = parser.parse_args()
    if NOCOLORS == None:
        NOCOLORS = commandlineArgs.no_colors
    cleanUp({"path":"home"}) # sarts main function
