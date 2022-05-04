---
layout: archive
title: "Research"
permalink: research/
author_profile: true
---

Kunkel, Sky. "Double Delegation: An Investigation of the UN Use of Private Security Contractors." <i>Working Paper</i>.


{% if author.googlescholar %}
  You can also find my articles on <u><a href="{{author.googlescholar}}">my Google Scholar profile</a>.</u>
{% endif %}

{% include base_path %}

{% for post in site.publications reversed %}
  {% include archive-single.html %}
{% endfor %}
