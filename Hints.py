import io
import hashlib
import logging
import os
import struct
import random

from HintList import getHint, getHintGroup, Hint
from ItemList import eventlocations
from Messages import update_message_by_id
from TextBox import lineWrap
from Utils import random_choices
from BaseClasses import CollectionState

class GossipStone():
    def __init__(self, name, location):
        self.name = name
        self.location = location

gossipLocations = {
    0x0405: GossipStone('Death Mountain Crater (Bombable Wall)', 'Death Mountain Crater Gossip Stone'),
    0x0404: GossipStone('Death Mountain Trail (Biggoron)', 'Death Mountain Trail Gossip Stone'),
    0x041A: GossipStone('Desert Colossus (Spirit Temple)', 'Desert Colossus Gossip Stone'),
    0x0414: GossipStone('Dodongos Cavern (Bombable Wall)', 'Dodongos Cavern Gossip Stone'),
    0x0418: GossipStone('Generic Grotto', 'Generic Grotto Gossip Stone'),
    0x0411: GossipStone('Gerudo Valley (Waterfall)', 'Gerudo Valley Gossip Stone'),
    0x0415: GossipStone('Goron City (Maze)', 'Goron City Maze Gossip Stone'),
    0x0419: GossipStone('Goron City (Medigoron)', 'Goron City Medigoron Gossip Stone'),
    0x040A: GossipStone('Graveyard (Shadow Temple)', 'Graveyard Gossip Stone'),
    0x0412: GossipStone('Hyrule Castle (Malon)', 'Hyrule Castle Malon Gossip Stone'),
    0x040B: GossipStone('Hyrule Castle (Rock Wall)', 'Hyrule Castle Rock Wall Gossip Stone'),
    0x0413: GossipStone('Hyrule Castle (Storms Grotto)', 'Castle Storms Grotto Gossip Stone'),
    0x041B: GossipStone('Hyrule Field (Hammer Grotto)', 'Field Valley Grotto Gossip Stone'),
    0x041F: GossipStone('Kokiri Forest (Deku Tree Left)', 'Deku Tree Gossip Stone (Left)'),
    0x0420: GossipStone('Kokiri Forest (Deku Tree Right)', 'Deku Tree Gossip Stone (Right)'),
    0x041E: GossipStone('Kokiri Forest (Storms)', 'Kokiri Forest Gossip Stone'),
    0x0403: GossipStone('Lake Hylia (Lab)', 'Lake Hylia Lab Gossip Stone'),
    0x040F: GossipStone('Lake Hylia (Southeast Corner)', 'Lake Hylia Gossip Stone (Southeast)'),
    0x0408: GossipStone('Lake Hylia (Southwest Corner)', 'Lake Hylia Gossip Stone (Southwest)'),
    0x041D: GossipStone('Lost Woods (Bridge)', 'Lost Woods Gossip Stone'),
    0x0416: GossipStone('Sacred Forest Meadow (Maze Lower)', 'Sacred Forest Meadow Maze Gossip Stone (Lower)'),
    0x0417: GossipStone('Sacred Forest Meadow (Maze Upper)', 'Sacred Forest Meadow Maze Gossip Stone (Upper)'),
    0x041C: GossipStone('Sacred Forest Meadow (Saria)', 'Sacred Forest Meadow Saria Gossip Stone'),
    0x0406: GossipStone('Temple of Time (Left)', 'Temple of Time Gossip Stone (Left)'),
    0x0407: GossipStone('Temple of Time (Left-Center)', 'Temple of Time Gossip Stone (Left-Center)'),
    0x0410: GossipStone('Temple of Time (Right)', 'Temple of Time Gossip Stone (Right)'),
    0x040E: GossipStone('Temple of Time (Right-Center)', 'Temple of Time Gossip Stone (Right-Center)'),
    0x0409: GossipStone('Zoras Domain (Mweep)', 'Zoras Domain Gossip Stone'),
    0x0401: GossipStone('Zoras Fountain (Fairy)', 'Zoras Fountain Fairy Gossip Stone'),
    0x0402: GossipStone('Zoras Fountain (Jabu)', 'Zoras Fountain Jabu Gossip Stone'),
    0x040D: GossipStone('Zoras River (Plateau)', 'Zoras River Plateau Gossip Stone'),
    0x040C: GossipStone('Zoras River (Waterfall)', 'Zoras River Waterfall Gossip Stone'),
}


def buildHintString(hintString):
    if len(hintString) < 77:
        hintString = "They say that " + hintString
    elif len(hintString) < 82:
        hintString = "They say " + hintString
    # captitalize the sentance
    hintString = hintString[:1].upper() + hintString[1:]

    return hintString


