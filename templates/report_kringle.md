# {{ world.world_name }}

[TOC]

## About KringleCon

KringleCon relates to SANS' Holiday Hacking Challenge which happens yearly around the Christmastime.<br>
You can find more information about the event here: https://www.sans.org/mlp/holiday-hack-challenge/
<br>

## About {{ world.world_name }}

This year the theme is: {{ world.world_desc }}.<br>
Visit {{ world.world_url }} to get more information.

![{{ world.world_name }} Logo]({{ world.world_img }})
<br>

## About this document

This document contains the report and all related scripts & code snippets that were used and/or created to solve the challenges.<br>
This document has been generated using https://kringle.info.
<br>

## About the author

Hello, my name is {{ creator.creator_name }}.<br>
{{ creator.creator_desc }}
<br>

## Document-structure

**Destinations**
Each destination contains certain events (the main objectives and the secondary hints). Have a look for the characters and terminals - you can talk and interact with them to get tasks and/or hints.
Follow [this link](#Destinations) to see which destinations are available for you. 

**Objectives**
The objectives are the main tasks you have to achieve. Each objective has a different difficulty so there's always something for you. Just focus on the objectives which you feel comfortable with and keep the more difficult ones for later.

**Hints**
The hints are somewhat secondary/side tasks you may want to achieve. On the one side they are fun and on the other side each elf can give you helpful hints for the main objectives by solving his task.
This year there are {{ objectives.count() }} objectives and hints, just follow [this link](#Hints) to get more information.

**Items**
The items can be found by looking around at the Con and eventually by solving other challenges. Items can be used to help you solve further challenges/objectives.
This year there are {{ items.count() }} items, just follow [this link](#Items) to get more information.
<br>

# Destinations

[Go back](#Document-structure)

Hint: Not all destinations are reachable when you start your adventure. You might to solve challenges to unlock all possible destinations.
You can reach a destination by moving your virtual character to the given area. after you have unlocked that area, and it's visible in the menu it's much faster to "teleport" by clicking on the matching entry.

{% for room in rooms %}
**{{ room.room_name.replace(" ", "-") }}**

{% for objective in objectives %}{% if objective.room_id == room.room_id %}
* {{ objective.objective_title }}: **{{ objective.objective_name }}**
{% endif %}{% endfor %}
{% for item in items %}{% if item.room_id == room.room_id %}
* {{ item.item_name }}
{% endif %}{% endfor %}
{% endfor %}

[Go back](#Document-structure)
<br>

# Objectives

[Go back](#Document-structure)

{% for objective in objectives %}{% if objective.difficulty > 0 %}
* [{{ objective.objective_title }}](#{{ objective.objective_title.replace(" ", "-") }}) **{{ objective.objective_name }}** 
{% endif %}{% endfor %}

[Go back](#Document-structure)
<br>

{% for objective in objectives %}{% if objective.difficulty > 0 %}
## {{ objective.objective_title.replace(" ", "-") }}

[Go back](#Objectives)

**Overview**
Requested by {{ objective.objective_name }}, {{ objective.objective_desc }}, {% for room in rooms %}{% if room.room_id == objective.room_id %}found in {{ room.room_name }}{% endif %}{% endfor %}
<br>
Difficulty: ({{ objective.difficulty }}/5)
Task Name: {{ objective.objective_title }}
Quest: 
{% if md_quests[objective.objective_id] | length < 5 %}This objective has no quest yet{% endif %}
{{ md_quests[objective.objective_id]|safe }}
{% if objective.objective_img != "" %}<img src="{{ objective.objective_img }}" alt="{{ objective.iobjective_name }}" style="zoom: 33%;" />{% endif %}

**Solution**
{% if md_solutions[objective.objective_id] | length < 5 %}This objective has no quest yet{% endif %}
{{ md_solutions[objective.objective_id]|safe }}

[Go back](#Objectives)
<br>
{% endif %}{% endfor %}
<br>

# Hints

[Go back](#Document-structure)

{% for objective in objectives %}{% if objective.difficulty == 0 %}
* [{{ objective.objective_title }}](#{{ objective.objective_title.replace(" ", "-") }}) **{{ objective.objective_name }}** 
{% endif %}{% endfor %}

[Go back](#Document-structure)
<br>

{% for objective in objectives %}{% if objective.difficulty == 0 %}
## {{ objective.objective_title.replace(" ", "-") }}

[Go back](#Hints)

**Overview**
Requested by {{ objective.objective_name }}, {{ objective.objective_desc }}, {% for room in rooms %}{% if room.room_id == objective.room_id %}found in {{ room.room_name }}{% endif %}{% endfor %}
<br>
Task Name: {{ objective.objective_title }}
Quest: 
{% if md_quests[objective.objective_id] | length < 5 %}This objective has no quest yet{% endif %}
{{ md_quests[objective.objective_id]|safe }}
{% if objective.objective_img != "" %}<img src="{{ objective.objective_img }}" alt="{{ objective.iobjective_name }}" style="zoom: 33%;" />{% endif %}

**Solution**
{% if md_solutions[objective.objective_id] | length < 5 %}This objective has no solution yet{% endif %}
{{ md_solutions[objective.objective_id]|safe }}

[Go back](#Hints)
<br>
{% endif %}{% endfor %}
<br>

# Items

[Go back](#Document-structure)

{% for item in items %}
* **{{ item.item_name }}**, {{ item.item_desc }}

Can be found in {% for room in rooms %}{% if room.room_id == item.room_id %}{{ room.room_name }}{% endif %}{% endfor %}
{% for objective in objectives %}{% if objective.requires == item.item_name %}Can be used to solve the objective [{{ objective.objective_title }}](#{{ objective.objective_title.replace(" ", "-") }}){% endif %}{% endfor %}
{% if item.item_img != "" %}<img src="{{ item.item_img }}" alt="{{ item.item_name }}" style="zoom: 33%;" />{% endif %}
<br>
{% endfor %}

[Go back](#Document-structure)
<br>