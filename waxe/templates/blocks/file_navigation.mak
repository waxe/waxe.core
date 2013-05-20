<ul id="file-navigation" data-path="${path}">
  % for css_class, name, data_href, href in data:
    <li><a data-href="${data_href}" href="${href}" class="${css_class}">${name}</a></li>
  % endfor
</ul>