def getItemGenericName(item):
    if item.type == 'Map' or item.type == 'Compass' or item.type == 'BossKey' or item.type == 'SmallKey' or item.type == 'FortressSmallKey':
        return item.type
    else:
        return item.name


def isRestrictedDungeonItem(dungeon, item):
    if (item.map or item.compass) and dungeon.world.shuffle_mapcompass == 'dungeon':
        return item in dungeon.dungeon_items
    if item.smallkey and dungeon.world.shuffle_smallkeys == 'dungeon':
        return item in dungeon.small_keys
    if item.bosskey and dungeon.world.shuffle_bosskeys == 'dungeon':
        return item in dungeon.boss_key
    return False


def add_hint(worlds, world, IDs, text, count, location=None):
    random.shuffle(IDs)
    skipped_ids = []
    first = True
    while random.random() < count:
        if IDs:
            id = IDs.pop(0)
            stone_location = gossipLocations[id].location
            if not first or can_reach_stone(worlds, stone_location, location):
                if first and location:
                    old_rule = location.access_rule
                    location.access_rule = lambda state: state.can_reach(stone_location, resolution_hint='Location') and old_rule(state)

                count -= 1
                first = False
                world.spoiler.hints[id] = lineWrap(text)
            else:
                skipped_ids.append(id)
        else:
            break
    IDs.extend(skipped_ids)


def can_reach_stone(worlds, stone_location, location):
    if location == None:
        return True

    old_item = location.item
    location.item = None
    stone_states = CollectionState.get_states_with_items([world.state for world in worlds], [])
    location.item = old_item

    return stone_states[location.world.id].can_reach(stone_location, resolution_hint='Location') and \
           stone_states[location.world.id].guarantee_hint()


def writeGossipStoneHintsHints(world, messages):
    for id,text in world.spoiler.hints.items():
        update_message_by_id(messages, id, get_raw_text(text))

def filterTrailingSpace(text):
    if text.endswith('& '):
        return text[:-1]
    else:
        return text

hintPrefixes = [
    'a few ',
    'some ',
    'plenty of ',
    'a ',
    'an ',
    'the ',
    '',
]

def getSimpleHintNoPrefix(item):
    hint = getHint(item.name, True).text

    for prefix in hintPrefixes:
        if hint.startswith(prefix):
            # return without the prefix
            return hint[len(prefix):]

    # no prefex
    return hint

def colorText(text, color):
    colorMap = {
        'White':      '\x40',
        'Red':        '\x41',
        'Green':      '\x42',
        'Blue':       '\x43',
        'Light Blue': '\x44',
        'Pink':       '\x45',
        'Yellow':     '\x46',
        'Black':      '\x47',
    }

    colorTags = False
    while True:
        splitText = text.split('#', 2)
        if len(splitText) == 3:
            splitText[1] = '\x05' + colorMap[color] + splitText[1] + '\x05\x40'
            text = ''.join(splitText)
            colorTags = True
        else:
            text = '#'.join(splitText)
            break

    if not colorTags:
        for prefix in hintPrefixes:
            if text.startswith(prefix):
                text = text[:len(prefix)] + '\x05' + colorMap[color] + text[len(prefix):] + '\x05\x40'
                break

    return text


def get_woth_hint(world, checked):
    locations = world.spoiler.required_locations[world.id]
    locations = list(filter(lambda location: location.name not in checked, locations))
    if not locations:
        return None

    location = random.choice(locations)
    checked.append(location.name)

    if location.parent_region.dungeon:
        return (buildHintString(colorText(getHint(location.parent_region.dungeon.name, world.clearer_hints).text, 'Light Blue') + \
            " is on the way of the hero."), location)
    else:
        return (buildHintString(colorText(location.hint, 'Light Blue') + " is on the way of the hero."), location)


def get_good_loc_hint(world, checked):
    locations = getHintGroup('location', world)
    locations = list(filter(lambda hint: hint.name not in checked, locations))
    if not locations:
        return None

    hint = random.choice(locations)
    location = world.get_location(hint.name)
    checked.append(location.name)

    return (buildHintString(colorText(getHint(location.name, world.clearer_hints).text, 'Green') + " " + \
                colorText(getHint(getItemGenericName(location.item), world.clearer_hints).text, 'Red') + "."), location)


