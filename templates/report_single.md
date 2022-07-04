# {{ objective.objective_title.replace(" ", "-") }}

**Overview**
Difficulty: ({{ objective.difficulty }})
Task Name: {{ objective.objective_title }}
Challenge: 
{% if md_quest | length < 5 %}This challenge has no description yet.{% endif %}
{{ md_quest|safe }}
{% if objective.objective_img != "" %}<img src="{{ objective.objective_img }}" alt="{{ objective.iobjective_name }}" style="zoom: 33%;" />{% endif %}

**Solution**
{% if md_solution | length < 5 %}This challenges has no solution yet.{% endif %}
{{ md_solution|safe }}

<br>
