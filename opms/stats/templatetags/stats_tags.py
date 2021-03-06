#from django import template
#from django.utils.safestring import mark_safe
#
#register = template.Library()
#
#@register.simple_tag
#def submenu(current_section=0):
#    menu_html = u'''<h3>Sub sections for Statistics</h3>
#    <ul class="level-2">'''
#    if int(current_section) == 1:
#        menu_html += '<li><span class="youarehere">iTU-Summary</span></li>\n'
#    else:
#        menu_html += '<li><a href="/stats/report/summary/">iTU-Summary</a></li>\n'
#    if int(current_section) == 2:
#        menu_html += '<li><span class="youarehere">Feeds</span></li>\n'
#    else:
#        menu_html += '<li><a href="/stats/report/summary/feeds/">Feeds</a></li>\n'
#    if int(current_section) == 3:
#        menu_html += '<li><span class="youarehere">Contributors</span></li>\n'
#    else:
#        menu_html += '<li><a href="/stats/report/authors/">Contributors</a></li>\n'
#    if int(current_section) == 4:
#        menu_html += '<li><span class="youarehere">URL-Monitor</span></li>\n'
#    else:
#        menu_html += '<li><a href="/stats/report/urlmonitoring/">URL-Monitor</a></li>\n'
#    menu_html += '</ul>'
#    return mark_safe(menu_html)