def get_good_item_hint(world, checked):
    locations = [location for location in world.get_filled_locations()
            if not location.name in checked and \
            location.item.majoritem and \
            not location.locked]
    if not locations:
        return None

    location = random.choice(locations)
    checked.append(location.name)

    if location.parent_region.dungeon:
        return (buildHintString(colorText(getHint(location.parent_region.dungeon.name, world.clearer_hints).text, 'Green') + \
            " hoards " + colorText(getHint(getItemGenericName(location.item), world.clearer_hints).text, 'Red') + "."), location)
    else:
        return (buildHintString(colorText(getHint(getItemGenericName(location.item), world.clearer_hints).text, 'Red') + \
            " can be found at " + colorText(location.hint, 'Green') + "."), location)


def get_overworld_hint(world, checked):
    locations = [location for location in world.get_filled_locations()
            if not location.name in checked and \
            location.item.type != 'Event' and \
            location.item.type != 'Shop' and \
            not location.locked and \
            not location.parent_region.dungeon]
    if not locations:
        return None

    location = random.choice(locations)
    checked.append(location.name)

    return (buildHintString(colorText(getHint(getItemGenericName(location.item), world.clearer_hints).text, 'Red') + \
        " can be found at " + colorText(location.hint, 'Green') + "."), location)


def get_dungeon_hint(world, checked):
    dungeons = list(filter(lambda dungeon: dungeon.name not in checked, world.dungeons))
    if not dungeons:
        return None

    dungeon = random.choice(dungeons)
    checked.append(dungeon.name)

    # Choose a random dungeon location that is a non-dungeon item
    locations = [location for region in dungeon.regions for location in region.locations
        if location.name not in checked and \
           location.item and \
           location.item.type != 'Event' and \
           location.item.type != 'Shop' and \
           not isRestrictedDungeonItem(dungeon, location.item) and \
           not location.locked]
    if not locations:
        return get_dungeon_hint(world, checked)

    location = random.choice(locations)
    checked.append(location.name)

    return (buildHintString(colorText(getHint(dungeon.name, world.clearer_hints).text, 'Green') + " hoards " + \
        colorText(getHint(getItemGenericName(location.item), world.clearer_hints).text, 'Red') + "."), location)


def get_junk_hint(world, checked):
    hints = getHintGroup('junkHint', world)
    hints = list(filter(lambda hint: hint.name not in checked, hints))
    if not hints:
        return None

    hint = random.choice(hints)
    checked.append(hint.name)

    return (hint.text, None)


hint_func = {
    'trial':    lambda world, checked: None,
    'always':   lambda world, checked: None,
    'woth':     get_woth_hint,
    'loc':      get_good_loc_hint,
    'item':     get_good_item_hint,
    'ow':       get_overworld_hint,
    'dungeon':  get_dungeon_hint,
    'junk':     get_junk_hint,
}


hint_dist_sets = {
    'normal': {
        'trial':    (0.0, 1),
        'always':   (0.0, 1),
        'woth':     (3.5, 1),
        'loc':      (4.0, 1),
        'item':     (5.0, 1),
        'ow':       (2.0, 1),
        'dungeon':  (3.5, 1),
        'junk':     (3.0, 1),
    },
    'tourney': {
        'trial':    (0.0, 1),
        'always':   (0.0, 1.75),
        'woth':     (4.0, 2),
        'loc':      (2.0, 1),
        'item':     (2.0, 1),
        'ow':       (2.0, 1),
        'dungeon':  (2.0, 1),
        'junk':     (0.0, 1),
    },
}


#builds out general hints based on location and whether an item is required or not
def buildGossipHints(worlds, world):
    checkedLocations = []

    stoneIDs = list(gossipLocations.keys())
    random.shuffle(stoneIDs)

    hint_dist = hint_dist_sets[world.hint_dist]
    hint_types = list(hint_dist.keys())
    hint_prob = [prob for prob,count in hint_dist.values()]

    # Add required location hints
    alwaysLocations = getHintGroup('alwaysLocation', world)
    for hint in alwaysLocations:
        location = world.get_location(hint.name)
        checkedLocations.append(hint.name)
        add_hint(worlds, world, stoneIDs, buildHintString(colorText(getHint(location.name, world.clearer_hints).text, 'Green') + " " + \
            colorText(getHint(getItemGenericName(location.item), world.clearer_hints).text, 'Red') + "."), hint_dist['always'][1], location)

    # Add trial hints
    if world.trials_random and world.trials == 6:
        add_hint(worlds, world, stoneIDs, buildHintString(colorText("Ganon's Tower", 'Pink') + " is protected by a powerful barrier."), hint_dist['trial'][1])
    elif world.trials_random and world.trials == 0:
        add_hint(worlds, world, stoneIDs, buildHintString("Sheik dispelled the barrier around " + colorText("Ganon's Tower", 'Yellow')), hint_dist['trial'][1])
    elif world.trials < 6 and world.trials > 3:
        for trial,skipped in world.skipped_trials.items():
            if skipped:
                add_hint(worlds, world, stoneIDs, buildHintString("the " + colorText(trial + " Trial", 'Yellow') + " was dispelled by Sheik."), hint_dist['trial'][1])
    elif world.trials <= 3 and world.trials > 0:
        for trial,skipped in world.skipped_trials.items():
            if not skipped:
                add_hint(worlds, world, stoneIDs, buildHintString("the " + colorText(trial + " Trial", 'Pink') + " protects Ganon's Tower."), hint_dist['trial'][1])

    while stoneIDs:
        [hint_type] = random_choices(hint_types, weights=hint_prob)

        hint = hint_func[hint_type](world, checkedLocations)
        if hint != None:
            text, location = hint
            add_hint(worlds, world, stoneIDs, text, hint_dist[hint_type][1], location)


