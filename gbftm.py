import tweepy
from urllib import request, parse
from urllib.parse import quote, unquote
import os
from PIL import Image, ImageFont, ImageDraw
import pyperclip
import base64
import json
from io import BytesIO
import re
import time
import sys

class GBFTM():
    def __init__(self, path=""):
        print("GBF Thumbnail Maker v1.16")
        self.path = path
        self.assets = []
        self.settings = {}
        self.load()
        self.client = None
        self.list_assets()
        self.cache = {}
        self.classes = { # class prefix (gotta add them manually, sadly)
            10: 'sw',
            11: 'sw',
            12: 'wa',
            13: 'wa',
            14: 'kn',
            15: 'sw',
            16: 'me',
            17: 'bw',
            18: 'mc',
            19: 'sp',
            30: 'sw',
            41: 'ax',
            42: 'sp',
            43: 'me',
            44: 'bw',
            45: 'sw',
            20: 'kn',
            21: 'kt',
            22: 'kt',
            23: 'sw',
            24: 'gu',
            25: 'wa',
            26: 'kn',
            27: 'mc',
            28: 'kn',
            29: 'gu'
        }
        self.nullchar = [3030182000, 3020072000]
        self.regex = [
            re.compile('(30[0-9]{8})_01\\.'),
            re.compile('(20[0-9]{8})_02\\.'),
            re.compile('(20[0-9]{8})\\.'),
            re.compile('(10[0-9]{8})\\.')
        ]
        self.asset_urls = [
            [
                "https://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/s/{}.jpg",
                "https://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/quest/{}.jpg",
                "ttp://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/my/{}.png",
                "https://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/job_change/{}.png",
                "https://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/job_change/{}.png"
            ],
            [
                "https://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/s/{}.jpg",
                "https://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/m/{}.jpg",
                "https://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/b/{}.png",
                "https://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/b/{}.png",
                "https://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/b/{}.png"
            ],
            [
                "https://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/s/{}.jpg",
                "https://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/{}.jpg",
                "https://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/my/{}.png",
                "https://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/b/{}.png",
                "https://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/b/{}.png"
            ],
            [
                "https://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/npc/s/{}.jpg",
                "https://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/npc/quest/{}.jpg",
                "https://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/npc/my/{}.png",
                "https://game-a.granbluefantasy.jp/assets_en/img_low/sp/assets/npc/b/{}.png",
                "https://media.skycompass.io/assets/customizes/characters/1138x1138/{}.png"
            ],
            [
                "assets/{}",
                "assets/{}",
                "assets/{}",
                "assets/{}",
                "assets/{}"
            ],
            [
                "https://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/s/{}.jpg",
                "https://game-a1.granbluefantasy.jp/assets_en/img/sp/deckcombination/base_empty_weapon_sub.png",
                "",
                "",
                ""
            ],
            [
                "https://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/npc/s/{}.jpg",
                "https://game-a1.granbluefantasy.jp/assets_en/img/sp/deckcombination/base_empty_npc.jpg",
                "",
                "",
                ""
            ]
        ]
        self.possible_pos = ["topleft", "left", "bottomleft", "bottom", "bottomright", "right", "topright", "top", "middle"]
        self.possible_display = ["squareicon", "partyicon", "fullart", "homeart", "skycompass"]

    def list_assets(self): # list all .png or .jpg files in the /assets folder
        try: self.assets = [f for f in os.listdir(self.path + "assets") if (os.path.isfile(os.path.join(self.path + "assets", f)) and (f.endswith('.png') or f.endswith('.jpg')))]
        except: self.assets = []
        print(len(self.assets), "asset(s) found")

    def test_twitter(self, silent=False): #  test if twitter is available
        try:
            self.client = tweepy.Client(bearer_token = self.settings.get('twitter', ''))
            if not silent: print("Twitter set")
            return True
        except:
            self.client = None
            if not silent: print("Failed to access Twitter, check your Bearer Token")
            return False

    def load(self): # load settings.json
        try:
            with open(self.path + 'settings.json') as f:
                self.settings = json.load(f)
        except Exception as e:
            print("Failed to load settings.json")
            while True:
                print("An empty settings.json file will be created, continue? (y/n)")
                i = input()
                if i.lower() == 'n': exit(0)
                elif i.lower() == 'y': break
                self.save()

    def save(self): # save settings.json
        try:
            with open(self.path + 'settings.json', 'w') as outfile:
                json.dump(self.settings, outfile)
        except:
            pass

    def request(self, url): # do a HTTP request and return the result
        try:
            req = request.Request(url)
            url_handle = request.urlopen(req)
            data = url_handle.read()
            url_handle.close()
            return data
        except:
            return None

    def checkDiskCache(self): # check if cache folder exists (and create it if needed)
        if not os.path.isdir(self.path + 'cache'):
            os.mkdir(self.path + 'cache')

    def checkAssetFolder(self): # check if assets folder exists (and create it if needed)
        if not os.path.isdir(self.path + 'assets'):
            os.mkdir(self.path + 'assets')

    def retrieve_raid_image(self, search): # retrieve and save a raid image from its tweetdeck code
        try:
            if self.client is None and not self.test_twitter():
                print("Twitter Bearer token not set")
                return None
            tweets = self.client.search_recent_tweets(query=search, tweet_fields=['source'], media_fields=['preview_image_url', 'url'], expansions=['attachments.media_keys'], max_results=10, user_auth=False)
            if tweets.data is None: raise Exception("No results found")
            try: media = {m["media_key"]: m for m in tweets.includes['media']}
            except: media = {}
            for t in tweets.data:
                if t['data']['source'] == "グランブルー ファンタジー":
                    raid_key = t.text.split("I need backup!\n")[1].split('\n')[0].lower()
                    img = self.request(media[t['attachments']['media_keys'][0]].url)
                    self.checkAssetFolder()
                    with open(self.path + "assets/" + raid_key + ".jpg", "wb") as f:
                        f.write(img)
                    self.assets.append(raid_key + ".jpg")
                    print("Image saved as", raid_key + ".jpg")
                    return raid_key + ".jpg"
            print("No images found")
        except Exception as e:
            print("An error occured:", e)
        return None

    def edit_settings(self): # edit setting menu
        while True:
            print()
            print("SETTINGS MENU")
            print("[0] Set Twitter Token")
            print("[Any] Back")
            s = input()
            match s:
                case "0":
                    t = input("Please copy and paste your token (Leave blank to cancel):")
                    if t != "":
                        self.settings["twitter"] = t
                        if self.test_twitter():
                            self.save()
                case _:
                    break

    def add_asset(self): # to download and save files into the assets folder
        while True:
            print()
            print("ASSET MENU")
            print("[0] Download Item")
            print("[1] Download Pride of Ascendant")
            print("[2] Download from URL")
            print("[3] Download from Twitter")
            print("[Any] Back")
            s = input()
            match s:
                case "0":
                    try:
                        s = int(input("Input the item ID:"))
                        if s < 0: raise Exception()
                        u = "https://game-a.granbluefantasy.jp/assets_en/img/sp/assets/item/article/m/{}.jpg".format(s)
                    except:
                        print("Invalid ID")
                        continue
                case "1":
                    try:
                        s = int(input("Input the pride ID:"))
                        if s < 1: raise Exception()
                        while True:
                            print("[0] Proud")
                            print("[1] Proud+")
                            p = input()
                            if p in ["0", "1"]: break
                        u = "https://game-a1.granbluefantasy.jp/assets_en/img/sp/quest/assets/free/conquest_{}_proud{}.png".format(str(s).zfill(3), ("plus" if p == "1" else ""))
                    except:
                        print("Invalid ID")
                        continue
                case "2":
                    u = input("Input the URL:")
                    if not u.startswith("http") and not u.endswith(".png") and not u.endswith(".jpg"):
                        print("Invalid URL")
                        continue
                case "3":
                    self.retrieve_raid_image(input("Input a Tweetdeck code:"))
                    continue
                case _:
                    break
            try:
                img = self.request(u)
                self.checkAssetFolder()
                s = input("Please input a name for this asset:")
                with open(self.path + "assets/" + s + "." + u.split(".")[-1], "wb") as f:
                    f.write(img)
                self.assets.append(s + "." + u.split(".")[-1])
            except:
                print("Asset not found or can't be saved")

    def cmd(self): # main command line menu
        while True:
            print()
            print("MAIN MENU")
            print("[0] Make Image")
            print("[1] Add Asset")
            print("[2] Settings")
            print("[Any] Quit")
            s = input()
            match s:
                case "0":
                    self.make()
                case "1":
                    self.add_asset()
                case "2":
                    self.edit_settings()
                case _:
                    break

    def search_asset(self, query): # search a file in the assets folder
        qs = query.lower().split(' ')
        res = []
        for a in self.assets:
            for q in qs:
                if q not in a.lower():
                    break
                if q is qs[-1]:
                    res.append(a)
        return res

    def make_canvas(self, size): # make a blank image to the specified size
        i = Image.new('RGB', size, "black")
        im_a = Image.new("L", i.size, "black")
        i.putalpha(im_a)
        im_a.close()
        return i

    def addTuple(self, A:tuple, B:tuple): # to add pairs together
        return (A[0]+B[0], A[1]+B[1])

    def mulTuple(self, A:tuple, f:float): # multiply a pair by a value
        return (int(A[0]*f), int(A[1]*f))

    def dlImage(self, url): # download an image (check the cache first)
        if url not in self.cache:
            self.checkDiskCache()
            try: # get from disk cache if enabled
                with open(self.path + "cache/" + base64.b64encode(url.encode('utf-8')).decode('utf-8'), "rb") as f:
                    self.cache[url] = f.read()
            except: # else request it from gbf
                req = request.Request(url)
                url_handle = request.urlopen(req)
                self.cache[url] = url_handle.read()
                try:
                    with open(self.path + "cache/" + base64.b64encode(url.encode('utf-8')).decode('utf-8'), "wb") as f:
                        f.write(self.cache[url])
                except Exception as e:
                    print(url, ":", e)
                    pass
                url_handle.close()
        return self.cache[url]

    def dlAndPasteImage(self, img, url, offset, resize=None, resizeType="default"): # call dlImage() and pasteImage()
        with BytesIO(self.dlImage(url)) as file_jpgdata:
            return self.pasteImage(img, file_jpgdata, offset, resize, resizeType)

    def pasteImage(self, img, file, offset, resize=None, resizeType="default"): # paste an image onto another
        buffers = [Image.open(file)]
        buffers.append(buffers[-1].convert('RGBA'))
        if resize is not None:
            match resizeType.lower():
                case "default":
                    buffers.append(buffers[-1].resize(resize, Image.Resampling.LANCZOS))
                case "fit":
                    size = buffers[-1].size
                    mod = min(resize[0]/size[0], resize[1]/size[1])
                    offset = self.addTuple(offset, (int(resize[0]-size[0]*mod)//2, int(resize[1]-size[1]*mod)//2))
                    buffers.append(buffers[-1].resize((int(size[0]*mod), int(size[1]*mod)), Image.Resampling.LANCZOS))
                case "fill":
                    size = buffers[-1].size
                    mod = max(resize[0]/size[0], resize[1]/size[1])
                    offset = self.addTuple(offset, (int(resize[0]-size[0]*mod)//2, int(resize[1]-size[1]*mod)//2))
                    buffers.append(buffers[-1].resize((int(size[0]*mod), int(size[1]*mod)), Image.Resampling.LANCZOS))
        size = buffers[-1].size
        if size[0] == img.size[0] and size[1] == img.size[1] and offset[0] == 0 and offset[1] == 0:
            modified = Image.alpha_composite(img, buffers[-1])
        else:
            layer = self.make_canvas((1280, 720))
            layer.paste(buffers[-1], offset, buffers[-1])
            modified = Image.alpha_composite(img, layer)
            layer.close()
        for buf in buffers: buf.close()
        del buffers
        return modified

    def fixCase(self, terms): # function to fix the case (for wiki search requests)
        terms = terms.split(' ')
        fixeds = []
        for term in terms:
            fixed = ""
            up = False
            special = {"and":"and", "of":"of", "de":"de", "for":"for", "the":"the", "(sr)":"(SR)", "(ssr)":"(SSR)", "(r)":"(R)"} # case where we don't don't fix anything and return it
            if term.lower() in special:
                fixeds.append(special[term.lower()])
                continue
            for i in range(0, len(term)): # for each character
                if term[i].isalpha(): # if letter
                    if term[i].isupper(): # is uppercase
                        if not up: # we haven't encountered an uppercase letter
                            up = True
                            fixed += term[i] # save
                        else: # we have
                            fixed += term[i].lower() # make it lowercase and save
                    elif term[i].islower(): # is lowercase
                        if not up: # we haven't encountered an uppercase letter
                            fixed += term[i].upper() # make it uppercase and save
                            up = True
                        else: # we have
                            fixed += term[i] # save
                    else: # other characters
                        fixed += term[i] # we just save
                elif term[i] == "/" or term[i] == ":" or term[i] == "#" or term[i] == "-": # we reset the uppercase detection if we encounter those
                    up = False
                    fixed += term[i]
                else: # everything else,
                    fixed += term[i] # we save
            fixeds.append(fixed)
        return "_".join(fixeds) # return the result

    def search_id_on_wiki(self, sps): # search on gbf.wiki to match a summon name to its id
        try:
            req = request.Request("https://gbf.wiki/" + quote(self.fixCase(sps)))
            url_handle = request.urlopen(req)
            data = url_handle.read().decode('utf-8')
            url_handle.close()
            for r in self.regex:
                group = r.findall(data)
                if len(group) > 0:
                    return group[0]
            return None
        except:
            return None

    def ask_color(self, s): # take a color sring and output a tuple
        s = s.replace(' ', '').replace('(', '').replace(')', '').split(',')
        if len(s) < 3 or len(s) > 4: return None
        for i, v in enumerate(s):
            try:
                s[i] = int(v)
                if s[i] < 0 or s[i] > 255: raise Exception()
            except:
                return None
        return tuple(s)

    def make_pixel_offset(self, coor): # take an array of two string value and output a pair
        for i, v in enumerate(coor):
            try:
                coor[i] = int(v)
            except:
                return None
        return tuple(coor)

    def make_img_from_text(self, img, text = "", fc = (255, 255, 255), oc = (0, 0, 0), os = 10, bold = False, italic = False, pos = "middle", offset = (0, 0), fs = 24, preview=False): # to draw text into an image
        text = text.replace('\\n', '\n')
        modified = img.copy()
        d = ImageDraw.Draw(modified, 'RGBA')
        font_file = "font"
        if bold: font_file += "b"
        if italic: font_file += "i"
        font = ImageFont.truetype(self.path + "assets/" + font_file + ".ttf", fs, encoding="unic")
        nl = text.split('\n')
        size = [0, 0]
        for l in nl:
            s = font.getsize(l, stroke_width=os)
            size[0] = max(size[0], s[0])
            size[1] += s[1]
        match pos.lower():
            case "topleft":
                text_pos = (0, 0)
            case "top":
                text_pos = (640-size[0]//2, 0)
            case "topright":
                text_pos = (1280-size[0], 0)
            case "right":
                text_pos = (1280-size[0], 360-size[1]//2)
            case "bottomright":
                text_pos = (1280-size[0], 720-size[1])
            case "bottom":
                text_pos = (640-size[0]//2, 720-size[1])
            case "bottomleft":
                text_pos = (0, 720-size[1])
            case "left":
                text_pos = (0, 360-size[1]//2)
            case "middle":
                text_pos = (640-size[0]//2, 360-size[1]//2)
        text_pos = self.addTuple(text_pos, offset)
        d.text(text_pos, text, fill=fc, font=font, stroke_width=os, stroke_fill=oc)
        if preview:
            modified.show()
            modified.close()
        else:
            img.close()
        return modified

    def make_add_text(self, img): # menu to add a text element
        text = ""
        fc = (255, 255, 255)
        oc = (255, 0, 0)
        os = 10
        bold = False
        italic = False
        pos = "middle"
        offset = (0, 0)
        fs = 120
        while True:
            print()
            print("TEXT DRAW MENU")
            print("[0] Input Text (Current:" + text + ")")
            print("[1] Select Fill Color (Current:" + str(fc) + ")")
            print("[2] Select Outline Color (Current:" + str(oc) + ")")
            print("[3] Set the Outline Size (Current:" + str(os) + ")")
            print("[4] Toggle Bold (Current:" + str(bold) + ")")
            print("[5] Toggle Italic (Current:" + str(italic) + ")")
            print("[6] Set Position (Current:" + str(pos) + ")")
            print("[7] Set Offset (Current:" + str(offset) + ")")
            print("[8] Set Font Size (Current:" + str(fs) + ")")
            print("[9] Preview")
            print("[10] Confirm")
            print("[11] Cancel")
            s = input()
            match s:
                case "0":
                    text = input("Please input the text to write:")
                case "1":
                    t = self.ask_color(input("Please input the fill color of the text (format: (R,G,B) or (R,G,B,A)):"))
                    if t is None:
                        print("Invalid color string")
                    else:
                        fc = t
                        print("Fill color set to", s)
                case "2":
                    t = self.ask_color(input("Please input the outline color of the text (format: (R,G,B) or (R,G,B,A)):"))
                    if t is None:
                        print("Invalid color string")
                    else:
                        oc = t
                        print("Outline color set to", s)
                case "3":
                    s = input("Please input the outline size:")
                    try:
                        s = int(s)
                        if s < 0: raise Exception()
                        os = s
                        print("Outline size set to", s)
                    except:
                        print("Not a positive number")
                case "4":
                    bold = not bold
                case "5":
                    italic = not italic
                case "6":
                    print("Possible positions:", self.possible_pos)
                    s = input("Please select where to anchor the text:").lower()
                    if s not in self.possible_pos:
                        print("Invalid choice")
                    else:
                        pos = s
                        print("Position anchor set to", s)
                case "7":
                    x = input("Please input the horizontal offset X in pixel:")
                    y = input("Please input the vertical offset Y in pixel:")
                    t = self.make_pixel_offset([x, y])
                    if t is None:
                        print("Invalid offset")
                    else:
                        offset = t
                        print("Position offset set to", t)
                case "8":
                    s = input("Please input the font size:")
                    try:
                        s = int(s)
                        if s < 0: raise Exception()
                        fs = s
                        print("Font Size set to", s)
                    except:
                        print("Not a positive number")
                case "9":
                    self.make_img_from_text(img, text, fc, oc, os, bold, italic, pos, offset, fs, True)
                case "10":
                    return self.make_img_from_text(img, text, fc, oc, os, bold, italic, pos, offset, fs, False)
                case "11":
                    return img

    def get_mc_job_look(self, skin, job): # get the MC unskined filename based on id
        jid = job // 10000
        if jid not in self.classes: return skin
        return "{}_{}_{}".format(job, self.classes[jid], '_'.join(skin.split('_')[2:]))

    def check_id(self, id, recur=True): # check an element id and return it if valid (None if error)
        if id is None or not isinstance(id, str): return None
        try:
            if len(id.replace('skin/', '').split('_')[0]) != 10: raise Exception("MC?")
            int(id.replace('skin/', '').split('_')[0])
            t = int(id.replace('skin/', '')[0])
        except Exception as e:
            if str(e) == "MC?":
                t = 0
                if len(id.split("_")) != 4:
                    try:
                        id = self.get_mc_job_look(None, id)
                    except:
                        if recur: return self.check_id(self.search_id_on_wiki(id), recur=False) # wiki check
                        else: return None
            else:
                if recur: return self.check_id(self.search_id_on_wiki(id), recur=False) # wiki check
                else: return None
        if id is None:
            return None
        if t > 1 and '_' not in id:
            id += '_' + input("Input uncap/modifier string:")
        return id

    def get_uncap_id(self, cs): # to get character portraits based on uncap levels
        return {2:'02', 3:'02', 4:'02', 5:'03', 6:'04'}.get(cs, '01')

    def import_gbfpib(self): # import data from GBFPIB
        options = []
        try:
            input("Use the GBFPIB bookmark to copy a party data and press Return to continue")
            export = json.loads(pyperclip.paste())
            babyl = (len(export['c']) > 5)
            sandbox = (len(export['w']) > 10 and not isinstance(export['est'][0], str))
            options.append(["MC", self.get_mc_job_look(export['pcjs'], export['p']), export['pcjs'], 0])
            if babyl: nchara = 12
            else: nchara = 5
            for i in range(0, nchara):
                if babyl and i == 0: continue
                if i >= len(export['c']) or export['c'][i] is None: continue
                if export['c'][i] in self.nullchar: 
                    cid = "{}_{}_0{}".format(export['c'][i], self.get_uncap_id(export['cs'][i]), export['ce'][i])
                else:
                    cid = "{}_{}".format(export['c'][i], self.get_uncap_id(export['cs'][i]))
                options.append([export['cn'][i], cid, export['ci'][i], 0])
            for i in range(0, 7):
                if export['s'][i] is None: continue
                options.append(["SUM #" + str(i+1), export['ss'][i], None, 0])
            for i in range(0, len(export['w'])):
                if export['w'][i] is None or export['wl'][i] is None: continue
                options.append(["WPN #" + str(i+1), str(export['w'][i]) + "00", None, 0])

            while True:
                print()
                print("Select What to import")
                for i, v in enumerate(options):
                    print("[{}][{}] {}".format(i, " " if v[-1] == 0 else ("X" if v[-1] == 1 else "S"), v[0]))
                print("[C] to Confirm")
                s = input()
                match s.lower():
                    case "c":
                        break
                    case _:
                        try:
                            s = int(s)
                            options[int(s)][3] = (options[int(s)][3] + 1) % 3
                            if options[int(s)][3] == 2 and options[int(s)][2] is None:
                                options[int(s)][3] = 0
                        except:
                            pass
            res = []
            for o in options:
                if o[3] == 2: res.append(o[2])
                elif o[3] == 1: res.append(o[1])
            print("Selected elements imported")
            return res
        except Exception as e:
            print("An error occured:", e)
            print("Failed to import party data")
            return []

    def get_element_size(self, c, display): # retrive an element asset and return its size
        try:
            if c == "1999999999":
                t = 5
            elif c == "3999999999":
                t = 6
            else:
                try:
                    if len(c.replace('skin/', '').split('_')[0]) < 10: raise Exception("MC?")
                    int(c.replace('skin/', '').split('_')[0])
                    t = int(c.replace('skin/', '')[0])
                except Exception as e:
                    if str(e) == "MC?":
                        t = 0
                        if len(c.split("_")) != 4:
                            try:
                                c = self.get_mc_job_look(None, c)
                            except:
                                if c in self.assets:
                                    t = 4
                                else:
                                    return None, None
                    else:
                        if c in self.assets:
                            t = 4
                        else:
                            return None, None
            try: u = self.asset_urls[t][self.possible_display.index(display.lower())].format(c)
            except: u = self.asset_urls[t][self.possible_display.index(display.lower())]
            if t == 4: u = self.path + u
            if u.startswith("http"):
                with BytesIO(self.dlImage(u)) as file_jpgdata:
                    buf = Image.open(file_jpgdata)
                    size = buf.size
                    buf.close()
            else:
                buf = Image.open(u)
                size = buf.size
                buf.close()
            return size, u
        except:
            return None, None

    def calc_ratio(self, c, display): # calculate the ratio needed to fit an element into an image
        try:
            size, u = self.get_element_size(c, display)
            return min(1280/size[0], 720/size[1])
        except:
            print("An error occured")
            return None

    def make_img_from_element(self, img, characters = [], pos = "middle", offset = (0, 0), ratio = 1.0, display = "squareicon", preview=False, fixedsize=None): # draw elements onto an image
        modified = img.copy()
        d = ImageDraw.Draw(modified, 'RGBA')
        match pos.lower():
            case "topleft":
                cur_pos = (0, 0)
            case "top":
                cur_pos = (640, 0)
            case "topright":
                cur_pos = (1280-200, 0)
            case "right":
                cur_pos = (1280-200, 360)
            case "bottomright":
                cur_pos = (1280-200, 720-200)
            case "bottom":
                cur_pos = (640, 720-200)
            case "bottomleft":
                cur_pos = (0, 720-200)
            case "left":
                cur_pos = (0, 360)
            case "middle":
                cur_pos = (640, 360)
        cur_pos = self.addTuple(cur_pos, offset)
        for c in characters:
            size, u = self.get_element_size(c, display)
            if size is None: continue
            if fixedsize is not None:
                size = fixedsize
            size = self.mulTuple(size, ratio)
            if u.startswith("http"):
                modified = self.dlAndPasteImage(modified, u, cur_pos, resize=size)
            else:
                modified = self.pasteImage(modified, u, cur_pos, resize=size)
            cur_pos = self.addTuple(cur_pos, (size[0], 0))
        if preview:
            modified.show()
            modified.close()
        else:
            img.close()
        return modified

    def make_add_element(self, img): # menu to add elements
        characters = []
        pos = "middle"
        offset = (0, 0)
        ratio = 1.0
        display = "squareicon"
        while True:
            print()
            print("ELEMENT DRAW MENU")
            print("Current Element(s):", characters)
            print("[0] Add Element")
            print("[1] Remove Element")
            print("[2] Import Party")
            print("[3] Set Display type (Current:" + display + ")")
            print("[4] Set Display Ratio (Current:" + str(ratio) + ")")
            print("[5] Set Display Ratio to fit first Element")
            print("[6] Set Position (Current:" + str(pos) + ")")
            print("[7] Set Offset (Current:" + str(offset) + ")")
            print("[8] Preview")
            print("[9] Confirm")
            print("[10] Cancel")
            s = input()
            match s:
                case "0":
                    s = input("Please input the ID of the element to add:")
                    x = self.check_id(s)
                    if x is None:
                        res = self.search_asset(s)
                        if len(res) == 0:
                            print("Invalid ID")
                        elif len(res) == 1:
                            characters.append(res[0])
                            print(res[0], "added")
                        else:
                            while True:
                                print()
                                print("Select the image you want:")
                                for i, r in enumerate(res):
                                    print("[{}] {}".format(i, r))
                                try: 
                                    s = int(input())
                                    if s < 0: raise Exception()
                                    characters.append(res[s])
                                    print(res[s], "added")
                                    break
                                except:
                                    print("Invalid selection")
                    else:
                        characters.append(x)
                        print(s, "added")
                case "1":
                    print("Current Element(s):", characters)
                    s = input("Please input the name of the element to remove:")
                    if s not in characters:
                        print("Invalid name")
                    else:
                        i = 0
                        while i < len(characters):
                            if characters[i] == s:
                                characters.pop(i)
                            else:
                                i += 1
                        print(s, "removed")
                case "2":
                    characters += self.import_gbfpib()
                case "3":
                    print("Possible Display types:", self.possible_display)
                    s = input("Please select how to display the element:").lower()
                    if s not in self.possible_display:
                        print("Invalid choice")
                    else:
                        display = s
                        print("Display type set to", s)
                case "4":
                    s = input("Input the multiplier for the element size:")
                    try:
                        s = float(s)
                        if s <= 0: raise Exception()
                        ratio = s
                        print("Display ratio set to", ratio)
                    except:
                        print("Not a float value")
                case "5":
                    if len(characters) == 0:
                        print("An element must be set to use this function")
                    else:
                        s = self.calc_ratio(characters[0], display)
                        if s is not None:
                            ratio = s
                            print("Display ratio set to", ratio)
                case "6":
                    print("Possible positions:", self.possible_pos)
                    s = input("Please select where to anchor the text:").lower()
                    if s not in self.possible_pos:
                        print("Invalid choice")
                    else:
                        pos = s
                        print("Position anchor set to", s)
                case "7":
                    x = input("Please input the horizontal offset X in pixel:")
                    y = input("Please input the vertical offset Y in pixel:")
                    t = self.make_pixel_offset([x, y])
                    if t is None:
                        print("Invalid offset")
                    else:
                        offset = t
                        print("Position offset set to", t)
                case "8":
                    self.make_img_from_element(img, characters, pos, offset, ratio, display, True)
                case "9":
                    return self.make_img_from_element(img, characters, pos, offset, ratio, display, False)
                case "10":
                    return img

    def make_background(self, img, query, rtype=None): # menu to add a background
        res = self.search_asset(query)
        if len(res) == 0:
            print("No results found")
            if self.client is not None or self.test_twitter(silent=True):
                print("Searching on Twitter...")
                b = self.retrieve_raid_image(query)
                if b is None:
                    print("No images found")
                    raise Exception("No valid background found")
            else:
                raise Exception("No valid background found")
        elif len(res) == 1 or self.path != "":
            b = res[0]
        else:
            while True:
                print()
                print("Select the image you want:")
                for i, r in enumerate(res):
                    print("[{}] {}".format(i, r))
                try: 
                    s = int(input())
                    if s < 0: raise Exception()
                    b = res[s]
                    break
                except:
                    print("Invalid selection")
        if rtype is None:
            while True:
                print()
                print("Select a resizing type:")
                print("[0] Fit")
                print("[1] Fill")
                s = input()
                if s == "0":
                    rtype = "fit"
                    break
                elif s == "1":
                    rtype = "fill"
                    break
                else:
                    print("Invalid choice")
        return self.pasteImage(img, self.path + "assets/" + b, (0, 0), (1280, 720), rtype)

    def make(self, img=None): # main sub menu
        try:
            if img is None:
                init = False
                img = self.make_canvas((1280, 720))
                print()
                s = input("Search a background (Leave blank to skip):")
                if s != "":
                    img = self.make_background(img, s)
            else:
                init = True
            while True:
                print()
                print("Please select the next step:")
                print("[0] Add Text")
                print("[1] Add Element")
                print("[2] Preview")
                print("[3] Confirm")
                s = input()
                match s:
                    case '0':
                        img = self.make_add_text(img)
                    case '1':
                        img = self.make_add_element(img)
                    case '2':
                        img.show()
                    case '3':
                        break
            if not init:
                img.save("thumbnail.png", "PNG")
                print("Image saved to thumbnail.png")
            else:
                return img
        except Exception as e:
            print("An error occured:", e)

    def auto_text(self, img, args, i): # auto text parsing
        text = ""
        fc = (255, 255, 255)
        oc = (255, 0, 0)
        os = 10
        bold = False
        italic = False
        pos = "middle"
        offset = (0, 0)
        fs = 120
        while i < len(args):
            match args[i]:
                case '-input':
                    text = input("Please input the text to write:")
                case '-content':
                    text = args[i+1]
                    i += 1
                case '-color':
                    fc = self.ask_color(args[i+1])
                    i += 1
                case '-outcolor':
                    oc = self.ask_color(args[i+1])
                    i += 1
                case '-outsize':
                    os = int(args[i+1])
                    i += 1
                case '-bold':
                    bold = True
                case '-italic':
                    italic = True
                case '-position':
                    if args[i+1].lower() not in self.possible_pos: raise Exception("Invalid position parameter")
                    pos = args[i+1].lower()
                    i += 1
                case '-offset':
                    p = args[i+1].split(',')
                    offset = self.make_pixel_offset(p)
                    i += 1
                case '-fontsize':
                    fs = int(args[i+1])
                    i += 1
                case _:
                    i -= 1
                    break
            i += 1
        img = self.make_img_from_text(img, text, fc, oc, os, bold, italic, pos, offset, fs, False)
        return i, img

    def auto_element(self, img, args, i): # auto element parsing
        characters = []
        pos = "middle"
        offset = (0, 0)
        ratio = 1.0
        display = "squareicon"
        while i < len(args):
            match args[i]:
                case '-input':
                    s = self.check_id(input("Please input the id of the element to add:"))
                    if s is None:
                        if args[i+1] in self.assets:
                            characters.append(args[i+1])
                        else:
                            raise Exception("Invalid ID or asset")
                    else:
                        characters.append(s)
                case '-import':
                    characters += self.import_gbfpib()
                case '-add':
                    s = self.check_id(args[i+1])
                    if s is None:
                        if args[i+1] in self.assets:
                            characters.append(args[i+1])
                        else:
                            raise Exception("Invalid ID or asset")
                    else:
                        characters.append(s)
                    i += 1
                case '-ratio':
                    ratio = float(args[i+1].replace(',', '.'))
                    i += 1
                case '-ratiofit':
                    if len(characters) == 0: raise Exception("No elements set")
                    s = self.calc_ratio(characters[0], display)
                    if s is None: raise Exception("Couldn't calculate ratio")
                    ratio = s
                case '-position':
                    if args[i+1].lower() not in self.possible_pos: raise Exception("Invalid position parameter")
                    pos = args[i+1].lower()
                    i += 1
                case '-display':
                    if args[i+1].lower() not in self.possible_display: raise Exception("Invalid display parameter")
                    display = args[i+1].lower()
                    i += 1
                case '-offset':
                    p = args[i+1].split(',')
                    offset = self.make_pixel_offset(p)
                    i += 1
                case _:
                    i -= 1
                    break
            i += 1
        img = self.make_img_from_element(img, characters, pos, offset, ratio, display, False)
        return i, img

    def auto_party(self, img, args, i, noskin=False, auto_import=None, mainsummon=False): # auto party drawing
        characters = []
        try:
            if auto_import is not None:
                export = auto_import
            else:
                input("Use the GBFPIB bookmark to copy a party data and press Return to continue")
                export = json.loads(pyperclip.paste())
            babyl = (len(export['c']) > 5)
            if not mainsummon:
                if noskin:
                    characters.append(self.get_mc_job_look(export['pcjs'], export['p']))
                else:
                    characters.append(export['pcjs'])
            if babyl: nchara = 12
            else: nchara = 5
            for x in range(0, nchara):
                if mainsummon:break
                if babyl and x == 0:
                    continue
                if x >= len(export['c']) or export['c'][x] is None:
                    characters.append("3999999999")
                    continue
                if noskin:
                    if export['c'][x] in self.nullchar: 
                        cid = "{}_{}_0{}".format(export['c'][x], self.get_uncap_id(export['cs'][x]), export['ce'][x])
                    else:
                        cid = "{}_{}".format(export['c'][x], self.get_uncap_id(export['cs'][x]))
                    characters.append(cid)
                else:
                    characters.append(export['ci'][x])
            if export['s'][0] is not None:
                characters.append(export['ss'][0])
            if not mainsummon:
                if export['w'][0] is not None and export['wl'][0] is not None:
                    characters.append(str(export['w'][0]) + "00")
                else:
                    characters.append("1999999999")
        except Exception as e:
            print("An error occured while importing a party:", e)
            raise Exception("Failed to import party data")

        pos = "topleft"
        offset = (0, 0)
        ratio = 1.0
        while i < len(args):
            match args[i]:
                case '-ratio':
                    ratio = float(args[i+1].replace(',', '.'))
                    i += 1
                case '-position':
                    if args[i+1].lower() not in self.possible_pos: raise Exception("Invalid position parameter")
                    pos = args[i+1].lower()
                    i += 1
                case '-offset':
                    p = args[i+1].split(',')
                    offset = self.make_pixel_offset(p)
                    i += 1
                case _:
                    i -= 1
                    break
            i += 1
        if mainsummon:
            img = self.make_img_from_element(img, characters, pos, offset, ratio, "partyicon", False)
        elif babyl:
            img = self.make_img_from_element(img, characters[:4], pos, offset, ratio, "squareicon", False, (100, 100))
            img = self.make_img_from_element(img, characters[4:8], pos, self.addTuple(offset, self.mulTuple((0, 100), ratio)), ratio, "squareicon", False, (100, 100))
            img = self.make_img_from_element(img, characters[8:12], pos, self.addTuple(offset, self.mulTuple((0, 200), ratio)), ratio, "squareicon", False, (100, 100))
            img = self.make_img_from_element(img, characters[12:13], pos, self.addTuple(offset, self.mulTuple((0, 310), ratio)), ratio, "partyicon", False, (192, 108))
            img = self.make_img_from_element(img, characters[13:14], pos, self.addTuple(offset, self.mulTuple((208, 310), ratio)), ratio, "partyicon", False, (192, 108))
        else:
            img = self.make_img_from_element(img, characters[:4], pos, offset, ratio, "partyicon", False, (78, 142))
            img = self.make_img_from_element(img, characters[4:6], pos, self.addTuple(offset, self.mulTuple((78*4+15, 0), ratio)), ratio, "partyicon", False, (78, 142))
            img = self.make_img_from_element(img, characters[6:7], pos, self.addTuple(offset, self.mulTuple((15, 142+10), ratio)), 0.75*ratio, "partyicon", False, (280, 160))
            img = self.make_img_from_element(img, characters[7:8], pos, self.addTuple(offset, self.mulTuple((15+280*0.75+15, 142+10), ratio)), 0.75*ratio, "partyicon", False, (280, 160))
        
        return i, img

    def auto(self, args, nowait=False, auto_import=None): # main auto parsing
        try:
            i = 0
            img = self.make_canvas((1280, 720))
            while i < len(args):
                match args[i]:
                    case '-bg':
                        rtype = '-fit'
                        thumb = args[i+1]
                        if thumb == "-input":
                            thumb = input("Search a background (Leave blank to skip):")
                            if thumb == "":
                                i += 2
                                continue
                        try:
                            if args[i+2] in ['-fit', '-fill']:
                                rtype = args[i+2]
                                i += 2
                            else:
                                i += 1
                        except:
                            i += 1
                        img = self.make_background(img, thumb, rtype[1:])
                    case '-text':
                        i, img = self.auto_text(img, args, i+1)
                    case '-element':
                        i, img = self.auto_element(img, args, i+1)
                    case '-party':
                        i, img = self.auto_party(img, args, i+1, auto_import=auto_import)
                    case '-party_mainsummon':
                        i, img = self.auto_party(img, args, i+1, noskin=True, auto_import=auto_import, mainsummon=True)
                    case '-party_noskin':
                        i, img = self.auto_party(img, args, i+1, noskin=True, auto_import=auto_import)
                    case '-manual':
                        img = self.make(img)
                    case '-fadein':
                        img = self.pasteImage(img, self.path + "assets/fade_in.png", (0,40), resize=(1280,640), resizeType="default")
                    case '-nm150':
                        img = self.pasteImage(img, self.path + "assets/nm150_filter.png", (0,40), resize=(1280,640), resizeType="default")
                        gwid = input("Input the GW Number:")
                        img = self.dlAndPasteImage(img, "https://game-a1.granbluefantasy.jp/assets_en/img/sp/event/teamraid{}/assets/thumb/teamraid{}_hell150.png".format(gwid.zfill(3), gwid.zfill(3)), (5,410), resize=(304,256), resizeType="default")
                    case '-nm200':
                        img = self.pasteImage(img, self.path + "assets/nm200_filter.png", (0,40), resize=(1280,640), resizeType="default")
                        gwid = input("Input the GW Number:")
                        img = self.dlAndPasteImage(img, "https://game-a1.granbluefantasy.jp/assets_en/img/sp/event/teamraid{}/assets/thumb/teamraid{}_hell200.png".format(gwid.zfill(3), gwid.zfill(3)), (5,410), resize=(304,256), resizeType="default")
                    case _:
                        print("Warning: Ignoring unknown parameter:", args[i])
                i += 1
            img.save("thumbnail.png", "PNG")
            print("Image saved to thumbnail.png")
        except Exception as e:
            print("Error while parsing argument", i, ":", args[i])
            print("Exception:", e)
        if not nowait:
            print("Closing in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    t = GBFTM()
    if  len(sys.argv) > 2 and sys.argv[1] == '-auto':
        t.auto(sys.argv[2:])
    else:
        t.cmd()