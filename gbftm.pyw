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

class GBFTM():
    def __init__(self):
        print("GBF Thumbnail Maker v1.0")
        self.assets = []
        self.settings = {}
        self.client = None
        self.list_assets()
        self.test_twitter(silent=True)
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
            re.compile('(20[0-9]{8}_02)\\.'),
            re.compile('([0-9]{10})\\.')
        ]

    def list_assets(self):
        try: self.assets = [f for f in os.listdir("assets") if (os.path.isfile(os.path.join("assets", f)) and (f.endswith('.png') or f.endswith('.jpg')))]
        except: self.assets = []
        print(len(self.assets), "asset(s) found")

    def test_twitter(self, silent=False):
        try:
            self.client = tweepy.Client(bearer_token = self.settings.get('twitter', ''))
            if not silent: print("Twitter connected")
            return True
        except:
            self.client = None
            if not silent: print("Failed to access Twitter, check your Bearer Token")
            return False

    def load(self): # load settings.json
        try:
            with open('settings.json') as f:
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
            with open('settings.json', 'w') as outfile:
                json.dump(self.settings, outfile)
        except:
            pass

    def request(self, url):
        try:
            req = request.Request(url)
            url_handle = request.urlopen(req)
            data = url_handle.read()
            url_handle.close()
            return data
        except:
            return None

    def checkDiskCache(self): # check if cache folder exists (and create it if needed)
        if not os.path.isdir('cache'):
            os.mkdir('cache')

    def checkAssetFolder(self): # check if assets folder exists (and create it if needed)
        if not os.path.isdir('assets'):
            os.mkdir('assets')

    def retrieve_raid_image(self, search):
        try:
            if self.client is None:
                print("Twitter Bearer token not set")
                return none
            tweets = self.client.search_recent_tweets(query=search, tweet_fields=['source'], user_fields=['profile_image_url'], media_fields=['preview_image_url', 'url'], expansions=['author_id', 'attachments.media_keys', 'entities.mentions.username', 'referenced_tweets.id', 'referenced_tweets.id.author_id'], max_results=10)
            try: media = {m["media_key"]: m for m in tweets.includes['media']}
            except: media = {}
            for t in tweets.data:
                if t['data']['source'] == "グランブルー ファンタジー":
                    raid_key = t.text.split("I need backup!\n")[1].split('\n')[0].lower()
                    img = self.request(media[t['attachments']['media_keys'][0]].url)
                    self.checkAssetFolder()
                    with open("assets/" + raid_key + ".jpg", "wb") as f:
                        f.write(img)
                    self.assets.append(raid_key + ".jpg")
                    print("Image saved as", raid_key + ".jpg")
                    return raid_key + ".jpg"
            print("No images found")
        except:
            print("An error occured")
        return None

    def edit_settings(self):
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

    def cmd(self):
        while True:
            print()
            print("MAIN MENU")
            print("[0] Make Image")
            print("[1] Settings")
            print("[Any] Quit")
            s = input()
            match s:
                case "0":
                    self.make()
                case "1":
                    self.edit_settings()
                case _:
                    break

    def search_asset(self, query):
        qs = query.split(' ')
        res = []
        for a in self.assets:
            for q in qs:
                if q not in a:
                    break
                if q is qs[-1]:
                    res.append(a)
        return res

    def make_canvas(self, size):
        i = Image.new('RGB', size, "black")
        im_a = Image.new("L", i.size, "black")
        i.putalpha(im_a)
        im_a.close()
        return i

    def addTuple(self, A:tuple, B:tuple):
        return (A[0]+B[0], A[1]+B[1])

    def subTuple(self, A:tuple, B:tuple):
        return (A[0]-B[0], A[1]-B[1])

    def dlImage(self, url):
        if url not in self.cache:
            self.checkDiskCache()
            try: # get from disk cache if enabled
                with open("cache/" + base64.b64encode(url.encode('utf-8')).decode('utf-8'), "rb") as f:
                    self.cache[url] = f.read()
            except: # else request it from gbf
                req = request.Request(url)
                url_handle = request.urlopen(req)
                self.cache[url] = url_handle.read()
                try:
                    with open("cache/" + base64.b64encode(url.encode('utf-8')).decode('utf-8'), "wb") as f:
                        f.write(self.cache[url])
                except Exception as e:
                    print(e)
                    pass
                url_handle.close()
        return self.cache[url]

    def dlAndPasteImage(self, img, url, offset, resize=None, resizeType="default"): # dl an image and call pasteImage()
        with BytesIO(self.dlImage(url)) as file_jpgdata:
            self.pasteImage(img, file_jpgdata, offset, resize, resizeType)

    def pasteImage(self, img, file, offset, resize=None, resizeType="default"): # paste an image onto another
        buffers = [Image.open(file)]
        buffers.append(buffers[-1].convert('RGBA'))
        if resize is not None:
            match resizeType.lower():
                case "default":
                    buffers.append(buffers[-1].resize(resize, Image.LANCZOS))
                case "fit":
                    size = buffers[-1].size
                    mod = min(resize[0]/size[0], resize[1]/size[1])
                    offset = self.addTuple(offset, (int(resize[0]-size[0]*mod)//2, int(resize[1]-size[1]*mod)//2))
                    buffers.append(buffers[-1].resize((int(size[0]*mod), int(size[1]*mod)), Image.LANCZOS))
                case "fill":
                    size = buffers[-1].size
                    mod = max(resize[0]/size[0], resize[1]/size[1])
                    offset = self.addTuple(offset, (int(resize[0]-size[0]*mod)//2, int(resize[1]-size[1]*mod)//2))
                    buffers.append(buffers[-1].resize((int(size[0]*mod), int(size[1]*mod)), Image.LANCZOS))
        img.paste(buffers[-1], offset, buffers[-1])
        for buf in buffers: buf.close()
        del buffers

    def fixCase(self, terms): # function to fix the case (for wiki search requests)
        terms = terms.split(' ')
        fixeds = []
        for term in terms:
            fixed = ""
            up = False
            special = {"and":"and", "of":"of", "de":"de", "for":"for", "the":"the", "(sr)":"(SR)", "(ssr)":"(SSR)", "(r)":"(R)"} # case where we don't don't fix anything and return it
            if term.lower() in special:
                return special[term.lower()]
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
            group = self.regex[0].findall(data)
            if len(group) > 0:
                return group[0]
            group = self.regex[1].findall(data)
            return group[0]
        except:
            return None

    def ask_color(self, s):
        s = s.replace(' ', '').replace('(', '').replace(')', '').split(',')
        if len(s) < 3 or len(s) > 4: return None
        for i, v in enumerate(s):
            try:
                s[i] = int(v)
                if s[i] < 0 or s[i] > 255: raise Exception()
            except:
                return None
        return tuple(s)

    def make_pixel_offset(self, coor):
        for i, v in enumerate(coor):
            try:
                coor[i] = int(v)
            except:
                return None
        return tuple(coor)

    def make_img_from_text(self, img, text = "", fc = (255, 255, 255), oc = (0, 0, 0), os = 2, bold = False, italic = False, pos = "middle", offset = (0, 0), fs = 24, preview=False):
        modified = img.copy()
        d = ImageDraw.Draw(modified, 'RGBA')
        font_file = "font"
        if bold: font_file += "b"
        if italic: font_file += "i"
        font = ImageFont.truetype("assets/" + font_file + ".ttf", fs, encoding="unic")
        size = font.getsize(text, stroke_width=2)
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

    def make_add_text(self, img):
        text = ""
        fc = (255, 255, 255)
        oc = (255, 0, 0)
        os = 10
        bold = False
        italic = False
        pos = "middle"
        offset = (0, 0)
        fs = 120
        possible_pos = ["topleft", "left", "bottomleft", "bottom", "bottomright", "right", "topright", "top", "middle"]
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
                    print("Possible positions:", possible_pos)
                    s = input("Please select where to anchor the text:").lower()
                    if s not in possible_pos:
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

    def get_mc_job_look(self, skin, job): # get the MC unskined filename based on id
        jid = job // 10000
        if jid not in self.classes: return skin
        return "{}_{}_{}".format(job, self.classes[jid], '_'.join(skin.split('_')[2:]))

    def check_id(self, id, recur=True):
        try:
            if len(id) != 10: raise Exception("MC?")
            int(id)
            t = int(id[0])
        except Exception as e:
            if str(e) == "MC?":
                t = 0
                if len(id.split("_")) != 4:
                    try:
                        id = self.get_mc_job_look(None, id)
                    except:
                        if recur: return self.check_id(self.search_id_on_wiki(id), recur=False)
                        else: return None
            else:
                if recur: return self.check_id(self.search_id_on_wiki(id), recur=False)
                else: return None
        if id is None:
            return None
        if t > 1:
            id.append('_' + input("Input uncap/modifier string:"))
        return id

    def get_uncap_id(self, cs): # to get character portraits based on uncap levels
        return {2:'02', 3:'02', 4:'02', 5:'03', 6:'04'}.get(cs, '01')

    def import_gbfpib(self):
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


    def make_img_from_element(self, img, characters = [], pos = "middle", offset = (0, 0), ratio = 1.0, display = "squareicon", preview=False):
        modified = img.copy()
        d = ImageDraw.Draw(modified, 'RGBA')
        urls = [
            [
                "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/s/{}.jpg",
                "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/f/{}.jpg",
                "ttp://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/leader/my/{}.png"
            ],
            [
                "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/s/{}.jpg",
                "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/m/{}.jpg",
                "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/weapon/b/{}.png"
            ],
            [
                "http://game-a.granbluefantasy.jp/assets_en/img/sp/assets/summon/s/{}.jpg",
                "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/m/{}.jpg",
                "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/summon/my/{}.png"
            ],
            [
                "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/npc/s/{}.jpg",
                "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/npc/f/{}.jpg",
                "http://game-a1.granbluefantasy.jp/assets_en/img/sp/assets/npc/my/{}.png"
            ]
        ]
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
            try:
                if len(c.split('_')[0]) < 10: raise Exception("MC?")
                t = int(c[0])
            except:
                if str(e) == "MC?":
                    t = 0
                    if len(c.split("_")) != 4:
                        try:
                            c = self.get_mc_job_look(None, c)
                        except:
                            continue
                else:
                    continue
            match display.lower():
                case "squareicon":
                    u = urls[t][0].format(c)
                case "partyicon":
                    u = urls[t][1].format(c)
                case "fullart":
                    u = urls[t][2].format(c)
            data = self.dlImage(u)
            with BytesIO(self.dlImage(u)) as file_jpgdata:
                buf = Image.open(file_jpgdata)
                size = buf.size
                buf.close()
            size = (int(size[0] * ratio), int(size[1] * ratio))
            self.dlAndPasteImage(modified, u, cur_pos, resize=size)
            cur_pos = self.addTuple(cur_pos, (size[0], 0))
        if preview:
            modified.show()
            modified.close()
        else:
            img.close()
        return modified

    def make_add_element(self, img):
        characters = []
        pos = "middle"
        offset = (0, 0)
        ratio = 1.0
        display = "squareicon"
        possible_pos = ["topleft", "left", "bottomleft", "bottom", "bottomright", "right", "topright", "top", "middle"]
        possible_display = ["squareicon", "partyicon", "fullart"]
        while True:
            print()
            print("ELEMENT DRAW MENU")
            print("Current Element(s):", characters)
            print("[0] Add Element")
            print("[1] Remove Element")
            print("[2] Import Party")
            print("[3] Set Display type (Current:" + display + ")")
            print("[4] Set Display Ratio (Current:" + str(ratio) + ")")
            print("[5] Set Position (Current:" + str(pos) + ")")
            print("[6] Set Offset (Current:" + str(offset) + ")")
            print("[7] Preview")
            print("[8] Confirm")
            s = input()
            match s:
                case "0":
                    s = self.check_id(input("Please input the ID of the element to add:"))
                    if s is None:
                        print("Invalid ID")
                    else:
                        characters.append(s)
                        print(s, "added")
                case "1":
                    print("Current Element(s):", characters)
                    s = input("Please input the ID of the element to remove:")
                    if s not in characters:
                        print("Invalid ID")
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
                    print("Possible Display types:", possible_display)
                    s = input("Please select how to display the element:").lower()
                    if s not in possible_display:
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
                    print("Possible positions:", possible_pos)
                    s = input("Please select where to anchor the text:").lower()
                    if s not in possible_pos:
                        print("Invalid choice")
                    else:
                        pos = s
                        print("Position anchor set to", s)
                case "6":
                    x = input("Please input the horizontal offset X in pixel:")
                    y = input("Please input the vertical offset Y in pixel:")
                    t = self.make_pixel_offset([x, y])
                    if t is None:
                        print("Invalid offset")
                    else:
                        offset = t
                        print("Position offset set to", t)
                case "7":
                    self.make_img_from_element(img, characters, pos, offset, ratio, display, True)
                case "8":
                    return self.make_img_from_element(img, characters, pos, offset, ratio, display, False)

    def make(self):
        try:
            img = self.make_canvas((1280, 720))
            print()
            s = input("Search a background (Leave blank to skip):")
            if s != "":
                res = self.search_asset(s)
                if len(res) == 0:
                    print("No results found")
                    if self.client is not None:
                        print("Searching on Twitter...")
                        b = self.retrieve_raid_image(s)
                        if b is None:
                            print("No images found")
                            raise Exception("No valid background found")
                    else:
                        raise Exception("No valid background found")
                elif len(res) == 1:
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
                while True:
                    print()
                    print("Select a resizing type:")
                    print("[0] Fit")
                    print("[1] Fill")
                    s = input()
                    if s == "0":
                        x = "fit"
                        break
                    elif s == "1":
                        x = "fill"
                        break
                    else:
                        print("Invalid choice")
                self.pasteImage(img, "assets/" + b, (0, 0), (1280, 720), x)
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
            img.save("thumbnail.png", "PNG")
            print("Image saved to thumbnail.png")
        except Exception as e:
            print("An error occured:", e)

if __name__ == "__main__":
    t = GBFTM()
    t.cmd()