# builds boss reward text that is displayed at the temple of time altar for child and adult, pull based off of item in a fixed order.
def buildBossRewardHints(world, messages):
    # text that appears at altar as a child.
    bossRewardsSpiritualStones = [
        ('Kokiri Emerald',   'Green'), 
        ('Goron Ruby',       'Red'), 
        ('Zora Sapphire',    'Blue'),
    ]
    child_text = '\x08'
    child_text += getHint('Spiritual Stone Text Start', world.clearer_hints).text
    for (reward, color) in bossRewardsSpiritualStones:
        child_text += buildBossString(reward, color, world)
    child_text += getHint('Spiritual Stone Text End', world.clearer_hints).text
    child_text += '\x0B'
    update_message_by_id(messages, 0x707A, get_raw_text(child_text), 0x20)

    # text that appears at altar as an adult.
    bossRewardsMedallions = [
        ('Light Medallion',  'Light Blue'),
        ('Forest Medallion', 'Green'),
        ('Fire Medallion',   'Red'),
        ('Water Medallion',  'Blue'),
        ('Shadow Medallion', 'Pink'),
        ('Spirit Medallion', 'Yellow'),
    ]
    adult_text = '\x08'
    adult_text += getHint('Medallion Text Start', world.clearer_hints).text
    for (reward, color) in bossRewardsMedallions:
        adult_text += buildBossString(reward, color, world)
    adult_text += getHint('Medallion Text End', world.clearer_hints).text
    adult_text += '\x0B'
    update_message_by_id(messages, 0x7057, get_raw_text(adult_text), 0x20)


# pulls text string from hintlist for reward after sending the location to hintlist.
def buildBossString(reward, color, world):
    text = ''
    for location in world.get_filled_locations():
        if location.item.name == reward:
            text += '\x08\x13' + chr(location.item.code)
            text += colorText(getHint(location.name, world.clearer_hints).text, color)
    return text


# fun new lines for Ganon during the final battle
def buildGanonText(world, messages):
    # empty now unused messages to make space for ganon lines
    update_message_by_id(messages, 0x70C8, " ")
    update_message_by_id(messages, 0x70C9, " ")
    update_message_by_id(messages, 0x70CA, " ")

    # lines before battle
    text = '\x08'
    ganonLines = getHintGroup('ganonLine', world)
    random.shuffle(ganonLines)
    text = get_raw_text(ganonLines.pop().text)
    update_message_by_id(messages, 0x70CB, text)

    # light arrow hint or validation chest item
    text = '\x08'
    if world.trials == 0:
        for location in world.get_filled_locations():
            if location.item.name == 'Light Arrows':
                text = get_raw_text(getHint('Light Arrow Location', world.clearer_hints).text)
                location_hint = location.hint.replace('Ganon\'s Castle', 'my castle')
                location_hint = location.hint.replace('Ganon\'s Tower', 'my tower')
                text += get_raw_text(location_hint)
                text += '!'
                break
    else:
        text = get_raw_text(getHint('Validation Line', world.clearer_hints).text)
        for location in world.get_filled_locations():
            if location.name == 'Ganons Tower Boss Key Chest':
                text += get_raw_text(getHint(getItemGenericName(location.item), world.clearer_hints).text)
                text += '!'
                break

    update_message_by_id(messages, 0x70CC, text)

def get_raw_text(string):
    text = ''
    for char in string:
        if char == '^':
            text += '\x04' # box break
        elif char == '&':
            text += '\x01' #new line
        elif char == '@':
            text += '\x0F' #print player name
        elif char == '#':
            text += '\x05\x40' #sets color to white
        else:
            text += char
    return text
