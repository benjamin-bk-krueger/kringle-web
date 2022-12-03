# {{ world.world_name }}

[TOC]

## About KringleCon

KringleCon relates to SANS' Holiday Hacking Challenge which happens yearly around the Christmastime.

## About {{ world.world_name }}

This year's theme is: {{ world.world_desc }} - Visit {{ world.world_url }} to get more information.

![{{ world.world_name }} Logo]({{ session['s3_folder'] }}/world/{{ world.world_name }}/{{ world.world_img }})

## About this document

This document contains the report and all related scripts & code snippets that were used and/or created to solve the challenges. It has been generated using [Kringle.info](https://kringle.info).

## About the author

Hello, my name is {{ creator.creator_name }} - {{ creator.creator_desc }}.

## Document structure

**Rooms**   
Each room contains certain events (the main objectives and secondary hints). Have a look for the characters and terminals - you can talk and interact with them to get tasks and/or hints. Follow [this link](#Rooms) to see which rooms are available.

**Objectives**   
The objectives are the main tasks you have to achieve. Each objective has a different difficulty so there's always something for you. Just focus on the objectives which you feel comfortable with and keep the more difficult ones for later. This year there are {{ objectives.count() }} objectives and hints, just follow [this link](#Objectives) to get more information.

**Hints**   
The hints are somewhat secondary/side tasks you may want to achieve. On the one side they are fun and on the other side each character can give you helpful hints for the main objectives by solving his task. This year there are {{ objectives.count() }} objectives and hints, just follow [this link](#Hints) to get more information.

**Items**   
The items can be found by looking around at the Con and eventually by solving other challenges. Items can be used to help you solve further challenges/objectives.  This year there are {{ items.count() }} items, just follow [this link](#Items) to get more information.

# Rooms

Hint: Not all destinations are reachable when you start your journey. You might need to solve other challenges to unlock all possible destinations.  You can reach a destination by moving your virtual character to the given area. After you have unlocked that area it's visible in the menu and it's much faster to "teleport" by clicking on the matching entry.

{% for room in rooms %}
**{{ room.room_name }}**   

{% for objective in objectives %}{% if objective.room_id == room.room_id %}
* {{ objective.objective_title }}: **{{ objective.objective_name }}**
{% endif %}{% endfor %}
{% for item in items %}{% if item.room_id == room.room_id %}
* {{ item.item_name }}
{% endif %}{% endfor %}
{% endfor %}

[Go back to Document structure](#Document structure)

# Objectives

{% for objective in objectives %}{% if objective.difficulty > 0 %}
* [{{ objective.objective_title }}](#{{ objective.objective_title }}) **{{ objective.objective_name }}** 
{% endif %}{% endfor %}

{% for objective in objectives %}{% if objective.difficulty > 0 %}
## {{ objective.objective_title }}

**Overview**   
Requested by {{ objective.objective_name }}, {{ objective.objective_desc }}, {% for room in rooms %}{% if room.room_id == objective.room_id %}found in {{ room.room_name }}{% endif %}{% endfor %}   
Difficulty: ({{ objective.difficulty }}/5)   
Task Name: {{ objective.objective_title }}   
Challenge:   
{% if md_quests[objective.objective_id] | length < 5 %}This objective has no quest yet{% endif %}   
{{ md_quests[objective.objective_id] | safe }}   
{% if objective.objective_img != "" and objective.objective_img != "NoImage" %}<img src="{{ session['s3_folder'] }}/world/{{ world.world_name }}/{{ objective.objective_img }}" alt="{{ objective.objective_name }}" style="zoom: 33%;" />{% endif %}

**Solution**   
{% if md_solutions[objective.objective_id] | length < 5 %}This objective has no quest yet{% endif %}   
{{ md_solutions[objective.objective_id]|safe }}

[Go back to Objective list](#Objectives)

{% endif %}{% endfor %}

[Go back to Document structure](#Document structure)

# Hints

{% for objective in objectives %}{% if objective.difficulty == 0 %}
* [{{ objective.objective_title }}](#{{ objective.objective_title }}) **{{ objective.objective_name }}** 
{% endif %}{% endfor %}

{% for objective in objectives %}{% if objective.difficulty == 0 %}
## {{ objective.objective_title }}

**Overview**
Requested by {{ objective.objective_name }}, {{ objective.objective_desc }}, {% for room in rooms %}{% if room.room_id == objective.room_id %}found in {{ room.room_name }}{% endif %}{% endfor %}   
Task Name: {{ objective.objective_title }}   
Quest:   
{% if md_quests[objective.objective_id] | length < 5 %}This objective has no quest yet{% endif %}   
{{ md_quests[objective.objective_id] | safe }}   
{% if objective.objective_img != "" and objective.objective_img != "NoImage" %}<img src="{{ session['s3_folder'] }}/world/{{ world.world_name }}/{{ objective.objective_img }}" alt="{{ objective.objective_name }}" style="zoom: 33%;" />{% endif %}

**Solution**   
{% if md_solutions[objective.objective_id] | length < 5 %}This objective has no solution yet{% endif %}   
{{ md_solutions[objective.objective_id] | safe }}

[Go back to Hint list](#Hints)

{% endif %}{% endfor %}

[Go back to Document structure](#Document structure)

# Items

{% for item in items %}
* **{{ item.item_name }}**, {{ item.item_desc }}

Can be found in {% for room in rooms %}{% if room.room_id == item.room_id %}{{ room.room_name }}{% endif %}{% endfor %}   
{% for objective in objectives %}{% if objective.requires == item.item_name %}Can be used to solve the objective [{{ objective.objective_title }}](#{{ objective.objective_title }}){% endif %}{% endfor %}   
{% if item.item_img != "" and item.item_img != "NoImage" %}<img src="{{ session['s3_folder'] }}/world/{{ world.world_name }}/{{ item.item_img }}" alt="{{ item.item_name }}" style="zoom: 33%;" />{% endif %}

[Go back to Item list](#Items)

{% endfor %}

[Go back to Document structure](#Document structure)
