# {{ world.world_name }}

[TOC]

## About {{ world.world_name }}

{{ world.world_desc }}<br>
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

**Rooms**
Each room contains certain challenges.
Follow [this link](#Rooms) to see which rooms are available.

**Challenges**
The challenges are the main tasks you have to achieve.
<br>

# Rooms

[Go back](#Document-structure)

{% for room in rooms %}
**{{ room.room_name.replace(" ", "-") }}**

{% for objective in objectives %}{% if objective.room_id == room.room_id %}
* {{ objective.objective_title }}: **{{ objective.objective_name }}**
{% endif %}{% endfor %}
{% endfor %}

[Go back](#Document-structure)
<br>

# Challenges

[Go back](#Document-structure)

{% for objective in objectives %}{% if objective.difficulty > 0 %}
* [{{ objective.objective_title }}](#{{ objective.objective_title.replace(" ", "-") }}) **{{ objective.objective_name }}** 
{% endif %}{% endfor %}

[Go back](#Document-structure)
<br>

{% for objective in objectives %}
## {{ objective.objective_title.replace(" ", "-") }}

[Go back](#Challenges)

**Overview**
Difficulty: ({{ objective.difficulty }})
Task Name: {{ objective.objective_title }}
Challenge: 
{% if md_quests[objective.objective_id] | length < 5 %}This challenge has no description yet.{% endif %}
{{ md_quests[objective.objective_id]|safe }}
{% if objective.objective_img != "" %}<img src="{{ objective.objective_img }}" alt="{{ objective.iobjective_name }}" style="zoom: 33%;" />{% endif %}

**Solution**
{% if md_solutions[objective.objective_id] | length < 5 %}This challenges has no solution yet.{% endif %}
{{ md_solutions[objective.objective_id]|safe }}

[Go back](#Challenges)
<br>
{% endfor %}
<br>
