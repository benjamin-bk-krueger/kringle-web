# {{ world.world_name }}

[TOC]

## About KringleCon

KringleCon relates to SANS' Holiday Hacking Challenge which happens yearly around the Christmas time. You can find more information about the event here: https://www.sans.org/mlp/holiday-hack-challenge/

## About {{ world.world_name }}

This year the theme is: {{ world.world_desc }}. Visit {{ world.world_url }} to get more information.
![{{ world.world_name }} Logo]({{ world.world_img }})

## About this document

This document contains the report and all related scripts & code snippets I have used and/or created to solve the challenges. The document has been written in GitHub flavored markdown  and exported to PDF for easier delivery.
When the log files or output contains too much output I have removed that passages (".." as indicator).
I wasn't able to polish this document until 04. of January but I'll update it later when there is some time.

## About the author

Hello, my name is Ben. I'm a Cyber Security Fanatic and Generic IT Fairy. I love solving puzzles, doing CTFs and trying out new stuff. Sadly I have to do all this in my free time which is quite limited :(
You can reach me here: http://blk.pm

## Document structure

**Story**
Each Holiday Hack Challenge has a certain story you can unlock by solving the challenges.
Follow [this link](#Story) to review the full story.

**Destinations**
This year we have two competing conventions, the KringleCon (hosted by Santa) on the one side and the FrostFest (hosted by Jack Frost).
Each destination contains certain events (the main objectives and the secondary hints). Have a look for the elves and terminals - you can talk and interact with them to get tasks and/or hints.
Follow [this link](#Destinations) to see which destinations are available for you. 

**Objectives**
The objectives are the main tasks you have to achieve. Each objective has a different difficulty so there's always something for you. Just focus on the objectives which you feel comfortable with and keep the more difficult ones for later.
This year there are 13 objectives, just follow [this link](#Objectives) to get more information.

**Hints**
The hints are somewhat secondary/side tasks you may want to achieve. On the one side they are fun and on the other side each elf can give you helpful hints for the main objectives by solving his task.
This year there are 43 hints, just follow [this link](#Hints) to get more information.

**Items**
The items can be found by looking around at the Con and eventually by solving other challenges. Items can be used to help you solve further challenges/objectives.
This year there a 2 items, just follow [this link](#Items) to get more information.

# Story

[Go back](#Document-structure)

<div align="center">Listen children to a story that was written in the cold</div>
<div align="center">'Bout a Kringle and his castle hosting hackers, meek and bold</div>
<div align="center">Then from somewhere came another, built his tower tall and proud</div>
<div align="center">Surely he, our Frosty villain hides intentions 'neath a shroud</div>
<div align="center">So begins Jack's reckless mission: gather trolls to win a war</div>
<div align="center">Build a con that's fresh and shiny, has this yet been done before?</div>
<div align="center">Is his Fest more feint than folly? Some have noticed subtle clues</div>
<div align="center">Running 'round and raiding repos, stealing Santa's Don'ts and Do's</div>
<div align="center">Misdirected, scheming, grasping, Frost intends to seize the day</div>
<div align="center">Funding research with a gift shop, can Frost build the better sleigh?</div>
<div align="center">Lo, we find unlikely allies: trolls within Jack's own command</div>
<div align="center">Doubting Frost and searching motive, questioning his dark demand</div>
<div align="center">Is our Jack just lost and rotten - one more outlaw stomping toes?</div>
<div align="center">Why then must we piece together cludgy, wacky radios?</div>
<div align="center">With this object from the heavens, Frost must know his cover's blown</div>
<div align="center">Hearkening from distant planet! We the heroes should have known</div>
<div align="center">Go ahead and hack your neighbor, go ahead and phish a friend</div>
<div align="center">Do it in the name of holidays, you can justify it at year's end</div>
<div align="center">There won't be any retweets praising you, come disclosure day</div>
<div align="center">But on the snowy evening after? Still Kris Kringle rides the sleigh</div>

[Go back](#Document-structure)

# Destinations

[Go back](#Document-structure)

Hint: Not all destinations are reachable when you start your KringleCon / FrostFest adventure. You might to solve challenges to unlock all possible destinations.
You can reach a destination by moving your virtual character to the given area. after you have unlocked that area and it's visible in the menu it's much faster to "teleport" by clicking on the matching entry.

## Overview

|                |Destination                          |
|----------------|-------------------------------|
|The North Pole	 |Orientation<br>The North Pole |
|KringleCon      |Entry<br>Dining Room<br>Great Room<br>Kitchen<br>Courtyard<br>Talks Lobby<br>Speaker UNpreparation Room<br>Santa's Office<br>NetWars |
|FrostFest       | Frost Tower Lobby<br>Jack's Studio<br>Jack's Office<br>Jack's Restroom<br>Frost Tower Gift Shop<br>Frost Tower Rooftop<br>Talks Lobby<br>The Third Kind |

## Detailed list

**The North Pole - Orientation**

* Elf/Terminal Jingle Ringford: **Objective 1** KringleCon Orientation
* Items WiFi Dongle

**The North Pole - The North Pole**

* Elf/Terminal Noel Boetie: Hint Logic Munchers
* Troll Grimy McTrolkins: **Objective 3** Thaw Frost Tower's Entrance
* Troll/Terminal Greasy GopherGuts: Hint Grepping for Gold
* Side Figures Santa and the pigeons, Jack Frost

**KringleCon - Entry**
* Elf/Terminal Fitzy Shortstack: Hint Yara Analysis
* Side Figures Santa, Sparkle Redburry

**KringleCon - Dining Room**
* Elf/Terminal Ribb Bonbowford: Hint The Elf Code

**KringleCon - Great Room**

* Elf/Terminal Angel Candysalt: **Objective 9** Splunk!

**KringleCon - Kitchen**
* Elf/Terminal Tinsel Upatree: Hint Strace Ltrace Retrace

**KringleCon - Courtyard**
* Elf/Terminal Tangle Coalbox: **Objective 2** Where in the World is Caramel Santiago?
* Elf/Terminal Piney Sappington: Hint Exif Metadata
* Side Figures Cyberus, Sponsors

**KringleCon - Talks Lobby**
* Elf/Terminal Jewel Loggins: Hint IPv6 Sandbox

**KringleCon - Speaker UNpreparation Room**

* Elf/Terminal Morcel Nougat: **Objective 5** Strange USB Device

**KringleCon - Santa’s Office**
* Elf/Terminal Eve Snowshoes: Hint HoHo ... No

**KringleCon - NetWars**
* Elf/Terminal Chimney Scissorsticks: Hint Holiday Hero game

**FrostFest - Frost Tower Lobby**

* Troll/Terminal Hubris Selfington: **Objective 4** Slot Machine Investiation
* Troll Grody Goiterson: Hint Broken Elevator
* Side Figures Jack Frost

**FrostFest - Jack’s Studio**

* Troll/Terminal Ingreta Tude: **Objective 12** Frost Tower Website Checkup 

**FrostFest - Jack’s Office**

* Troll/Terminal Ruby Oyster: **Objective 6** Shellcode Primer
* Device Printer: **Objective 7** Printer Exploitation

**FrostFest - Jack’s Restroom**
* Troll/Terminal Noxious O D'or: Hint IMDS Exploration

**FrostFest - Frost Tower Gift Shop**
* Side Figures Jack Frost

**FrostFest - Frost Tower Rooftop**

* Troll/Terminal Crunchy Squishter: **Objective 13** FPGA Programming
* Side Figures Rose Mold, Numby Chilblain
* Items FPGA

**FrostFest - Talks Lobby**

* Troll Pat Tronizer: **Objective 10** Now Hiring!

**FrostFest - The Third Kind**
* Side Figures Jack Frost, Santa, Buttercup, Icy Sickles, Erin Fection

[Go back](#Document-structure)

# Objectives

[Go back](#Document-structure)

{% for objective in objectives %}{% if objective.difficulty > 0 %}
* [{{ objective.objective_title }}](#Hints-for-{{ objective.objective_title }}) **{{ objective.objective_name }}** 
{% endif %}{% endfor %}

[Go back](#Document-structure)

{% for objective in objectives %}{% if objective.difficulty > 0 %}
## Objective {{ objective.objective_title }}

[Go back](#Objectives)

**Overview**
Requested by {{ objective.objective_name }}, {{ objective.objective_desc }}, found in [{{ rooms[objective.room_id].room_name }}]({{ rooms[objective.room_id].room_name }})
<br>
Difficulty: ({{ objective.difficulty }}/5)
Task Name: TBD
{{ mdquests[objective.objective_id]|safe }}

{% if objective.objective_img != "" %}<img src="{{ objective.objective_img }}" alt="{{ objective.iobjective_name }}" style="zoom: 33%;" />{% endif %}

**Solution**
{{ mdsolutions[objective.objective_id]|safe }}

[Go back](#Objectives)
{% endif %}{% endfor %}

# Hints

[Go back](#Document-structure)

{% for objective in objectives %}{% if objective.difficulty == 0 %}
* [{{ objective.objective_title }}](#Hints-for-{{ objective.objective_title }}) **{{ objective.objective_name }}** 
{% endif %}{% endfor %}

[Go back](#Document-structure)

{% for objective in objectives %}{% if objective.difficulty == 0 %}
## Hints for {{ objective.objective_title }}

[Go back](#Hints)

**Overview**
Requested by {{ objective.objective_name }}, {{ objective.objective_desc }}, found in [{{ rooms[objective.room_id].room_name }}]({{ rooms[objective.room_id].room_name }})
<br>
Task Name: Exifdate
Description: 
{{ mdquests[objective.objective_id]|safe }}

{% if objective.objective_img != "" %}<img src="{{ objective.objective_img }}" alt="{{ objective.iobjective_name }}" style="zoom: 33%;" />{% endif %}

**Solution**
{{ mdsolutions[objective.objective_id]|safe }}

[Go back](#Hints)
{% endif %}{% endfor %}

# Items

[Go back](#Document-structure)

{% for item in items %}
* {{ item.item_name }} **{{ item.item_desc }}**

Can be found in [{{ rooms[item.room_id].room_name }}]({{ rooms[item.room_id].room_name }})
{% for objective in objectives %}{% if objective.requires == item.item_name %}Can be used to solve the objective [{{ objective.objective_title }}]({{ objective.objective_title }}){% endif %}{% endfor %}
{% if item.item_img != "" %}<img src="{{ item.item_img }}" alt="{{ item.item_name }}" style="zoom: 33%;" />{% endif %}
{% endfor %}

[Go back](#Document-structure)
