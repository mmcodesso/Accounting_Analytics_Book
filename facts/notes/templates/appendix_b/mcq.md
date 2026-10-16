{%- macro sep(loop) -%}{% if loop.revindex == 2 %}{{ ',' if loop.length > 2 }} and {% elif not loop.last %}, {% endif %}{%- endmacro -%}
<!-- Answer key, Appendix B (for instructors; HTML comments are removed from every rendered format):
     1 D, 2 B, 3 C, 4 D, 5 A, 6 C, 7 A, 8 B.
     1 D: a rule filters its table and, through active relationships, the tables on the many side.
     2 B: row-level security applies to Viewers and app readers, not to Admin, Member, or Contributor, and a person in several
          groups gets the highest role any of them holds.
     3 C: managers of record {{ terminated|join(', ') }} are terminated; the {% for a in actual %}{{ a.center }}{{ sep(loop) }}{% endfor %} Managers are not recorded.
     4 D: the rule is true for every item or for none, so a user in the role but missing from the table sees no sales and no
          cost centers, while a table no rule reaches, such as Customer, stays readable.
     5 A: object-level security hides tables and columns from a role; row-level security hides rows.
     6 C: Publish to web needs no sign-in, exposes all the model's data, and does not support row-level security.
     7 A: a local file is an on-premises source, so the service needs a gateway that can reach it (queries connected to the
          workbook's address in OneDrive or SharePoint need none, but a copy in a synced local folder is still a local file).
     8 B: no setting secures a page by role, and app audiences show whole reports, so finance's pages go in a separate report,
          hidden from the managers' audience, with the managers reading the app without a workspace role, because an audience
          cannot hide an item from someone who holds one. On the pages managers keep, a card naming the cost centers shown tells
          them what they see. A hidden page can still be reached, so hiding it is not security. -->