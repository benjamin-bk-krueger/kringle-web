# {{ objective.objective_title }}

**Overview**   
Difficulty: ({{ objective.difficulty }})   
Task Name: {{ objective.objective_name }}   
Challenge:   
{% if md_quest | length < 5 %}This challenge has no description yet.{% endif %}   
{{ md_quest | safe }}   
{% if objective.objective_img != "" and objective.objective_img != "NoImage" %}<img src="{{ session['s3_folder'] }}/world/{{ world.world_name }}/{{ objective.objective_img }}" alt="{{ objective.objective_name }}" style="zoom: 33%;" />{% endif %}

**Solution**   
{% if md_solution | length < 5 %}This challenges has no solution yet.{% endif %}   
{{ md_solution | safe }}
