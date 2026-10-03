{%- macro sep(loop) -%}{% if loop.revindex == 2 %}{{ ',' if loop.length > 2 }} and {% elif not loop.last %}, {% endif %}{%- endmacro -%}
<!-- Answer key, Appendix A (for instructors; HTML comments are removed from every rendered format):
     1 D, 2 B, 3 C, 4 D, 5 A, 6 C, 7 A, 8 B.
     1 D: a rule filters its table and, through active relationships, the tables on the many side.
     2 B: row-level security applies to Viewers and app readers, not to Admin, Member, or Contributor.
     3 C: managers of record {{ terminated|join(', ') }} are terminated; the {% for a in actual %}{{ a.center }}{{ sep(loop) }}{% endfor %} Managers are not recorded.
     4 D: deny by default; a user in the role but missing from the table sees no sales (and no cost centers).
     5 A: object-level security hides tables and columns from a role; row-level security hides rows.
     6 C: Publish to web needs no sign-in, exposes all the model's data, and does not support row-level security.
     7 A: a local file is an on-premises source; a gateway (or moving the file to OneDrive or SharePoint) is needed.
     8 B: no setting secures a page by role, and app audiences show whole reports, so finance's pages go in a separate report;
          on the pages managers keep, a card naming the cost centers shown tells them what they see. A hidden page can still be
          reached, so hiding it is not security. -->