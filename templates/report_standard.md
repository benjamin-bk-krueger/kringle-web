# {{ world.world_name }}

[TOC]

## About {{ world.world_name }}

{{ world.world_desc }}  
Visit {{ world.world_url }} to get more information.

![{{ world.world_name }} Logo]({{ session['s3_folder'] }}/world/{{ world.world_name }}/{{ world.world_img }})

## About this document

This document contains the report and all related scripts & code snippets that were used and/or created to solve the challenges.  
It has been generated using [Kringle.info](https://kringle.info).

## About the author

Document creator: {{ creator.creator_name }}.  
{{ creator.creator_desc }}

## Document structure

**Rooms**   
Each room contains certain challenges.  
Follow [this link](#Rooms) to see which rooms are available.

**Challenges**   
The challenges are the main tasks you have to achieve.  
Follow [this link](#Challenges) to see which challenges are available.

# Rooms

{% for room in rooms %}
**{{ room.room_name }}**   

{% for objective in objectives %}{% if objective.room_id == room.room_id %}
* {{ objective.objective_title }}: **{{ objective.objective_name }}**
{% endif %}{% endfor %}
{% endfor %}

[Go back to Document structure](#Document-structure)

# Challenges

{% for objective in objectives %}
* [{{ objective.objective_title }}](#{{ objective.objective_title.replace(" ", "-") }}) **{{ objective.objective_name }}** 
{% endfor %}

{% for objective in objectives %}
## {{ objective.objective_title }}

**Overview**   
Difficulty: ({{ objective.difficulty }})   
Task Name: {{ objective.objective_title }}   

**Challenge**   
{% if md_quests[objective.objective_id] | length < 5 %}This challenge has no description yet.{% endif %}   
{{ md_quests[objective.objective_id] | safe }}   
{% if objective.objective_img != "" and objective.objective_img != "NoImage" %}<img src="{{ session['s3_folder'] }}/world/{{ world.world_name }}/{{ objective.objective_img }}" alt="{{ objective.objective_name }}" style="zoom: 33%;" />{% endif %}

**Solution**   
{% if md_solutions[objective.objective_id] | length < 5 %}This challenges has no solution yet.{% endif %}   
{{ md_solutions[objective.objective_id] | safe }}

[Go back to Challenge list](#Challenges)

{% endfor %}

[Go back to Document structure](#Document-structure)
